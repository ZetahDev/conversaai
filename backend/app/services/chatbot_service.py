"""
Servicio para manejar la lógica de chatbots
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..models.chatbot import Chatbot
from ..models.conversation import Conversation, Message
from .ai_service import AIService
from ..core.database import get_db

class ChatbotService:
    def __init__(self):
        self.ai_service = AIService()
    
    async def process_message(
        self,
        chatbot_id: int,
        message: str,
        user_id: str,
        platform: str = "web",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar un mensaje enviado a un chatbot
        """
        try:
            # Obtener sesión de base de datos
            db = next(get_db())
            
            # Obtener el chatbot
            chatbot = db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
            if not chatbot:
                return {
                    "error": "Chatbot no encontrado",
                    "response": "Lo siento, no pude encontrar el chatbot."
                }
            
            # Verificar si el chatbot está activo
            if chatbot.status != "ACTIVE":
                return {
                    "error": "Chatbot inactivo",
                    "response": "El chatbot no está disponible en este momento."
                }
            
            # Obtener o crear conversación
            conversation = await self._get_or_create_conversation(
                db, chatbot_id, user_id, platform, conversation_id
            )
            
            # Guardar mensaje del usuario
            user_message = Message(
                conversation_id=conversation.id,
                content=message,
                role="user",
                platform=platform,
                metadata=metadata or {}
            )
            db.add(user_message)
            db.commit()
            
            # Obtener historial de conversación
            conversation_history = await self._get_conversation_history(
                db, conversation.id, limit=10
            )
            
            # Generar respuesta con IA
            ai_response = await self.ai_service.generate_response(
                model=chatbot.model,
                system_prompt=chatbot.system_prompt,
                conversation_history=conversation_history,
                user_message=message,
                temperature=chatbot.temperature,
                max_tokens=chatbot.max_tokens
            )
            
            # Guardar respuesta del bot
            bot_message = Message(
                conversation_id=conversation.id,
                content=ai_response.get("response", "Lo siento, no pude generar una respuesta."),
                role="assistant",
                platform=platform,
                metadata={
                    "model": chatbot.model,
                    "tokens_used": ai_response.get("tokens_used", 0),
                    "processing_time": ai_response.get("processing_time", 0)
                }
            )
            db.add(bot_message)
            
            # Actualizar estadísticas de la conversación
            conversation.message_count += 2  # Usuario + Bot
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "response": ai_response.get("response"),
                "conversation_id": conversation.id,
                "message_id": bot_message.id,
                "timestamp": bot_message.created_at.isoformat(),
                "tokens_used": ai_response.get("tokens_used", 0),
                "platform": platform
            }
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return {
                "error": str(e),
                "response": "Lo siento, ocurrió un error al procesar tu mensaje."
            }
        finally:
            db.close()
    
    async def _get_or_create_conversation(
        self,
        db: Session,
        chatbot_id: int,
        user_id: str,
        platform: str,
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """
        Obtener conversación existente o crear una nueva
        """
        if conversation_id:
            # Buscar conversación existente
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.chatbot_id == chatbot_id
            ).first()
            
            if conversation:
                return conversation
        
        # Buscar conversación activa del usuario
        active_conversation = db.query(Conversation).filter(
            Conversation.chatbot_id == chatbot_id,
            Conversation.user_id == user_id,
            Conversation.platform == platform,
            Conversation.status == "active"
        ).first()
        
        if active_conversation:
            return active_conversation
        
        # Crear nueva conversación
        new_conversation = Conversation(
            id=str(uuid.uuid4()),
            chatbot_id=chatbot_id,
            user_id=user_id,
            platform=platform,
            status="active",
            message_count=0
        )
        
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        
        return new_conversation
    
    async def _get_conversation_history(
        self,
        db: Session,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Obtener historial de conversación
        """
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Invertir para tener orden cronológico
        messages.reverse()
        
        history = []
        for message in messages:
            history.append({
                "role": message.role,
                "content": message.content
            })
        
        return history
    
    async def get_chatbot_stats(self, chatbot_id: int) -> Dict[str, Any]:
        """
        Obtener estadísticas de un chatbot
        """
        try:
            db = next(get_db())
            
            # Contar conversaciones
            total_conversations = db.query(Conversation).filter(
                Conversation.chatbot_id == chatbot_id
            ).count()
            
            # Contar mensajes
            total_messages = db.query(Message).join(Conversation).filter(
                Conversation.chatbot_id == chatbot_id
            ).count()
            
            # Conversaciones activas
            active_conversations = db.query(Conversation).filter(
                Conversation.chatbot_id == chatbot_id,
                Conversation.status == "active"
            ).count()
            
            # Plataformas utilizadas
            platforms = db.query(Conversation.platform).filter(
                Conversation.chatbot_id == chatbot_id
            ).distinct().all()
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_conversations": active_conversations,
                "platforms": [p[0] for p in platforms],
                "chatbot_id": chatbot_id
            }
            
        except Exception as e:
            print(f"Error getting chatbot stats: {e}")
            return {
                "error": str(e),
                "total_conversations": 0,
                "total_messages": 0,
                "active_conversations": 0,
                "platforms": []
            }
        finally:
            db.close()
    
    async def end_conversation(self, conversation_id: str) -> bool:
        """
        Finalizar una conversación
        """
        try:
            db = next(get_db())
            
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                conversation.status = "ended"
                conversation.updated_at = datetime.utcnow()
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error ending conversation: {e}")
            return False
        finally:
            db.close()
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtener mensajes de una conversación
        """
        try:
            db = next(get_db())
            
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).limit(limit).all()
            
            return [
                {
                    "id": message.id,
                    "content": message.content,
                    "role": message.role,
                    "platform": message.platform,
                    "created_at": message.created_at.isoformat(),
                    "metadata": message.metadata
                }
                for message in messages
            ]
            
        except Exception as e:
            print(f"Error getting conversation messages: {e}")
            return []
        finally:
            db.close()
