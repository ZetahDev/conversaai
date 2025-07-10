"""
Integración con WhatsApp Business API
"""
import httpx
import json
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.config import settings
from app.models.chatbot import Chatbot
from ..services.chatbot_service import ChatbotService

class WhatsAppIntegration:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        
    async def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verificar webhook de WhatsApp"""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        raise HTTPException(status_code=403, detail="Forbidden")
    
    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar webhook de WhatsApp"""
        try:
            # Extraer información del mensaje
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Verificar si hay mensajes
            messages = value.get("messages", [])
            if not messages:
                return {"status": "no_messages"}
            
            message = messages[0]
            phone_number = message.get("from")
            message_text = message.get("text", {}).get("body", "")
            message_id = message.get("id")
            
            # Obtener información del contacto
            contacts = value.get("contacts", [{}])
            contact_name = contacts[0].get("profile", {}).get("name", "Usuario")
            
            # Buscar chatbot asociado al número de WhatsApp
            whatsapp_number = value.get("metadata", {}).get("phone_number_id")
            chatbot = await self.get_chatbot_by_whatsapp_number(whatsapp_number)
            
            if not chatbot:
                return {"status": "no_chatbot_found"}
            
            # Procesar mensaje con el chatbot
            chatbot_service = ChatbotService()
            response = await chatbot_service.process_message(
                chatbot_id=chatbot.id,
                message=message_text,
                user_id=phone_number,  # Usar número de teléfono como user_id
                platform="whatsapp",
                metadata={
                    "contact_name": contact_name,
                    "message_id": message_id,
                    "phone_number": phone_number
                }
            )
            
            # Enviar respuesta por WhatsApp
            await self.send_message(
                phone_number_id=whatsapp_number,
                to=phone_number,
                message=response.get("response", "Lo siento, no pude procesar tu mensaje."),
                access_token=chatbot.whatsapp_token
            )
            
            return {"status": "success", "response": response}
            
        except Exception as e:
            print(f"Error processing WhatsApp webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    async def send_message(
        self, 
        phone_number_id: str, 
        to: str, 
        message: str, 
        access_token: str
    ) -> Dict[str, Any]:
        """Enviar mensaje por WhatsApp"""
        url = f"{self.base_url}/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json()
    
    async def send_template_message(
        self,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str,
        access_token: str,
        parameters: Optional[list] = None
    ) -> Dict[str, Any]:
        """Enviar mensaje de plantilla por WhatsApp"""
        url = f"{self.base_url}/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        template_data = {
            "name": template_name,
            "language": {"code": language_code}
        }
        
        if parameters:
            template_data["components"] = [{
                "type": "body",
                "parameters": parameters
            }]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_data
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json()
    
    async def get_chatbot_by_whatsapp_number(self, phone_number_id: str) -> Optional[Chatbot]:
        """Obtener chatbot por número de WhatsApp"""
        from ..core.database import get_db
        from ..models.integration import Integration, IntegrationType
        from ..models.chatbot import Chatbot

        db = next(get_db())
        try:
            # Buscar integración de WhatsApp con el phone_number_id
            integration = db.query(Integration).filter(
                Integration.integration_type == IntegrationType.WHATSAPP,
                Integration.channel_config.contains({"phone_number_id": phone_number_id})
            ).first()

            if integration:
                return integration.chatbot
            return None
        finally:
            db.close()
    
    async def setup_webhook(self, chatbot_id: int, phone_number_id: str, access_token: str) -> Dict[str, Any]:
        """Configurar webhook para WhatsApp"""
        webhook_url = f"{settings.BASE_URL}/api/v1/integrations/whatsapp/webhook"
        
        url = f"{self.base_url}/{phone_number_id}/webhooks"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "webhook_url": webhook_url,
            "verify_token": self.verify_token,
            "fields": ["messages", "message_deliveries", "message_reads"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json()

# Configuración de WhatsApp Business
class WhatsAppConfig:
    """Configuración para WhatsApp Business"""
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "step": 1,
                    "title": "Crear App en Meta for Developers",
                    "description": "Ve a developers.facebook.com y crea una nueva app",
                    "url": "https://developers.facebook.com/apps/"
                },
                {
                    "step": 2,
                    "title": "Agregar WhatsApp Business API",
                    "description": "Agrega el producto WhatsApp Business API a tu app"
                },
                {
                    "step": 3,
                    "title": "Configurar Webhook",
                    "description": f"Configura el webhook URL: {settings.BASE_URL}/api/v1/integrations/whatsapp/webhook"
                },
                {
                    "step": 4,
                    "title": "Obtener Token de Acceso",
                    "description": "Genera un token de acceso permanente para tu número de WhatsApp Business"
                },
                {
                    "step": 5,
                    "title": "Verificar Número",
                    "description": "Verifica tu número de WhatsApp Business en la consola de Meta"
                }
            ],
            "webhook_url": f"{settings.BASE_URL}/api/v1/integrations/whatsapp/webhook",
            "verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "required_permissions": [
                "whatsapp_business_messaging",
                "whatsapp_business_management"
            ]
        }
