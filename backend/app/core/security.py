"""
Módulo de seguridad: autenticación, autorización y protección
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any, Tuple, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import re
import logging

from .config import settings
from .database import get_async_db, get_db

logger = logging.getLogger(__name__)

# Configuración de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Patrones para validación de seguridad
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"forget\s+everything",
    r"system\s*:\s*you\s+are",
    r"act\s+as\s+if\s+you\s+are",
    r"pretend\s+to\s+be",
    r"roleplay\s+as",
    r"\\n\\n.*system",
    r"<\s*script\s*>",
    r"javascript\s*:",
    r"data\s*:\s*text/html"
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS]


class SecurityManager:
    """Manager principal de seguridad"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generar hash de contraseña"""
        return pwd_context.hash(password)

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validar fortaleza de contraseña"""
        errors = []

        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")

        if len(password) > 128:
            errors.append("La contraseña no puede tener más de 128 caracteres")

        if not re.search(r"[a-z]", password):
            errors.append("La contraseña debe contener al menos una letra minúscula")

        if not re.search(r"[A-Z]", password):
            errors.append("La contraseña debe contener al menos una letra mayúscula")

        if not re.search(r"\d", password):
            errors.append("La contraseña debe contener al menos un número")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("La contraseña debe contener al menos un carácter especial")

        # Verificar patrones comunes débiles
        weak_patterns = [
            r"123456",
            r"password",
            r"qwerty",
            r"abc123",
            r"admin",
            r"letmein"
        ]

        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append("La contraseña contiene patrones comunes débiles")
                break

        return len(errors) == 0, errors
    
    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Crear token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Crear token de refresh"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """Verificar y decodificar token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            # Verificar tipo de token
            if payload.get("type") != token_type:
                return None

            # Verificar expiración
            exp = payload.get("exp")
            if exp:
                current_time = datetime.now(timezone.utc)
                exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                if exp_time < current_time:
                    return None

            return payload

        except JWTError as e:
            logger.warning(f"Error al verificar token: {e}")
            return None
    
    @staticmethod
    def generate_api_key() -> str:
        """Generar API key segura"""
        return f"cb_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validar fortaleza de contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if not re.search(r"[A-Z]", password):
            return False, "La contraseña debe tener al menos una mayúscula"
        
        if not re.search(r"[a-z]", password):
            return False, "La contraseña debe tener al menos una minúscula"
        
        if not re.search(r"\d", password):
            return False, "La contraseña debe tener al menos un número"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "La contraseña debe tener al menos un carácter especial"
        
        return True, "Contraseña válida"


class PromptInjectionDetector:
    """Detector de inyección de prompts"""
    
    @staticmethod
    def is_malicious(text: str) -> tuple[bool, Optional[str]]:
        """Detectar contenido malicioso en el texto"""
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        # Verificar patrones conocidos
        for pattern in COMPILED_PATTERNS:
            if pattern.search(text):
                return True, f"Patrón sospechoso detectado: {pattern.pattern}"
        
        # Verificar longitud excesiva
        if len(text) > 10000:
            return True, "Texto excesivamente largo"
        
        # Verificar repetición de caracteres
        if len(set(text)) < len(text) * 0.1:
            return True, "Repetición excesiva de caracteres"
        
        return False, None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitizar entrada del usuario"""
        if not text:
            return ""
        
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limitar longitud
        text = text[:5000]
        
        # Escapar caracteres especiales para prevenir inyección
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        return text.strip()


class RateLimiter:
    """Rate limiter simple en memoria"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, dict]:
        """
        Verificar si la request está permitida
        
        Args:
            key: Identificador único (IP, user_id, etc.)
            limit: Número máximo de requests
            window: Ventana de tiempo en segundos
        
        Returns:
            (is_allowed, info_dict)
        """
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Limpiar requests antiguas
        cutoff = now - timedelta(seconds=window)
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if req_time > cutoff
        ]
        
        current_count = len(self.requests[key])
        
        if current_count >= limit:
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_time": (self.requests[key][0] + timedelta(seconds=window)).isoformat()
            }
        
        # Agregar request actual
        self.requests[key].append(now)
        
        return True, {
            "allowed": True,
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset_time": (now + timedelta(seconds=window)).isoformat()
        }


# Instancias globales
security_manager = SecurityManager()
prompt_detector = PromptInjectionDetector()
rate_limiter = RateLimiter()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Dependency para obtener usuario actual"""
    from ..models.user import User
    from sqlalchemy.orm import Session

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security_manager.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Buscar el usuario en la base de datos
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise credentials_exception

            # Verificar que el usuario esté activo
            if user.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario inactivo"
                )

            return user
        finally:
            db.close()

    except JWTError:
        raise credentials_exception


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Dependency para obtener usuario activo"""
    # La verificación de usuario activo ya se hace en get_current_user
    return current_user


async def get_current_tenant(current_user: dict = Depends(get_current_active_user)):
    """Dependency para obtener tenant actual"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se pudo determinar el tenant"
        )
    return tenant_id


def require_permissions(*permissions: str):
    """Decorator para requerir permisos específicos"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )
            
            user_permissions = current_user.get("permissions", [])
            for permission in permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permiso requerido: {permission}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
