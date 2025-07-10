"""
Modelos de Chatbot y configuración
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

from .base import BaseModel


class ChatbotStatus(str, Enum):
    """Estados del chatbot"""
    DRAFT = "draft"
    TRAINING = "training"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class ChatbotPersonality(str, Enum):
    """Personalidades predefinidas"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"
    HELPFUL = "helpful"
    CUSTOM = "custom"


class AIProvider(str, Enum):
    """Proveedores de IA"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT4_MINI = "openai_gpt4_mini"
    GEMINI_FLASH = "gemini_flash"
    GEMINI_FLASH_LITE = "gemini_flash_lite"


class Chatbot(BaseModel):
    """Modelo de chatbot"""
    __tablename__ = "chatbots"
    __table_args__ = {'extend_existing': True}
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Estado y configuración
    status = Column(SQLEnum(ChatbotStatus), nullable=False, default=ChatbotStatus.DRAFT)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Personalidad y comportamiento
    personality = Column(SQLEnum(ChatbotPersonality), nullable=False, default=ChatbotPersonality.HELPFUL)
    custom_instructions = Column(Text, nullable=True)
    greeting_message = Column(Text, nullable=True, default="¡Hola! ¿En qué puedo ayudarte hoy?")
    fallback_message = Column(Text, nullable=True, default="Lo siento, no entendí tu pregunta. ¿Podrías reformularla?")
    
    # Configuración de IA
    primary_ai_provider = Column(SQLEnum(AIProvider), nullable=False, default=AIProvider.GEMINI_FLASH_LITE)
    fallback_ai_provider = Column(SQLEnum(AIProvider), nullable=True, default=AIProvider.OPENAI_GPT4_MINI)
    temperature = Column(Integer, nullable=False, default=70)  # 0-100
    max_tokens = Column(Integer, nullable=False, default=500)
    
    # Límites y configuración
    max_conversation_length = Column(Integer, nullable=False, default=20)
    response_delay_ms = Column(Integer, nullable=False, default=1000)
    enable_typing_indicator = Column(Boolean, default=True, nullable=False)
    
    # Configuración avanzada
    enable_context_memory = Column(Boolean, default=True, nullable=False)
    enable_sentiment_analysis = Column(Boolean, default=False, nullable=False)
    enable_language_detection = Column(Boolean, default=True, nullable=False)
    
    # Configuración de seguridad
    enable_content_filter = Column(Boolean, default=True, nullable=False)
    enable_rate_limiting = Column(Boolean, default=True, nullable=False)
    max_messages_per_hour = Column(Integer, nullable=False, default=100)
    
    # Métricas
    total_conversations = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    average_rating = Column(Integer, nullable=True)  # 1-5 stars
    
    # Configuración personalizada (JSON)
    custom_config = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    company_id = Column(String(36), ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company", back_populates="chatbots")

    created_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_chatbots")
    
    # Relaciones con otros modelos
    conversations = relationship("Conversation", back_populates="chatbot", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="chatbot", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="chatbot", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="chatbot")
    
    def __repr__(self):
        return f"<Chatbot(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Verificar si el chatbot está activo"""
        return self.status == ChatbotStatus.ACTIVE and not self.is_deleted
    
    @property
    def can_receive_messages(self) -> bool:
        """Verificar si puede recibir mensajes"""
        return self.is_active and self.company.is_active
    
    def get_config(self, key: str, default=None):
        """Obtener configuración personalizada"""
        if not self.custom_config:
            return default
        return self.custom_config.get(key, default)
    
    def set_config(self, key: str, value):
        """Establecer configuración personalizada"""
        if not self.custom_config:
            self.custom_config = {}
        self.custom_config[key] = value
    
    def increment_conversation_count(self):
        """Incrementar contador de conversaciones"""
        self.total_conversations += 1
    
    def increment_message_count(self):
        """Incrementar contador de mensajes"""
        self.total_messages += 1
    
    def update_rating(self, new_rating: int):
        """Actualizar rating promedio"""
        if self.average_rating is None:
            self.average_rating = new_rating
        else:
            # Promedio simple - en producción usar una fórmula más sofisticada
            self.average_rating = int((self.average_rating + new_rating) / 2)
    
    def to_dict(self, include_config=False):
        """Convertir a diccionario"""
        data = {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "avatar_url": self.avatar_url,
            "status": self.status,
            "is_public": self.is_public,
            "personality": self.personality,
            "greeting_message": self.greeting_message,
            "total_conversations": self.total_conversations,
            "total_messages": self.total_messages,
            "average_rating": self.average_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_config:
            data.update({
                "custom_instructions": self.custom_instructions,
                "fallback_message": self.fallback_message,
                "primary_ai_provider": self.primary_ai_provider,
                "fallback_ai_provider": self.fallback_ai_provider,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "max_conversation_length": self.max_conversation_length,
                "response_delay_ms": self.response_delay_ms,
                "enable_typing_indicator": self.enable_typing_indicator,
                "enable_context_memory": self.enable_context_memory,
                "enable_sentiment_analysis": self.enable_sentiment_analysis,
                "enable_language_detection": self.enable_language_detection,
                "enable_content_filter": self.enable_content_filter,
                "enable_rate_limiting": self.enable_rate_limiting,
                "max_messages_per_hour": self.max_messages_per_hour,
                "custom_config": self.custom_config
            })
        
        return data


class ChatbotConfig(BaseModel):
    """Configuración adicional del chatbot (para configuraciones complejas)"""
    __tablename__ = "chatbot_configs"
    
    # Relación con chatbot
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey('chatbots.id'), nullable=False, index=True)
    chatbot = relationship("Chatbot", backref="configs")
    
    # Configuración
    config_key = Column(String(100), nullable=False, index=True)
    config_value = Column(JSON, nullable=True)
    config_type = Column(String(50), nullable=False)  # string, number, boolean, object, array
    
    # Metadatos
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)  # Para datos sensibles
    
    def __repr__(self):
        return f"<ChatbotConfig(chatbot_id={self.chatbot_id}, key='{self.config_key}')>"
