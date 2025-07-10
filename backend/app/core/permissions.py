"""
Sistema de roles y permisos
"""
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from fastapi import HTTPException, Depends
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class Role(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class Permission(str, Enum):
    # Permisos de chatbots
    CHATBOT_CREATE = "chatbot:create"
    CHATBOT_READ = "chatbot:read"
    CHATBOT_UPDATE = "chatbot:update"
    CHATBOT_DELETE = "chatbot:delete"
    CHATBOT_ACTIVATE = "chatbot:activate"
    
    # Permisos de empresa
    COMPANY_READ = "company:read"
    COMPANY_UPDATE = "company:update"
    COMPANY_SETTINGS = "company:settings"
    
    # Permisos de usuarios
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ASSIGN_ROLES = "user:assign_roles"
    
    # Permisos de dashboard y métricas
    DASHBOARD_VIEW = "dashboard:view"
    METRICS_VIEW = "metrics:view"
    ANALYTICS_VIEW = "analytics:view"
    
    # Permisos de notificaciones
    NOTIFICATION_CREATE = "notification:create"
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_MANAGE = "notification:manage"
    
    # Permisos de sistema
    SYSTEM_SETTINGS = "system:settings"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_MAINTENANCE = "system:maintenance"
    
    # Permisos de límites
    LIMITS_VIEW = "limits:view"
    LIMITS_MODIFY = "limits:modify"

class RolePermissions:
    """Definición de permisos por rol"""
    
    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.SUPERADMIN: {
            # Todos los permisos
            Permission.CHATBOT_CREATE,
            Permission.CHATBOT_READ,
            Permission.CHATBOT_UPDATE,
            Permission.CHATBOT_DELETE,
            Permission.CHATBOT_ACTIVATE,
            Permission.COMPANY_READ,
            Permission.COMPANY_UPDATE,
            Permission.COMPANY_SETTINGS,
            Permission.USER_CREATE,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.USER_ASSIGN_ROLES,
            Permission.DASHBOARD_VIEW,
            Permission.METRICS_VIEW,
            Permission.ANALYTICS_VIEW,
            Permission.NOTIFICATION_CREATE,
            Permission.NOTIFICATION_READ,
            Permission.NOTIFICATION_MANAGE,
            Permission.SYSTEM_SETTINGS,
            Permission.SYSTEM_LOGS,
            Permission.SYSTEM_BACKUP,
            Permission.SYSTEM_MAINTENANCE,
            Permission.LIMITS_VIEW,
            Permission.LIMITS_MODIFY,
        },
        
        Role.ADMIN: {
            # Permisos de administración de empresa
            Permission.CHATBOT_CREATE,
            Permission.CHATBOT_READ,
            Permission.CHATBOT_UPDATE,
            Permission.CHATBOT_DELETE,
            Permission.CHATBOT_ACTIVATE,
            Permission.COMPANY_READ,
            Permission.COMPANY_UPDATE,
            Permission.USER_CREATE,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.DASHBOARD_VIEW,
            Permission.METRICS_VIEW,
            Permission.ANALYTICS_VIEW,
            Permission.NOTIFICATION_CREATE,
            Permission.NOTIFICATION_READ,
            Permission.NOTIFICATION_MANAGE,
            Permission.LIMITS_VIEW,
        },
        
        Role.MANAGER: {
            # Permisos de gestión de chatbots y usuarios
            Permission.CHATBOT_CREATE,
            Permission.CHATBOT_READ,
            Permission.CHATBOT_UPDATE,
            Permission.CHATBOT_ACTIVATE,
            Permission.COMPANY_READ,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.DASHBOARD_VIEW,
            Permission.METRICS_VIEW,
            Permission.NOTIFICATION_READ,
            Permission.LIMITS_VIEW,
        },
        
        Role.USER: {
            # Permisos básicos de usuario
            Permission.CHATBOT_CREATE,
            Permission.CHATBOT_READ,
            Permission.CHATBOT_UPDATE,
            Permission.CHATBOT_DELETE,  # Solo sus propios chatbots
            Permission.COMPANY_READ,
            Permission.DASHBOARD_VIEW,
            Permission.NOTIFICATION_READ,
        },
        
        Role.VIEWER: {
            # Solo lectura
            Permission.CHATBOT_READ,
            Permission.COMPANY_READ,
            Permission.DASHBOARD_VIEW,
            Permission.NOTIFICATION_READ,
        }
    }
    
    @classmethod
    def get_permissions(cls, role: Role) -> Set[Permission]:
        """Obtener permisos de un rol"""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        """Verificar si un rol tiene un permiso específico"""
        return permission in cls.get_permissions(role)
    
    @classmethod
    def get_role_hierarchy(cls) -> Dict[Role, int]:
        """Obtener jerarquía de roles (mayor número = más permisos)"""
        return {
            Role.VIEWER: 1,
            Role.USER: 2,
            Role.MANAGER: 3,
            Role.ADMIN: 4,
            Role.SUPERADMIN: 5
        }
    
    @classmethod
    def can_manage_role(cls, manager_role: Role, target_role: Role) -> bool:
        """Verificar si un rol puede gestionar otro rol"""
        hierarchy = cls.get_role_hierarchy()
        return hierarchy.get(manager_role, 0) > hierarchy.get(target_role, 0)

class PermissionChecker:
    """Verificador de permisos"""
    
    def __init__(self):
        self.role_permissions = RolePermissions()
    
    def get_user_role(self, user: Dict[str, Any]) -> Role:
        """Obtener rol del usuario desde el token JWT"""
        email = user.get("email", "")
        
        # Mapeo de emails a roles (en producción esto vendría de la BD)
        if "johan@techcorp.com" in email:
            return Role.SUPERADMIN
        elif "admin@techcorp.com" in email:
            return Role.ADMIN
        elif "manager@techcorp.com" in email:
            return Role.MANAGER
        elif "usuario1@techcorp.com" in email:
            return Role.USER
        elif "viewer@techcorp.com" in email:
            return Role.VIEWER
        else:
            # Rol por defecto
            return Role.USER
    
    def check_permission(self, user: Dict[str, Any], permission: Permission) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        user_role = self.get_user_role(user)
        return self.role_permissions.has_permission(user_role, permission)
    
    def check_multiple_permissions(
        self, 
        user: Dict[str, Any], 
        permissions: List[Permission],
        require_all: bool = True
    ) -> bool:
        """Verificar múltiples permisos"""
        if require_all:
            return all(self.check_permission(user, perm) for perm in permissions)
        else:
            return any(self.check_permission(user, perm) for perm in permissions)
    
    def get_user_permissions(self, user: Dict[str, Any]) -> Set[Permission]:
        """Obtener todos los permisos del usuario"""
        user_role = self.get_user_role(user)
        return self.role_permissions.get_permissions(user_role)
    
    def can_access_resource(
        self, 
        user: Dict[str, Any], 
        resource_owner_id: str,
        permission: Permission
    ) -> bool:
        """Verificar si puede acceder a un recurso específico"""
        user_id = user.get("sub")
        user_role = self.get_user_role(user)
        
        # SuperAdmin y Admin pueden acceder a todo
        if user_role in [Role.SUPERADMIN, Role.ADMIN]:
            return self.check_permission(user, permission)
        
        # Manager puede acceder a recursos de su empresa
        if user_role == Role.MANAGER:
            # Aquí verificaríamos si pertenecen a la misma empresa
            return self.check_permission(user, permission)
        
        # Usuario normal solo puede acceder a sus propios recursos
        if user_role == Role.USER:
            if permission in [Permission.CHATBOT_DELETE, Permission.CHATBOT_UPDATE]:
                return user_id == resource_owner_id and self.check_permission(user, permission)
            else:
                return self.check_permission(user, permission)
        
        # Viewer solo lectura
        if user_role == Role.VIEWER:
            return permission in [Permission.CHATBOT_READ, Permission.COMPANY_READ, Permission.DASHBOARD_VIEW]
        
        return False

# Instancia global del verificador de permisos
permission_checker = PermissionChecker()

# Decoradores para verificar permisos
def require_permission(permission: Permission):
    """Decorador para requerir un permiso específico"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar current_user en los argumentos
            current_user = None
            for arg in args:
                if isinstance(arg, dict) and "email" in arg:
                    current_user = arg
                    break
            
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, dict):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            if not permission_checker.check_permission(current_user, permission):
                user_role = permission_checker.get_user_role(current_user)
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required: {permission.value}, User role: {user_role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(permissions: List[Permission]):
    """Decorador para requerir cualquiera de los permisos especificados"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar current_user en los argumentos
            current_user = None
            for arg in args:
                if isinstance(arg, dict) and "email" in arg:
                    current_user = arg
                    break
            
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, dict):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            if not permission_checker.check_multiple_permissions(current_user, permissions, require_all=False):
                user_role = permission_checker.get_user_role(current_user)
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required any of: {[p.value for p in permissions]}, User role: {user_role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: Role):
    """Decorador para requerir un rol específico o superior"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar current_user en los argumentos
            current_user = None
            for arg in args:
                if isinstance(arg, dict) and "email" in arg:
                    current_user = arg
                    break
            
            for key, value in kwargs.items():
                if key == "current_user" and isinstance(value, dict):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            user_role = permission_checker.get_user_role(current_user)
            hierarchy = RolePermissions.get_role_hierarchy()
            
            if hierarchy.get(user_role, 0) < hierarchy.get(role, 0):
                raise HTTPException(
                    status_code=403,
                    detail=f"Role denied. Required: {role.value} or higher, User role: {user_role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
