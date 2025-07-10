"""
Servicio para integración con APIs de IA (OpenAI, Gemini, etc.)
"""
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from abc import ABC, abstractmethod
import json
import logging
try:
    import google.generativeai
except ImportError:
    google = None

from app.core.config import get_settings
from app.models.chatbot import Chatbot

settings = get_settings()
logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Clase base para proveedores de IA"""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> str:
        """Generar respuesta de IA"""
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> AsyncGenerator[str, None]:
        """Generar respuesta de IA con streaming"""
        pass


class OpenAIProvider(AIProvider):
    """Proveedor de OpenAI"""
    
    def __init__(self, api_key: str, org_id: Optional[str] = None):
        self.api_key = api_key
        self.org_id = org_id
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                organization=self.org_id
            )
        return self._client
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> str:
        """Generar respuesta usando OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Error generating OpenAI response: {str(e)}")
    
    async def generate_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> AsyncGenerator[str, None]:
        """Generar respuesta streaming usando OpenAI"""
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"


class GeminiProvider(AIProvider):
    """Proveedor de Google Gemini"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel('gemini-pro')
            except ImportError:
                raise Exception("Google Generative AI library not installed. Install with: pip install google-generativeai")
        return self._client
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> str:
        """Generar respuesta usando Gemini"""
        try:
            # Convertir mensajes al formato de Gemini
            prompt = self._convert_messages_to_prompt(messages)
            
            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise Exception(f"Error generating Gemini response: {str(e)}")
    
    async def generate_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> AsyncGenerator[str, None]:
        """Generar respuesta streaming usando Gemini"""
        try:
            prompt = self._convert_messages_to_prompt(messages)
            
            # Gemini no tiene streaming nativo, simular
            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
            )
            
            # Simular streaming dividiendo la respuesta
            words = response.text.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)  # Pequeño delay para simular streaming
                
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convertir mensajes de OpenAI format a prompt de Gemini"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n".join(prompt_parts)


class MockProvider(AIProvider):
    """Proveedor mock para desarrollo"""
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> str:
        """Generar respuesta mock"""
        user_message = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        return f"Esta es una respuesta simulada del modelo {model} para el mensaje: '{user_message}'. Temperatura: {temperature}, Max tokens: {max_tokens}"
    
    async def generate_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> AsyncGenerator[str, None]:
        """Generar respuesta streaming mock"""
        response = await self.generate_response(messages, model, temperature, max_tokens)
        
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)  # Simular delay


class AIService:
    """Servicio principal para manejo de IA"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Inicializar proveedores disponibles"""
        
        # OpenAI
        if settings.OPENAI_API_KEY and not settings.MOCK_EXTERNAL_APIS:
            self.providers['openai'] = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                org_id=getattr(settings, 'OPENAI_ORG_ID', None)
            )
            logger.info("OpenAI provider initialized")
        
        # Gemini
        if settings.GEMINI_API_KEY and not settings.MOCK_EXTERNAL_APIS:
            self.providers['gemini'] = GeminiProvider(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini provider initialized")
        
        # Mock provider (siempre disponible)
        self.providers['mock'] = MockProvider()
        logger.info("Mock provider initialized")
    
    def _get_provider_for_model(self, model: str) -> AIProvider:
        """Obtener proveedor apropiado para el modelo"""
        
        if settings.MOCK_EXTERNAL_APIS:
            return self.providers['mock']
        
        # Mapeo de modelos a proveedores
        if model.startswith('gpt-'):
            if 'openai' in self.providers:
                return self.providers['openai']
        elif model.startswith('gemini-'):
            if 'gemini' in self.providers:
                return self.providers['gemini']
        
        # Fallback a mock si no hay proveedor disponible
        logger.warning(f"No provider available for model {model}, using mock")
        return self.providers['mock']
    
    async def generate_chatbot_response(
        self,
        chatbot: Chatbot,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generar respuesta del chatbot"""
        try:
            provider = self._get_provider_for_model(chatbot.model)
            
            # Preparar mensajes con system prompt
            messages = [
                {"role": "system", "content": chatbot.system_prompt}
            ] + conversation_history
            
            response = await provider.generate_response(
                messages=messages,
                model=chatbot.model,
                temperature=chatbot.temperature,
                max_tokens=chatbot.max_tokens
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}")
            return f"Lo siento, ocurrió un error al generar la respuesta: {str(e)}"
    
    async def generate_streaming_chatbot_response(
        self,
        chatbot: Chatbot,
        conversation_history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Generar respuesta streaming del chatbot"""
        try:
            provider = self._get_provider_for_model(chatbot.model)
            
            # Preparar mensajes con system prompt
            messages = [
                {"role": "system", "content": chatbot.system_prompt}
            ] + conversation_history
            
            async for chunk in provider.generate_streaming_response(
                messages=messages,
                model=chatbot.model,
                temperature=chatbot.temperature,
                max_tokens=chatbot.max_tokens
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Obtener modelos disponibles por proveedor"""
        models = {
            'openai': [
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k',
                'gpt-4',
                'gpt-4-turbo-preview'
            ],
            'gemini': [
                'gemini-pro',
                'gemini-pro-vision'
            ],
            'mock': [
                'mock-model'
            ]
        }
        
        # Filtrar por proveedores disponibles
        available_models = {}
        for provider_name, provider in self.providers.items():
            if provider_name in models:
                available_models[provider_name] = models[provider_name]
        
        return available_models


# Instancia global del servicio
ai_service = AIService()
