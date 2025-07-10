"""
Modelos de Conversación y Mensajes
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from enum import Enum
from datetime import datetime

from .base import BaseModel


class ConversationStatus(str, Enum):
    """Estados de la conversación"""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    TRANSFERRED = "transferred"
    ARCHIVED = "archived"


class MessageType(str, Enum):
    """Tipos de mensaje"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    SYSTEM = "system"
    QUICK_REPLY = "quick_reply"
    BUTTON = "button"


class MessageSender(str, Enum):
    """Remitente del mensaje"""
    USER = "user"
    BOT = "bot"
    AGENT = "agent"
    SYSTEM = "system"


class ConversationChannel(str, Enum):
    """Canal de la conversación"""
    WEB = "web"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    API = "api"


class Conversation(BaseModel):
    """Modelo de conversación"""
    __tablename__ = "conversations"
    
    # Información básica
    title = Column(String(255), nullable=True)
    status = Column(SQLEnum(ConversationStatus), nullable=False, default=ConversationStatus.ACTIVE)
    channel = Column(SQLEnum(ConversationChannel), nullable=False, default=ConversationChannel.WEB)
    
    # Identificadores externos
    external_user_id = Column(String(255), nullable=True, index=True)  # ID del usuario en el canal
    external_conversation_id = Column(String(255), nullable=True, index=True)  # ID en el canal externo
    session_id = Column(String(255), nullable=True, index=True)  # ID de sesión web
    
    # Información del usuario
    user_name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_phone = Column(String(50), nullable=True)
    user_avatar_url = Column(String(500), nullable=True)
    
    # Metadatos de la conversación
    language = Column(String(10), nullable=False, default="es")
    timezone = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Métricas
    message_count = Column(Integer, default=0, nullable=False)
    bot_message_count = Column(Integer, default=0, nullable=False)
    user_message_count = Column(Integer, default=0, nullable=False)
    
    # Tiempos
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Satisfacción y rating
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)
    satisfaction_score = Column(Float, nullable=True)  # 0.0-1.0
    
    # Configuración
    context_data = Column(JSON, nullable=True, default=dict)  # Datos de contexto
    tags = Column(JSON, nullable=True, default=list)  # Tags para categorización
    
    # Flags
    is_test = Column(Boolean, default=False, nullable=False)
    requires_human = Column(Boolean, default=False, nullable=False)
    is_escalated = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    chatbot_id = Column(String(36), ForeignKey('chatbots.id'), nullable=False, index=True)
    chatbot = relationship("Chatbot", back_populates="conversations")

    user_id = Column(String(36), ForeignKey('users.id'), nullable=True, index=True)
    user = relationship("User", foreign_keys=[user_id], back_populates="conversations")

    assigned_agent_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id])
    
    # Mensajes
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, chatbot_id={self.chatbot_id}, status='{self.status}')>"
    
    @property
    def duration_minutes(self) -> float:
        """Duración de la conversación en minutos"""
        if not self.ended_at:
            end_time = datetime.utcnow()
        else:
            end_time = self.ended_at
        
        duration = end_time - self.started_at
        return duration.total_seconds() / 60
    
    @property
    def is_active(self) -> bool:
        """Verificar si la conversación está activa"""
        return self.status == ConversationStatus.ACTIVE and not self.is_deleted
    
    def add_message(self, content: str, sender: MessageSender, message_type: MessageType = MessageType.TEXT, **kwargs):
        """Agregar mensaje a la conversación"""
        message = Message(
            conversation_id=self.id,
            content=content,
            sender=sender,
            message_type=message_type,
            **kwargs
        )
        
        # Actualizar contadores
        self.message_count += 1
        if sender == MessageSender.BOT:
            self.bot_message_count += 1
        elif sender == MessageSender.USER:
            self.user_message_count += 1
        
        # Actualizar última actividad
        self.last_activity_at = datetime.utcnow()
        
        return message
    
    def end_conversation(self, reason: str = None):
        """Finalizar conversación"""
        self.status = ConversationStatus.ENDED
        self.ended_at = datetime.utcnow()
        if reason:
            self.set_context("end_reason", reason)
    
    def get_context(self, key: str, default=None):
        """Obtener dato de contexto"""
        if not self.context_data:
            return default
        return self.context_data.get(key, default)
    
    def set_context(self, key: str, value):
        """Establecer dato de contexto"""
        if not self.context_data:
            self.context_data = {}
        self.context_data[key] = value
    
    def add_tag(self, tag: str):
        """Agregar tag"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remover tag"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)


class Message(BaseModel):
    """Modelo de mensaje"""
    __tablename__ = "messages"
    
    # Contenido del mensaje
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), nullable=False, default=MessageType.TEXT)
    sender = Column(SQLEnum(MessageSender), nullable=False)
    
    # Metadatos
    external_message_id = Column(String(255), nullable=True, index=True)
    reply_to_message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=True)
    reply_to_message = relationship("Message", remote_side="Message.id")
    
    # Información adicional
    message_metadata = Column(JSON, nullable=True, default=dict)  # Metadatos específicos del canal
    attachments = Column(JSON, nullable=True, default=list)  # URLs de archivos adjuntos
    
    # Métricas de IA
    ai_provider = Column(String(50), nullable=True)  # Proveedor usado para generar respuesta
    ai_model = Column(String(100), nullable=True)  # Modelo específico usado
    ai_tokens_used = Column(Integer, nullable=True)  # Tokens consumidos
    ai_cost = Column(Float, nullable=True)  # Costo en USD
    processing_time_ms = Column(Integer, nullable=True)  # Tiempo de procesamiento
    
    # Estado del mensaje
    is_read = Column(Boolean, default=False, nullable=False)
    is_delivered = Column(Boolean, default=False, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Análisis de sentimiento
    sentiment_score = Column(Float, nullable=True)  # -1.0 a 1.0
    sentiment_label = Column(String(20), nullable=True)  # positive, negative, neutral
    
    # Flags
    is_flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(String(255), nullable=True)
    
    # Relaciones
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False, index=True)
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender='{self.sender}', type='{self.message_type}')>"
    
    @property
    def is_from_bot(self) -> bool:
        """Verificar si el mensaje es del bot"""
        return self.sender == MessageSender.BOT
    
    @property
    def is_from_user(self) -> bool:
        """Verificar si el mensaje es del usuario"""
        return self.sender == MessageSender.USER
    
    def mark_as_read(self):
        """Marcar mensaje como leído"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def mark_as_delivered(self):
        """Marcar mensaje como entregado"""
        self.is_delivered = True
        self.delivered_at = datetime.utcnow()
    
    def flag_message(self, reason: str):
        """Marcar mensaje como problemático"""
        self.is_flagged = True
        self.flag_reason = reason
    
    def get_metadata(self, key: str, default=None):
        """Obtener metadato específico"""
        if not self.message_metadata:
            return default
        return self.message_metadata.get(key, default)

    def set_metadata(self, key: str, value):
        """Establecer metadato"""
        if not self.message_metadata:
            self.message_metadata = {}
        self.message_metadata[key] = value
    
    def add_attachment(self, url: str, file_type: str, file_name: str = None):
        """Agregar archivo adjunto"""
        if not self.attachments:
            self.attachments = []
        
        attachment = {
            "url": url,
            "type": file_type,
            "name": file_name,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        self.attachments.append(attachment)
