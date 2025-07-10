"""
Modelos de Suscripción, Planes y Facturación
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal

from .base import BaseModel


class PlanType(str, Enum):
    """Tipos de plan"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(str, Enum):
    """Ciclos de facturación"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class SubscriptionStatus(str, Enum):
    """Estados de suscripción"""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class PaymentStatus(str, Enum):
    """Estados de pago"""
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class UsageType(str, Enum):
    """Tipos de uso"""
    MESSAGE = "message"
    CONVERSATION = "conversation"
    CHATBOT = "chatbot"
    USER = "user"
    STORAGE = "storage"
    API_CALL = "api_call"


class Plan(BaseModel):
    """Planes de suscripción"""
    __tablename__ = "plans"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    plan_type = Column(SQLEnum(PlanType), nullable=False, index=True)
    
    # Precios
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_quarterly = Column(Numeric(10, 2), nullable=True)
    price_yearly = Column(Numeric(10, 2), nullable=True)
    
    # Límites
    max_chatbots = Column(Integer, nullable=False, default=1)
    max_users = Column(Integer, nullable=False, default=5)
    max_monthly_messages = Column(Integer, nullable=False, default=5000)
    max_integrations = Column(Integer, nullable=False, default=2)
    max_knowledge_bases = Column(Integer, nullable=False, default=1)
    max_storage_mb = Column(Integer, nullable=False, default=100)
    
    # Características
    features = Column(JSON, nullable=True, default=list)  # Lista de características
    ai_providers = Column(JSON, nullable=True, default=list)  # Proveedores de IA disponibles
    
    # Configuración
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    trial_days = Column(Integer, nullable=False, default=14)
    
    # Orden y prioridad
    sort_order = Column(Integer, nullable=False, default=0)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Metadatos
    plan_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}', type='{self.plan_type}')>"
    
    def get_price(self, billing_cycle: BillingCycle) -> Decimal:
        """Obtener precio según ciclo de facturación"""
        if billing_cycle == BillingCycle.MONTHLY:
            return self.price_monthly
        elif billing_cycle == BillingCycle.QUARTERLY and self.price_quarterly:
            return self.price_quarterly
        elif billing_cycle == BillingCycle.YEARLY and self.price_yearly:
            return self.price_yearly
        else:
            return self.price_monthly
    
    def has_feature(self, feature: str) -> bool:
        """Verificar si tiene una característica"""
        return feature in (self.features or [])
    
    def supports_ai_provider(self, provider: str) -> bool:
        """Verificar si soporta un proveedor de IA"""
        return provider in (self.ai_providers or [])


class Subscription(BaseModel):
    """Suscripción de empresa"""
    __tablename__ = "subscriptions"
    
    # Información básica
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL)
    billing_cycle = Column(SQLEnum(BillingCycle), nullable=False, default=BillingCycle.MONTHLY)
    
    # Fechas importantes
    trial_start_date = Column(DateTime(timezone=True), nullable=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Precios y facturación
    current_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Configuración
    auto_renew = Column(Boolean, default=True, nullable=False)
    prorate_upgrades = Column(Boolean, default=True, nullable=False)
    
    # IDs externos (Stripe, etc.)
    external_subscription_id = Column(String(255), nullable=True, index=True)
    external_customer_id = Column(String(255), nullable=True, index=True)
    
    # Uso actual
    current_usage = Column(JSON, nullable=True, default=dict)  # {"messages": 1500, "chatbots": 2, ...}
    
    # Metadatos
    subscription_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    company_id = Column(String(36), ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company", back_populates="subscriptions")

    plan_id = Column(String(36), ForeignKey('plans.id'), nullable=False, index=True)
    plan = relationship("Plan", back_populates="subscriptions")
    
    invoices = relationship("Invoice", back_populates="subscription", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, company_id={self.company_id}, status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Verificar si está activa"""
        return self.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE] and not self.is_deleted
    
    @property
    def is_trial(self) -> bool:
        """Verificar si está en período de prueba"""
        return self.status == SubscriptionStatus.TRIAL
    
    @property
    def days_until_renewal(self) -> int:
        """Días hasta la renovación"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def is_past_due(self) -> bool:
        """Verificar si está vencida"""
        return datetime.utcnow() > self.current_period_end
    
    def get_usage(self, usage_type: str) -> int:
        """Obtener uso actual de un tipo específico"""
        if not self.current_usage:
            return 0
        return self.current_usage.get(usage_type, 0)
    
    def increment_usage(self, usage_type: str, amount: int = 1):
        """Incrementar uso"""
        if not self.current_usage:
            self.current_usage = {}
        current = self.current_usage.get(usage_type, 0)
        self.current_usage[usage_type] = current + amount
    
    def reset_usage(self):
        """Resetear uso (para nuevo período)"""
        self.current_usage = {}
    
    def can_use_feature(self, feature: str) -> bool:
        """Verificar si puede usar una característica"""
        return self.is_active and self.plan.has_feature(feature)
    
    def is_within_limits(self, usage_type: str) -> bool:
        """Verificar si está dentro de los límites"""
        if not self.is_active:
            return False
        
        current_usage = self.get_usage(usage_type)
        
        if usage_type == "messages":
            return current_usage < self.plan.max_monthly_messages
        elif usage_type == "chatbots":
            return current_usage < self.plan.max_chatbots
        elif usage_type == "users":
            return current_usage < self.plan.max_users
        elif usage_type == "integrations":
            return current_usage < self.plan.max_integrations
        
        return True
    
    def renew_subscription(self):
        """Renovar suscripción"""
        if self.billing_cycle == BillingCycle.MONTHLY:
            self.current_period_start = self.current_period_end
            self.current_period_end = self.current_period_end + timedelta(days=30)
        elif self.billing_cycle == BillingCycle.YEARLY:
            self.current_period_start = self.current_period_end
            self.current_period_end = self.current_period_end + timedelta(days=365)
        
        self.reset_usage()
        self.status = SubscriptionStatus.ACTIVE


class Invoice(BaseModel):
    """Facturas"""
    __tablename__ = "invoices"
    
    # Información básica
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Montos
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Fechas
    issue_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    
    # Período facturado
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # IDs externos
    external_invoice_id = Column(String(255), nullable=True, index=True)
    external_payment_id = Column(String(255), nullable=True, index=True)
    
    # Detalles
    line_items = Column(JSON, nullable=True, default=list)
    notes = Column(Text, nullable=True)
    
    # Relaciones
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False, index=True)
    subscription = relationship("Subscription", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', status='{self.status}')>"
    
    @property
    def is_paid(self) -> bool:
        """Verificar si está pagada"""
        return self.status == PaymentStatus.PAID
    
    @property
    def is_overdue(self) -> bool:
        """Verificar si está vencida"""
        return not self.is_paid and datetime.utcnow() > self.due_date
    
    def mark_as_paid(self, payment_date: datetime = None):
        """Marcar como pagada"""
        self.status = PaymentStatus.PAID
        self.paid_date = payment_date or datetime.utcnow()


class UsageLog(BaseModel):
    """Log de uso para facturación"""
    __tablename__ = "usage_logs"
    
    # Información del uso
    usage_type = Column(SQLEnum(UsageType), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_cost = Column(Numeric(10, 4), nullable=True)  # Costo por unidad
    total_cost = Column(Numeric(10, 2), nullable=True)  # Costo total
    
    # Contexto
    resource_id = Column(String(255), nullable=True, index=True)  # ID del recurso usado
    description = Column(Text, nullable=True)
    
    # Metadatos
    usage_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False, index=True)
    subscription = relationship("Subscription", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, type='{self.usage_type}', quantity={self.quantity})>"
