"""
Configuración de la aplicación usando Pydantic Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""
    
    # Aplicación
    APP_NAME: str = "ConversaAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BASE_URL: str = "http://localhost:8000"

    # Integraciones
    WHATSAPP_VERIFY_TOKEN: str = secrets.token_urlsafe(32)
    
    # Base de datos
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    REDIS_ENABLED: bool = True
    
    # APIs de IA
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Vector Database
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: str = "us-west1-gcp-free"
    PINECONE_INDEX_NAME: str = "chatbot-vectors"

    # Qdrant (alternativa)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_ENABLED: bool = False

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_ENABLED: bool = False
    
    # WhatsApp
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # Facebook
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_VERIFY_TOKEN: Optional[str] = None
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Google Services
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_SHEETS_CREDENTIALS: Optional[str] = None
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: str = "chatbot-files"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "chatbot-files"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    FROM_EMAIL: Optional[str] = None
    EMAIL_ENABLED: bool = True
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:4321"
    
    # Webhooks
    WEBHOOK_SECRET: str = secrets.token_urlsafe(32)
    
    # Desarrollo
    RELOAD: bool = False
    WORKERS: int = 1
    
    # Ambiente
    ENVIRONMENT: str = "development"

    # Feature Flags
    WHATSAPP_ENABLED: bool = False
    TELEGRAM_ENABLED: bool = False
    FACEBOOK_ENABLED: bool = False

    # File Storage
    FILE_STORAGE_TYPE: str = "local"  # local, s3, minio
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB

    # Development flags
    MOCK_EXTERNAL_APIS: bool = False
    SKIP_EMAIL_VERIFICATION: bool = False

    # Security
    SENTRY_ENABLED: bool = False
    FORCE_HTTPS: bool = False
    SECURE_COOKIES: bool = False

    # Monitoring
    HEALTH_CHECK_ENABLED: bool = True
    METRICS_ENABLED: bool = False
    PROMETHEUS_ENABLED: bool = False
    
    @property
    def cors_origins(self) -> List[str]:
        """Convertir ALLOWED_ORIGINS string a lista"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [i.strip() for i in self.ALLOWED_ORIGINS.split(",") if i.strip()]
        return ["http://localhost:3000", "http://localhost:4321"]
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()


# Configuración específica para diferentes ambientes
class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    RELOAD: bool = True


class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    RELOAD: bool = False
    WORKERS: int = 4


class TestingSettings(Settings):
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    DATABASE_URL_ASYNC: str = "sqlite+aiosqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/15"  # Base de datos separada para tests


def get_settings() -> Settings:
    """Factory para obtener la configuración según el ambiente"""
    environment = settings.ENVIRONMENT.lower()
    
    if environment == "development":
        return DevelopmentSettings()
    elif environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return settings
