"""
Router principal de la API v1
"""
from fastapi import APIRouter

# Importar routers individuales
from .auth import router as auth_router
from .companies import router as companies_router
from .chatbots import router as chatbots_router
from .analytics import router as analytics_router
from .dashboard import router as dashboard_router
from .notifications import router as notifications_router
from .permissions import router as permissions_router
from .backup import router as backup_router
from .integrations import router as integrations_router
# from .users import router as users_router
# from .conversations import router as conversations_router
# from .webhooks import router as webhooks_router

api_router = APIRouter()

# Incluir todos los routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])
api_router.include_router(chatbots_router, prefix="/chatbots", tags=["chatbots"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
api_router.include_router(backup_router, prefix="/backup", tags=["backup"])
api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
# api_router.include_router(users_router, prefix="/users", tags=["users"])
# api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
# api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])

# Endpoint temporal de prueba
@api_router.get("/")
async def api_root():
    """Endpoint raíz de la API"""
    return {
        "message": "ConversaAI API v1",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "companies": "/api/v1/companies",
            "users": "/api/v1/users",
            "chatbots": "/api/v1/chatbots",
            "conversations": "/api/v1/conversations",
            "integrations": "/api/v1/integrations",
            "analytics": "/api/v1/analytics",
            "dashboard": "/api/v1/dashboard",
            "notifications": "/api/v1/notifications",
            "permissions": "/api/v1/permissions",
            "backup": "/api/v1/backup",
            "webhooks": "/api/v1/webhooks"
        }
    }


@api_router.get("/status")
async def api_status():
    """Estado de la API"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "multi_tenant": True,
            "ai_integration": True,
            "multi_channel": True,
            "analytics": True,
            "webhooks": True
        }
    }
