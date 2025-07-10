"""
Endpoints para funcionalidad de chat
"""
from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import json
import uuid
from datetime import datetime

from app.core.database import get_async_db
from app.core.security import get_current_active_user
from app.models.chatbot import Chatbot
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


# Modelos Pydantic
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    chatbot_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    response: str
    timestamp: str


class ConversationResponse(BaseModel):
    id: str
    chatbot_id: str
    user_id: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    messages: List[ChatMessage] = []


@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> ChatResponse:
    """
    Enviar un mensaje al chatbot y obtener respuesta
    """
    try:
        # Verificar que el chatbot existe y pertenece a la empresa del usuario
        chatbot_query = select(Chatbot).where(
            Chatbot.id == chat_request.chatbot_id,
            Chatbot.company_id == current_user.company_id,
            Chatbot.status == "ACTIVE"
        )
        chatbot_result = await db.execute(chatbot_query)
        chatbot = chatbot_result.scalar_one_or_none()
        
        if not chatbot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found or not active"
            )
        
        # Obtener o crear conversación
        conversation = None
        if chat_request.conversation_id:
            conv_query = select(Conversation).where(
                Conversation.id == chat_request.conversation_id,
                Conversation.chatbot_id == chat_request.chatbot_id
            )
            conv_result = await db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            # Crear nueva conversación
            conversation = Conversation(
                id=str(uuid.uuid4()),
                chatbot_id=chat_request.chatbot_id,
                user_id=current_user.id,
                status="ACTIVE",
                title=f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(conversation)
            await db.flush()
        
        # Guardar mensaje del usuario
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=chat_request.message,
            sender_type="USER",
            sender_id=current_user.id
        )
        db.add(user_message)
        
        # Generar respuesta del chatbot
        bot_response = await generate_chatbot_response(
            chatbot, chat_request.message, conversation.id, db
        )
        
        # Guardar respuesta del bot
        bot_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=bot_response,
            sender_type="CHATBOT",
            sender_id=chatbot.id
        )
        db.add(bot_message)
        
        await db.commit()
        
        return ChatResponse(
            conversation_id=conversation.id,
            message=chat_request.message,
            response=bot_response,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.post("/stream/{chatbot_id}")
async def stream_chat(
    chatbot_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Chat con streaming de respuesta en tiempo real
    """
    async def generate_stream():
        try:
            # Verificar chatbot
            chatbot_query = select(Chatbot).where(
                Chatbot.id == chatbot_id,
                Chatbot.company_id == current_user.company_id,
                Chatbot.status == "ACTIVE"
            )
            chatbot_result = await db.execute(chatbot_query)
            chatbot = chatbot_result.scalar_one_or_none()
            
            if not chatbot:
                yield f"data: {json.dumps({'error': 'Chatbot not found'})}\n\n"
                return
            
            # Generar respuesta streaming
            async for chunk in generate_streaming_response(chatbot, message):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    chatbot_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> List[ConversationResponse]:
    """
    Obtener conversaciones del usuario
    """
    try:
        query = select(Conversation).where(Conversation.user_id == current_user.id)
        
        if chatbot_id:
            query = query.where(Conversation.chatbot_id == chatbot_id)
        
        query = query.order_by(Conversation.updated_at.desc())
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        conversation_responses = []
        for conv in conversations:
            # Obtener mensajes de la conversación
            messages_query = select(Message).where(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.asc())
            messages_result = await db.execute(messages_query)
            messages = messages_result.scalars().all()
            
            chat_messages = [
                ChatMessage(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.created_at.isoformat()
                )
                for msg in messages
            ]
            
            conversation_responses.append(ConversationResponse(
                id=conv.id,
                chatbot_id=conv.chatbot_id,
                user_id=conv.user_id,
                status=conv.status,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                messages=chat_messages
            ))
        
        return conversation_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversations: {str(e)}"
        )


# Funciones auxiliares
async def generate_chatbot_response(
    chatbot: Chatbot, 
    user_message: str, 
    conversation_id: str, 
    db: AsyncSession
) -> str:
    """
    Generar respuesta del chatbot usando OpenAI
    """
    try:
        # Si las APIs están deshabilitadas, usar respuesta mock
        if settings.MOCK_EXTERNAL_APIS:
            return f"Esta es una respuesta simulada del chatbot '{chatbot.name}' para el mensaje: '{user_message}'"
        
        # Usar OpenAI real
        if settings.OPENAI_API_KEY:
            import openai
            
            # Configurar cliente OpenAI
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Obtener historial de conversación
            messages_query = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).limit(10)  # Últimos 10 mensajes
            
            messages_result = await db.execute(messages_query)
            previous_messages = messages_result.scalars().all()
            
            # Construir contexto
            conversation_history = [
                {"role": "system", "content": chatbot.system_prompt}
            ]
            
            for msg in previous_messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Llamar a OpenAI
            response = await client.chat.completions.create(
                model=chatbot.model,
                messages=conversation_history,
                temperature=chatbot.temperature,
                max_tokens=chatbot.max_tokens
            )
            
            return response.choices[0].message.content
        
        else:
            return "OpenAI API key not configured. Please configure it to use real AI responses."
            
    except Exception as e:
        return f"Error generating response: {str(e)}"


async def generate_streaming_response(
    chatbot: Chatbot, 
    user_message: str
) -> AsyncGenerator[str, None]:
    """
    Generar respuesta streaming del chatbot
    """
    try:
        if settings.MOCK_EXTERNAL_APIS:
            # Simular streaming
            response = f"Respuesta streaming del chatbot '{chatbot.name}' para: '{user_message}'"
            for word in response.split():
                yield word + " "
                # Simular delay
                import asyncio
                await asyncio.sleep(0.1)
        else:
            # Implementar streaming real con OpenAI
            if settings.OPENAI_API_KEY:
                import openai
                
                client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                
                stream = await client.chat.completions.create(
                    model=chatbot.model,
                    messages=[
                        {"role": "system", "content": chatbot.system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=chatbot.temperature,
                    max_tokens=chatbot.max_tokens,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield "OpenAI API key not configured."
                
    except Exception as e:
        yield f"Error: {str(e)}"
