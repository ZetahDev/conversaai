#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de prueba
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.core.database import Base
from app.models.user import User
from app.models.company import Company
from app.models.chatbot import Chatbot
from app.core.security import SecurityManager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

settings = get_settings()

async def create_tables():
    """Crear todas las tablas"""
    print("🔧 Creando tablas de la base de datos...")
    
    engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Tablas creadas exitosamente")

async def create_test_data():
    """Crear datos de prueba"""
    print("📝 Creando datos de prueba...")
    
    engine = create_async_engine(settings.DATABASE_URL_ASYNC)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Crear empresa de prueba
            company = Company(
                name="TechCorp Demo",
                slug="techcorp-demo",
                email="admin@techcorp.com",
                website="https://techcorp-demo.com",
                description="Empresa de demostración para ChatBot SAAS",
                company_type="other",
                status="active"
            )
            session.add(company)
            await session.flush()  # Para obtener el ID
            
            # Crear usuario administrador
            admin_user = User(
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
            
            # Crear chatbots de prueba
            chatbot1 = Chatbot(
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
            
            chatbot3 = Chatbot(
                name="Asistente General",
                description="Chatbot de propósito general para consultas diversas",
                model="claude-3-sonnet",
                system_prompt="Eres un asistente virtual útil y amigable. Respondes preguntas generales y ayudas con diversas consultas.",
                temperature=0.5,
                max_tokens=180,
                status="DRAFT",
                company_id=company.id,
                created_by=regular_user.id
            )
            session.add(chatbot3)
            
            await session.commit()
            
            print("✅ Datos de prueba creados exitosamente:")
            print(f"   👤 Admin: admin@techcorp.com / admin123")
            print(f"   👤 Usuario: user@techcorp.com / user123")
            print(f"   🏢 Empresa: {company.name}")
            print(f"   🤖 Chatbots: {chatbot1.name}, {chatbot2.name}, {chatbot3.name}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creando datos de prueba: {e}")
            raise
        finally:
            await session.close()
    
    await engine.dispose()

async def reset_database():
    """Resetear la base de datos (eliminar y recrear)"""
    print("🗑️ Reseteando base de datos...")
    
    engine = create_async_engine(settings.DATABASE_URL_ASYNC)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Base de datos reseteada")

async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inicializar base de datos")
    parser.add_argument("--reset", action="store_true", help="Resetear base de datos")
    parser.add_argument("--no-data", action="store_true", help="No crear datos de prueba")
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            await reset_database()
        else:
            await create_tables()
        
        if not args.no_data:
            await create_test_data()
        
        print("🎉 Inicialización completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
