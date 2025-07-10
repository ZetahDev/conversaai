"""
Aplicación principal FastAPI
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import time
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, db_manager
from app.core.security import rate_limiter, prompt_detector
from app.api.v1.router import api_router
from app.middleware import (
    SecurityMiddleware,
    RequestLoggingMiddleware,
    SQLInjectionProtectionMiddleware,
    SessionSecurityMiddleware
)

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("Iniciando aplicación...")
    
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("Base de datos inicializada")
        
        # Verificar conexiones
        db_healthy = await db_manager.health_check()
        if not db_healthy:
            logger.error("Error en conexión a base de datos")
            raise Exception("Database connection failed")
        
        logger.info("Aplicación iniciada correctamente")
        
    except Exception as e:
        logger.error(f"Error durante el startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para plataforma SAAS de chatbots con IA",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de hosts confiables (solo en producción)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.chatbot-saas.com", "localhost"]
    )

# Middlewares de seguridad adicionales
app.add_middleware(SecurityMiddleware)
app.add_middleware(SQLInjectionProtectionMiddleware)
app.add_middleware(SessionSecurityMiddleware)

# Middleware de logging (solo en desarrollo)
if settings.DEBUG:
    app.add_middleware(RequestLoggingMiddleware)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Middleware de seguridad"""
    start_time = time.time()
    
    # Rate limiting
    client_ip = request.client.host
    is_allowed, rate_info = rate_limiter.is_allowed(
        key=f"ip:{client_ip}",
        limit=settings.RATE_LIMIT_PER_MINUTE,
        window=60
    )
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": "Too many requests",
                **rate_info
            },
            headers={
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": rate_info["reset_time"]
            }
        )
    
    # Procesar request
    response = await call_next(request)
    
    # Agregar headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Agregar tiempo de procesamiento
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Rate limit headers
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
    
    return response


@app.middleware("http")
async def prompt_injection_middleware(request: Request, call_next):
    """Middleware para detectar inyección de prompts"""
    
    # Solo verificar en endpoints de chat/AI
    if any(path in str(request.url) for path in ["/chat", "/ai", "/generate"]):
        try:
            # Leer body si existe
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8")
                    is_malicious, reason = prompt_detector.is_malicious(body_str)
                    
                    if is_malicious:
                        logger.warning(f"Prompt injection detectado: {reason} - IP: {request.client.host}")
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": "Invalid input",
                                "detail": "El contenido enviado no es válido"
                            }
                        )
                
                # Recrear request con body leído
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
        except Exception as e:
            logger.error(f"Error en middleware de prompt injection: {e}")
    
    response = await call_next(request)
    return response


# Manejadores de errores globales
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador de errores HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador de errores generales"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": "Ha ocurrido un error interno del servidor"
            }
        )


# Rutas principales
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verificar base de datos
        db_healthy = await db_manager.health_check()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@app.get("/metrics")
async def metrics():
    """Métricas básicas del sistema"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        db_info = await db_manager.get_connection_info()
        table_stats = await db_manager.get_table_stats()
        
        return {
            "database": {
                "name": db_info.database if db_info else "unknown",
                "user": db_info.user if db_info else "unknown",
                "size": db_info.size if db_info else "unknown"
            },
            "tables": [
                {
                    "name": stat.tablename,
                    "live_tuples": stat.live_tuples,
                    "dead_tuples": stat.dead_tuples,
                    "inserts": stat.inserts,
                    "updates": stat.updates,
                    "deletes": stat.deletes
                }
                for stat in (table_stats or [])
            ]
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo métricas")


# Incluir rutas de la API
app.include_router(api_router, prefix="/api/v1")


# Documentación personalizada
if settings.DEBUG:
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Documentación",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )


def custom_openapi():
    """OpenAPI personalizado"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Agregar información de seguridad
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower()
    )
