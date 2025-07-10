"""
Modelos de Usuario, Roles y Permisos
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

from .base import BaseModel


class UserRole(str, Enum):
    """Roles de usuario"""
    SUPER_ADMIN = "super_admin"      # Administrador del sistema
    COMPANY_ADMIN = "company_admin"   # Administrador de empresa
    MANAGER = "manager"               # Manager de empresa
    AGENT = "agent"                   # Agente de soporte
    VIEWER = "viewer"                 # Solo lectura


class UserStatus(str, Enum):
    """Estados de usuario"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


# Tabla de asociación para roles y permisos
user_permissions = Table(
    'user_permissions',
    BaseModel.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)


class Permission(BaseModel):
    """Modelo de permisos"""
    __tablename__ = "permissions"
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False)  # chatbots, users, analytics, etc.
    action = Column(String(50), nullable=False)    # create, read, update, delete
    
    # Relaciones
    users = relationship("User", secondary=user_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class User(BaseModel):
    """Modelo de usuario"""
    __tablename__ = "users"
    
    # Información personal
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Autenticación
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Rol y estado
    role = Column(String(50), nullable=False, default=UserRole.VIEWER)
    status = Column(String(50), nullable=False, default=UserStatus.PENDING)
    
    # Información adicional
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), nullable=True)
    language = Column(String(10), nullable=False, default="es")
    
    # Configuración de notificaciones
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    
    # Seguridad
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    
    # 2FA
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(100), nullable=True)
    backup_codes = Column(Text, nullable=True)  # JSON array de códigos de respaldo
    
    # API
    api_key = Column(String(100), unique=True, nullable=True, index=True)
    api_key_last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Relación con empresa
    company_id = Column(String(36), ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company", back_populates="users")
    
    # Permisos
    permissions = relationship("Permission", secondary=user_permissions, back_populates="users")
    
    # Relaciones con otros modelos
    created_chatbots = relationship("Chatbot", foreign_keys="Chatbot.created_by", back_populates="creator")
    conversations = relationship("Conversation", foreign_keys="Conversation.user_id", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self) -> str:
        """Nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar"""
        return self.username or self.full_name or self.email
    
    @property
    def is_admin(self) -> bool:
        """Verificar si es administrador"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.COMPANY_ADMIN]
    
    @property
    def is_super_admin(self) -> bool:
        """Verificar si es super administrador"""
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_locked(self) -> bool:
        """Verificar si la cuenta está bloqueada"""
        if not self.locked_until:
            return False
        from datetime import datetime
        return datetime.utcnow() < self.locked_until
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Verificar si tiene un permiso específico"""
        # Super admin tiene todos los permisos
        if self.role == UserRole.SUPER_ADMIN:
            return True
        
        # Verificar permisos específicos
        for permission in self.permissions:
            if permission.resource == resource and permission.action == action:
                return True
        
        # Verificar permisos por rol
        role_permissions = self._get_role_permissions()
        return f"{resource}:{action}" in role_permissions
    
    def _get_role_permissions(self) -> set:
        """Obtener permisos por rol"""
        role_permissions = {
            UserRole.COMPANY_ADMIN: {
                "chatbots:create", "chatbots:read", "chatbots:update", "chatbots:delete",
                "users:create", "users:read", "users:update", "users:delete",
                "analytics:read", "integrations:create", "integrations:read",
                "integrations:update", "integrations:delete", "settings:update"
            },
            UserRole.MANAGER: {
                "chatbots:create", "chatbots:read", "chatbots:update",
                "users:read", "analytics:read", "integrations:read"
            },
            UserRole.AGENT: {
                "chatbots:read", "conversations:read", "conversations:update",
                "analytics:read"
            },
            UserRole.VIEWER: {
                "chatbots:read", "conversations:read", "analytics:read"
            }
        }
        
        return role_permissions.get(self.role, set())
    
    def can_access_company(self, company_id: int) -> bool:
        """Verificar si puede acceder a una empresa específica"""
        if self.role == UserRole.SUPER_ADMIN:
            return True
        return self.company_id == company_id
    
    def lock_account(self, minutes: int = 30):
        """Bloquear cuenta temporalmente"""
        from datetime import datetime, timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.failed_login_attempts += 1
    
    def unlock_account(self):
        """Desbloquear cuenta"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def update_last_login(self):
        """Actualizar último login"""
        from datetime import datetime
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
    
    def to_dict(self, include_sensitive=False):
        """Convertir a diccionario"""
        data = {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "role": self.role,
            "status": self.status,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "language": self.language,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "two_factor_enabled": self.two_factor_enabled,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                "company_id": self.company_id,
                "failed_login_attempts": self.failed_login_attempts,
                "is_locked": self.is_locked,
                "api_key": self.api_key,
                "permissions": [p.name for p in self.permissions]
            })
        
        return data
