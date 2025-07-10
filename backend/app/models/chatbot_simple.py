"""
Modelo simplificado de Chatbot para la estructura actual de la base de datos
"""
from sqlalchemy import Column, String, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .base import BaseModel


class ChatbotSimple(BaseModel):
    """Modelo simplificado de chatbot que coincide con la estructura actual de la BD"""
    __tablename__ = "chatbots"
    __table_args__ = {'extend_existing': True}
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    model = Column(String(100), nullable=False, default="gpt-3.5-turbo")
    system_prompt = Column(Text, nullable=True)
    
    # Configuración de IA
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=150)
    
    # Estado
    status = Column(String(50), nullable=False, default="DRAFT")
    
    # Relaciones
    company_id = Column(String(36), nullable=False, index=True)
    created_by = Column(String(36), nullable=True)
    
    def __repr__(self):
        return f"<ChatbotSimple(id={self.id}, name={self.name}, status={self.status})>"
