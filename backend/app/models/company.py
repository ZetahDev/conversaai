"""
Modelo de Company (Tenant principal)
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from .base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin


class CompanyStatus(str, Enum):
    """Estados de la empresa"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class CompanyType(str, Enum):
    """Tipos de empresa"""
    RESTAURANT = "restaurant"
    BARBERSHOP = "barbershop"
    ECOMMERCE = "ecommerce"
    RETAIL = "retail"
    SERVICES = "services"
    OTHER = "other"


class Company(Base, TimestampMixin, UUIDMixin, SoftDeleteMixin):
    """
    Modelo de empresa (tenant principal del sistema)
    """
    __tablename__ = "companies"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Tipo y estado
    company_type = Column(SQLEnum(CompanyType), nullable=False, default=CompanyType.OTHER)
    status = Column(SQLEnum(CompanyStatus), nullable=False, default=CompanyStatus.TRIAL)
    
    # Información de contacto
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Dirección
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, default="México")
    postal_code = Column(String(20), nullable=True)
    
    # Configuración
    timezone = Column(String(50), nullable=False, default="America/Mexico_City")
    language = Column(String(10), nullable=False, default="es")
    currency = Column(String(3), nullable=False, default="MXN")
    
    # Límites y configuración
    max_users = Column(Integer, nullable=False, default=5)
    max_chatbots = Column(Integer, nullable=False, default=1)
    max_monthly_messages = Column(Integer, nullable=False, default=5000)
    
    # Configuración personalizada
    settings = Column(JSON, nullable=True, default=dict)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True, default="#3B82F6")
    secondary_color = Column(String(7), nullable=True, default="#1F2937")
    
    # API y webhooks
    api_key = Column(String(100), unique=True, nullable=True, index=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(100), nullable=True)
    
    # Facturación
    billing_email = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    
    # Relaciones
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    chatbots = relationship("Chatbot", back_populates="company", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="company", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="company", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="company", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Verificar si la empresa está activa"""
        return self.status == CompanyStatus.ACTIVE and not self.is_deleted
    
    @property
    def is_trial(self) -> bool:
        """Verificar si está en período de prueba"""
        return self.status == CompanyStatus.TRIAL
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar"""
        return self.name
    
    def get_setting(self, key: str, default=None):
        """Obtener configuración específica"""
        if not self.settings:
            return default
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Establecer configuración específica"""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value
    
    def can_create_chatbot(self) -> bool:
        """Verificar si puede crear más chatbots"""
        current_count = len([cb for cb in self.chatbots if not cb.is_deleted])
        return current_count < self.max_chatbots
    
    def can_add_user(self) -> bool:
        """Verificar si puede agregar más usuarios"""
        current_count = len([u for u in self.users if not u.is_deleted])
        return current_count < self.max_users
    
    def get_usage_percentage(self, current_messages: int) -> float:
        """Obtener porcentaje de uso de mensajes"""
        if self.max_monthly_messages == 0:
            return 0.0
        return min((current_messages / self.max_monthly_messages) * 100, 100.0)
    
    def to_public_dict(self):
        """Convertir a diccionario público (sin datos sensibles)"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "company_type": self.company_type,
            "status": self.status,
            "website": self.website,
            "city": self.city,
            "country": self.country,
            "timezone": self.timezone,
            "language": self.language,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
