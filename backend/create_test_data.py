#!/usr/bin/env python3
"""
Script para crear datos de prueba incluyendo superadmin y empresa
"""
import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_async_db, async_engine
from app.core.security import SecurityManager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid

async def create_test_data():
    """Crear datos de prueba completos"""
    print("🚀 Creando datos de prueba...")
    
    try:
        # Obtener sesión de base de datos
        async for db in get_async_db():
            # 1. Crear empresa principal
            company_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO companies (id, name, slug, email, status, company_type, created_at, updated_at, is_deleted)
                VALUES (:id, :name, :slug, :email, :status, :company_type, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """), {
                "id": company_id,
                "name": "TechCorp Solutions",
                "slug": "techcorp-solutions",
                "email": "contacto@techcorp.com",
                "status": "ACTIVE",
                "company_type": "ECOMMERCE"
            })
            
            print(f"✅ Empresa creada: TechCorp Solutions (ID: {company_id})")
            
            # 2. Crear superadmin (tu usuario)
            superadmin_id = str(uuid.uuid4())
            password_hash = SecurityManager.get_password_hash("SuperAdmin123!")
            
            await db.execute(text("""
                INSERT INTO users (id, username, email, password_hash, full_name, role, status, company_id, created_at, updated_at, is_deleted)
                VALUES (:id, :username, :email, :password_hash, :full_name, :role, :status, :company_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """), {
                "id": superadmin_id,
                "username": "superadmin",
                "email": "johan@techcorp.com",
                "password_hash": password_hash,
                "full_name": "Johan S. Castro - SuperAdmin",
                "role": "SUPERADMIN",
                "status": "ACTIVE",
                "company_id": company_id
            })
            
            print(f"✅ SuperAdmin creado: johan@techcorp.com (ID: {superadmin_id})")
            
            # 3. Crear admin de empresa
            admin_id = str(uuid.uuid4())
            admin_password_hash = SecurityManager.get_password_hash("Admin123!")
            
            await db.execute(text("""
                INSERT INTO users (id, username, email, password_hash, full_name, role, status, company_id, created_at, updated_at, is_deleted)
                VALUES (:id, :username, :email, :password_hash, :full_name, :role, :status, :company_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """), {
                "id": admin_id,
                "username": "admin",
                "email": "admin@techcorp.com",
                "password_hash": admin_password_hash,
                "full_name": "Administrador TechCorp",
                "role": "ADMIN",
                "status": "ACTIVE",
                "company_id": company_id
            })
            
            print(f"✅ Admin creado: admin@techcorp.com (ID: {admin_id})")
            
            # 4. Crear usuario regular
            user_id = str(uuid.uuid4())
            user_password_hash = SecurityManager.get_password_hash("User123!")
            
            await db.execute(text("""
                INSERT INTO users (id, username, email, password_hash, full_name, role, status, company_id, created_at, updated_at, is_deleted)
                VALUES (:id, :username, :email, :password_hash, :full_name, :role, :status, :company_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """), {
                "id": user_id,
                "username": "usuario1",
                "email": "usuario1@techcorp.com",
                "password_hash": user_password_hash,
                "full_name": "Usuario de Prueba",
                "role": "USER",
                "status": "ACTIVE",
                "company_id": company_id
            })
            
            print(f"✅ Usuario creado: usuario1@techcorp.com (ID: {user_id})")
            
            # 5. Crear chatbot de prueba
            chatbot_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO chatbots (id, name, description, status, personality, company_id, created_by, created_at, updated_at, is_deleted)
                VALUES (:id, :name, :description, :status, :personality, :company_id, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """), {
                "id": chatbot_id,
                "name": "Asistente TechCorp",
                "description": "Chatbot de atención al cliente para TechCorp Solutions",
                "status": "ACTIVE",
                "personality": "PROFESSIONAL",
                "company_id": company_id,
                "created_by": admin_id
            })
            
            print(f"✅ Chatbot creado: Asistente TechCorp (ID: {chatbot_id})")
            
            # 6. Crear conversación de prueba
            conversation_id = str(uuid.uuid4())
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            await db.execute(text("""
                INSERT INTO conversations (id, session_id, status, user_name, user_email, chatbot_id, company_id, created_at, updated_at, is_deleted)
                VALUES (:id, :session_id, :status, :user_name, :user_email, :chatbot_id, :company_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            """), {
                "id": conversation_id,
                "session_id": session_id,
                "status": "ACTIVE",
                "user_name": "Cliente Demo",
                "user_email": "cliente@ejemplo.com",
                "chatbot_id": chatbot_id,
                "company_id": company_id
            })
            
            print(f"✅ Conversación creada: {session_id} (ID: {conversation_id})")
            
            # 7. Crear mensajes de prueba
            messages = [
                {
                    "id": str(uuid.uuid4()),
                    "content": "Hola, necesito ayuda con mi pedido",
                    "sender": "USER",
                    "message_type": "TEXT"
                },
                {
                    "id": str(uuid.uuid4()),
                    "content": "¡Hola! Estaré encantado de ayudarte con tu pedido. ¿Podrías proporcionarme tu número de pedido?",
                    "sender": "BOT",
                    "message_type": "TEXT"
                },
                {
                    "id": str(uuid.uuid4()),
                    "content": "Mi número de pedido es #12345",
                    "sender": "USER",
                    "message_type": "TEXT"
                }
            ]
            
            for msg in messages:
                await db.execute(text("""
                    INSERT INTO messages (id, content, message_type, sender, conversation_id, company_id, created_at, updated_at, is_deleted)
                    VALUES (:id, :content, :message_type, :sender, :conversation_id, :company_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
                """), {
                    "id": msg["id"],
                    "content": msg["content"],
                    "message_type": msg["message_type"],
                    "sender": msg["sender"],
                    "conversation_id": conversation_id,
                    "company_id": company_id
                })
            
            print(f"✅ {len(messages)} mensajes creados")
            
            await db.commit()
            
            # Mostrar resumen
            print("\n" + "="*60)
            print("🎉 DATOS DE PRUEBA CREADOS EXITOSAMENTE")
            print("="*60)
            print(f"🏢 Empresa: TechCorp Solutions")
            print(f"   ID: {company_id}")
            print(f"   Email: contacto@techcorp.com")
            print()
            print("👥 USUARIOS CREADOS:")
            print(f"   🔑 SuperAdmin: johan@techcorp.com")
            print(f"      Password: SuperAdmin123!")
            print(f"      ID: {superadmin_id}")
            print()
            print(f"   👨‍💼 Admin: admin@techcorp.com")
            print(f"      Password: Admin123!")
            print(f"      ID: {admin_id}")
            print()
            print(f"   👤 Usuario: usuario1@techcorp.com")
            print(f"      Password: User123!")
            print(f"      ID: {user_id}")
            print()
            print(f"🤖 Chatbot: Asistente TechCorp")
            print(f"   ID: {chatbot_id}")
            print(f"   Estado: ACTIVE")
            print()
            print(f"💬 Conversación de prueba creada con {len(messages)} mensajes")
            print(f"   ID: {conversation_id}")
            print("="*60)
            print()
            print("🚀 PRÓXIMOS PASOS:")
            print("1. Importa el archivo 'ChatBot_SAAS_API.postman_collection.json' en Postman")
            print("2. Usa las credenciales de SuperAdmin para hacer login")
            print("3. Prueba los endpoints de la API")
            print("4. Accede a http://localhost:8000/docs para ver la documentación")
            
            break
            
        return True
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    print("🔧 Inicializando creación de datos de prueba...")
    
    success = await create_test_data()
    if success:
        print("\n✅ ¡Proceso completado exitosamente!")
    else:
        print("\n❌ El proceso falló")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
