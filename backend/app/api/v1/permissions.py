"""
Endpoints de gestión de roles y permisos
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_active_user
from app.core.permissions import (
    permission_checker, 
    Role, 
    Permission, 
    RolePermissions,
    require_role,
    require_permission
)

router = APIRouter()

# Modelos de respuesta
class UserRoleResponse(BaseModel):
    user_email: str
    role: str
    permissions: List[str]

class RoleInfoResponse(BaseModel):
    role: str
    permissions: List[str]
    hierarchy_level: int

class PermissionCheckResponse(BaseModel):
    has_permission: bool
    user_role: str
    required_permission: str

class RoleHierarchyResponse(BaseModel):
    roles: Dict[str, int]
    current_user_role: str
    current_user_level: int

# Helper function para obtener atributos del usuario
def get_user_attr(user, attr):
    """Obtener atributo del usuario, compatible con dict y objeto"""
    if isinstance(user, dict):
        if attr == "id":
            return user.get("sub")
        elif attr == "company_id":
            email = user.get("email", "")
            if "johan@techcorp.com" in email:
                return "company_1"
            elif "admin@techcorp.com" in email:
                return "company_1"
            elif "usuario1@techcorp.com" in email:
                return "company_1"
            else:
                return "company_1"
        return user.get(attr)
    return getattr(user, attr, None)

@router.get("/my-role", response_model=UserRoleResponse)
async def get_my_role(
    current_user: dict = Depends(get_current_active_user)
) -> UserRoleResponse:
    """
    Obtener rol y permisos del usuario actual
    """
    try:
        user_role = permission_checker.get_user_role(current_user)
        user_permissions = permission_checker.get_user_permissions(current_user)
        
        return UserRoleResponse(
            user_email=current_user.get("email", "unknown"),
            role=user_role.value,
            permissions=[perm.value for perm in user_permissions]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user role: {str(e)}"
        )

@router.get("/roles", response_model=List[RoleInfoResponse])
async def get_all_roles(
    current_user: dict = Depends(get_current_active_user)
) -> List[RoleInfoResponse]:
    """
    Obtener información de todos los roles disponibles
    """
    try:
        # Verificar que tenga permisos para ver roles
        if not permission_checker.check_permission(current_user, Permission.USER_READ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. Cannot view roles information."
            )
        
        roles_info = []
        hierarchy = RolePermissions.get_role_hierarchy()
        
        for role in Role:
            permissions = RolePermissions.get_permissions(role)
            roles_info.append(RoleInfoResponse(
                role=role.value,
                permissions=[perm.value for perm in permissions],
                hierarchy_level=hierarchy.get(role, 0)
            ))
        
        # Ordenar por nivel de jerarquía
        roles_info.sort(key=lambda x: x.hierarchy_level, reverse=True)
        
        return roles_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving roles: {str(e)}"
        )

@router.get("/check/{permission}")
async def check_permission(
    permission: str,
    current_user: dict = Depends(get_current_active_user)
) -> PermissionCheckResponse:
    """
    Verificar si el usuario actual tiene un permiso específico
    """
    try:
        # Validar que el permiso existe
        try:
            perm_enum = Permission(permission)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid permission: {permission}. Valid permissions: {[p.value for p in Permission]}"
            )
        
        user_role = permission_checker.get_user_role(current_user)
        has_perm = permission_checker.check_permission(current_user, perm_enum)
        
        return PermissionCheckResponse(
            has_permission=has_perm,
            user_role=user_role.value,
            required_permission=permission
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking permission: {str(e)}"
        )

@router.get("/hierarchy", response_model=RoleHierarchyResponse)
async def get_role_hierarchy(
    current_user: dict = Depends(get_current_active_user)
) -> RoleHierarchyResponse:
    """
    Obtener jerarquía de roles
    """
    try:
        hierarchy = RolePermissions.get_role_hierarchy()
        user_role = permission_checker.get_user_role(current_user)
        
        return RoleHierarchyResponse(
            roles={role.value: level for role, level in hierarchy.items()},
            current_user_role=user_role.value,
            current_user_level=hierarchy.get(user_role, 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving role hierarchy: {str(e)}"
        )

@router.get("/permissions")
async def get_all_permissions(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, List[str]]:
    """
    Obtener todas las categorías de permisos disponibles
    """
    try:
        # Verificar que tenga permisos para ver información del sistema
        if not permission_checker.check_permission(current_user, Permission.USER_READ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. Cannot view permissions information."
            )
        
        # Agrupar permisos por categoría
        permissions_by_category = {
            "chatbot": [p.value for p in Permission if p.value.startswith("chatbot:")],
            "company": [p.value for p in Permission if p.value.startswith("company:")],
            "user": [p.value for p in Permission if p.value.startswith("user:")],
            "dashboard": [p.value for p in Permission if p.value.startswith("dashboard:")],
            "metrics": [p.value for p in Permission if p.value.startswith("metrics:")],
            "analytics": [p.value for p in Permission if p.value.startswith("analytics:")],
            "notification": [p.value for p in Permission if p.value.startswith("notification:")],
            "system": [p.value for p in Permission if p.value.startswith("system:")],
            "limits": [p.value for p in Permission if p.value.startswith("limits:")],
        }
        
        return permissions_by_category
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving permissions: {str(e)}"
        )

@router.get("/can-manage-role/{target_role}")
async def can_manage_role(
    target_role: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Verificar si el usuario actual puede gestionar un rol específico
    """
    try:
        # Validar que el rol existe
        try:
            target_role_enum = Role(target_role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {target_role}. Valid roles: {[r.value for r in Role]}"
            )
        
        user_role = permission_checker.get_user_role(current_user)
        can_manage = RolePermissions.can_manage_role(user_role, target_role_enum)
        
        return {
            "can_manage": can_manage,
            "manager_role": user_role.value,
            "target_role": target_role,
            "reason": "Higher hierarchy level required" if not can_manage else "Authorized"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking role management: {str(e)}"
        )

@router.get("/access-matrix")
@require_role(Role.ADMIN)
async def get_access_matrix(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Obtener matriz completa de acceso (roles vs permisos) - Solo para administradores
    """
    try:
        access_matrix = {}
        
        for role in Role:
            permissions = RolePermissions.get_permissions(role)
            access_matrix[role.value] = {
                "permissions": [perm.value for perm in permissions],
                "permission_count": len(permissions),
                "hierarchy_level": RolePermissions.get_role_hierarchy().get(role, 0)
            }
        
        # Estadísticas adicionales
        total_permissions = len(Permission)
        permission_usage = {}
        
        for permission in Permission:
            roles_with_permission = [
                role.value for role in Role 
                if RolePermissions.has_permission(role, permission)
            ]
            permission_usage[permission.value] = {
                "roles": roles_with_permission,
                "role_count": len(roles_with_permission)
            }
        
        return {
            "access_matrix": access_matrix,
            "permission_usage": permission_usage,
            "statistics": {
                "total_roles": len(Role),
                "total_permissions": total_permissions,
                "most_permissive_role": max(
                    access_matrix.items(), 
                    key=lambda x: x[1]["permission_count"]
                )[0],
                "least_permissive_role": min(
                    access_matrix.items(), 
                    key=lambda x: x[1]["permission_count"]
                )[0]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving access matrix: {str(e)}"
        )

@router.get("/my-permissions")
async def get_my_permissions(
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Obtener permisos detallados del usuario actual
    """
    try:
        user_role = permission_checker.get_user_role(current_user)
        user_permissions = permission_checker.get_user_permissions(current_user)
        
        # Agrupar permisos por categoría
        permissions_by_category = {}
        for permission in user_permissions:
            category = permission.value.split(":")[0]
            if category not in permissions_by_category:
                permissions_by_category[category] = []
            permissions_by_category[category].append(permission.value)
        
        return {
            "user_email": current_user.get("email", "unknown"),
            "role": user_role.value,
            "hierarchy_level": RolePermissions.get_role_hierarchy().get(user_role, 0),
            "total_permissions": len(user_permissions),
            "permissions_by_category": permissions_by_category,
            "all_permissions": [perm.value for perm in user_permissions]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user permissions: {str(e)}"
        )
