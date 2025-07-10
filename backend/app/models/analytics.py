"""
Modelos de Analytics y Métricas
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from enum import Enum
from datetime import datetime, date

from .base import BaseModel


class MetricType(str, Enum):
    """Tipos de métricas"""
    CONVERSATION_COUNT = "conversation_count"
    MESSAGE_COUNT = "message_count"
    USER_COUNT = "user_count"
    RESPONSE_TIME = "response_time"
    SATISFACTION_SCORE = "satisfaction_score"
    RESOLUTION_RATE = "resolution_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    CONVERSION_RATE = "conversion_rate"
    COST_PER_CONVERSATION = "cost_per_conversation"
    AI_ACCURACY = "ai_accuracy"


class TimeGranularity(str, Enum):
    """Granularidad temporal"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class EventType(str, Enum):
    """Tipos de eventos"""
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    USER_RATING = "user_rating"
    BOT_ESCALATION = "bot_escalation"
    ERROR_OCCURRED = "error_occurred"
    FEATURE_USED = "feature_used"


class Analytics(BaseModel):
    """Métricas agregadas por período"""
    __tablename__ = "analytics"
    
    # Dimensiones
    metric_type = Column(SQLEnum(MetricType), nullable=False, index=True)
    granularity = Column(SQLEnum(TimeGranularity), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Valores de la métrica
    value = Column(Float, nullable=False)
    count = Column(Integer, nullable=False, default=1)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    avg_value = Column(Float, nullable=True)
    
    # Dimensiones adicionales
    channel = Column(String(50), nullable=True, index=True)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey('chatbots.id'), nullable=True, index=True)
    integration_id = Column(UUID(as_uuid=True), ForeignKey('integrations.id'), nullable=True, index=True)
    
    # Metadatos
    analytics_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    chatbot = relationship("Chatbot")
    integration = relationship("Integration")
    
    def __repr__(self):
        return f"<Analytics(metric='{self.metric_type}', period='{self.period_start}', value={self.value})>"


class ConversationMetrics(BaseModel):
    """Métricas específicas de conversación"""
    __tablename__ = "conversation_metrics"
    
    # Métricas de tiempo
    duration_seconds = Column(Integer, nullable=False, default=0)
    first_response_time_seconds = Column(Integer, nullable=True)
    avg_response_time_seconds = Column(Float, nullable=True)
    
    # Métricas de mensajes
    total_messages = Column(Integer, nullable=False, default=0)
    bot_messages = Column(Integer, nullable=False, default=0)
    user_messages = Column(Integer, nullable=False, default=0)
    
    # Métricas de calidad
    satisfaction_score = Column(Float, nullable=True)  # 0.0-1.0
    resolution_score = Column(Float, nullable=True)  # 0.0-1.0
    escalation_occurred = Column(Boolean, default=False, nullable=False)
    
    # Métricas de IA
    ai_confidence_avg = Column(Float, nullable=True)  # 0.0-1.0
    ai_tokens_used = Column(Integer, nullable=False, default=0)
    ai_cost = Column(Float, nullable=False, default=0.0)
    
    # Métricas de engagement
    user_engagement_score = Column(Float, nullable=True)  # 0.0-1.0
    bounce_rate = Column(Boolean, default=False, nullable=False)  # Si el usuario se fue rápido
    
    # Análisis de sentimiento
    sentiment_positive = Column(Integer, nullable=False, default=0)
    sentiment_negative = Column(Integer, nullable=False, default=0)
    sentiment_neutral = Column(Integer, nullable=False, default=0)
    
    # Relaciones
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False, unique=True, index=True)
    conversation = relationship("Conversation")
    
    def __repr__(self):
        return f"<ConversationMetrics(conversation_id={self.conversation_id}, duration={self.duration_seconds}s)>"
    
    @property
    def response_rate(self) -> float:
        """Tasa de respuesta del bot"""
        if self.total_messages == 0:
            return 0.0
        return self.bot_messages / self.total_messages
    
    @property
    def messages_per_minute(self) -> float:
        """Mensajes por minuto"""
        if self.duration_seconds == 0:
            return 0.0
        return (self.total_messages / self.duration_seconds) * 60
    
    def calculate_engagement_score(self):
        """Calcular score de engagement"""
        # Fórmula simple basada en duración y mensajes
        if self.duration_seconds == 0 or self.user_messages == 0:
            self.user_engagement_score = 0.0
            return
        
        # Normalizar métricas
        duration_score = min(1.0, self.duration_seconds / 300)  # Max 5 minutos
        message_score = min(1.0, self.user_messages / 10)  # Max 10 mensajes
        
        self.user_engagement_score = (duration_score + message_score) / 2


class EventLog(BaseModel):
    """Log de eventos para analytics"""
    __tablename__ = "event_logs"
    
    # Información del evento
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    
    # Contexto
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=True, index=True)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey('chatbots.id'), nullable=True, index=True)
    
    # Metadatos técnicos
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    channel = Column(String(50), nullable=True, index=True)
    
    # Timestamp específico del evento
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Relaciones
    conversation = relationship("Conversation")
    chatbot = relationship("Chatbot")
    
    def __repr__(self):
        return f"<EventLog(type='{self.event_type}', timestamp='{self.event_timestamp}')>"


class DashboardWidget(BaseModel):
    """Configuración de widgets del dashboard"""
    __tablename__ = "dashboard_widgets"
    
    # Información básica
    title = Column(String(255), nullable=False)
    widget_type = Column(String(50), nullable=False)  # chart, metric, table, etc.
    
    # Configuración
    config = Column(JSON, nullable=False)  # Configuración específica del widget
    position_x = Column(Integer, nullable=False, default=0)
    position_y = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=4)
    height = Column(Integer, nullable=False, default=3)
    
    # Estado
    is_visible = Column(Boolean, default=True, nullable=False)
    refresh_interval_seconds = Column(Integer, nullable=False, default=300)  # 5 minutos
    
    # Relaciones
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User")
    
    def __repr__(self):
        return f"<DashboardWidget(title='{self.title}', type='{self.widget_type}')>"


class Report(BaseModel):
    """Reportes programados"""
    __tablename__ = "reports"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    
    # Configuración
    config = Column(JSON, nullable=False)  # Métricas, filtros, formato
    schedule = Column(String(100), nullable=True)  # Cron expression
    
    # Destinatarios
    recipients = Column(JSON, nullable=True, default=list)  # Lista de emails
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    last_generated_at = Column(DateTime(timezone=True), nullable=True)
    next_generation_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadatos
    generation_count = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company")
    
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    creator = relationship("User")
    
    def __repr__(self):
        return f"<Report(name='{self.name}', type='{self.report_type}')>"
    
    def increment_generation(self):
        """Incrementar contador de generación"""
        self.generation_count += 1
        self.last_generated_at = datetime.utcnow()


class AlertRule(BaseModel):
    """Reglas de alertas"""
    __tablename__ = "alert_rules"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Condición
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    condition = Column(String(20), nullable=False)  # >, <, >=, <=, ==
    threshold_value = Column(Float, nullable=False)
    
    # Configuración
    time_window_minutes = Column(Integer, nullable=False, default=60)
    cooldown_minutes = Column(Integer, nullable=False, default=30)
    
    # Notificación
    notification_channels = Column(JSON, nullable=True, default=list)  # email, slack, webhook
    message_template = Column(Text, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company")
    
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey('chatbots.id'), nullable=True, index=True)
    chatbot = relationship("Chatbot")
    
    def __repr__(self):
        return f"<AlertRule(name='{self.name}', metric='{self.metric_type}')>"
    
    def should_trigger(self, current_value: float) -> bool:
        """Verificar si debe disparar la alerta"""
        if not self.is_active:
            return False
        
        # Verificar cooldown
        if self.last_triggered_at:
            cooldown_end = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False
        
        # Evaluar condición
        if self.condition == ">":
            return current_value > self.threshold_value
        elif self.condition == "<":
            return current_value < self.threshold_value
        elif self.condition == ">=":
            return current_value >= self.threshold_value
        elif self.condition == "<=":
            return current_value <= self.threshold_value
        elif self.condition == "==":
            return current_value == self.threshold_value
        
        return False
    
    def trigger_alert(self):
        """Disparar alerta"""
        self.last_triggered_at = datetime.utcnow()
        self.trigger_count += 1
