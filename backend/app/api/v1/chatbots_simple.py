"""
Endpoints simplificados de chatbots que funcionan con la estructura actual de la BD
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.core.database import get_async_db
from app.core.security import get_current_active_user

router = APIRouter()


# Función auxiliar para obtener atributos del usuario
def get_user_attr(user, attr):
    """Obtener atributo del usuario, compatible con dict y objeto"""
    if isinstance(user, dict):
        return user.get(attr)
    return getattr(user, attr, None)


# Modelos Pydantic simplificados
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


class ChatbotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    system_prompt: str = "Eres un asistente útil y amigable."
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


@router.get("/", response_model=ChatbotListResponse)
async def list_chatbots(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotListResponse:
    """
    Listar chatbots del usuario/empresa actual
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        
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
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as subquery"
        count_result = await db.execute(text(count_query), params)
        total = count_result.scalar()
        
        # Aplicar paginación
        offset = (page - 1) * size
        paginated_query = f"{base_query} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": size, "offset": offset})
        
        # Ejecutar query
        result = await db.execute(text(paginated_query), params)
        rows = result.fetchall()
        
        # Convertir a response models
        chatbot_responses = []
        for row in rows:
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
                created_at=row.created_at.isoformat() if row.created_at else datetime.now().isoformat(),
                updated_at=row.updated_at.isoformat() if row.updated_at else datetime.now().isoformat()
            ))
        
        # Calcular páginas
        pages = (total + size - 1) // size if total > 0 else 1
        
        return ChatbotListResponse(
            items=chatbot_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chatbots: {str(e)}"
        )


@router.post("/", response_model=ChatbotResponse, status_code=201)
async def create_chatbot(
    chatbot_data: ChatbotCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotResponse:
    """
    Crear un nuevo chatbot
    """
    try:
        chatbot_id = str(uuid.uuid4())
        company_id = get_user_attr(current_user, "company_id")
        user_id = get_user_attr(current_user, "id")
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
        raise HTTPException(
            status_code=500,
            detail=f"Error creating chatbot: {str(e)}"
        )


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
        
        return ChatbotResponse(
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
            created_at=row.created_at.isoformat() if row.created_at else datetime.now().isoformat(),
            updated_at=row.updated_at.isoformat() if row.updated_at else datetime.now().isoformat()
        )
        
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
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatbotResponse:
    """
    Actualizar un chatbot
    """
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
        params = {"chatbot_id": chatbot_id, "company_id": company_id, "updated_at": datetime.now()}
        
        update_data = chatbot_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            update_fields.append(f"{field} = :{field}")
            params[field] = value
        
        if update_fields:
            update_query = f"""
            UPDATE chatbots 
            SET {', '.join(update_fields)}, updated_at = :updated_at
            WHERE id = :chatbot_id AND company_id = :company_id
            """
            
            await db.execute(text(update_query), params)
            await db.commit()
        
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
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Eliminar un chatbot
    """
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
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting chatbot: {str(e)}"
        )
