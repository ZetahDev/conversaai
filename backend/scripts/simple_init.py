#!/usr/bin/env python3
"""
Script simple para inicializar la base de datos con datos básicos
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.core.database import Base
from app.core.security import SecurityManager
from app.models.user import User
from app.models.company import Company
from app.models.chatbot import Chatbot
import uuid
from datetime import datetime

settings = get_settings()

async def create_tables():
    """Crear todas las tablas"""
    print("🔧 Creando tablas de la base de datos...")
    
    engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Tablas creadas exitosamente")

async def create_basic_data():
    """Crear datos básicos usando ORM"""
    print("📝 Creando datos básicos...")

    engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Crear empresa
            company = Company(
                id=str(uuid.uuid4()),
                name="TechCorp Demo",
                slug="techcorp-demo",
                email="admin@techcorp.com",
                company_type="other",
                status="active",
                max_users=10,
                max_chatbots=5,
                max_monthly_messages=10000
            )
            session.add(company)
            await session.flush()  # Para obtener el ID

            # Crear usuario administrador
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@techcorp.com",
                hashed_password=SecurityManager.get_password_hash("admin123"),
                full_name="Administrador Demo",
                role="SUPERADMIN",
                is_active=True,
                is_verified=True,
                company_id=company.id
            )
            session.add(admin_user)

            # Crear usuario regular
            regular_user = User(
                id=str(uuid.uuid4()),
                email="user@techcorp.com",
                hashed_password=SecurityManager.get_password_hash("user123"),
                full_name="Usuario Demo",
                role="USER",
                is_active=True,
                is_verified=True,
                company_id=company.id
            )
            session.add(regular_user)

            await session.flush()  # Para obtener los IDs de usuarios

            # Crear chatbots
            chatbot1 = Chatbot(
                id=str(uuid.uuid4()),
                name="Asistente de Ventas",
                description="Chatbot especializado en ventas y atención al cliente",
                model="gpt-3.5-turbo",
                system_prompt="Eres un asistente de ventas amigable y profesional. Ayudas a los clientes a encontrar productos y resolver dudas sobre compras.",
                temperature=0.7,
                max_tokens=150,
                status="ACTIVE",
                company_id=company.id,
                created_by=admin_user.id
            )
            session.add(chatbot1)

            chatbot2 = Chatbot(
                id=str(uuid.uuid4()),
                name="Soporte Técnico",
                description="Chatbot para resolver problemas técnicos y dudas sobre productos",
                model="gpt-4",
                system_prompt="Eres un especialista en soporte técnico. Ayudas a resolver problemas técnicos de manera clara y paso a paso.",
                temperature=0.3,
                max_tokens=200,
                status="ACTIVE",
                company_id=company.id,
                created_by=admin_user.id
            )
            session.add(chatbot2)

            await session.commit()

            print("✅ Datos básicos creados exitosamente:")
            print(f"   👤 Admin: admin@techcorp.com / admin123")
            print(f"   👤 Usuario: user@techcorp.com / user123")
            print(f"   🏢 Empresa: TechCorp Demo")
            print(f"   🤖 Chatbots: Asistente de Ventas, Soporte Técnico")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creando datos básicos: {e}")
            raise
        finally:
            await session.close()

    await engine.dispose()

async def main():
    """Función principal"""
    print("🎯 Inicialización Simple de Base de Datos")
    print("=" * 50)
    
    try:
        await create_tables()
        await create_basic_data()
        print("🎉 Inicialización completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
