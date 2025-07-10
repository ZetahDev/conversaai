"""
Endpoints para integraciones de chatbots
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from ...deps import get_current_user, get_db
from ...models.user import User
from ...integrations.whatsapp import WhatsAppIntegration, WhatsAppConfig
from ...integrations.telegram import TelegramIntegration, TelegramConfig
from ...integrations.web_widget import WebWidgetIntegration, WebWidgetConfig

router = APIRouter()

# Instancias de integraciones
whatsapp = WhatsAppIntegration()
telegram = TelegramIntegration()
web_widget = WebWidgetIntegration()

# ==================== WHATSAPP ====================

@router.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verificar webhook de WhatsApp"""
    return PlainTextResponse(
        await whatsapp.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    )

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Procesar mensajes de WhatsApp"""
    data = await request.json()
    result = await whatsapp.process_webhook(data)
    return result

@router.post("/whatsapp/setup/{chatbot_id}")
async def setup_whatsapp_integration(
    chatbot_id: int,
    phone_number_id: str,
    access_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configurar integración con WhatsApp"""
    result = await whatsapp.setup_webhook(chatbot_id, phone_number_id, access_token)
    return result

@router.get("/whatsapp/config")
async def get_whatsapp_config():
    """Obtener configuración de WhatsApp"""
    return WhatsAppConfig.get_setup_instructions()

# ==================== TELEGRAM ====================

@router.post("/telegram/webhook/{bot_token}")
async def telegram_webhook(bot_token: str, request: Request):
    """Procesar mensajes de Telegram"""
    data = await request.json()
    result = await telegram.process_webhook(data, bot_token)
    return result

@router.post("/telegram/setup/{chatbot_id}")
async def setup_telegram_integration(
    chatbot_id: int,
    bot_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configurar integración con Telegram"""
    # Verificar que el token sea válido
    bot_info = await telegram.get_bot_info(bot_token)
    if not bot_info.get("ok"):
        raise HTTPException(status_code=400, detail="Token de bot inválido")
    
    # Configurar webhook
    result = await telegram.setup_webhook(bot_token, chatbot_id)
    return {
        "bot_info": bot_info,
        "webhook_result": result
    }

@router.delete("/telegram/webhook/{bot_token}")
async def delete_telegram_webhook(bot_token: str):
    """Eliminar webhook de Telegram"""
    result = await telegram.delete_webhook(bot_token)
    return result

@router.get("/telegram/config")
async def get_telegram_config():
    """Obtener configuración de Telegram"""
    return TelegramConfig.get_setup_instructions()

# ==================== WEB WIDGET ====================

@router.post("/web/message/{chatbot_id}")
async def web_widget_message(
    chatbot_id: int,
    message: str,
    session_id: str,
    user_data: Optional[Dict[str, Any]] = None
):
    """Procesar mensaje del widget web"""
    result = await web_widget.process_message(
        chatbot_id=chatbot_id,
        message=message,
        session_id=session_id,
        user_data=user_data
    )
    return result

@router.get("/web/widget-code/{chatbot_id}")
async def get_widget_code(
    chatbot_id: int,
    widget_type: str = "embedded",
    config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Generar código del widget web"""
    if widget_type == "embedded":
        code = web_widget.generate_widget_code(chatbot_id, config)
    elif widget_type == "iframe":
        code = web_widget.generate_iframe_code(chatbot_id, config)
    elif widget_type == "popup":
        code = web_widget.generate_popup_code(chatbot_id, config)
    else:
        raise HTTPException(status_code=400, detail="Tipo de widget no válido")
    
    return {"code": code, "type": widget_type}

@router.get("/web/config")
async def get_web_widget_config():
    """Obtener configuración del widget web"""
    return WebWidgetConfig.get_setup_instructions()

# ==================== GENERAL ====================

@router.get("/available")
async def get_available_integrations():
    """Obtener integraciones disponibles"""
    return {
        "integrations": [
            {
                "id": "whatsapp",
                "name": "WhatsApp Business",
                "description": "Integra tu chatbot con WhatsApp Business API",
                "icon": "📱",
                "status": "available",
                "features": [
                    "Mensajes de texto",
                    "Plantillas de mensaje",
                    "Multimedia",
                    "Botones interactivos"
                ]
            },
            {
                "id": "telegram",
                "name": "Telegram Bot",
                "description": "Crea un bot de Telegram para tu chatbot",
                "icon": "✈️",
                "status": "available",
                "features": [
                    "Mensajes de texto",
                    "Comandos personalizados",
                    "Teclados inline",
                    "Multimedia"
                ]
            },
            {
                "id": "web",
                "name": "Widget Web",
                "description": "Embebe tu chatbot en cualquier sitio web",
                "icon": "🌐",
                "status": "available",
                "features": [
                    "Widget embebido",
                    "Popup flotante",
                    "iFrame",
                    "Personalización completa"
                ]
            },
            {
                "id": "facebook",
                "name": "Facebook Messenger",
                "description": "Integra con Facebook Messenger",
                "icon": "💬",
                "status": "coming_soon",
                "features": [
                    "Mensajes de texto",
                    "Plantillas",
                    "Botones rápidos"
                ]
            },
            {
                "id": "instagram",
                "name": "Instagram Direct",
                "description": "Responde mensajes directos de Instagram",
                "icon": "📸",
                "status": "coming_soon",
                "features": [
                    "Mensajes directos",
                    "Respuestas automáticas",
                    "Multimedia"
                ]
            }
        ]
    }

@router.get("/status/{chatbot_id}")
async def get_integration_status(
    chatbot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estado de integraciones para un chatbot"""
    # Implementar lógica para verificar qué integraciones están activas
    return {
        "chatbot_id": chatbot_id,
        "integrations": {
            "whatsapp": {
                "active": False,
                "configured": False,
                "last_message": None
            },
            "telegram": {
                "active": False,
                "configured": False,
                "last_message": None
            },
            "web": {
                "active": True,
                "configured": True,
                "last_message": None
            }
        }
    }
