#!/usr/bin/env python3
"""
Script para cambiar entre diferentes environments
"""
import sys
import shutil
from pathlib import Path
import argparse

def set_environment(env: str):
    """Cambiar al environment especificado"""
    
    # Validar environment
    valid_envs = ['development', 'staging', 'production']
    if env not in valid_envs:
        print(f"❌ Environment inválido: {env}")
        print(f"💡 Environments válidos: {', '.join(valid_envs)}")
        return False
    
    # Rutas de archivos
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    source_file = backend_dir / f".env.{env}"
    
    # Verificar que el archivo fuente existe
    if not source_file.exists():
        print(f"❌ Archivo de configuración no encontrado: {source_file}")
        return False
    
    try:
        # Hacer backup del archivo actual si existe
        if env_file.exists():
            backup_file = backend_dir / f".env.backup.{env_file.stat().st_mtime}"
            shutil.copy2(env_file, backup_file)
            print(f"📦 Backup creado: {backup_file.name}")
        
        # Copiar el nuevo archivo
        shutil.copy2(source_file, env_file)
        print(f"✅ Environment cambiado a: {env}")
        print(f"📁 Archivo copiado: {source_file.name} → .env")
        
        # Mostrar configuraciones importantes
        show_environment_info(env_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error cambiando environment: {e}")
        return False

def show_environment_info(env_file: Path):
    """Mostrar información importante del environment"""
    print("\n📋 Configuración actual:")
    
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        important_vars = [
            'ENVIRONMENT',
            'DEBUG',
            'DATABASE_URL',
            'REDIS_ENABLED',
            'EMAIL_ENABLED',
            'STRIPE_ENABLED',
            'LOG_LEVEL'
        ]
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                if key in important_vars:
                    print(f"   {key}: {value}")
                    
    except Exception as e:
        print(f"⚠️ No se pudo leer la configuración: {e}")

def list_environments():
    """Listar environments disponibles"""
    print("📂 Environments disponibles:")
    
    backend_dir = Path(__file__).parent.parent
    
    for env in ['development', 'staging', 'production']:
        env_file = backend_dir / f".env.{env}"
        status = "✅" if env_file.exists() else "❌"
        print(f"   {status} {env}")
        
        if env_file.exists():
            # Mostrar algunas configuraciones clave
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    if 'DEBUG=true' in content:
                        print(f"      🔧 Debug: Habilitado")
                    if 'ENVIRONMENT=' in content:
                        for line in content.split('\n'):
                            if line.startswith('ENVIRONMENT='):
                                env_val = line.split('=')[1].strip('"')
                                print(f"      🌍 Environment: {env_val}")
                                break
            except:
                pass

def validate_environment(env_file: Path):
    """Validar que el environment tenga las configuraciones mínimas"""
    print(f"\n🔍 Validando configuración...")
    
    required_vars = [
        'APP_NAME',
        'SECRET_KEY',
        'DATABASE_URL',
        'ENVIRONMENT'
    ]
    
    missing_vars = []
    empty_vars = []
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)
            else:
                # Verificar si está vacío
                for line in content.split('\n'):
                    if line.startswith(f"{var}="):
                        value = line.split('=', 1)[1].strip().strip('"')
                        if not value or value.startswith('your-') or value.startswith('CHANGE-THIS'):
                            empty_vars.append(var)
                        break
        
        if missing_vars:
            print(f"❌ Variables faltantes: {', '.join(missing_vars)}")
        
        if empty_vars:
            print(f"⚠️ Variables que necesitan configuración: {', '.join(empty_vars)}")
        
        if not missing_vars and not empty_vars:
            print("✅ Configuración válida")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error validando configuración: {e}")
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Gestionar environments del backend")
    parser.add_argument('action', choices=['set', 'list', 'validate'], 
                       help='Acción a realizar')
    parser.add_argument('environment', nargs='?', 
                       choices=['development', 'staging', 'production'],
                       help='Environment a configurar (solo para "set")')
    
    args = parser.parse_args()
    
    print("🎯 Gestor de Environments - ChatBot SAAS Backend")
    print("=" * 50)
    
    if args.action == 'list':
        list_environments()
        
    elif args.action == 'validate':
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            validate_environment(env_file)
        else:
            print("❌ No se encontró archivo .env")
            
    elif args.action == 'set':
        if not args.environment:
            print("❌ Debes especificar un environment")
            print("💡 Uso: python set_environment.py set development")
            sys.exit(1)
        
        if set_environment(args.environment):
            # Validar después de cambiar
            env_file = Path(__file__).parent.parent / ".env"
            validate_environment(env_file)
            
            print(f"\n🚀 Para aplicar los cambios:")
            print("   1. Reinicia el servidor backend")
            print("   2. Verifica que los servicios externos estén configurados")
            print("   3. Ejecuta las migraciones si es necesario")
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
