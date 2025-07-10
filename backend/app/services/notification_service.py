"""
Servicio para manejar notificaciones
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from ..models.notification import Notification, NotificationType, NotificationPriority, NOTIFICATION_EVENTS
from ..models.user import User
from ..models.company import Company
from ..models.chatbot import Chatbot
from ..models.integration import Integration
from ..core.database import get_db

class NotificationService:
    def __init__(self):
        pass
    
    async def create_notification(
        self,
        user_id: str,
        company_id: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        chatbot_id: Optional[str] = None,
        integration_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        expires_hours: Optional[int] = None
    ) -> Notification:
        """Crear una nueva notificación"""
        db = next(get_db())
        try:
            expires_at = None
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            notification = Notification(
                id=str(uuid.uuid4()),
                title=title,
                message=message,
                type=notification_type,
                priority=priority,
                user_id=user_id,
                company_id=company_id,
                chatbot_id=chatbot_id,
                integration_id=integration_id,
                extra_data=metadata or {},
                action_url=action_url,
                expires_at=expires_at
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            return notification
        finally:
            db.close()
    
    async def create_from_event(
        self,
        event_type: str,
        user_id: str,
        company_id: str,
        variables: Dict[str, Any],
        chatbot_id: Optional[str] = None,
        integration_id: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Optional[Notification]:
        """Crear notificación desde un evento predefinido"""
        if event_type not in NOTIFICATION_EVENTS:
            return None
        
        event_config = NOTIFICATION_EVENTS[event_type]
        
        # Formatear título y mensaje con variables
        title = event_config["title"].format(**variables)
        message = event_config["message"].format(**variables)
        
        return await self.create_notification(
            user_id=user_id,
            company_id=company_id,
            title=title,
            message=message,
            notification_type=event_config["type"],
            priority=event_config["priority"],
            chatbot_id=chatbot_id,
            integration_id=integration_id,
            action_url=action_url
        )
    
    async def get_user_notifications(
        self,
        user_id: str,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        include_archived: bool = False
    ) -> List[Notification]:
        """Obtener notificaciones de un usuario"""
        db = next(get_db())
        try:
            query = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.company_id == company_id
            )
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            if not include_archived:
                query = query.filter(Notification.is_archived == False)
            
            # Filtrar notificaciones expiradas
            query = query.filter(
                (Notification.expires_at.is_(None)) | 
                (Notification.expires_at > datetime.utcnow())
            )
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return notifications
        finally:
            db.close()
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Marcar notificación como leída"""
        db = next(get_db())
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.commit()
                return True
            
            return False
        finally:
            db.close()
    
    async def mark_all_as_read(self, user_id: str, company_id: str) -> int:
        """Marcar todas las notificaciones como leídas"""
        db = next(get_db())
        try:
            count = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.company_id == company_id,
                Notification.is_read == False
            ).update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })
            
            db.commit()
            return count
        finally:
            db.close()
    
    async def archive_notification(self, notification_id: str, user_id: str) -> bool:
        """Archivar notificación"""
        db = next(get_db())
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                notification.is_archived = True
                db.commit()
                return True
            
            return False
        finally:
            db.close()
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Eliminar notificación"""
        db = next(get_db())
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if notification:
                db.delete(notification)
                db.commit()
                return True
            
            return False
        finally:
            db.close()
    
    async def get_unread_count(self, user_id: str, company_id: str) -> int:
        """Obtener cantidad de notificaciones no leídas"""
        db = next(get_db())
        try:
            count = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.company_id == company_id,
                Notification.is_read == False,
                Notification.is_archived == False,
                (Notification.expires_at.is_(None)) | 
                (Notification.expires_at > datetime.utcnow())
            ).count()
            
            return count
        finally:
            db.close()
    
    async def cleanup_expired_notifications(self) -> int:
        """Limpiar notificaciones expiradas"""
        db = next(get_db())
        try:
            count = db.query(Notification).filter(
                Notification.expires_at < datetime.utcnow()
            ).delete()
            
            db.commit()
            return count
        finally:
            db.close()
    
    # Métodos de conveniencia para eventos comunes
    async def notify_chatbot_created(self, user_id: str, company_id: str, chatbot_name: str, chatbot_id: str):
        """Notificar creación de chatbot"""
        return await self.create_from_event(
            "chatbot_created",
            user_id,
            company_id,
            {"chatbot_name": chatbot_name},
            chatbot_id=chatbot_id,
            action_url=f"/chatbots/{chatbot_id}"
        )
    
    async def notify_integration_connected(self, user_id: str, company_id: str, integration_type: str, integration_id: str):
        """Notificar conexión de integración"""
        return await self.create_from_event(
            "integration_connected",
            user_id,
            company_id,
            {"integration_type": integration_type},
            integration_id=integration_id,
            action_url=f"/integrations"
        )
    
    async def notify_integration_disconnected(self, user_id: str, company_id: str, integration_type: str, integration_id: str):
        """Notificar desconexión de integración"""
        return await self.create_from_event(
            "integration_disconnected",
            user_id,
            company_id,
            {"integration_type": integration_type},
            integration_id=integration_id,
            action_url=f"/integrations"
        )
    
    async def notify_new_conversation(self, user_id: str, company_id: str, platform: str, chatbot_id: str):
        """Notificar nueva conversación"""
        return await self.create_from_event(
            "new_conversation",
            user_id,
            company_id,
            {"platform": platform},
            chatbot_id=chatbot_id,
            action_url=f"/conversations"
        )

# Instancia global del servicio
notification_service = NotificationService()
