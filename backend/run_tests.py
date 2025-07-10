#!/usr/bin/env python3
"""
Script para ejecutar tests de ConversaAI con coverage
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔄 {description}...")
    print(f"Ejecutando: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        print(f"✅ {description} completado exitosamente")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}")
        print(f"Error: {e.stderr}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        return False


def main():
    """Función principal"""
    print("🤖 ConversaAI - Test Runner")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("app"):
        print("❌ Error: No se encuentra el directorio 'app'")
        print("Asegúrate de ejecutar este script desde el directorio backend/")
        sys.exit(1)
    
    # Verificar que pytest está instalado
    try:
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: pytest no está instalado")
        print("Instala las dependencias con: pip install -r requirements.txt")
        sys.exit(1)
    
    # Lista de comandos a ejecutar
    commands = [
        {
            "command": ["pytest", "--version"],
            "description": "Verificando versión de pytest"
        },
        {
            "command": [
                "pytest", 
                "tests/", 
                "-v", 
                "--cov=app",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
                "--tb=short"
            ],
            "description": "Ejecutando tests con coverage"
        }
    ]
    
    # Ejecutar comandos
    all_success = True
    for cmd_info in commands:
        success = run_command(cmd_info["command"], cmd_info["description"])
        if not success:
            all_success = False
    
    # Mostrar resultados finales
    print("\n" + "=" * 50)
    if all_success:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
        print("\n📊 Reportes de coverage generados:")
        print("  - Terminal: Mostrado arriba")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")
        
        # Verificar si existe el reporte HTML
        html_report = Path("htmlcov/index.html")
        if html_report.exists():
            print(f"\n🌐 Abre el reporte HTML en: file://{html_report.absolute()}")
        
        print("\n🚀 ¡ConversaAI está listo para deployment!")
    else:
        print("❌ Algunos tests fallaron")
        print("Revisa los errores arriba y corrige los problemas")
        sys.exit(1)


if __name__ == "__main__":
    main()
