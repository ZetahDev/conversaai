#!/usr/bin/env python3
"""
Script para actualizar las credenciales de prueba en la base de datos
"""
import sqlite3
import sys
import uuid
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.security import SecurityManager

def update_credentials():
    """Actualizar credenciales de prueba"""
    print("🔐 Actualizando credenciales de prueba...")
    
    # Conectar a la base de datos
    db_path = Path(__file__).parent.parent / "chatbot_minimal.db"
    
    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Limpiar usuarios existentes
        cursor.execute("DELETE FROM users")
        
        # Obtener company_id existente
        cursor.execute("SELECT id FROM companies LIMIT 1")
        result = cursor.fetchone()
        if not result:
            print("❌ No se encontró empresa en la base de datos")
            return False
        
        company_id = result[0]
        
        # Crear nuevos usuarios con las credenciales especificadas
        users = [
            {
                "id": str(uuid.uuid4()),
                "email": "johan@techcorp.com",
                "password": "SuperAdmin123!",
                "full_name": "Johan SuperAdmin",
                "role": "SUPERADMIN"
            },
            {
                "id": str(uuid.uuid4()),
                "email": "admin@techcorp.com",
                "password": "Admin123!",
                "full_name": "Administrador",
                "role": "ADMIN"
            },
            {
                "id": str(uuid.uuid4()),
                "email": "usuario1@techcorp.com",
                "password": "User123!",
                "full_name": "Usuario Demo",
                "role": "USER"
            }
        ]
        
        # Insertar usuarios
        for user in users:
            hashed_password = SecurityManager.get_password_hash(user["password"])
            
            cursor.execute("""
                INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, company_id)
                VALUES (?, ?, ?, ?, ?, 1, 1, ?)
            """, (
                user["id"],
                user["email"],
                hashed_password,
                user["full_name"],
                user["role"],
                company_id
            ))
            
            print(f"✅ Usuario creado: {user['email']} ({user['role']})")
        
        # Actualizar chatbots para que tengan el created_by correcto (SuperAdmin)
        superadmin_id = users[0]["id"]  # Johan
        cursor.execute("UPDATE chatbots SET created_by = ?", (superadmin_id,))
        
        conn.commit()
        
        print("\n🎉 Credenciales actualizadas exitosamente!")
        print("\n👤 Credenciales de Prueba:")
        print("   🔑 SuperAdmin: johan@techcorp.com / SuperAdmin123!")
        print("   🔑 Admin: admin@techcorp.com / Admin123!")
        print("   🔑 Usuario: usuario1@techcorp.com / User123!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando credenciales: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_credentials():
    """Verificar que las credenciales funcionan"""
    print("\n🔍 Verificando credenciales...")
    
    db_path = Path(__file__).parent.parent / "chatbot_minimal.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Verificar usuarios
        cursor.execute("SELECT email, full_name, role FROM users ORDER BY role DESC")
        users = cursor.fetchall()
        
        print("\n📋 Usuarios en la base de datos:")
        for email, full_name, role in users:
            print(f"   📧 {email} - {full_name} ({role})")
        
        # Verificar chatbots
        cursor.execute("SELECT name, status FROM chatbots")
        chatbots = cursor.fetchall()
        
        print("\n🤖 Chatbots disponibles:")
        for name, status in chatbots:
            print(f"   🤖 {name} ({status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando credenciales: {e}")
        return False
    finally:
        conn.close()

def main():
    """Función principal"""
    print("🎯 Actualización de Credenciales de Prueba")
    print("=" * 50)
    
    if update_credentials():
        verify_credentials()
        
        print("\n🚀 Para probar las credenciales:")
        print("   1. Asegúrate de que el backend esté ejecutándose")
        print("   2. Ve a http://localhost:4322/login")
        print("   3. Usa cualquiera de las credenciales mostradas arriba")
        
    else:
        print("❌ Error durante la actualización")
        sys.exit(1)

if __name__ == "__main__":
    main()
