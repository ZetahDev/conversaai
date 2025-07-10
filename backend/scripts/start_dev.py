#!/usr/bin/env python3
"""
Script para iniciar el servidor de desarrollo
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    try:
        import uvicorn
        import fastapi
        import sqlalchemy
        print("✅ Dependencias principales encontradas")
        return True
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return False

def setup_environment():
    """Configurar variables de entorno"""
    print("⚙️ Configurando entorno de desarrollo...")
    
    env_file = Path(__file__).parent.parent / ".env.development"
    if env_file.exists():
        # Cargar variables de entorno desde archivo
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')
        print("✅ Variables de entorno cargadas")
    else:
        print("⚠️ Archivo .env.development no encontrado, usando valores por defecto")

async def init_database():
    """Inicializar base de datos si es necesario"""
    print("🗄️ Verificando base de datos...")
    
    db_file = Path(__file__).parent.parent / "chatbot_saas.db"
    
    if not db_file.exists():
        print("📝 Base de datos no existe, creando...")
        try:
            from scripts.init_db import create_tables, create_test_data
            await create_tables()
            await create_test_data()
            print("✅ Base de datos inicializada con datos de prueba")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
            return False
    else:
        print("✅ Base de datos encontrada")
    
    return True

def start_server():
    """Iniciar el servidor de desarrollo"""
    print("🚀 Iniciando servidor de desarrollo...")
    
    try:
        # Cambiar al directorio del backend
        os.chdir(Path(__file__).parent.parent)
        
        # Comando para iniciar uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ]
        
        print(f"📡 Servidor disponible en: http://localhost:8000")
        print(f"📚 Documentación API: http://localhost:8000/docs")
        print(f"🔧 Redoc: http://localhost:8000/redoc")
        print("\n🛑 Presiona Ctrl+C para detener el servidor\n")
        
        # Ejecutar el servidor
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return False
    
    return True

async def main():
    """Función principal"""
    print("🎯 ConversaAI - Servidor de Desarrollo")
    print("=" * 50)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Configurar entorno
    setup_environment()
    
    # Inicializar base de datos
    if not await init_database():
        sys.exit(1)
    
    # Iniciar servidor
    start_server()

if __name__ == "__main__":
    asyncio.run(main())
