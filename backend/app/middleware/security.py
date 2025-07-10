"""
Middleware de seguridad para la aplicación
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import ipaddress
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware de seguridad general"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_storage = defaultdict(lambda: deque())
        self.blocked_ips = set()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Obtener IP del cliente
        client_ip = self.get_client_ip(request)
        
        # Verificar IP bloqueada
        if client_ip in self.blocked_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "IP address blocked"}
            )
        
        # Rate limiting básico
        if self.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # Agregar headers de seguridad
        response = await call_next(request)
        
        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Tiempo de procesamiento
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Obtener IP real del cliente"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def is_rate_limited(self, client_ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """Rate limiting simple por IP"""
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Limpiar requests antiguos
        requests = self.rate_limit_storage[client_ip]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Verificar límite
        if len(requests) >= max_requests:
            return True
        
        # Agregar request actual
        requests.append(now)
        return False

class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para CORS seguro"""
    
    def __init__(self, app: ASGIApp, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "http://localhost:4321",
            "https://yourdomain.com"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # Procesar request
        response = await call_next(request)
        
        # Configurar CORS solo para orígenes permitidos
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Max-Age"] = "86400"
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"in {process_time:.4f}s"
        )
        
        return response

class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware para detectar intentos de SQL injection"""
    
    SQL_INJECTION_PATTERNS = [
        "union select",
        "drop table",
        "delete from",
        "insert into",
        "update set",
        "exec(",
        "execute(",
        "sp_",
        "xp_",
        "'; --",
        "' or '1'='1",
        "' or 1=1",
        "admin'--",
        "admin'/*"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar query parameters
        query_string = str(request.url.query).lower()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern in query_string:
                logger.warning(f"SQL injection attempt detected from {request.client.host}: {pattern}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request"}
                )
        
        # Verificar body si es JSON
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.body()
                body_str = body.decode().lower()
                for pattern in self.SQL_INJECTION_PATTERNS:
                    if pattern in body_str:
                        logger.warning(f"SQL injection attempt in body from {request.client.host}: {pattern}")
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Invalid request"}
                        )
            except:
                pass
        
        return await call_next(request)

class SessionSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para seguridad de sesiones"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.active_sessions = {}  # En producción usar Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar si es un endpoint protegido
        if self.is_protected_endpoint(request.url.path):
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
                # Verificar si el token está en sesiones activas
                # En una implementación completa, verificar contra Redis
                pass
        
        response = await call_next(request)
        
        # Configurar cookies seguras
        if "Set-Cookie" in response.headers:
            cookie_value = response.headers["Set-Cookie"]
            if "Secure" not in cookie_value:
                response.headers["Set-Cookie"] = f"{cookie_value}; Secure; HttpOnly; SameSite=Strict"
        
        return response
    
    def is_protected_endpoint(self, path: str) -> bool:
        """Verificar si el endpoint requiere autenticación"""
        protected_paths = [
            "/api/v1/chatbots",
            "/api/v1/integrations",
            "/api/v1/notifications",
            "/api/v1/dashboard",
            "/api/v1/analytics"
        ]
        return any(path.startswith(protected) for protected in protected_paths)
