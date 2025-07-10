"""
Modelo de notificaciones
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from ..core.database import Base

class NotificationType(enum.Enum):
    """Tipos de notificación"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INTEGRATION = "integration"
    CHATBOT = "chatbot"
    SYSTEM = "system"

class NotificationPriority(enum.Enum):
    """Prioridad de notificación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    """Modelo de notificación"""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.INFO)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    
    # Relaciones
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    chatbot_id = Column(String, ForeignKey("chatbots.id"), nullable=True)
    integration_id = Column(String, ForeignKey("integrations.id"), nullable=True)
    
    # Estado
    is_read = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Metadatos
    extra_data = Column(JSON, nullable=True)
    action_url = Column(String(500), nullable=True)  # URL para acción relacionada
    expires_at = Column(DateTime, nullable=True)  # Fecha de expiración
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    read_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="notifications")
    company = relationship("Company", back_populates="notifications")
    chatbot = relationship("Chatbot", back_populates="notifications")
    integration = relationship("Integration", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, title={self.title}, type={self.type})>"

    def to_dict(self):
        """Convertir a diccionario para JSON"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "priority": self.priority.value,
            "is_read": self.is_read,
            "is_archived": self.is_archived,
            "metadata": self.extra_data,
            "action_url": self.action_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "chatbot_id": self.chatbot_id,
            "integration_id": self.integration_id,
            "chatbot_name": self.chatbot.name if self.chatbot else None,
            "integration_name": self.integration.name if self.integration else None
        }

class NotificationTemplate(Base):
    """Plantillas de notificaciones"""
    __tablename__ = "notification_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    title_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    
    # Configuración
    is_active = Column(Boolean, default=True, nullable=False)
    auto_expire_hours = Column(String, nullable=True)  # Horas para auto-expirar
    
    # Metadatos
    variables = Column(JSON, nullable=True)  # Variables disponibles en la plantilla
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name={self.name})>"

# Eventos predefinidos para notificaciones
NOTIFICATION_EVENTS = {
    "chatbot_created": {
        "title": "Nuevo chatbot creado",
        "message": "Tu chatbot '{chatbot_name}' ha sido creado exitosamente",
        "type": NotificationType.SUCCESS,
        "priority": NotificationPriority.MEDIUM
    },
    "chatbot_error": {
        "title": "Error en chatbot",
        "message": "Tu chatbot '{chatbot_name}' ha experimentado un error: {error_message}",
        "type": NotificationType.ERROR,
        "priority": NotificationPriority.HIGH
    },
    "integration_connected": {
        "title": "Integración conectada",
        "message": "Tu integración de {integration_type} ha sido conectada exitosamente",
        "type": NotificationType.SUCCESS,
        "priority": NotificationPriority.MEDIUM
    },
    "integration_disconnected": {
        "title": "Integración desconectada",
        "message": "Tu integración de {integration_type} se ha desconectado",
        "type": NotificationType.WARNING,
        "priority": NotificationPriority.HIGH
    },
    "message_limit_reached": {
        "title": "Límite de mensajes alcanzado",
        "message": "Has alcanzado el límite de mensajes para tu plan actual",
        "type": NotificationType.WARNING,
        "priority": NotificationPriority.HIGH
    },
    "new_conversation": {
        "title": "Nueva conversación",
        "message": "Tienes una nueva conversación en {platform}",
        "type": NotificationType.INFO,
        "priority": NotificationPriority.LOW
    },
    "system_maintenance": {
        "title": "Mantenimiento programado",
        "message": "El sistema estará en mantenimiento el {date} de {start_time} a {end_time}",
        "type": NotificationType.INFO,
        "priority": NotificationPriority.MEDIUM
    }
}
