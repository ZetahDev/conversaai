"""
Modelos de Base de Conocimiento y Documentos
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from enum import Enum
from datetime import datetime

from .base import BaseModel


class KnowledgeBaseStatus(str, Enum):
    """Estados de la base de conocimiento"""
    DRAFT = "draft"
    PROCESSING = "processing"
    ACTIVE = "active"
    ERROR = "error"
    PAUSED = "paused"


class DocumentType(str, Enum):
    """Tipos de documento"""
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    URL = "url"
    FAQ = "faq"
    MANUAL = "manual"
    POLICY = "policy"
    PRODUCT_INFO = "product_info"


class DocumentStatus(str, Enum):
    """Estados del documento"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"
    ARCHIVED = "archived"


class ChunkType(str, Enum):
    """Tipos de chunk"""
    PARAGRAPH = "paragraph"
    SECTION = "section"
    SENTENCE = "sentence"
    CUSTOM = "custom"


class KnowledgeBase(BaseModel):
    """Base de conocimiento del chatbot"""
    __tablename__ = "knowledge_bases"
    
    # Información básica
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(KnowledgeBaseStatus), nullable=False, default=KnowledgeBaseStatus.DRAFT)
    
    # Configuración
    language = Column(String(10), nullable=False, default="es")
    auto_update = Column(Boolean, default=False, nullable=False)
    update_frequency_hours = Column(Integer, nullable=True)  # Para auto-update
    
    # Configuración de vectorización
    embedding_model = Column(String(100), nullable=False, default="text-embedding-ada-002")
    chunk_size = Column(Integer, nullable=False, default=1000)
    chunk_overlap = Column(Integer, nullable=False, default=200)
    
    # Métricas
    total_documents = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuración avanzada
    similarity_threshold = Column(Float, nullable=False, default=0.7)
    max_results = Column(Integer, nullable=False, default=5)
    
    # Metadatos
    kb_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    company_id = Column(String(36), ForeignKey('companies.id'), nullable=False, index=True)
    company = relationship("Company", back_populates="knowledge_bases")

    chatbot_id = Column(String(36), ForeignKey('chatbots.id'), nullable=False, index=True)
    chatbot = relationship("Chatbot", back_populates="knowledge_bases")

    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_ready(self) -> bool:
        """Verificar si está lista para usar"""
        return self.status == KnowledgeBaseStatus.ACTIVE and self.total_chunks > 0
    
    def update_metrics(self):
        """Actualizar métricas desde documentos"""
        self.total_documents = len([d for d in self.documents if not d.is_deleted])
        self.total_chunks = sum(d.chunk_count for d in self.documents if not d.is_deleted)
        self.total_tokens = sum(d.token_count for d in self.documents if not d.is_deleted)
        self.last_updated_at = datetime.utcnow()


class Document(BaseModel):
    """Documento en la base de conocimiento"""
    __tablename__ = "documents"
    
    # Información básica
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=True)  # Contenido extraído
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.PENDING)
    
    # Fuente del documento
    source_url = Column(String(1000), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # En bytes
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    
    # Metadatos de procesamiento
    extracted_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Métricas
    chunk_count = Column(Integer, default=0, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    character_count = Column(Integer, default=0, nullable=False)
    
    # Configuración
    priority = Column(Integer, default=1, nullable=False)  # 1-10
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Metadatos adicionales
    doc_metadata = Column(JSON, nullable=True, default=dict)
    tags = Column(JSON, nullable=True, default=list)
    
    # Relaciones
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey('knowledge_bases.id'), nullable=False, index=True)
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', type='{self.document_type}')>"
    
    @property
    def is_processed(self) -> bool:
        """Verificar si está procesado"""
        return self.status == DocumentStatus.PROCESSED
    
    @property
    def is_url_source(self) -> bool:
        """Verificar si es de URL"""
        return self.document_type == DocumentType.URL and self.source_url is not None
    
    def mark_as_processed(self):
        """Marcar como procesado"""
        self.status = DocumentStatus.PROCESSED
        self.processed_at = datetime.utcnow()
    
    def mark_as_error(self, error_message: str):
        """Marcar como error"""
        self.status = DocumentStatus.ERROR
        self.error_message = error_message
    
    def update_metrics(self):
        """Actualizar métricas desde chunks"""
        self.chunk_count = len([c for c in self.chunks if not c.is_deleted])
        self.token_count = sum(c.token_count for c in self.chunks if not c.is_deleted)
        if self.content:
            self.character_count = len(self.content)
    
    def add_tag(self, tag: str):
        """Agregar tag"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)


class DocumentChunk(BaseModel):
    """Chunk de documento para vectorización"""
    __tablename__ = "document_chunks"
    
    # Contenido
    content = Column(Text, nullable=False)
    chunk_type = Column(SQLEnum(ChunkType), nullable=False, default=ChunkType.PARAGRAPH)
    
    # Posición en el documento
    chunk_index = Column(Integer, nullable=False)
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    
    # Métricas
    token_count = Column(Integer, nullable=False, default=0)
    character_count = Column(Integer, nullable=False, default=0)
    
    # Vector embedding
    embedding_vector = Column(JSON, nullable=True)  # Array de floats
    embedding_model = Column(String(100), nullable=True)
    
    # Metadatos para búsqueda
    keywords = Column(JSON, nullable=True, default=list)
    summary = Column(Text, nullable=True)
    
    # Configuración
    similarity_threshold = Column(Float, nullable=True)
    is_indexed = Column(Boolean, default=False, nullable=False)
    
    # Metadatos adicionales
    chunk_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relaciones
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False, index=True)
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
    
    @property
    def is_vectorized(self) -> bool:
        """Verificar si tiene vector embedding"""
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
    
    def set_embedding(self, vector: list, model: str):
        """Establecer vector embedding"""
        self.embedding_vector = vector
        self.embedding_model = model
        self.is_indexed = True
    
    def calculate_similarity(self, other_vector: list) -> float:
        """Calcular similitud coseno con otro vector"""
        if not self.is_vectorized or not other_vector:
            return 0.0
        
        # Implementación simple de similitud coseno
        import math
        
        dot_product = sum(a * b for a, b in zip(self.embedding_vector, other_vector))
        magnitude_a = math.sqrt(sum(a * a for a in self.embedding_vector))
        magnitude_b = math.sqrt(sum(b * b for b in other_vector))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def update_metrics(self):
        """Actualizar métricas del chunk"""
        if self.content:
            self.character_count = len(self.content)
            # Estimación simple de tokens (1 token ≈ 4 caracteres)
            self.token_count = max(1, len(self.content) // 4)
