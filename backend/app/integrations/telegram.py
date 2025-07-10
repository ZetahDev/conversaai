"""
Integración con Telegram Bot API
"""
import httpx
import json
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from app.core.config import settings
from app.models.chatbot import Chatbot
from ..services.chatbot_service import ChatbotService

class TelegramIntegration:
    def __init__(self):
        self.base_url = "https://api.telegram.org/bot"
    
    async def process_webhook(self, data: Dict[str, Any], bot_token: str) -> Dict[str, Any]:
        """Procesar webhook de Telegram"""
        try:
            # Extraer información del mensaje
            message = data.get("message", {})
            if not message:
                return {"status": "no_message"}
            
            chat_id = message.get("chat", {}).get("id")
            user_id = message.get("from", {}).get("id")
            username = message.get("from", {}).get("username", "")
            first_name = message.get("from", {}).get("first_name", "Usuario")
            message_text = message.get("text", "")
            message_id = message.get("message_id")
            
            # Buscar chatbot asociado al token
            chatbot = await self.get_chatbot_by_telegram_token(bot_token)
            
            if not chatbot:
                return {"status": "no_chatbot_found"}
            
            # Procesar comandos especiales
            if message_text.startswith("/"):
                return await self.handle_command(
                    command=message_text,
                    chat_id=chat_id,
                    bot_token=bot_token,
                    user_name=first_name
                )
            
            # Procesar mensaje con el chatbot
            chatbot_service = ChatbotService()
            response = await chatbot_service.process_message(
                chatbot_id=chatbot.id,
                message=message_text,
                user_id=str(user_id),
                platform="telegram",
                metadata={
                    "chat_id": chat_id,
                    "username": username,
                    "first_name": first_name,
                    "message_id": message_id
                }
            )
            
            # Enviar respuesta por Telegram
            await self.send_message(
                bot_token=bot_token,
                chat_id=chat_id,
                text=response.get("response", "Lo siento, no pude procesar tu mensaje.")
            )
            
            return {"status": "success", "response": response}
            
        except Exception as e:
            print(f"Error processing Telegram webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_command(
        self, 
        command: str, 
        chat_id: int, 
        bot_token: str, 
        user_name: str
    ) -> Dict[str, Any]:
        """Manejar comandos de Telegram"""
        if command == "/start":
            welcome_message = f"¡Hola {user_name}! 👋\n\nSoy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
            await self.send_message(bot_token, chat_id, welcome_message)
            
        elif command == "/help":
            help_message = """
🤖 **Comandos disponibles:**

/start - Iniciar conversación
/help - Mostrar esta ayuda
/info - Información del bot
/reset - Reiniciar conversación

💬 También puedes escribirme cualquier pregunta y te ayudaré lo mejor que pueda.
            """
            await self.send_message(bot_token, chat_id, help_message, parse_mode="Markdown")
            
        elif command == "/info":
            info_message = "🤖 **ConversaAI**\n\nSoy un asistente virtual inteligente creado para ayudarte."
            await self.send_message(bot_token, chat_id, info_message, parse_mode="Markdown")
            
        elif command == "/reset":
            reset_message = "🔄 Conversación reiniciada. ¡Empecemos de nuevo!"
            await self.send_message(bot_token, chat_id, reset_message)
        
        return {"status": "command_handled", "command": command}
    
    async def send_message(
        self, 
        bot_token: str, 
        chat_id: int, 
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Enviar mensaje por Telegram"""
        url = f"{self.base_url}{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
            
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.json()
    
    async def send_photo(
        self, 
        bot_token: str, 
        chat_id: int, 
        photo_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enviar foto por Telegram"""
        url = f"{self.base_url}{bot_token}/sendPhoto"
        
        payload = {
            "chat_id": chat_id,
            "photo": photo_url
        }
        
        if caption:
            payload["caption"] = caption
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.json()
    
    async def send_keyboard(
        self, 
        bot_token: str, 
        chat_id: int, 
        text: str,
        buttons: List[List[str]]
    ) -> Dict[str, Any]:
        """Enviar mensaje con teclado personalizado"""
        keyboard = {
            "keyboard": [[{"text": button} for button in row] for row in buttons],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
        
        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def send_inline_keyboard(
        self, 
        bot_token: str, 
        chat_id: int, 
        text: str,
        buttons: List[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        """Enviar mensaje con teclado inline"""
        keyboard = {
            "inline_keyboard": buttons
        }
        
        return await self.send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def get_chatbot_by_telegram_token(self, bot_token: str) -> Optional[Chatbot]:
        """Obtener chatbot por token de Telegram"""
        from ..core.database import get_db
        from ..models.integration import Integration, IntegrationType
        from ..models.chatbot import Chatbot

        db = next(get_db())
        try:
            # Buscar integración de Telegram con el bot_token
            integration = db.query(Integration).filter(
                Integration.integration_type == IntegrationType.TELEGRAM,
                Integration.api_key == bot_token
            ).first()

            if integration:
                return integration.chatbot
            return None
        finally:
            db.close()
    
    async def setup_webhook(self, bot_token: str, chatbot_id: int) -> Dict[str, Any]:
        """Configurar webhook para Telegram"""
        webhook_url = f"{settings.BASE_URL}/api/v1/integrations/telegram/webhook/{bot_token}"
        
        url = f"{self.base_url}{bot_token}/setWebhook"
        
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.json()
    
    async def get_bot_info(self, bot_token: str) -> Dict[str, Any]:
        """Obtener información del bot"""
        url = f"{self.base_url}{bot_token}/getMe"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    
    async def delete_webhook(self, bot_token: str) -> Dict[str, Any]:
        """Eliminar webhook"""
        url = f"{self.base_url}{bot_token}/deleteWebhook"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            return response.json()

# Configuración de Telegram Bot
class TelegramConfig:
    """Configuración para Telegram Bot"""
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "step": 1,
                    "title": "Crear Bot con BotFather",
                    "description": "Habla con @BotFather en Telegram y usa /newbot",
                    "url": "https://t.me/BotFather"
                },
                {
                    "step": 2,
                    "title": "Obtener Token del Bot",
                    "description": "BotFather te dará un token único para tu bot"
                },
                {
                    "step": 3,
                    "title": "Configurar Webhook",
                    "description": f"El sistema configurará automáticamente el webhook"
                },
                {
                    "step": 4,
                    "title": "Personalizar Bot",
                    "description": "Configura nombre, descripción y foto de perfil con BotFather"
                },
                {
                    "step": 5,
                    "title": "Probar Bot",
                    "description": "Envía /start a tu bot para probarlo"
                }
            ],
            "webhook_url_pattern": f"{settings.BASE_URL}/api/v1/integrations/telegram/webhook/{{bot_token}}",
            "botfather_url": "https://t.me/BotFather",
            "commands": [
                {"command": "start", "description": "Iniciar conversación"},
                {"command": "help", "description": "Mostrar ayuda"},
                {"command": "info", "description": "Información del bot"},
                {"command": "reset", "description": "Reiniciar conversación"}
            ]
        }
