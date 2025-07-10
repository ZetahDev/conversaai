"""
Sistema de rate limiting para controlar la frecuencia de requests
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        # Almacenar requests por IP y por usuario
        # Estructura: {key: deque(timestamps)}
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.user_requests: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Configuración de límites
        self.limits = {
            # Límites por IP (por minuto)
            "ip_per_minute": 60,
            "ip_per_hour": 1000,
            
            # Límites por usuario autenticado (por minuto)
            "user_per_minute": 100,
            "user_per_hour": 2000,
            
            # Límites especiales para operaciones específicas
            "create_chatbot_per_minute": 10,
            "update_chatbot_per_minute": 20,
            "delete_chatbot_per_minute": 5,
            
            # Límites para usuarios no autenticados
            "anonymous_per_minute": 20,
            "anonymous_per_hour": 200
        }
        
        # Ventanas de tiempo en segundos
        self.windows = {
            "minute": 60,
            "hour": 3600
        }
        
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
    
    def _clean_old_requests(self, request_queue: deque, window_seconds: int):
        """Limpiar requests antiguos fuera de la ventana de tiempo"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        while request_queue and request_queue[0] < cutoff_time:
            request_queue.popleft()
    
    async def _check_limit(
        self, 
        key: str, 
        request_queue: deque, 
        limit: int, 
        window_seconds: int,
        limit_name: str
    ) -> bool:
        """Verificar si se ha excedido el límite"""
        async with self._lock:
            # Limpiar requests antiguos
            self._clean_old_requests(request_queue, window_seconds)
            
            # Verificar límite
            if len(request_queue) >= limit:
                logger.warning(f"Rate limit exceeded for {key}: {len(request_queue)}/{limit} {limit_name}")
                return False
            
            # Agregar request actual
            request_queue.append(time.time())
            return True
    
    async def check_ip_limit(self, ip: str) -> bool:
        """Verificar límites por IP"""
        ip_queue = self.ip_requests[ip]
        
        # Verificar límite por minuto
        if not await self._check_limit(
            ip, ip_queue, 
            self.limits["ip_per_minute"], 
            self.windows["minute"],
            "requests per minute"
        ):
            return False
        
        # Verificar límite por hora
        if not await self._check_limit(
            ip, ip_queue, 
            self.limits["ip_per_hour"], 
            self.windows["hour"],
            "requests per hour"
        ):
            return False
        
        return True
    
    async def check_user_limit(self, user_id: str, operation: Optional[str] = None) -> bool:
        """Verificar límites por usuario"""
        user_queue = self.user_requests[user_id]
        
        # Verificar límite general por minuto
        if not await self._check_limit(
            user_id, user_queue,
            self.limits["user_per_minute"],
            self.windows["minute"],
            "user requests per minute"
        ):
            return False
        
        # Verificar límite general por hora
        if not await self._check_limit(
            user_id, user_queue,
            self.limits["user_per_hour"],
            self.windows["hour"],
            "user requests per hour"
        ):
            return False
        
        # Verificar límites específicos por operación
        if operation:
            operation_key = f"{user_id}_{operation}"
            operation_queue = self.user_requests[operation_key]
            
            operation_limit_key = f"{operation}_per_minute"
            if operation_limit_key in self.limits:
                if not await self._check_limit(
                    operation_key, operation_queue,
                    self.limits[operation_limit_key],
                    self.windows["minute"],
                    f"{operation} per minute"
                ):
                    return False
        
        return True
    
    async def check_anonymous_limit(self, ip: str) -> bool:
        """Verificar límites para usuarios no autenticados"""
        anon_key = f"anon_{ip}"
        anon_queue = self.user_requests[anon_key]
        
        # Verificar límite por minuto
        if not await self._check_limit(
            anon_key, anon_queue,
            self.limits["anonymous_per_minute"],
            self.windows["minute"],
            "anonymous requests per minute"
        ):
            return False
        
        # Verificar límite por hora
        if not await self._check_limit(
            anon_key, anon_queue,
            self.limits["anonymous_per_hour"],
            self.windows["hour"],
            "anonymous requests per hour"
        ):
            return False
        
        return True
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del rate limiter"""
        current_time = time.time()
        
        stats = {
            "active_ips": len(self.ip_requests),
            "active_users": len(self.user_requests),
            "total_requests_last_minute": 0,
            "total_requests_last_hour": 0,
            "top_ips": [],
            "top_users": []
        }
        
        # Contar requests en la última hora
        cutoff_minute = current_time - 60
        cutoff_hour = current_time - 3600
        
        ip_counts = {}
        user_counts = {}
        
        for ip, queue in self.ip_requests.items():
            recent_requests = [req for req in queue if req > cutoff_minute]
            hour_requests = [req for req in queue if req > cutoff_hour]
            
            stats["total_requests_last_minute"] += len(recent_requests)
            stats["total_requests_last_hour"] += len(hour_requests)
            
            if hour_requests:
                ip_counts[ip] = len(hour_requests)
        
        for user, queue in self.user_requests.items():
            if not user.startswith("anon_"):
                hour_requests = [req for req in queue if req > cutoff_hour]
                if hour_requests:
                    user_counts[user] = len(hour_requests)
        
        # Top IPs y usuarios
        stats["top_ips"] = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        stats["top_users"] = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return stats
    
    async def cleanup_old_data(self):
        """Limpiar datos antiguos periódicamente"""
        current_time = time.time()
        cutoff_time = current_time - self.windows["hour"]
        
        async with self._lock:
            # Limpiar IPs
            for ip in list(self.ip_requests.keys()):
                self._clean_old_requests(self.ip_requests[ip], self.windows["hour"])
                if not self.ip_requests[ip]:
                    del self.ip_requests[ip]
            
            # Limpiar usuarios
            for user in list(self.user_requests.keys()):
                self._clean_old_requests(self.user_requests[user], self.windows["hour"])
                if not self.user_requests[user]:
                    del self.user_requests[user]

# Instancia global del rate limiter
rate_limiter = RateLimiter()

# Función helper para obtener IP del cliente
def get_client_ip(request: Request) -> str:
    """Obtener la IP del cliente desde el request"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

# Dependency para verificar rate limits
async def check_rate_limit(
    request: Request,
    operation: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Dependency para verificar rate limits en endpoints"""
    client_ip = get_client_ip(request)
    
    # Verificar límite por IP
    if not await rate_limiter.check_ip_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests from this IP address. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    # Verificar límites por usuario si está autenticado
    if user_id:
        if not await rate_limiter.check_user_limit(user_id, operation):
            raise HTTPException(
                status_code=429,
                detail="Too many requests from this user. Please try again later.",
                headers={"Retry-After": "60"}
            )
    else:
        # Verificar límites para usuarios anónimos
        if not await rate_limiter.check_anonymous_limit(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please authenticate or try again later.",
                headers={"Retry-After": "60"}
            )


# Decorator para aplicar rate limiting a endpoints específicos
def rate_limit(operation: Optional[str] = None):
    """Decorator para aplicar rate limiting a endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Buscar Request y current_user en los argumentos
            request = None
            current_user = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, dict) and "email" in arg:
                    current_user = arg

            for key, value in kwargs.items():
                if key == "request" and isinstance(value, Request):
                    request = value
                elif key == "current_user" and isinstance(value, dict):
                    current_user = value

            if request:
                user_id = None
                if current_user:
                    user_id = current_user.get("sub") or current_user.get("id")

                await check_rate_limit(request, operation, user_id)

            return await func(*args, **kwargs)
        return wrapper
    return decorator
