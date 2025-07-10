"""
Endpoints de autenticación
"""
from datetime import timedelta, datetime
from typing import Any
import re
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import (
    security_manager,
    get_current_user,
    get_current_active_user
)

router = APIRouter()


# Schemas de request/response
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: str
    company_type: str = "other"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Registrar nuevo usuario y empresa
    """
    # TODO: Implementar lógica de registro
    # 1. Validar que el email no exista
    # 2. Validar fortaleza de contraseña
    # 3. Crear empresa
    # 4. Crear usuario
    # 5. Enviar email de verificación
    # 6. Generar tokens
    
    # Por ahora retornamos un token de ejemplo
    access_token = security_manager.create_access_token(
        data={"sub": "temp_user_id", "email": user_data.email}
    )
    refresh_token = security_manager.create_refresh_token(
        data={"sub": "temp_user_id", "email": user_data.email}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Login de usuario
    """
    # TODO: Implementar lógica de login real
    # 1. Buscar usuario por email
    # 2. Verificar contraseña
    # 3. Verificar que el usuario esté activo
    # 4. Actualizar último login
    # 5. Generar tokens

    # Por ahora aceptamos cualquier login y retornamos un token temporal
    token_data = {"sub": "temp_user_id", "email": user_credentials.email, "is_active": True}

    access_token = security_manager.create_access_token(data=token_data)
    refresh_token = security_manager.create_refresh_token(data=token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login/oauth", response_model=Token)
async def oauth_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Login OAuth2 compatible (para documentación automática)
    """
    user_credentials = UserLogin(
        email=form_data.username,
        password=form_data.password
    )
    return await login(user_credentials, db)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Refrescar token de acceso
    """
    # Verificar refresh token
    payload = security_manager.verify_token(token_data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido"
        )
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    # TODO: Verificar que el usuario siga existiendo y activo
    
    # Generar nuevos tokens
    access_token = security_manager.create_access_token(
        data={"sub": user_id, "email": email}
    )
    new_refresh_token = security_manager.create_refresh_token(
        data={"sub": user_id, "email": email}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Logout de usuario
    """
    # TODO: Implementar blacklist de tokens o invalidación
    # Por ahora solo retornamos mensaje de éxito
    return {"message": "Logout exitoso"}


@router.post("/password-reset")
async def password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Solicitar reset de contraseña
    """
    # TODO: Implementar lógica de reset
    # 1. Verificar que el email exista
    # 2. Generar token de reset
    # 3. Enviar email con link de reset
    
    return {"message": "Si el email existe, recibirás instrucciones para resetear tu contraseña"}


@router.post("/password-reset/confirm")
async def password_reset_confirm(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Confirmar reset de contraseña
    """
    # TODO: Implementar confirmación de reset
    # 1. Verificar token de reset
    # 2. Validar nueva contraseña
    # 3. Actualizar contraseña
    # 4. Invalidar token de reset
    
    return {"message": "Contraseña actualizada exitosamente"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Cambiar contraseña del usuario actual
    """
    # TODO: Implementar cambio de contraseña
    # 1. Verificar contraseña actual
    # 2. Validar nueva contraseña
    # 3. Actualizar contraseña
    # 4. Invalidar tokens existentes (opcional)
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Obtener información del usuario actual
    """
    # TODO: Obtener datos completos del usuario desde la BD
    return {
        "id": current_user.get("sub"),
        "email": current_user.get("email"),
        "is_active": True,
        "role": "user"
    }


@router.post("/verify-email")
async def verify_email(
    token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Verificar email del usuario
    """
    # TODO: Implementar verificación de email
    # 1. Verificar token de verificación
    # 2. Marcar email como verificado
    # 3. Activar usuario si es necesario
    
    return {"message": "Email verificado exitosamente"}


@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr = Body(..., embed=True),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Reenviar email de verificación
    """
    # TODO: Implementar reenvío de verificación
    # 1. Verificar que el email exista
    # 2. Verificar que no esté ya verificado
    # 3. Generar nuevo token
    # 4. Enviar email
    
    return {"message": "Email de verificación enviado"}


@router.get("/check-email")
async def check_email_availability(
    email: EmailStr,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Verificar disponibilidad de email
    """
    # TODO: Verificar si el email ya está registrado
    return {"available": True}


@router.get("/check-company-slug")
async def check_company_slug_availability(
    slug: str,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    Verificar disponibilidad de slug de empresa
    """
    # TODO: Verificar si el slug ya está en uso
    return {"available": True}

@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str = Body(..., embed=True)
) -> Any:
    """
    Renovar token de acceso usando refresh token
    """
    from ...models.user import User
    from sqlalchemy.orm import Session
    from ...core.database import get_db

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de refresh inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verificar refresh token
        payload = security_manager.verify_token(refresh_token, token_type="refresh")
        if payload is None:
            raise credentials_exception

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Buscar usuario en la base de datos
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None or user.status != "active":
                raise credentials_exception

            # Crear nuevos tokens
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = security_manager.create_access_token(
                data={"sub": user.id, "email": user.email, "role": user.role.value},
                expires_delta=access_token_expires
            )

            new_refresh_token = security_manager.create_refresh_token(
                data={"sub": user.id}
            )

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise credentials_exception

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_active_user)
) -> Any:
    """
    Cerrar sesión del usuario
    """
    # En una implementación completa, aquí se podría:
    # 1. Invalidar el token en una blacklist
    # 2. Limpiar sesiones activas
    # 3. Registrar el evento de logout

    return {"message": "Sesión cerrada exitosamente"}

@router.get("/me")
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
) -> Any:
    """
    Obtener información del usuario actual
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "company_id": current_user.company_id,
        "is_active": current_user.status == "active",
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

@router.post("/validate-password")
async def validate_password(
    password: str = Body(..., embed=True)
) -> Any:
    """
    Validar fortaleza de contraseña
    """
    is_valid, errors = security_manager.validate_password_strength(password)

    return {
        "is_valid": is_valid,
        "errors": errors,
        "strength_score": calculate_password_strength_score(password)
    }

def calculate_password_strength_score(password: str) -> int:
    """Calcular puntuación de fortaleza de contraseña (0-100)"""
    score = 0

    # Longitud
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10

    # Variedad de caracteres
    if re.search(r"[a-z]", password):
        score += 10
    if re.search(r"[A-Z]", password):
        score += 10
    if re.search(r"\d", password):
        score += 10
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 15

    # Complejidad adicional
    if len(set(password)) > len(password) * 0.7:  # Variedad de caracteres
        score += 10

    # Penalizar patrones repetitivos
    if re.search(r"(.)\1{2,}", password):  # 3+ caracteres repetidos
        score -= 10

    if re.search(r"(012|123|234|345|456|567|678|789|890)", password):  # Secuencias numéricas
        score -= 10

    return max(0, min(100, score))

@router.post("/change-password")
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    current_user = Depends(get_current_active_user)
) -> Any:
    """
    Cambiar contraseña del usuario
    """
    from ...models.user import User
    from sqlalchemy.orm import Session
    from ...core.database import get_db

    # Validar contraseña actual
    if not security_manager.verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Validar nueva contraseña
    is_valid, errors = security_manager.validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Contraseña no válida", "errors": errors}
        )

    # Verificar que no sea la misma contraseña
    if security_manager.verify_password(new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual"
        )

    # Actualizar contraseña
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        user.password_hash = security_manager.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        return {"message": "Contraseña actualizada exitosamente"}
    finally:
        db.close()
