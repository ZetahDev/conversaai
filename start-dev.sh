#!/bin/bash

# Script para inicializar el entorno de desarrollo completo
echo "🎯 ChatBot SAAS - Inicialización de Desarrollo"
echo "=============================================="

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar si un puerto está en uso
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Verificar dependencias
echo "🔍 Verificando dependencias..."

if ! command_exists python3; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js no está instalado"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm no está instalado"
    exit 1
fi

echo "✅ Dependencias básicas encontradas"

# Verificar e instalar dependencias del backend
echo ""
echo "🐍 Configurando backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

echo "🔧 Activando entorno virtual..."
source venv/bin/activate || source venv/Scripts/activate

echo "📥 Instalando dependencias del backend..."
pip install -r requirements.txt

echo "🗄️ Inicializando base de datos..."
python scripts/init_db.py

cd ..

# Verificar e instalar dependencias del frontend
echo ""
echo "🌐 Configurando frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📥 Instalando dependencias del frontend..."
    npm install
fi

cd ..

# Verificar puertos
echo ""
echo "🔌 Verificando puertos..."

if port_in_use 8000; then
    echo "⚠️ Puerto 8000 (backend) ya está en uso"
    echo "💡 Detén el proceso existente o usa otro puerto"
fi

if port_in_use 4322; then
    echo "⚠️ Puerto 4322 (frontend) ya está en uso"
    echo "💡 Detén el proceso existente o usa otro puerto"
fi

# Crear archivos de configuración si no existen
echo ""
echo "⚙️ Verificando configuración..."

if [ ! -f "backend/.env" ]; then
    echo "📝 Creando archivo de configuración del backend..."
    cp backend/.env.development backend/.env
fi

if [ ! -f "frontend/.env" ]; then
    echo "📝 Creando archivo de configuración del frontend..."
    cp frontend/.env.example frontend/.env
fi

echo ""
echo "🎉 Inicialización completada!"
echo ""
echo "🚀 Para iniciar el desarrollo:"
echo "   1. Backend:  cd backend && source venv/bin/activate && python scripts/start_dev.py"
echo "   2. Frontend: cd frontend && npm run dev"
echo ""
echo "📡 URLs de desarrollo:"
echo "   🌐 Frontend: http://localhost:4322"
echo "   🔧 Backend:  http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Credenciales de prueba:"
echo "   📧 Admin: admin@techcorp.com / admin123"
echo "   👤 User:  user@techcorp.com / user123"
echo ""
echo "🧪 Para probar la conexión:"
echo "   cd frontend && node scripts/test-connection.js"
