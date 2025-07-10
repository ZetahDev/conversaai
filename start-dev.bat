@echo off
REM Script para inicializar el entorno de desarrollo completo en Windows

echo 🎯 ChatBot SAAS - Inicialización de Desarrollo
echo ==============================================

REM Verificar dependencias
echo 🔍 Verificando dependencias...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python no está instalado
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js no está instalado
    pause
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ npm no está instalado
    pause
    exit /b 1
)

echo ✅ Dependencias básicas encontradas

REM Configurar backend
echo.
echo 🐍 Configurando backend...
cd backend

if not exist "venv" (
    echo 📦 Creando entorno virtual...
    python -m venv venv
)

echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat

echo 📥 Instalando dependencias del backend...
pip install -r requirements.txt

echo 🗄️ Inicializando base de datos...
python scripts\init_db.py

cd ..

REM Configurar frontend
echo.
echo 🌐 Configurando frontend...
cd frontend

if not exist "node_modules" (
    echo 📥 Instalando dependencias del frontend...
    npm install
)

cd ..

REM Verificar configuración
echo.
echo ⚙️ Verificando configuración...

if not exist "backend\.env" (
    echo 📝 Creando archivo de configuración del backend...
    copy "backend\.env.development" "backend\.env"
)

if not exist "frontend\.env" (
    echo 📝 Creando archivo de configuración del frontend...
    copy "frontend\.env.example" "frontend\.env"
)

echo.
echo 🎉 Inicialización completada!
echo.
echo 🚀 Para iniciar el desarrollo:
echo    1. Backend:  cd backend ^&^& venv\Scripts\activate ^&^& python scripts\start_dev.py
echo    2. Frontend: cd frontend ^&^& npm run dev
echo.
echo 📡 URLs de desarrollo:
echo    🌐 Frontend: http://localhost:4322
echo    🔧 Backend:  http://localhost:8000
echo    📚 API Docs: http://localhost:8000/docs
echo.
echo 👤 Credenciales de prueba:
echo    📧 Admin: admin@techcorp.com / admin123
echo    👤 User:  user@techcorp.com / user123
echo.
echo 🧪 Para probar la conexión:
echo    cd frontend ^&^& node scripts\test-connection.js

pause
