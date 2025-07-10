#!/usr/bin/env python3
"""
Script mínimo para inicializar la base de datos con datos básicos
"""
import asyncio
import sys
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.security import SecurityManager

def create_minimal_db():
    """Crear base de datos mínima con datos básicos"""
    print("🎯 Creando base de datos mínima...")
    
    # Eliminar base de datos existente si existe
    db_path = Path(__file__).parent.parent / "chatbot_minimal.db"
    if db_path.exists():
        db_path.unlink()
    
    # Crear conexión
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Crear tabla companies
        cursor.execute("""
            CREATE TABLE companies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                company_type TEXT DEFAULT 'other',
                status TEXT DEFAULT 'active',
                max_users INTEGER DEFAULT 10,
                max_chatbots INTEGER DEFAULT 5,
                max_monthly_messages INTEGER DEFAULT 10000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla users
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'USER',
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 1,
                company_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)
        
        # Crear tabla chatbots
        cursor.execute("""
            CREATE TABLE chatbots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                model TEXT DEFAULT 'gpt-3.5-turbo',
                system_prompt TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 150,
                status TEXT DEFAULT 'ACTIVE',
                company_id TEXT NOT NULL,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)
        
        # Insertar datos de prueba
        company_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Insertar empresa
        cursor.execute("""
            INSERT INTO companies (id, name, slug, email, company_type, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company_id, "TechCorp Demo", "techcorp-demo", "admin@techcorp.com", "other", "active"))
        
        # Insertar usuarios
        admin_password = SecurityManager.get_password_hash("admin123")
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, company_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_id, "admin@techcorp.com", admin_password, "Administrador Demo", "SUPERADMIN", company_id))
        
        user_password = SecurityManager.get_password_hash("user123")
        cursor.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, role, company_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "user@techcorp.com", user_password, "Usuario Demo", "USER", company_id))
        
        # Insertar chatbots
        chatbot1_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO chatbots (id, name, description, model, system_prompt, company_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chatbot1_id,
            "Asistente de Ventas",
            "Chatbot especializado en ventas y atención al cliente",
            "gpt-3.5-turbo",
            "Eres un asistente de ventas amigable y profesional. Ayudas a los clientes a encontrar productos y resolver dudas sobre compras.",
            company_id,
            admin_id
        ))
        
        chatbot2_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO chatbots (id, name, description, model, system_prompt, company_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chatbot2_id,
            "Soporte Técnico",
            "Chatbot para resolver problemas técnicos y dudas sobre productos",
            "gpt-4",
            "Eres un especialista en soporte técnico. Ayudas a resolver problemas técnicos de manera clara y paso a paso.",
            company_id,
            admin_id
        ))
        
        conn.commit()
        
        print("✅ Base de datos mínima creada exitosamente:")
        print(f"   📁 Archivo: {db_path}")
        print(f"   👤 Admin: admin@techcorp.com / admin123")
        print(f"   👤 Usuario: user@techcorp.com / user123")
        print(f"   🏢 Empresa: TechCorp Demo")
        print(f"   🤖 Chatbots: Asistente de Ventas, Soporte Técnico")
        
        return str(db_path)
        
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        raise
    finally:
        conn.close()

def update_config():
    """Actualizar configuración para usar la base de datos mínima"""
    print("⚙️ Actualizando configuración...")
    
    env_file = Path(__file__).parent.parent / ".env"
    
    # Leer archivo existente
    lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    
    # Actualizar o agregar configuración de base de datos
    db_url_found = False
    db_async_url_found = False
    
    for i, line in enumerate(lines):
        if line.startswith('DATABASE_URL='):
            lines[i] = 'DATABASE_URL="sqlite:///./chatbot_minimal.db"\n'
            db_url_found = True
        elif line.startswith('DATABASE_URL_ASYNC='):
            lines[i] = 'DATABASE_URL_ASYNC="sqlite+aiosqlite:///./chatbot_minimal.db"\n'
            db_async_url_found = True
    
    # Agregar si no existen
    if not db_url_found:
        lines.append('DATABASE_URL="sqlite:///./chatbot_minimal.db"\n')
    if not db_async_url_found:
        lines.append('DATABASE_URL_ASYNC="sqlite+aiosqlite:///./chatbot_minimal.db"\n')
    
    # Escribir archivo
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print("✅ Configuración actualizada")

def main():
    """Función principal"""
    print("🎯 Inicialización Mínima de Base de Datos")
    print("=" * 50)
    
    try:
        db_path = create_minimal_db()
        update_config()
        
        print("\n🎉 Inicialización completada exitosamente!")
        print("\n🚀 Para iniciar el backend:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n📡 URLs:")
        print("   🔧 Backend:  http://localhost:8000")
        print("   📚 API Docs: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
