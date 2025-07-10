"""
Sistema de notificaciones para alertas y avisos
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict, deque
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationCategory(str, Enum):
    LIMITS = "limits"
    SYSTEM = "system"
    SECURITY = "security"
    USAGE = "usage"
    MAINTENANCE = "maintenance"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Notification:
    def __init__(
        self,
        id: str,
        title: str,
        message: str,
        type: NotificationType,
        category: NotificationCategory,
        priority: NotificationPriority,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        data: Optional[Dict] = None,
        expires_at: Optional[datetime] = None
    ):
        self.id = id
        self.title = title
        self.message = message
        self.type = type
        self.category = category
        self.priority = priority
        self.user_id = user_id
        self.company_id = company_id
        self.data = data or {}
        self.created_at = datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(days=7))
        self.read = False
        self.dismissed = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "read": self.read,
            "dismissed": self.dismissed
        }

class NotificationManager:
    def __init__(self):
        # Almacenar notificaciones en memoria (en producción usar Redis o BD)
        self.notifications: Dict[str, Notification] = {}
        self.user_notifications: Dict[str, List[str]] = defaultdict(list)
        self.company_notifications: Dict[str, List[str]] = defaultdict(list)
        
        # Configuración de límites para alertas
        self.limit_thresholds = {
            "chatbots_per_company": {
                "warning": 0.8,  # 80% del límite
                "critical": 0.95  # 95% del límite
            },
            "chatbots_per_user": {
                "warning": 0.8,
                "critical": 0.95
            },
            "requests_per_minute": {
                "warning": 0.9,
                "critical": 0.98
            }
        }
        
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
    
    async def create_notification(
        self,
        title: str,
        message: str,
        type: NotificationType,
        category: NotificationCategory,
        priority: NotificationPriority,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        data: Optional[Dict] = None,
        expires_in_hours: int = 168  # 7 días por defecto
    ) -> str:
        """Crear una nueva notificación"""
        async with self._lock:
            import uuid
            
            notification_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            notification = Notification(
                id=notification_id,
                title=title,
                message=message,
                type=type,
                category=category,
                priority=priority,
                user_id=user_id,
                company_id=company_id,
                data=data,
                expires_at=expires_at
            )
            
            self.notifications[notification_id] = notification
            
            # Indexar por usuario y empresa
            if user_id:
                self.user_notifications[user_id].append(notification_id)
            if company_id:
                self.company_notifications[company_id].append(notification_id)
            
            logger.info(f"Notification created: {title} for user {user_id}, company {company_id}")
            return notification_id
    
    async def get_user_notifications(
        self,
        user_id: str,
        company_id: Optional[str] = None,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Obtener notificaciones de un usuario"""
        async with self._lock:
            notifications = []
            
            # Notificaciones específicas del usuario
            user_notification_ids = self.user_notifications.get(user_id, [])
            
            # Notificaciones de la empresa si se especifica
            if company_id:
                company_notification_ids = self.company_notifications.get(company_id, [])
                user_notification_ids.extend(company_notification_ids)
            
            # Filtrar y ordenar notificaciones
            for notification_id in user_notification_ids:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]
                    
                    # Verificar si ha expirado
                    if notification.expires_at < datetime.now():
                        continue
                    
                    # Filtrar por estado de lectura
                    if unread_only and notification.read:
                        continue
                    
                    # Filtrar por categoría
                    if category and notification.category != category:
                        continue
                    
                    notifications.append(notification.to_dict())
            
            # Ordenar por prioridad y fecha
            priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            notifications.sort(
                key=lambda x: (
                    priority_order.get(x["priority"], 0),
                    x["created_at"]
                ),
                reverse=True
            )
            
            return notifications[:limit]
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Marcar notificación como leída"""
        async with self._lock:
            if notification_id in self.notifications:
                notification = self.notifications[notification_id]
                if notification.user_id == user_id or notification.company_id:
                    notification.read = True
                    return True
            return False
    
    async def dismiss_notification(self, notification_id: str, user_id: str) -> bool:
        """Descartar notificación"""
        async with self._lock:
            if notification_id in self.notifications:
                notification = self.notifications[notification_id]
                if notification.user_id == user_id or notification.company_id:
                    notification.dismissed = True
                    return True
            return False
    
    async def check_limits_and_notify(
        self,
        user_id: str,
        company_id: str,
        db: AsyncSession
    ):
        """Verificar límites y crear notificaciones si es necesario"""
        try:
            from app.api.v1.chatbots import validate_chatbot_limits
            
            # Obtener límites actuales (sin current_user para usar límites por defecto)
            limits_info = await validate_chatbot_limits(company_id, user_id, db)
            
            # Verificar límite de empresa
            company_usage = limits_info["company_count"] / limits_info["company_limit"]
            if company_usage >= self.limit_thresholds["chatbots_per_company"]["critical"]:
                await self.create_notification(
                    title="⚠️ Límite de Chatbots Crítico",
                    message=f"La empresa ha alcanzado el {company_usage*100:.0f}% del límite de chatbots ({limits_info['company_count']}/{limits_info['company_limit']}). Considere actualizar su plan.",
                    type=NotificationType.ERROR,
                    category=NotificationCategory.LIMITS,
                    priority=NotificationPriority.CRITICAL,
                    company_id=company_id,
                    data={
                        "current_count": limits_info["company_count"],
                        "limit": limits_info["company_limit"],
                        "usage_percentage": company_usage * 100
                    }
                )
            elif company_usage >= self.limit_thresholds["chatbots_per_company"]["warning"]:
                await self.create_notification(
                    title="⚠️ Acercándose al Límite de Chatbots",
                    message=f"La empresa ha usado el {company_usage*100:.0f}% del límite de chatbots ({limits_info['company_count']}/{limits_info['company_limit']}). Planifique su uso.",
                    type=NotificationType.WARNING,
                    category=NotificationCategory.LIMITS,
                    priority=NotificationPriority.HIGH,
                    company_id=company_id,
                    data={
                        "current_count": limits_info["company_count"],
                        "limit": limits_info["company_limit"],
                        "usage_percentage": company_usage * 100
                    }
                )
            
            # Verificar límite de usuario
            user_usage = limits_info["user_count"] / limits_info["user_limit"]
            if user_usage >= self.limit_thresholds["chatbots_per_user"]["critical"]:
                await self.create_notification(
                    title="🚫 Límite Personal Alcanzado",
                    message=f"Has alcanzado el {user_usage*100:.0f}% de tu límite personal de chatbots ({limits_info['user_count']}/{limits_info['user_limit']}).",
                    type=NotificationType.ERROR,
                    category=NotificationCategory.LIMITS,
                    priority=NotificationPriority.HIGH,
                    user_id=user_id,
                    data={
                        "current_count": limits_info["user_count"],
                        "limit": limits_info["user_limit"],
                        "usage_percentage": user_usage * 100
                    }
                )
            elif user_usage >= self.limit_thresholds["chatbots_per_user"]["warning"]:
                await self.create_notification(
                    title="📊 Acercándose al Límite Personal",
                    message=f"Has usado el {user_usage*100:.0f}% de tu límite personal de chatbots ({limits_info['user_count']}/{limits_info['user_limit']}).",
                    type=NotificationType.WARNING,
                    category=NotificationCategory.LIMITS,
                    priority=NotificationPriority.MEDIUM,
                    user_id=user_id,
                    data={
                        "current_count": limits_info["user_count"],
                        "limit": limits_info["user_limit"],
                        "usage_percentage": user_usage * 100
                    }
                )
            
        except Exception as e:
            logger.error(f"Error checking limits for notifications: {e}")
    
    async def create_system_notification(
        self,
        title: str,
        message: str,
        company_id: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict] = None
    ) -> str:
        """Crear notificación del sistema para toda la empresa"""
        return await self.create_notification(
            title=title,
            message=message,
            type=NotificationType.INFO,
            category=NotificationCategory.SYSTEM,
            priority=priority,
            company_id=company_id,
            data=data
        )
    
    async def create_success_notification(
        self,
        title: str,
        message: str,
        user_id: str,
        data: Optional[Dict] = None
    ) -> str:
        """Crear notificación de éxito para un usuario"""
        return await self.create_notification(
            title=title,
            message=message,
            type=NotificationType.SUCCESS,
            category=NotificationCategory.USAGE,
            priority=NotificationPriority.LOW,
            user_id=user_id,
            data=data,
            expires_in_hours=24  # Expira en 24 horas
        )
    
    async def cleanup_expired_notifications(self):
        """Limpiar notificaciones expiradas"""
        async with self._lock:
            current_time = datetime.now()
            expired_ids = [
                notification_id for notification_id, notification in self.notifications.items()
                if notification.expires_at < current_time or notification.dismissed
            ]
            
            for notification_id in expired_ids:
                notification = self.notifications[notification_id]
                
                # Remover de índices
                if notification.user_id and notification_id in self.user_notifications[notification.user_id]:
                    self.user_notifications[notification.user_id].remove(notification_id)
                
                if notification.company_id and notification_id in self.company_notifications[notification.company_id]:
                    self.company_notifications[notification.company_id].remove(notification_id)
                
                # Remover notificación
                del self.notifications[notification_id]
            
            logger.info(f"Cleaned up {len(expired_ids)} expired notifications")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de notificaciones"""
        total_notifications = len(self.notifications)
        unread_count = sum(1 for n in self.notifications.values() if not n.read)
        
        # Estadísticas por tipo
        by_type = defaultdict(int)
        by_category = defaultdict(int)
        by_priority = defaultdict(int)
        
        for notification in self.notifications.values():
            by_type[notification.type.value] += 1
            by_category[notification.category.value] += 1
            by_priority[notification.priority.value] += 1
        
        return {
            "total_notifications": total_notifications,
            "unread_notifications": unread_count,
            "read_notifications": total_notifications - unread_count,
            "by_type": dict(by_type),
            "by_category": dict(by_category),
            "by_priority": dict(by_priority),
            "active_users": len(self.user_notifications),
            "active_companies": len(self.company_notifications)
        }

# Instancia global del manager de notificaciones
notification_manager = NotificationManager()
