"""
Endpoints de chatbots
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_async_db
from app.core.security import get_current_active_user
from app.core.audit import audit_logger, AuditAction
from app.core.rate_limiter import rate_limit, check_rate_limit, rate_limiter
from app.core.cache import (
    cache, cache_chatbot_list, set_chatbot_list_cache,
    cache_chatbot_detail, set_chatbot_detail_cache,
    cache_chatbot_stats, set_chatbot_stats_cache,
    invalidate_chatbot_cache
)
from app.core.metrics import metrics_collector
from app.core.notifications import notification_manager
from app.core.permissions import permission_checker, Permission, require_permission
# from app.models.chatbot_simple import ChatbotSimple as Chatbot
# from app.models.user import User

router = APIRouter()


# Función auxiliar para obtener atributos del usuario
def get_user_attr(user, attr):
    """Obtener atributo del usuario, compatible con dict y objeto"""
    if isinstance(user, dict):
        # Mapear atributos del token JWT a los nombres esperados
        if attr == "id":
            return user.get("sub")  # 'sub' es el ID del usuario en JWT
        elif attr == "company_id":
            # Por ahora usar un company_id fijo hasta que implementemos la relación correcta
            # Usamos el email del usuario como identificador de empresa temporal
            email = user.get("email", "")
            if "johan@techcorp.com" in email:
                return "company_1"
            elif "admin@techcorp.com" in email:
                return "company_1"  # Misma empresa
            elif "usuario1@techcorp.com" in email:
                return "company_1"  # Misma empresa
            else:
                return "company_1"  # Default
        return user.get(attr)
    return getattr(user, attr, None)


def get_client_ip(request: Request) -> str:
    """Obtener la IP del cliente desde el request"""
    # Verificar headers de proxy primero
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback a la IP del cliente directo
    return request.client.host if request.client else "unknown"


# Funciones de validación de negocio
async def validate_chatbot_limits(company_id: str, user_id: str, db: AsyncSession, current_user: dict = None) -> dict:
    """Validar límites de negocio para chatbots según roles"""

    # Si no se pasa current_user, usar límites por defecto
    if not current_user:
        limits = BusinessLimits()
        company_limit = limits.max_chatbots_per_company
        user_limit = limits.max_chatbots_per_user
        is_superadmin = False
    else:
        user_email = current_user.get("email", "")

        # SUPERADMIN (dueño del sistema) - SIN LÍMITES
        if "johan@techcorp.com" in user_email:
            return {
                "can_create": True,
                "company_count": 0,
                "company_limit": 999999,
                "user_count": 0,
                "user_limit": 999999,
                "remaining_company": 999999,
                "remaining_user": 999999,
                "is_superadmin": True,
                "role": "superadmin"
            }

        # Límites por empresa según plan contratado
        company_limits = {
            "company_1": 50,   # Plan empresarial ($99/mes) - Telegram + WhatsApp + Web + Email + Llamadas
            "company_2": 20,   # Plan profesional ($49/mes) - Telegram + WhatsApp + Web
            "company_3": 10,   # Plan básico ($19/mes) - WhatsApp + Web
            "company_4": 5     # Plan starter ($9/mes) - Solo Web
        }

        # Límites por usuario según rol
        if "admin@techcorp.com" in user_email:
            # ADMIN (cliente que contrata) puede usar todo el límite de su plan
            user_limit = company_limits.get(company_id, 10)
            role = "admin"
        elif "manager@techcorp.com" in user_email:
            # MANAGER puede crear bastantes pero no todos
            user_limit = min(15, company_limits.get(company_id, 10))
            role = "manager"
        else:
            # USER (empleado) tiene límite personal más bajo
            user_limit = min(5, company_limits.get(company_id, 10) // 2)
            role = "user"

        company_limit = company_limits.get(company_id, 10)
        is_superadmin = False

    # Contar chatbots de la empresa
    company_count_query = "SELECT COUNT(*) FROM chatbots WHERE company_id = :company_id"
    company_result = await db.execute(text(company_count_query), {"company_id": company_id})
    company_count = company_result.scalar()

    # Contar chatbots del usuario
    user_count_query = "SELECT COUNT(*) FROM chatbots WHERE created_by = :user_id"
    user_result = await db.execute(text(user_count_query), {"user_id": user_id})
    user_count = user_result.scalar()

    can_create = company_count < company_limit and user_count < user_limit

    return {
        "can_create": can_create,
        "company_count": company_count,
        "company_limit": company_limit,
        "user_count": user_count,
        "user_limit": user_limit,
        "remaining_company": company_limit - company_count,
        "remaining_user": user_limit - user_count,
        "is_superadmin": is_superadmin,
        "role": role if current_user else "unknown"
    }





# Modelos Pydantic para respuestas
class ChatbotResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    model: str
    system_prompt: Optional[str] = None
    temperature: float
    max_tokens: int
    status: str
    company_id: str
    created_by: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ChatbotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 150


class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    status: Optional[str] = None


class ChatbotListResponse(BaseModel):
    items: List[ChatbotResponse]
    total: int
    page: int
    size: int
    pages: int


class ChatbotStatsResponse(BaseModel):
    total_chatbots: int
    by_status: dict
    by_model: dict
    recent_activity: int  # Chatbots creados en los últimos 7 días


class BusinessLimits(BaseModel):
    max_chatbots_per_company: int = 50
    max_chatbots_per_user: int = 10
    max_conversations_per_hour: int = 1000
    max_messages_per_conversation: int = 100


# Funciones de validación de negocio
def validate_chatbot_data(chatbot_data: ChatbotCreate) -> list:
    """Validar datos del chatbot"""
    errors = []

    # Validar nombre
    if not chatbot_data.name or len(chatbot_data.name.strip()) < 3:
        errors.append("El nombre debe tener al menos 3 caracteres")

    if len(chatbot_data.name) > 100:
        errors.append("El nombre no puede exceder 100 caracteres")

    # Validar modelo
    valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "claude-3-sonnet", "claude-3-haiku"]
    if chatbot_data.model not in valid_models:
        errors.append(f"Modelo no válido. Modelos permitidos: {', '.join(valid_models)}")

    # Validar temperatura
    if not (0.0 <= chatbot_data.temperature <= 2.0):
        errors.append("La temperatura debe estar entre 0.0 y 2.0")

    # Validar max_tokens
    if not (1 <= chatbot_data.max_tokens <= 4000):
        errors.append("max_tokens debe estar entre 1 y 4000")

    # Validar system_prompt
    if len(chatbot_data.system_prompt) > 2000:
        errors.append("El system_prompt no puede exceder 2000 caracteres")

    return errors


def validate_chatbot_update_data(chatbot_data: ChatbotUpdate) -> list:
    """Validar datos del chatbot para actualización"""
    errors = []

    # Solo validar campos que están siendo actualizados
    if chatbot_data.name is not None:
        if not chatbot_data.name or len(chatbot_data.name.strip()) < 3:
            errors.append("El nombre debe tener al menos 3 caracteres")

        if len(chatbot_data.name) > 100:
            errors.append("El nombre no puede exceder 100 caracteres")

    if chatbot_data.model is not None:
        valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "claude-3-sonnet", "claude-3-haiku"]
        if chatbot_data.model not in valid_models:
            errors.append(f"Modelo no válido. Modelos permitidos: {', '.join(valid_models)}")

    if chatbot_data.temperature is not None:
        if not (0.0 <= chatbot_data.temperature <= 2.0):
            errors.append("La temperatura debe estar entre 0.0 y 2.0")

    if chatbot_data.max_tokens is not None:
        if not (1 <= chatbot_data.max_tokens <= 4000):
            errors.append("max_tokens debe estar entre 1 y 4000")

    if chatbot_data.system_prompt is not None:
        if len(chatbot_data.system_prompt) > 2000:
            errors.append("El system_prompt no puede exceder 2000 caracteres")

    if chatbot_data.status is not None:
        valid_statuses = ["DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED"]
        if chatbot_data.status not in valid_statuses:
            errors.append(f"Status no válido. Status permitidos: {', '.join(valid_statuses)}")

    return errors


@router.get("/", response_model=ChatbotListResponse)
async def list_chatbots(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    status: Optional[str] = Query(None, description="Filtrar por status (DRAFT, ACTIVE, INACTIVE, ARCHIVED)"),
    model: Optional[str] = Query(None, description="Filtrar por modelo de IA"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción"),
    sort_by: Optional[str] = Query("created_at", description="Campo para ordenar (name, created_at, updated_at, status)"),
    sort_order: Optional[str] = Query("desc", description="Orden (asc, desc)"),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotListResponse:
    """
    Listar chatbots del usuario/empresa actual
    """
    try:
        company_id = get_user_attr(current_user, "company_id")

        # Intentar obtener del caché primero
        cached_result = await cache_chatbot_list(
            company_id=company_id,
            page=page,
            size=size,
            status=status,
            model=model,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        if cached_result is not None:
            return cached_result

        # Construir query base
        base_query = """
        SELECT id, name, description, model, system_prompt, temperature, max_tokens,
               status, company_id, created_by, created_at, updated_at
        FROM chatbots
        WHERE company_id = :company_id
        """

        params = {"company_id": company_id}

        # Aplicar filtros
        if status:
            base_query += " AND status = :status"
            params["status"] = status

        if model:
            base_query += " AND model = :model"
            params["model"] = model

        if search:
            base_query += " AND (name LIKE :search OR description LIKE :search)"
            params["search"] = f"%{search}%"

        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
        count_result = await db.execute(text(count_query), params)
        total = count_result.scalar()

        # Aplicar ordenamiento
        valid_sort_fields = ["name", "created_at", "updated_at", "status", "model"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"

        valid_sort_orders = ["asc", "desc"]
        if sort_order.lower() not in valid_sort_orders:
            sort_order = "desc"

        # Aplicar paginación
        offset = (page - 1) * size
        paginated_query = f"{base_query} ORDER BY {sort_by} {sort_order.upper()} LIMIT :limit OFFSET :offset"
        params.update({"limit": size, "offset": offset})

        # Ejecutar query
        result = await db.execute(text(paginated_query), params)
        rows = result.fetchall()

        # Convertir a response models
        chatbot_responses = []
        for row in rows:
            from datetime import datetime

            # Manejar fechas que pueden ser strings o datetime objects
            def format_datetime(dt_value):
                if dt_value is None:
                    return datetime.now().isoformat()
                if isinstance(dt_value, str):
                    return dt_value  # Ya es string
                if hasattr(dt_value, 'isoformat'):
                    return dt_value.isoformat()
                return str(dt_value)

            chatbot_responses.append(ChatbotResponse(
                id=row.id,
                name=row.name,
                description=row.description,
                model=row.model,
                system_prompt=row.system_prompt,
                temperature=row.temperature,
                max_tokens=row.max_tokens,
                status=row.status,
                company_id=row.company_id,
                created_by=row.created_by,
                created_at=format_datetime(row.created_at),
                updated_at=format_datetime(row.updated_at)
            ))

        # Calcular páginas
        pages = (total + size - 1) // size if total > 0 else 1

        result = ChatbotListResponse(
            items=chatbot_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

        # Guardar en caché
        await set_chatbot_list_cache(
            data=result.model_dump(),
            company_id=company_id,
            page=page,
            size=size,
            status=status,
            model=model,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chatbots: {str(e)}"
        )


@router.post("/", response_model=ChatbotResponse, status_code=201)
async def create_chatbot(
    chatbot_data: ChatbotCreate,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotResponse:
    """
    Crear un nuevo chatbot
    """
    # Verificar permisos
    if not permission_checker.check_permission(current_user, Permission.CHATBOT_CREATE):
        raise HTTPException(
            status_code=403,
            detail="Permission denied. You don't have permission to create chatbots."
        )

    # Rate limiting
    user_id = get_user_attr(current_user, "id")
    await check_rate_limit(request, "create_chatbot", user_id)

    # 1. Validar datos del chatbot
    validation_errors = validate_chatbot_data(chatbot_data)
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Errores de validación: {'; '.join(validation_errors)}"
        )

    company_id = get_user_attr(current_user, "company_id")
    user_id = get_user_attr(current_user, "id")

    # 2. Validar límites de negocio
    limits_check = await validate_chatbot_limits(company_id, user_id, db, current_user)
    if not limits_check["can_create"]:
        detail = f"Límite excedido. "
        if limits_check["remaining_company"] <= 0:
            detail += f"La empresa ha alcanzado el límite de {limits_check['company_limit']} chatbots. "
        if limits_check["remaining_user"] <= 0:
            detail += f"El usuario ha alcanzado el límite de {limits_check['user_limit']} chatbots."

        raise HTTPException(
            status_code=403,
            detail=detail
        )

    try:
        import uuid
        from datetime import datetime

        chatbot_id = str(uuid.uuid4())
        now = datetime.now()

        # Insertar nuevo chatbot
        insert_query = """
        INSERT INTO chatbots (
            id, name, description, model, system_prompt, temperature, max_tokens,
            status, company_id, created_by, created_at, updated_at
        ) VALUES (
            :id, :name, :description, :model, :system_prompt, :temperature, :max_tokens,
            :status, :company_id, :created_by, :created_at, :updated_at
        )
        """

        params = {
            "id": chatbot_id,
            "name": chatbot_data.name,
            "description": chatbot_data.description,
            "model": chatbot_data.model,
            "system_prompt": chatbot_data.system_prompt,
            "temperature": chatbot_data.temperature,
            "max_tokens": chatbot_data.max_tokens,
            "status": "DRAFT",
            "company_id": company_id,
            "created_by": user_id,
            "created_at": now,
            "updated_at": now
        }

        await db.execute(text(insert_query), params)
        await db.commit()

        # Invalidar caché relacionado
        await invalidate_chatbot_cache(chatbot_id, company_id)

        # Registrar métricas
        await metrics_collector.record_chatbot_operation(
            operation="create",
            model=chatbot_data.model,
            user_id=user_id
        )

        # Verificar límites y crear notificaciones si es necesario
        await notification_manager.check_limits_and_notify(user_id, company_id, db)

        # Crear notificación de éxito
        await notification_manager.create_success_notification(
            title="✅ Chatbot Creado",
            message=f"El chatbot '{chatbot_data.name}' ha sido creado exitosamente.",
            user_id=user_id,
            data={
                "chatbot_id": chatbot_id,
                "chatbot_name": chatbot_data.name,
                "model": chatbot_data.model
            }
        )

        # Log de auditoría para creación exitosa
        audit_logger.log_chatbot_create(
            chatbot_id=chatbot_id,
            chatbot_name=chatbot_data.name,
            user_id=user_id,
            user_email=current_user.get("email", "unknown"),
            company_id=company_id,
            ip_address=get_client_ip(request),
            success=True
        )

        return ChatbotResponse(
            id=chatbot_id,
            name=chatbot_data.name,
            description=chatbot_data.description,
            model=chatbot_data.model,
            system_prompt=chatbot_data.system_prompt,
            temperature=chatbot_data.temperature,
            max_tokens=chatbot_data.max_tokens,
            status="DRAFT",
            company_id=company_id,
            created_by=user_id,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

    except Exception as e:
        await db.rollback()

        # Log de auditoría para error en creación
        audit_logger.log_chatbot_create(
            chatbot_id="unknown",
            chatbot_name=chatbot_data.name,
            user_id=get_user_attr(current_user, "id") or "unknown",
            user_email=current_user.get("email", "unknown"),
            company_id=get_user_attr(current_user, "company_id") or "unknown",
            ip_address=get_client_ip(request),
            success=False,
            error_message=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=f"Error creating chatbot: {str(e)}"
        )


@router.get("/stats", response_model=ChatbotStatsResponse)
async def get_chatbot_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotStatsResponse:
    """
    Obtener estadísticas de chatbots de la empresa
    """
    try:
        company_id = get_user_attr(current_user, "company_id")

        # Intentar obtener del caché primero
        cached_result = await cache_chatbot_stats(company_id)
        if cached_result is not None:
            return ChatbotStatsResponse(**cached_result)

        # Total de chatbots
        total_query = "SELECT COUNT(*) FROM chatbots WHERE company_id = :company_id"
        total_result = await db.execute(text(total_query), {"company_id": company_id})
        total_chatbots = total_result.scalar()

        # Estadísticas por status
        status_query = """
        SELECT status, COUNT(*) as count
        FROM chatbots
        WHERE company_id = :company_id
        GROUP BY status
        """
        status_result = await db.execute(text(status_query), {"company_id": company_id})
        by_status = {row.status: row.count for row in status_result.fetchall()}

        # Estadísticas por modelo
        model_query = """
        SELECT model, COUNT(*) as count
        FROM chatbots
        WHERE company_id = :company_id
        GROUP BY model
        """
        model_result = await db.execute(text(model_query), {"company_id": company_id})
        by_model = {row.model: row.count for row in model_result.fetchall()}

        # Actividad reciente (últimos 7 días)
        recent_query = """
        SELECT COUNT(*)
        FROM chatbots
        WHERE company_id = :company_id
        AND created_at >= datetime('now', '-7 days')
        """
        recent_result = await db.execute(text(recent_query), {"company_id": company_id})
        recent_activity = recent_result.scalar()

        result = ChatbotStatsResponse(
            total_chatbots=total_chatbots,
            by_status=by_status,
            by_model=by_model,
            recent_activity=recent_activity
        )

        # Guardar en caché
        await set_chatbot_stats_cache(result.model_dump(), company_id)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chatbot stats: {str(e)}"
        )


@router.get("/limits")
async def get_chatbot_limits(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Obtener información sobre límites de chatbots
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        user_id = get_user_attr(current_user, "id")

        limits_info = await validate_chatbot_limits(company_id, user_id, db, current_user)

        return {
            "limits": BusinessLimits().model_dump(),
            "current_usage": {
                "company_chatbots": limits_info["company_count"],
                "company_limit": limits_info["company_limit"],
                "user_chatbots": limits_info["user_count"],
                "user_limit": limits_info["user_limit"],
                "role": limits_info.get("role", "unknown"),
                "is_superadmin": limits_info.get("is_superadmin", False)
            },
            "remaining": {
                "company_chatbots": limits_info["remaining_company"],
                "user_chatbots": limits_info["remaining_user"]
            },
            "can_create_chatbot": limits_info["can_create"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving limits: {str(e)}"
        )


@router.get("/rate-limit-stats")
async def get_rate_limit_stats(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Obtener estadísticas del rate limiter (solo para administradores)
    """
    # Solo permitir a superadmins
    user_email = current_user.get("email", "")
    if "johan@techcorp.com" not in user_email:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin privileges required."
        )

    stats = rate_limiter.get_stats()
    return {
        "rate_limiter_stats": stats,
        "limits_configuration": rate_limiter.limits
    }


@router.get("/cache-stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Obtener estadísticas del caché (solo para administradores)
    """
    # Solo permitir a superadmins
    user_email = current_user.get("email", "")
    if "johan@techcorp.com" not in user_email:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin privileges required."
        )

    stats = cache.get_stats()
    return {
        "cache_stats": stats,
        "cache_config": {
            "max_size": cache.max_size,
            "default_ttl": cache.default_ttl,
            "ttl_config": cache.ttl_config
        }
    }


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotResponse:
    """
    Obtener un chatbot específico
    """
    try:
        company_id = get_user_attr(current_user, "company_id")

        # Intentar obtener del caché primero
        cached_result = await cache_chatbot_detail(chatbot_id, company_id)
        if cached_result is not None:
            return ChatbotResponse(**cached_result)

        query = """
        SELECT id, name, description, model, system_prompt, temperature, max_tokens,
               status, company_id, created_by, created_at, updated_at
        FROM chatbots
        WHERE id = :chatbot_id AND company_id = :company_id
        """

        result = await db.execute(text(query), {
            "chatbot_id": chatbot_id,
            "company_id": company_id
        })
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Chatbot not found"
            )

        from datetime import datetime

        # Manejar fechas que pueden ser strings o datetime objects
        def format_datetime(dt_value):
            if dt_value is None:
                return datetime.now().isoformat()
            if isinstance(dt_value, str):
                return dt_value  # Ya es string
            if hasattr(dt_value, 'isoformat'):
                return dt_value.isoformat()
            return str(dt_value)

        result = ChatbotResponse(
            id=row.id,
            name=row.name,
            description=row.description,
            model=row.model,
            system_prompt=row.system_prompt,
            temperature=row.temperature,
            max_tokens=row.max_tokens,
            status=row.status,
            company_id=row.company_id,
            created_by=row.created_by,
            created_at=format_datetime(row.created_at),
            updated_at=format_datetime(row.updated_at)
        )

        # Guardar en caché
        await set_chatbot_detail_cache(result.model_dump(), chatbot_id, company_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chatbot: {str(e)}"
        )


@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: str,
    chatbot_data: ChatbotUpdate,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotResponse:
    """
    Actualizar un chatbot
    """
    # Rate limiting
    user_id = get_user_attr(current_user, "id")
    await check_rate_limit(request, "update_chatbot", user_id)

    # Validar datos de actualización
    validation_errors = validate_chatbot_update_data(chatbot_data)
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"Errores de validación: {'; '.join(validation_errors)}"
        )

    try:
        company_id = get_user_attr(current_user, "company_id")

        # Verificar que existe
        check_query = """
        SELECT id FROM chatbots
        WHERE id = :chatbot_id AND company_id = :company_id
        """

        result = await db.execute(text(check_query), {
            "chatbot_id": chatbot_id,
            "company_id": company_id
        })

        if not result.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Chatbot not found"
            )

        # Construir query de actualización
        update_fields = []
        params = {"chatbot_id": chatbot_id, "company_id": company_id}

        update_data = chatbot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            update_fields.append(f"{field} = :{field}")
            params[field] = value

        if update_fields:
            from datetime import datetime
            params["updated_at"] = datetime.now()
            update_query = f"""
            UPDATE chatbots
            SET {', '.join(update_fields)}, updated_at = :updated_at
            WHERE id = :chatbot_id AND company_id = :company_id
            """

            await db.execute(text(update_query), params)
            await db.commit()

            # Invalidar caché relacionado
            await invalidate_chatbot_cache(chatbot_id, company_id)

            # Registrar métricas
            await metrics_collector.record_chatbot_operation(
                operation="update",
                model=update_data.get("model", "unknown"),
                user_id=get_user_attr(current_user, "id") or "unknown"
            )

            # Registrar cambio de status si aplica
            if "status" in update_data:
                await metrics_collector.record_status_change(
                    chatbot_id=chatbot_id,
                    old_status="unknown",  # Tendríamos que obtenerlo de la BD
                    new_status=update_data["status"],
                    user_id=get_user_attr(current_user, "id") or "unknown"
                )

                # Crear notificación para cambio de status importante
                if update_data["status"] == "ACTIVE":
                    await notification_manager.create_success_notification(
                        title="🚀 Chatbot Activado",
                        message=f"El chatbot ha sido activado y está listo para usar.",
                        user_id=get_user_attr(current_user, "id") or "unknown",
                        data={
                            "chatbot_id": chatbot_id,
                            "new_status": update_data["status"]
                        }
                    )

            # Log de auditoría para actualización exitosa
            audit_logger.log_chatbot_update(
                chatbot_id=chatbot_id,
                updated_fields=update_data,
                user_id=get_user_attr(current_user, "id") or "unknown",
                user_email=current_user.get("email", "unknown"),
                company_id=company_id,
                ip_address=get_client_ip(request),
                success=True
            )

        # Obtener chatbot actualizado
        return await get_chatbot(chatbot_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating chatbot: {str(e)}"
        )


@router.delete("/{chatbot_id}", status_code=204)
async def delete_chatbot(
    chatbot_id: str,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Eliminar un chatbot
    """
    # Verificar permisos básicos
    if not permission_checker.check_permission(current_user, Permission.CHATBOT_DELETE):
        raise HTTPException(
            status_code=403,
            detail="Permission denied. You don't have permission to delete chatbots."
        )

    # Rate limiting
    user_id = get_user_attr(current_user, "id")
    await check_rate_limit(request, "delete_chatbot", user_id)

    try:
        company_id = get_user_attr(current_user, "company_id")

        # Verificar que existe y obtener información para auditoría y permisos
        check_query = """
        SELECT id, name, created_by FROM chatbots
        WHERE id = :chatbot_id AND company_id = :company_id
        """

        result = await db.execute(text(check_query), {
            "chatbot_id": chatbot_id,
            "company_id": company_id
        })

        chatbot_row = result.fetchone()
        if not chatbot_row:
            raise HTTPException(
                status_code=404,
                detail="Chatbot not found"
            )

        chatbot_name = chatbot_row.name
        chatbot_owner = chatbot_row.created_by

        # Verificar permisos específicos del recurso
        if not permission_checker.can_access_resource(
            current_user,
            chatbot_owner,
            Permission.CHATBOT_DELETE
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You can only delete your own chatbots."
            )

        # Eliminar chatbot
        delete_query = """
        DELETE FROM chatbots
        WHERE id = :chatbot_id AND company_id = :company_id
        """

        await db.execute(text(delete_query), {
            "chatbot_id": chatbot_id,
            "company_id": company_id
        })
        await db.commit()

        # Invalidar caché relacionado
        await invalidate_chatbot_cache(chatbot_id, company_id)

        # Log de auditoría para eliminación exitosa
        audit_logger.log_chatbot_delete(
            chatbot_id=chatbot_id,
            chatbot_name=chatbot_name,
            user_id=get_user_attr(current_user, "id") or "unknown",
            user_email=current_user.get("email", "unknown"),
            company_id=company_id,
            ip_address=get_client_ip(request),
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting chatbot: {str(e)}"
        )
