"""
Endpoints de notificaciones
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User
from ...models.notification import Notification, NotificationType, NotificationPriority
from ...services.notification_service import notification_service

router = APIRouter()

# Modelos de respuesta
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    priority: str
    is_read: bool
    is_archived: bool
    metadata: Optional[Dict[str, Any]]
    action_url: Optional[str]
    created_at: str
    read_at: Optional[str]
    expires_at: Optional[str]
    chatbot_id: Optional[str]
    integration_id: Optional[str]
    chatbot_name: Optional[str]
    integration_name: Optional[str]

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int

class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.MEDIUM
    chatbot_id: Optional[str] = None
    integration_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    expires_hours: Optional[int] = None

# ==================== ENDPOINTS ====================

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Obtener notificaciones del usuario actual"""
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            company_id=current_user.company_id,
            limit=limit,
            offset=skip,
            unread_only=unread_only,
            include_archived=include_archived
        )

        unread_count = await notification_service.get_unread_count(
            user_id=current_user.id,
            company_id=current_user.company_id
        )

        return NotificationListResponse(
            notifications=[
                NotificationResponse(**notif.to_dict()) for notif in notifications
            ],
            total=len(notifications),
            unread_count=unread_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo notificaciones: {str(e)}")

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    request: CreateNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """Crear nueva notificación"""
    try:
        notification = await notification_service.create_notification(
            user_id=current_user.id,
            company_id=current_user.company_id,
            title=request.title,
            message=request.message,
            notification_type=request.type,
            priority=request.priority,
            chatbot_id=request.chatbot_id,
            integration_id=request.integration_id,
            metadata=request.metadata,
            action_url=request.action_url,
            expires_hours=request.expires_hours
        )

        return NotificationResponse(**notification.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando notificación: {str(e)}")

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Marcar notificación como leída"""
    success = await notification_service.mark_as_read(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    return {"message": "Notificación marcada como leída"}

@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user)
):
    """Marcar todas las notificaciones como leídas"""
    count = await notification_service.mark_all_as_read(
        current_user.id,
        current_user.company_id
    )

    return {"message": f"{count} notificaciones marcadas como leídas"}

@router.put("/{notification_id}/archive")
async def archive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Archivar notificación"""
    success = await notification_service.archive_notification(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    return {"message": "Notificación archivada"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Eliminar notificación"""
    success = await notification_service.delete_notification(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    return {"message": "Notificación eliminada"}

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Obtener cantidad de notificaciones no leídas"""
    count = await notification_service.get_unread_count(
        current_user.id,
        current_user.company_id
    )

    return {"unread_count": count}
