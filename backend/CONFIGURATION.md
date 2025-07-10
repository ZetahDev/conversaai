# 🔧 Configuración del Backend - ConversaAI

Esta guía explica cómo configurar el backend para diferentes environments y funcionalidades.

## 📋 Índice

1. [Environments Disponibles](#environments-disponibles)
2. [Variables de Configuración](#variables-de-configuración)
3. [Servicios Externos](#servicios-externos)
4. [Scripts de Gestión](#scripts-de-gestión)
5. [Configuración por Environment](#configuración-por-environment)
6. [Troubleshooting](#troubleshooting)

## 🌍 Environments Disponibles

### Development

- **Archivo**: `.env.development`
- **Propósito**: Desarrollo local
- **Características**:
  - Debug habilitado
  - SQLite como base de datos
  - Servicios externos opcionales
  - Rate limiting relajado
  - Logs detallados

### Staging

- **Archivo**: `.env.staging`
- **Propósito**: Testing pre-producción
- **Características**:
  - PostgreSQL recomendado
  - Servicios externos con keys de test
  - Rate limiting moderado
  - Monitoreo habilitado

### Production

- **Archivo**: `.env.production`
- **Propósito**: Producción
- **Características**:
  - PostgreSQL con pooling
  - Todas las integraciones habilitadas
  - Rate limiting estricto
  - Logs de nivel WARNING
  - Seguridad máxima

## ⚙️ Variables de Configuración

### 🔐 Seguridad

```env
SECRET_KEY="tu-clave-secreta-muy-segura-32-caracteres-minimo"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 🗄️ Base de Datos

```env
# SQLite (Development)
DATABASE_URL="sqlite:///./chatbot.db"
DATABASE_URL_ASYNC="sqlite+aiosqlite:///./chatbot.db"

# PostgreSQL (Staging/Production)
DATABASE_URL="postgresql://user:pass@host:5432/dbname"
DATABASE_URL_ASYNC="postgresql+asyncpg://user:pass@host:5432/dbname"
```

### 🔴 Redis

```env
REDIS_URL="redis://localhost:6379/0"
REDIS_CACHE_TTL=3600
REDIS_ENABLED=true
```

### 🤖 APIs de IA

```env
OPENAI_API_KEY="sk-..."
OPENAI_ORG_ID="org-..."
GEMINI_API_KEY="..."
```

### 💳 Stripe (Pagos)

```env
# Test
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_PUBLISHABLE_KEY="pk_test_..."

# Live
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."
```

### 📧 Email

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="tu-email@gmail.com"
SMTP_PASSWORD="tu-app-password"
SMTP_TLS=true
FROM_EMAIL="noreply@tudominio.com"
EMAIL_ENABLED=true
```

### 📱 Integraciones

```env
# WhatsApp
WHATSAPP_TOKEN="tu-token"
WHATSAPP_PHONE_NUMBER_ID="tu-numero-id"
WHATSAPP_VERIFY_TOKEN="tu-verify-token"
WHATSAPP_ENABLED=true

# Telegram
TELEGRAM_BOT_TOKEN="tu-bot-token"
TELEGRAM_ENABLED=true

# Facebook
FACEBOOK_PAGE_ACCESS_TOKEN="tu-token"
FACEBOOK_VERIFY_TOKEN="tu-verify-token"
FACEBOOK_ENABLED=true
```

## 🛠️ Scripts de Gestión

### Cambiar Environment

```bash
# Cambiar a development
python scripts/set_environment.py set development

# Cambiar a staging
python scripts/set_environment.py set staging

# Cambiar a production
python scripts/set_environment.py set production

# Listar environments disponibles
python scripts/set_environment.py list

# Validar configuración actual
python scripts/set_environment.py validate
```

### Verificar Dependencias

```bash
# Verificar todas las dependencias
python scripts/check_dependencies.py
```

### Inicializar Base de Datos

```bash
# Inicialización completa
python scripts/init_db.py

# Inicialización mínima (solo tablas básicas)
python scripts/minimal_init.py

# Reset completo
python scripts/init_db.py --reset
```

## 🔧 Configuración por Environment

### Development Setup

1. **Copiar configuración**:

   ```bash
   python scripts/set_environment.py set development
   ```

2. **Verificar dependencias**:

   ```bash
   python scripts/check_dependencies.py
   ```

3. **Inicializar base de datos**:

   ```bash
   python scripts/minimal_init.py
   ```

4. **Iniciar servidor**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Staging Setup

1. **Configurar PostgreSQL**:

   ```sql
   CREATE DATABASE chatbot_staging;
   CREATE USER chatbot_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE chatbot_staging TO chatbot_user;
   ```

2. **Configurar Redis**:

   ```bash
   # Instalar Redis
   sudo apt install redis-server
   # O usar Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

3. **Cambiar environment**:

   ```bash
   python scripts/set_environment.py set staging
   ```

4. **Configurar variables específicas** en `.env.staging`:

   - Database URLs
   - API keys de test
   - SMTP settings

5. **Ejecutar migraciones**:
   ```bash
   alembic upgrade head
   ```

### Production Setup

1. **Configurar infraestructura**:

   - PostgreSQL con backup automático
   - Redis con persistencia
   - Load balancer
   - SSL/TLS certificates

2. **Configurar variables de producción**:

   ```bash
   python scripts/set_environment.py set production
   ```

3. **Configurar todas las API keys**:

   - OpenAI production keys
   - Stripe live keys
   - WhatsApp Business API
   - Email service

4. **Configurar monitoreo**:
   - Sentry para error tracking
   - Prometheus para métricas
   - Health checks

## 🚨 Troubleshooting

### Error: "SECRET_KEY too short"

```bash
# Generar nueva clave segura
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Error: "Database connection failed"

```bash
# Verificar que la base de datos esté ejecutándose
python scripts/check_dependencies.py

# Para PostgreSQL
sudo systemctl status postgresql

# Para SQLite, verificar permisos del archivo
ls -la *.db
```

### Error: "Redis connection failed"

```bash
# Verificar Redis
redis-cli ping

# Si no está instalado
sudo apt install redis-server
# O deshabilitar Redis
REDIS_ENABLED=false
```

### Error: "Import errors"

```bash
# Instalar dependencias faltantes
pip install -r requirements.txt

# Verificar instalación
python scripts/check_dependencies.py
```

### Error: "Permission denied"

```bash
# Verificar permisos del directorio
chmod 755 .
chmod 644 .env*

# Crear directorio uploads
mkdir -p uploads
chmod 755 uploads
```

## 📝 Checklist de Configuración

### Development ✅

- [ ] `.env.development` configurado
- [ ] SQLite funcionando
- [ ] Credenciales de prueba creadas
- [ ] Servidor iniciando correctamente

### Staging ✅

- [ ] PostgreSQL configurado
- [ ] Redis funcionando
- [ ] API keys de test configuradas
- [ ] Email SMTP configurado
- [ ] Migraciones ejecutadas

### Production ✅

- [ ] Infraestructura configurada
- [ ] SSL/TLS habilitado
- [ ] API keys de producción configuradas
- [ ] Backup automático configurado
- [ ] Monitoreo habilitado
- [ ] Rate limiting configurado
- [ ] Logs configurados

## 🔗 Enlaces Útiles

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)
- [Redis Documentation](https://redis.io/documentation)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 📞 Soporte

Si encuentras problemas con la configuración:

1. Ejecuta `python scripts/check_dependencies.py`
2. Revisa los logs del servidor
3. Verifica que todas las variables estén configuradas
4. Consulta esta documentación
5. Contacta al equipo de desarrollo
