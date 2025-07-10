"""
Sistema de caché en memoria para mejorar el rendimiento
"""
import asyncio
import json
import time
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> Any:
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value

class MemoryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
        
        # Configuración de TTL por tipo de dato
        self.ttl_config = {
            "chatbot_list": 60,      # 1 minuto para listas
            "chatbot_detail": 300,   # 5 minutos para detalles
            "chatbot_stats": 30,     # 30 segundos para estadísticas
            "user_limits": 120,      # 2 minutos para límites de usuario
            "search_results": 180,   # 3 minutos para resultados de búsqueda
            "company_data": 600      # 10 minutos para datos de empresa
        }
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generar clave única para el caché"""
        # Crear string con todos los parámetros ordenados
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        # Crear hash para evitar claves muy largas
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor del caché"""
        async with self._lock:
            entry = self.cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self.cache[key]
                logger.debug(f"Cache entry expired and removed: {key}")
                return None
            
            logger.debug(f"Cache hit: {key}")
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Establecer valor en el caché"""
        if ttl is None:
            ttl = self.default_ttl
        
        async with self._lock:
            # Si el caché está lleno, eliminar entradas antiguas
            if len(self.cache) >= self.max_size:
                await self._evict_old_entries()
            
            self.cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    async def delete(self, key: str) -> bool:
        """Eliminar entrada del caché"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Eliminar todas las entradas que coincidan con un patrón"""
        async with self._lock:
            keys_to_delete = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.cache[key]
            
            logger.debug(f"Cache pattern deleted: {pattern} ({len(keys_to_delete)} entries)")
            return len(keys_to_delete)
    
    async def _evict_old_entries(self) -> None:
        """Eliminar entradas antiguas cuando el caché está lleno"""
        # Eliminar entradas expiradas primero
        expired_keys = [
            key for key, entry in self.cache.items() 
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        # Si aún está lleno, eliminar las menos accedidas
        if len(self.cache) >= self.max_size:
            # Ordenar por último acceso y eliminar las más antiguas
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Eliminar el 20% más antiguo
            to_remove = max(1, len(sorted_entries) // 5)
            for key, _ in sorted_entries[:to_remove]:
                del self.cache[key]
            
            logger.debug(f"Evicted {to_remove} old cache entries")
    
    async def clear(self) -> None:
        """Limpiar todo el caché"""
        async with self._lock:
            self.cache.clear()
            logger.debug("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        current_time = time.time()
        
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        # Estadísticas por tipo
        type_stats = {}
        for key, entry in self.cache.items():
            cache_type = key.split(':')[0]
            if cache_type not in type_stats:
                type_stats[cache_type] = {
                    'count': 0,
                    'total_access': 0,
                    'avg_age': 0
                }
            
            type_stats[cache_type]['count'] += 1
            type_stats[cache_type]['total_access'] += entry.access_count
            type_stats[cache_type]['avg_age'] += current_time - entry.created_at
        
        # Calcular promedios
        for stats in type_stats.values():
            if stats['count'] > 0:
                stats['avg_access'] = stats['total_access'] / stats['count']
                stats['avg_age'] = stats['avg_age'] / stats['count']
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'max_size': self.max_size,
            'usage_percentage': (total_entries / self.max_size) * 100,
            'type_stats': type_stats
        }

# Instancia global del caché
cache = MemoryCache()

# Funciones helper para operaciones comunes de caché
async def cache_chatbot_list(
    company_id: str,
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    model: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Optional[Dict]:
    """Obtener lista de chatbots del caché"""
    key = cache._generate_key(
        "chatbot_list",
        company_id=company_id,
        page=page,
        size=size,
        status=status,
        model=model,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return await cache.get(key)

async def set_chatbot_list_cache(
    data: Dict,
    company_id: str,
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    model: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> None:
    """Guardar lista de chatbots en caché"""
    key = cache._generate_key(
        "chatbot_list",
        company_id=company_id,
        page=page,
        size=size,
        status=status,
        model=model,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    ttl = cache.ttl_config.get("chatbot_list", cache.default_ttl)
    await cache.set(key, data, ttl)

async def cache_chatbot_detail(chatbot_id: str, company_id: str) -> Optional[Dict]:
    """Obtener detalle de chatbot del caché"""
    key = cache._generate_key("chatbot_detail", chatbot_id=chatbot_id, company_id=company_id)
    return await cache.get(key)

async def set_chatbot_detail_cache(data: Dict, chatbot_id: str, company_id: str) -> None:
    """Guardar detalle de chatbot en caché"""
    key = cache._generate_key("chatbot_detail", chatbot_id=chatbot_id, company_id=company_id)
    ttl = cache.ttl_config.get("chatbot_detail", cache.default_ttl)
    await cache.set(key, data, ttl)

async def invalidate_chatbot_cache(chatbot_id: str, company_id: str) -> None:
    """Invalidar caché relacionado con un chatbot específico"""
    # Invalidar detalle específico
    detail_key = cache._generate_key("chatbot_detail", chatbot_id=chatbot_id, company_id=company_id)
    await cache.delete(detail_key)
    
    # Invalidar todas las listas de la empresa
    await cache.delete_pattern(f"chatbot_list")
    await cache.delete_pattern(f"chatbot_stats")
    
    logger.debug(f"Invalidated cache for chatbot {chatbot_id}")

async def cache_chatbot_stats(company_id: str) -> Optional[Dict]:
    """Obtener estadísticas de chatbots del caché"""
    key = cache._generate_key("chatbot_stats", company_id=company_id)
    return await cache.get(key)

async def set_chatbot_stats_cache(data: Dict, company_id: str) -> None:
    """Guardar estadísticas de chatbots en caché"""
    key = cache._generate_key("chatbot_stats", company_id=company_id)
    ttl = cache.ttl_config.get("chatbot_stats", cache.default_ttl)
    await cache.set(key, data, ttl)

# Decorator para cachear automáticamente resultados de funciones
def cached(cache_type: str, ttl: Optional[int] = None):
    """Decorator para cachear automáticamente resultados de funciones"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generar clave basada en argumentos
            key = cache._generate_key(cache_type, args=args, kwargs=kwargs)
            
            # Intentar obtener del caché
            cached_result = await cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            
            # Usar TTL específico o default
            cache_ttl = ttl or cache.ttl_config.get(cache_type, cache.default_ttl)
            await cache.set(key, result, cache_ttl)
            
            return result
        return wrapper
    return decorator
