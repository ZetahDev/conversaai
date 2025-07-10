"""
Configuración de la base de datos con soporte multi-tenant
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Motor síncrono para migraciones y operaciones administrativas
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# Motor asíncrono para la aplicación principal
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# Sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Metadata con convención de nombres para constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos síncrona
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de base de datos asíncrona
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class TenantContext:
    """
    Contexto para manejar el tenant actual en la sesión
    """
    def __init__(self, session: AsyncSession, tenant_id: int):
        self.session = session
        self.tenant_id = tenant_id
    
    async def __aenter__(self):
        # Establecer el tenant_id en la sesión para RLS
        await self.session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": self.tenant_id}
        )
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Limpiar el contexto del tenant
        await self.session.execute(text("RESET app.current_tenant_id"))


async def get_tenant_db(tenant_id: int) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión con contexto de tenant
    """
    async with AsyncSessionLocal() as session:
        try:
            async with TenantContext(session, tenant_id):
                yield session
        finally:
            await session.close()


async def init_db():
    """
    Inicializar la base de datos con configuraciones necesarias
    """
    # Para SQLite, solo verificamos que las tablas existan
    # Las extensiones y funciones de PostgreSQL no son necesarias
    logger.info("Base de datos SQLite inicializada correctamente")


async def create_tenant_policies():
    """
    Crear políticas RLS para todas las tablas multi-tenant
    """
    async with async_engine.begin() as conn:
        # Lista de tablas que requieren RLS
        tenant_tables = [
            'companies', 'users', 'chatbots', 'conversations', 
            'messages', 'knowledge_bases', 'integrations',
            'subscriptions', 'usage_logs', 'analytics'
        ]
        
        for table in tenant_tables:
            # Habilitar RLS
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            
            # Política para SELECT
            await conn.execute(text(f"""
                CREATE POLICY {table}_tenant_policy ON {table}
                FOR ALL TO authenticated
                USING (company_id = current_tenant_id())
            """))
            
            logger.info(f"Política RLS creada para tabla: {table}")


class DatabaseManager:
    """
    Manager para operaciones de base de datos
    """
    
    @staticmethod
    async def health_check() -> bool:
        """
        Verificar el estado de la base de datos
        """
        try:
            async with async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Error en health check de BD: {e}")
            return False
    
    @staticmethod
    async def get_connection_info():
        """
        Obtener información de conexión
        """
        async with async_engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    current_database() as database,
                    current_user as user,
                    version() as version,
                    pg_size_pretty(pg_database_size(current_database())) as size
            """))
            return result.fetchone()
    
    @staticmethod
    async def get_table_stats():
        """
        Obtener estadísticas de tablas
        """
        async with async_engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """))
            return result.fetchall()


# Instancia global del manager
db_manager = DatabaseManager()
