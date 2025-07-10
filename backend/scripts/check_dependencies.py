#!/usr/bin/env python3
"""
Script para verificar dependencias y servicios del backend
"""
import sys
import subprocess
import socket
import importlib
from pathlib import Path
import requests
from typing import Dict, List, Tuple

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

def check_python_packages() -> Dict[str, bool]:
    """Verificar que los paquetes de Python estén instalados"""
    print("🐍 Verificando paquetes de Python...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'alembic',
        'pydantic',
        'pydantic_settings',
        'python_jose',
        'passlib',
        'python_multipart',
        'aiosqlite',
        'redis',
        'celery',
        'openai',
        'stripe',
        'requests',
        'jinja2',
        'python_dotenv'
    ]
    
    results = {}
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            results[package] = True
            print(f"   ✅ {package}")
        except ImportError:
            results[package] = False
            print(f"   ❌ {package}")
    
    return results

def check_services() -> Dict[str, bool]:
    """Verificar que los servicios externos estén disponibles"""
    print("\n🔌 Verificando servicios externos...")
    
    services = {
        'Redis': ('localhost', 6379),
        'PostgreSQL': ('localhost', 5432),
        'Qdrant': ('localhost', 6333),
        'MinIO': ('localhost', 9000),
    }
    
    results = {}
    
    for service_name, (host, port) in services.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                results[service_name] = True
                print(f"   ✅ {service_name} ({host}:{port})")
            else:
                results[service_name] = False
                print(f"   ❌ {service_name} ({host}:{port}) - No disponible")
                
        except Exception as e:
            results[service_name] = False
            print(f"   ❌ {service_name} ({host}:{port}) - Error: {e}")
    
    return results

def check_environment_config() -> Dict[str, bool]:
    """Verificar configuración del environment"""
    print("\n⚙️ Verificando configuración del environment...")
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        checks = {
            'SECRET_KEY configurado': len(settings.SECRET_KEY) >= 32,
            'DATABASE_URL configurado': bool(settings.DATABASE_URL),
            'Environment válido': settings.ENVIRONMENT in ['development', 'staging', 'production'],
            'CORS configurado': len(settings.cors_origins) > 0,
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
        
        return checks
        
    except Exception as e:
        print(f"   ❌ Error cargando configuración: {e}")
        return {'Configuración': False}

def check_database_connection() -> bool:
    """Verificar conexión a la base de datos"""
    print("\n🗄️ Verificando conexión a la base de datos...")
    
    try:
        from app.core.config import get_settings
        from sqlalchemy import create_engine, text
        
        settings = get_settings()
        
        # Para SQLite
        if settings.DATABASE_URL.startswith('sqlite'):
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("   ✅ Conexión a SQLite exitosa")
            return True
            
        # Para PostgreSQL
        elif settings.DATABASE_URL.startswith('postgresql'):
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("   ✅ Conexión a PostgreSQL exitosa")
            return True
            
        else:
            print("   ⚠️ Tipo de base de datos no reconocido")
            return False
            
    except Exception as e:
        print(f"   ❌ Error conectando a la base de datos: {e}")
        return False

def check_api_keys() -> Dict[str, bool]:
    """Verificar que las API keys estén configuradas"""
    print("\n🔑 Verificando API keys...")
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        checks = {
            'OpenAI API Key': bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith('your-')),
            'Stripe Keys': bool(settings.STRIPE_SECRET_KEY and not settings.STRIPE_SECRET_KEY.startswith('sk_test_your-')),
            'Pinecone API Key': bool(settings.PINECONE_API_KEY and not settings.PINECONE_API_KEY.startswith('your-')),
        }
        
        for check_name, configured in checks.items():
            if configured:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ⚠️ {check_name} - No configurado (opcional para desarrollo)")
        
        return checks
        
    except Exception as e:
        print(f"   ❌ Error verificando API keys: {e}")
        return {}

def check_file_permissions() -> bool:
    """Verificar permisos de archivos"""
    print("\n📁 Verificando permisos de archivos...")
    
    try:
        backend_dir = Path(__file__).parent.parent
        
        # Verificar que se puede escribir en el directorio
        test_file = backend_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
        # Verificar directorio de uploads
        uploads_dir = backend_dir / "uploads"
        if not uploads_dir.exists():
            uploads_dir.mkdir(exist_ok=True)
            print("   📁 Directorio uploads creado")
        
        print("   ✅ Permisos de escritura correctos")
        return True
        
    except Exception as e:
        print(f"   ❌ Error con permisos de archivos: {e}")
        return False

def generate_report(results: Dict[str, Dict[str, bool]]):
    """Generar reporte final"""
    print("\n" + "="*60)
    print("📊 REPORTE FINAL")
    print("="*60)
    
    all_passed = True
    
    for category, checks in results.items():
        if isinstance(checks, dict):
            passed = sum(checks.values())
            total = len(checks)
            print(f"\n{category}: {passed}/{total} ✅")
            
            if passed < total:
                all_passed = False
                print("   Elementos faltantes:")
                for check, status in checks.items():
                    if not status:
                        print(f"   - {check}")
        else:
            status = "✅" if checks else "❌"
            print(f"\n{category}: {status}")
            if not checks:
                all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ¡Todas las verificaciones pasaron!")
        print("✅ El backend está listo para funcionar")
    else:
        print("⚠️ Algunas verificaciones fallaron")
        print("💡 Revisa los elementos marcados arriba")
        print("\n📝 Pasos sugeridos:")
        print("   1. Instalar paquetes faltantes: pip install -r requirements.txt")
        print("   2. Configurar servicios externos si es necesario")
        print("   3. Verificar configuración del environment")
        print("   4. Configurar API keys si planeas usar servicios externos")

def main():
    """Función principal"""
    print("🔍 Verificador de Dependencias - ConversaAI Backend")
    print("="*60)
    
    results = {}
    
    # Ejecutar todas las verificaciones
    results['Paquetes Python'] = check_python_packages()
    results['Servicios Externos'] = check_services()
    results['Configuración'] = check_environment_config()
    results['Conexión BD'] = check_database_connection()
    results['API Keys'] = check_api_keys()
    results['Permisos Archivos'] = check_file_permissions()
    
    # Generar reporte
    generate_report(results)

if __name__ == "__main__":
    main()
