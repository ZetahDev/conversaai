"""
Modelos base y mixins para el sistema
"""
from sqlalchemy import Column, Integer, DateTime, String, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class TimestampMixin:
    """Mixin para agregar timestamps automáticos"""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )


class UUIDMixin:
    """Mixin para agregar UUID como clave primaria"""
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin para soft delete"""
    
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self):
        """Marcar como eliminado"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restaurar elemento eliminado"""
        self.is_deleted = False
        self.deleted_at = None


class TenantMixin:
    """Mixin para multi-tenancy"""
    
    company_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID de la empresa (tenant)"
    )


class AuditMixin:
    """Mixin para auditoría"""
    
    created_by = Column(
        String(36),
        nullable=True,
        comment="Usuario que creó el registro"
    )

    updated_by = Column(
        String(36),
        nullable=True,
        comment="Usuario que actualizó el registro"
    )
    
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Versión del registro para control de concurrencia"
    )


class BaseModel(Base, TimestampMixin, UUIDMixin, SoftDeleteMixin, TenantMixin, AuditMixin):
    """Modelo base que incluye todos los mixins"""
    
    __abstract__ = True
    
    def to_dict(self, exclude_fields=None):
        """Convertir modelo a diccionario"""
        exclude_fields = exclude_fields or []
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: dict, exclude_fields=None):
        """Actualizar modelo desde diccionario"""
        exclude_fields = exclude_fields or ['id', 'created_at', 'company_id']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_table_name(cls):
        """Obtener nombre de la tabla"""
        return cls.__tablename__
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
