"""
Modelos de Integración con Canales
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from enum import Enum
from datetime import datetime

from .base import BaseModel


class IntegrationType(str, Enum):
    """Tipos de integración"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEB_WIDGET = "web_widget"
    API = "api"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"


class IntegrationStatus(str, Enum):
    """Estados de la integración"""
    DRAFT = "draft"
    CONFIGURING = "configuring"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ChannelType(str, Enum):
    """Tipos de canal"""
    MESSAGING = "messaging"
    SOCIAL = "social"
    EMAIL = "email"
    VOICE = "voice"
    WEB = "web"
    API = "api"


class Integration(BaseModel):
    """Integración con canales externos"""
    __tablename__ = "integrations"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    integration_type = Column(SQLEnum(IntegrationType), nullable=False, index=True)
    status = Column(SQLEnum(IntegrationStatus), nullable=False, default=IntegrationStatus.DRAFT)
    
    # Configuración de conexión
    api_key = Column(String(500), nullable=True)  # Encriptado
    api_secret = Column(String(500), nullable=True)  # Encriptado
    webhook_url = Column(String(1000), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    
    # Configuración específica del canal
    channel_config = Column(JSON, nullable=True, default=dict)
    
    # Configuración de comportamiento
    auto_respond = Column(Boolean, default=True, nullable=False)
    response_delay_ms = Column(Integer, nullable=False, default=1000)
    enable_typing_indicator = Column(Boolean, default=True, nullable=False)
    enable_read_receipts = Column(Boolean, default=True, nullable=False)
    
    # Horarios de operación
    business_hours_enabled = Column(Boolean, default=False, nullable=False)
    business_hours = Column(JSON, nullable=True)  # {"monday": {"start": "09:00", "end": "18:00"}, ...}
    timezone = Column(String(50), nullable=False, default="America/Mexico_City")
    
    # Mensajes automáticos
    welcome_message = Column(Text, nullable=True)
    offline_message = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    
    # Métricas
    total_messages_sent = Column(Integer, default=0, nullable=False)
    total_messages_received = Column(Integer, default=0, nullable=False)
    total_conversations = Column(Integer, default=0, nullable=False)
    
    # Estado de conexión
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    # Configuración avanzada
    rate_limit_per_minute = Column(Integer, nullable=False, default=60)
    max_message_length = Column(Integer, nullable=False, default=4096)
    supported_media_types = Column(JSON, nullable=True, default=list)
    
    # Flags
    is_verified = Column(Boolean, default=False, nullable=False)
    is_test_mode = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    company_id = Column(String(36), ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company", back_populates="integrations")

    chatbot_id = Column(String(36), ForeignKey('chatbots.id'), nullable=False, index=True)
    chatbot = relationship("Chatbot", back_populates="integrations")

    channels = relationship("Channel", back_populates="integration", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="integration")
    
    def __repr__(self):
        return f"<Integration(id={self.id}, type='{self.integration_type}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Verificar si está activa"""
        return self.status == IntegrationStatus.ACTIVE and not self.is_deleted
    
    @property
    def is_connected(self) -> bool:
        """Verificar si está conectada"""
        return self.is_active and self.last_connected_at is not None
    
    @property
    def is_in_business_hours(self) -> bool:
        """Verificar si está en horario de atención"""
        if not self.business_hours_enabled or not self.business_hours:
            return True
        
        # TODO: Implementar lógica de horarios de negocio
        return True
    
    def get_config(self, key: str, default=None):
        """Obtener configuración específica"""
        if not self.channel_config:
            return default
        return self.channel_config.get(key, default)
    
    def set_config(self, key: str, value):
        """Establecer configuración específica"""
        if not self.channel_config:
            self.channel_config = {}
        self.channel_config[key] = value
    
    def mark_as_connected(self):
        """Marcar como conectada"""
        self.status = IntegrationStatus.ACTIVE
        self.last_connected_at = datetime.utcnow()
        self.last_error_at = None
        self.last_error_message = None
    
    def mark_as_error(self, error_message: str):
        """Marcar como error"""
        self.status = IntegrationStatus.ERROR
        self.last_error_at = datetime.utcnow()
        self.last_error_message = error_message
    
    def increment_message_sent(self):
        """Incrementar contador de mensajes enviados"""
        self.total_messages_sent += 1
    
    def increment_message_received(self):
        """Incrementar contador de mensajes recibidos"""
        self.total_messages_received += 1
    
    def increment_conversation(self):
        """Incrementar contador de conversaciones"""
        self.total_conversations += 1


class Channel(BaseModel):
    """Canal específico dentro de una integración"""
    __tablename__ = "channels"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    channel_type = Column(SQLEnum(ChannelType), nullable=False)
    external_id = Column(String(255), nullable=True, index=True)  # ID en la plataforma externa
    
    # Configuración
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # 1-10
    
    # Configuración específica
    config = Column(JSON, nullable=True, default=dict)
    
    # Métricas
    message_count = Column(Integer, default=0, nullable=False)
    conversation_count = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    integration_id = Column(UUID(as_uuid=True), ForeignKey('integrations.id'), nullable=False, index=True)
    integration = relationship("Integration", back_populates="channels")
    
    def __repr__(self):
        return f"<Channel(id={self.id}, name='{self.name}', type='{self.channel_type}')>"
    
    def increment_message(self):
        """Incrementar contador de mensajes"""
        self.message_count += 1
    
    def increment_conversation(self):
        """Incrementar contador de conversaciones"""
        self.conversation_count += 1


class WebhookEvent(BaseModel):
    """Eventos de webhook recibidos"""
    __tablename__ = "webhook_events"
    
    # Información del evento
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    
    # Origen
    source_integration_id = Column(UUID(as_uuid=True), ForeignKey('integrations.id'), nullable=True, index=True)
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Procesamiento
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Metadatos
    headers = Column(JSON, nullable=True)
    signature = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, type='{self.event_type}', processed={self.is_processed})>"
    
    def mark_as_processed(self):
        """Marcar como procesado"""
        self.is_processed = True
        self.processed_at = datetime.utcnow()
    
    def mark_as_error(self, error_message: str):
        """Marcar como error"""
        self.processing_error = error_message


class APIKey(BaseModel):
    """Claves API para integraciones"""
    __tablename__ = "api_keys"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256
    key_prefix = Column(String(10), nullable=False)  # Primeros caracteres para identificación
    
    # Configuración
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Permisos
    permissions = Column(JSON, nullable=True, default=list)  # Lista de permisos
    rate_limit_per_hour = Column(Integer, nullable=False, default=1000)
    
    # Métricas
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_used_ip = Column(String(45), nullable=True)
    
    # Relaciones
    integration_id = Column(UUID(as_uuid=True), ForeignKey('integrations.id'), nullable=True, index=True)
    integration = relationship("Integration")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"
    
    @property
    def is_expired(self) -> bool:
        """Verificar si está expirada"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Verificar si es válida"""
        return self.is_active and not self.is_expired and not self.is_deleted
    
    def record_usage(self, ip_address: str = None):
        """Registrar uso de la API key"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        if ip_address:
            self.last_used_ip = ip_address
