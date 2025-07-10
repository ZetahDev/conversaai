"""
Endpoints de empresas/compañías
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_active_user

router = APIRouter()


@router.get("/me")
async def get_my_company(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Obtener información de la empresa del usuario actual
    """
    # TODO: Implementar lógica real cuando tengamos el modelo Company
    return {
        "id": 1,
        "name": "TechCorp",
        "email": "admin@techcorp.com",
        "phone": "+1234567890",
        "address": "123 Tech Street",
        "plan": "premium",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z"
    }


@router.get("/")
async def list_companies(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Listar empresas (solo para super admin)
    """
    # TODO: Verificar permisos de super admin
    return {
        "items": [
            {
                "id": 1,
                "name": "TechCorp",
                "email": "admin@techcorp.com",
                "plan": "premium",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 1,
        "page": 1,
        "size": 20,
        "pages": 1
    }
