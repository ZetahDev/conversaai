"""
Integración con Widget Web
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.config import settings
from app.models.chatbot import Chatbot
from ..services.chatbot_service import ChatbotService

class WebWidgetIntegration:
    def __init__(self):
        self.widget_base_url = f"{settings.BASE_URL}/widget"
    
    async def process_message(
        self, 
        chatbot_id: int, 
        message: str, 
        session_id: str,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Procesar mensaje del widget web"""
        try:
            # Obtener chatbot
            chatbot = await self.get_chatbot_by_id(chatbot_id)
            if not chatbot:
                raise HTTPException(status_code=404, detail="Chatbot no encontrado")
            
            # Procesar mensaje con el chatbot
            chatbot_service = ChatbotService()
            response = await chatbot_service.process_message(
                chatbot_id=chatbot_id,
                message=message,
                user_id=session_id,
                platform="web",
                metadata={
                    "session_id": session_id,
                    "user_data": user_data or {},
                    "widget_version": "1.0"
                }
            )
            
            return {
                "status": "success",
                "response": response.get("response", "Lo siento, no pude procesar tu mensaje."),
                "conversation_id": response.get("conversation_id"),
                "timestamp": response.get("timestamp")
            }
            
        except Exception as e:
            print(f"Error processing web widget message: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "response": "Lo siento, ocurrió un error. Por favor intenta de nuevo."
            }
    
    async def get_chatbot_by_id(self, chatbot_id: int) -> Optional[Chatbot]:
        """Obtener chatbot por ID"""
        from ..core.database import get_db
        from ..models.chatbot import Chatbot

        db = next(get_db())
        try:
            chatbot = db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()
            return chatbot
        finally:
            db.close()
    
    def generate_widget_code(
        self, 
        chatbot_id: int, 
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generar código del widget para insertar en sitios web"""
        
        default_config = {
            "position": "bottom-right",
            "theme": "light",
            "primaryColor": "#3B82F6",
            "title": "Asistente Virtual",
            "subtitle": "¿En qué puedo ayudarte?",
            "placeholder": "Escribe tu mensaje...",
            "height": "500px",
            "width": "350px",
            "showAvatar": True,
            "showTimestamp": True,
            "enableSound": True,
            "autoOpen": False,
            "welcomeMessage": "¡Hola! ¿En qué puedo ayudarte hoy?"
        }
        
        # Combinar configuración por defecto con la personalizada
        widget_config = {**default_config, **(config or {})}
        
        widget_code = f"""
<!-- ChatBot SAAS Widget -->
<div id="chatbot-widget-{chatbot_id}"></div>
<script>
(function() {{
    // Configuración del widget
    window.ChatBotConfig = {{
        chatbotId: {chatbot_id},
        apiUrl: '{settings.BASE_URL}/api/v1/integrations/web',
        ...{widget_config}
    }};
    
    // Cargar estilos del widget
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '{self.widget_base_url}/widget.css';
    document.head.appendChild(link);
    
    // Cargar script del widget
    var script = document.createElement('script');
    script.src = '{self.widget_base_url}/widget.js';
    script.async = true;
    document.head.appendChild(script);
}})();
</script>
<!-- Fin ChatBot SAAS Widget -->
        """.strip()
        
        return widget_code
    
    def generate_iframe_code(
        self, 
        chatbot_id: int, 
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generar código iframe para el widget"""
        
        default_config = {
            "height": "500px",
            "width": "350px",
            "theme": "light"
        }
        
        widget_config = {**default_config, **(config or {})}
        
        # Crear parámetros de URL
        params = "&".join([f"{k}={v}" for k, v in widget_config.items()])
        
        iframe_code = f"""
<iframe 
    src="{self.widget_base_url}/chat/{chatbot_id}?{params}"
    width="{widget_config['width']}"
    height="{widget_config['height']}"
    frameborder="0"
    style="border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
    title="ChatBot Assistant">
</iframe>
        """.strip()
        
        return iframe_code
    
    def generate_popup_code(
        self, 
        chatbot_id: int, 
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generar código para popup del widget"""
        
        default_config = {
            "buttonText": "💬 Ayuda",
            "buttonColor": "#3B82F6",
            "position": "bottom-right",
            "margin": "20px"
        }
        
        widget_config = {**default_config, **(config or {})}
        
        popup_code = f"""
<!-- ChatBot SAAS Popup Widget -->
<div id="chatbot-popup-{chatbot_id}">
    <button 
        id="chatbot-toggle-{chatbot_id}"
        style="
            position: fixed;
            {widget_config['position'].split('-')[1]}: {widget_config['margin']};
            {widget_config['position'].split('-')[0]}: {widget_config['margin']};
            background: {widget_config['buttonColor']};
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 20px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-size: 14px;
            font-weight: 500;
        "
    >
        {widget_config['buttonText']}
    </button>
    
    <div 
        id="chatbot-container-{chatbot_id}"
        style="
            position: fixed;
            {widget_config['position'].split('-')[1]}: {widget_config['margin']};
            {widget_config['position'].split('-')[0]}: calc({widget_config['margin']} + 60px);
            width: 350px;
            height: 500px;
            z-index: 1001;
            display: none;
        "
    >
        <iframe 
            src="{self.widget_base_url}/chat/{chatbot_id}"
            width="100%"
            height="100%"
            frameborder="0"
            style="border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
            title="ChatBot Assistant">
        </iframe>
    </div>
</div>

<script>
(function() {{
    var button = document.getElementById('chatbot-toggle-{chatbot_id}');
    var container = document.getElementById('chatbot-container-{chatbot_id}');
    var isOpen = false;
    
    button.addEventListener('click', function() {{
        if (isOpen) {{
            container.style.display = 'none';
            button.textContent = '{widget_config['buttonText']}';
            isOpen = false;
        }} else {{
            container.style.display = 'block';
            button.textContent = '✕ Cerrar';
            isOpen = true;
        }}
    }});
}})();
</script>
<!-- Fin ChatBot SAAS Popup Widget -->
        """.strip()
        
        return popup_code

# Configuración del Widget Web
class WebWidgetConfig:
    """Configuración para Widget Web"""
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "step": 1,
                    "title": "Generar Código del Widget",
                    "description": "Copia el código generado para tu chatbot"
                },
                {
                    "step": 2,
                    "title": "Insertar en tu Sitio Web",
                    "description": "Pega el código antes del cierre de la etiqueta </body>"
                },
                {
                    "step": 3,
                    "title": "Personalizar Apariencia",
                    "description": "Ajusta colores, posición y mensajes según tu marca"
                },
                {
                    "step": 4,
                    "title": "Probar Funcionamiento",
                    "description": "Verifica que el widget funcione correctamente en tu sitio"
                }
            ],
            "widget_types": [
                {
                    "type": "embedded",
                    "name": "Widget Embebido",
                    "description": "Se integra directamente en tu página web"
                },
                {
                    "type": "iframe",
                    "name": "iFrame",
                    "description": "Widget en un marco independiente"
                },
                {
                    "type": "popup",
                    "name": "Popup Flotante",
                    "description": "Botón flotante que abre el chat"
                }
            ],
            "customization_options": [
                "Colores y tema",
                "Posición en pantalla",
                "Mensajes personalizados",
                "Avatar y branding",
                "Sonidos y notificaciones"
            ]
        }
