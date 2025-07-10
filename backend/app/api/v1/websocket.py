"""
WebSocket endpoints para chat en tiempo real
"""
import json
import uuid
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_async_db
from app.core.security import get_current_user_from_token
from app.models.chatbot import Chatbot
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.ai_service import ai_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        # Conexiones activas: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Conversaciones activas: {conversation_id: [user_ids]}
        self.conversation_participants: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Conectar un usuario"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][connection_id] = websocket
        logger.info(f"User {user_id} connected with connection {connection_id}")
    
    def disconnect(self, user_id: str, connection_id: str):
        """Desconectar un usuario"""
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
                
            # Si no quedan conexiones, eliminar usuario
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remover de conversaciones
        for conv_id, participants in self.conversation_participants.items():
            if user_id in participants:
                participants.remove(user_id)
        
        logger.info(f"User {user_id} disconnected from connection {connection_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Enviar mensaje a un usuario específico"""
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected_connections.append(connection_id)
            
            # Limpiar conexiones muertas
            for conn_id in disconnected_connections:
                self.disconnect(user_id, conn_id)
    
    async def send_to_conversation(self, message: dict, conversation_id: str):
        """Enviar mensaje a todos los participantes de una conversación"""
        if conversation_id in self.conversation_participants:
            for user_id in self.conversation_participants[conversation_id]:
                await self.send_personal_message(message, user_id)
    
    def join_conversation(self, user_id: str, conversation_id: str):
        """Unir usuario a una conversación"""
        if conversation_id not in self.conversation_participants:
            self.conversation_participants[conversation_id] = []
        
        if user_id not in self.conversation_participants[conversation_id]:
            self.conversation_participants[conversation_id].append(user_id)
    
    def leave_conversation(self, user_id: str, conversation_id: str):
        """Remover usuario de una conversación"""
        if conversation_id in self.conversation_participants:
            if user_id in self.conversation_participants[conversation_id]:
                self.conversation_participants[conversation_id].remove(user_id)
    
    def get_active_users(self) -> List[str]:
        """Obtener lista de usuarios activos"""
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: str) -> bool:
        """Verificar si un usuario está online"""
        return user_id in self.active_connections


# Instancia global del gestor de conexiones
manager = ConnectionManager()


@router.websocket("/chat/{chatbot_id}")
async def websocket_chat(
    websocket: WebSocket,
    chatbot_id: str,
    token: str,
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    WebSocket para chat en tiempo real con un chatbot
    """
    connection_id = str(uuid.uuid4())
    user = None
    
    try:
        # Autenticar usuario
        user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Verificar que el chatbot existe y está activo
        chatbot_query = select(Chatbot).where(
            Chatbot.id == chatbot_id,
            Chatbot.company_id == user.company_id,
            Chatbot.status == "ACTIVE"
        )
        chatbot_result = await db.execute(chatbot_query)
        chatbot = chatbot_result.scalar_one_or_none()
        
        if not chatbot:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Conectar usuario
        await manager.connect(websocket, user.id, connection_id)
        
        # Obtener o crear conversación
        conversation = None
        if conversation_id:
            conv_query = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.chatbot_id == chatbot_id,
                Conversation.user_id == user.id
            )
            conv_result = await db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                chatbot_id=chatbot_id,
                user_id=user.id,
                status="ACTIVE",
                title=f"Chat WebSocket - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        
        # Unir usuario a la conversación
        manager.join_conversation(user.id, conversation.id)
        
        # Enviar mensaje de bienvenida
        welcome_message = {
            "type": "system",
            "message": f"Conectado al chatbot {chatbot.name}",
            "conversation_id": conversation.id,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Escuchar mensajes
        while True:
            try:
                # Recibir mensaje del cliente
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "message":
                    await handle_chat_message(
                        websocket, user, chatbot, conversation, message_data, db
                    )
                elif message_data.get("type") == "typing":
                    await handle_typing_indicator(
                        user, conversation, message_data
                    )
                elif message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error in websocket chat: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        if user:
            manager.disconnect(user.id, connection_id)
            if conversation:
                manager.leave_conversation(user.id, conversation.id)


async def handle_chat_message(
    websocket: WebSocket,
    user: User,
    chatbot: Chatbot,
    conversation: Conversation,
    message_data: dict,
    db: AsyncSession
):
    """Manejar mensaje de chat"""
    try:
        user_message = message_data.get("content", "").strip()
        if not user_message:
            return
        
        # Guardar mensaje del usuario
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=user_message,
            sender_type="USER",
            sender_id=user.id
        )
        db.add(user_msg)
        await db.flush()
        
        # Enviar confirmación de mensaje recibido
        await websocket.send_text(json.dumps({
            "type": "message_received",
            "message_id": user_msg.id,
            "timestamp": user_msg.created_at.isoformat()
        }))
        
        # Obtener historial de conversación para contexto
        messages_query = select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.asc()).limit(20)
        
        messages_result = await db.execute(messages_query)
        previous_messages = messages_result.scalars().all()
        
        # Construir historial para IA
        conversation_history = []
        for msg in previous_messages[:-1]:  # Excluir el último (que acabamos de agregar)
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Agregar mensaje actual
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Enviar indicador de que el bot está escribiendo
        await websocket.send_text(json.dumps({
            "type": "bot_typing",
            "chatbot_name": chatbot.name
        }))
        
        # Generar respuesta del bot con streaming
        bot_response_parts = []
        
        async for chunk in ai_service.generate_streaming_chatbot_response(
            chatbot, conversation_history
        ):
            bot_response_parts.append(chunk)
            
            # Enviar chunk al cliente
            await websocket.send_text(json.dumps({
                "type": "bot_response_chunk",
                "content": chunk,
                "conversation_id": conversation.id
            }))
        
        # Respuesta completa
        full_response = "".join(bot_response_parts)
        
        # Guardar respuesta del bot
        bot_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
            sender_type="CHATBOT",
            sender_id=chatbot.id
        )
        db.add(bot_msg)
        
        await db.commit()
        
        # Enviar mensaje de finalización
        await websocket.send_text(json.dumps({
            "type": "bot_response_complete",
            "message_id": bot_msg.id,
            "conversation_id": conversation.id,
            "timestamp": bot_msg.created_at.isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Error processing message"
        }))


async def handle_typing_indicator(
    user: User,
    conversation: Conversation,
    message_data: dict
):
    """Manejar indicador de escritura"""
    typing_message = {
        "type": "user_typing",
        "user_id": user.id,
        "user_name": user.full_name,
        "conversation_id": conversation.id,
        "is_typing": message_data.get("is_typing", False)
    }
    
    # Enviar a otros participantes de la conversación
    await manager.send_to_conversation(typing_message, conversation.id)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    WebSocket para notificaciones en tiempo real
    """
    connection_id = str(uuid.uuid4())
    user = None
    
    try:
        # Autenticar usuario
        user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Conectar usuario
        await manager.connect(websocket, user.id, connection_id)
        
        # Enviar estado inicial
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": user.id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Mantener conexión viva
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in notifications websocket: {e}")
    
    except Exception as e:
        logger.error(f"Notifications WebSocket error: {e}")
    
    finally:
        if user:
            manager.disconnect(user.id, connection_id)


# Funciones auxiliares para enviar notificaciones
async def send_notification_to_user(user_id: str, notification: dict):
    """Enviar notificación a un usuario específico"""
    await manager.send_personal_message({
        "type": "notification",
        **notification,
        "timestamp": datetime.now().isoformat()
    }, user_id)


async def send_notification_to_company(company_id: str, notification: dict, db: AsyncSession):
    """Enviar notificación a todos los usuarios de una empresa"""
    # Obtener usuarios de la empresa que están online
    users_query = select(User).where(User.company_id == company_id)
    users_result = await db.execute(users_query)
    users = users_result.scalars().all()
    
    for user in users:
        if manager.is_user_online(user.id):
            await send_notification_to_user(user.id, notification)


# Exportar el gestor para uso en otros módulos
__all__ = ["router", "manager", "send_notification_to_user", "send_notification_to_company"]
