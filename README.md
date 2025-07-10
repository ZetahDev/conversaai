# 🤖 ConversaAI - Sistema Completo de Asistentes Virtuales Empresariales

[![Build Status](https://github.com/your-org/conversaai/workflows/CI/badge.svg)](https://github.com/your-org/conversaai/actions)
[![Coverage](https://codecov.io/gh/your-org/conversaai/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/conversaai)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/your-org/conversaai/releases)

Sistema completo de asistentes virtuales como servicio (SAAS) con integraciones múltiples, gestión empresarial y análisis avanzado. Diseñado para PYMEs que buscan automatizar su atención al cliente de manera profesional y escalable.

## ✨ Características Principales

### 🤖 **Gestión Inteligente de Asistentes Virtuales**

- ✅ Creación y configuración de asistentes personalizados
- ✅ Múltiples personalidades de IA (Amigable, Profesional, Técnico)
- ✅ Gestión de conocimiento y entrenamiento personalizado
- ✅ Análisis de conversaciones y métricas en tiempo real

### 🔗 **Integraciones Multi-Canal**

- ✅ **WhatsApp Business API** - Integración completa y certificada
- ✅ **Telegram Bot API** - Bots nativos con comandos personalizados
- ✅ **Widget Web** - Embebido, popup e iframe para sitios web
- 🔄 **Facebook Messenger** (próximamente)
- 🔄 **Instagram Direct** (próximamente)

### 🏢 **Gestión Empresarial Avanzada**

- ✅ Sistema multi-tenant con aislamiento completo
- ✅ Roles granulares (SuperAdmin, Admin, Usuario)
- ✅ Gestión de suscripciones y límites por plan
- ✅ Dashboard analítico con métricas en tiempo real

### 🔐 **Seguridad de Nivel Empresarial**

- ✅ Autenticación JWT con refresh tokens automáticos
- ✅ Validación robusta de contraseñas con scoring
- ✅ Middlewares de seguridad (Rate limiting, SQL injection, XSS)
- ✅ Headers de seguridad y protección CSRF

### 📊 **Analytics y Monitoreo Completo**

- ✅ Métricas en tiempo real con WebSockets
- ✅ Sistema de notificaciones inteligentes
- ✅ Dashboards interactivos con Grafana
- ✅ Logs estructurados y auditoría completa

### 🧪 **Testing y Calidad**

- ✅ Tests unitarios y de integración (80%+ cobertura)
- ✅ Tests automatizados para APIs y componentes
- ✅ Validación continua con GitHub Actions
- ✅ Documentación automática con OpenAPI

## 🛠️ Stack Tecnológico

### **Backend (API)**

- **FastAPI** 0.104+ - Framework web moderno y rápido
- **PostgreSQL** 15+ - Base de datos principal con JSONB
- **Redis** 7+ - Cache, sesiones y colas de tareas
- **SQLAlchemy** 2.0+ - ORM con soporte async
- **Alembic** - Migraciones versionadas
- **Celery** - Tareas asíncronas y programadas

### **Frontend (Web)**

- **Astro** 4.0+ - Framework web moderno con SSR
- **React** 18+ - Componentes interactivos
- **TypeScript** 5+ - Tipado estático robusto
- **Tailwind CSS** 3+ - Estilos utilitarios

### **IA y Machine Learning**

- **Google Gemini** - Modelo de IA principal
- **OpenAI GPT-4** - Modelo alternativo
- **Qdrant** - Base de datos vectorial
- **LangChain** - Framework de IA conversacional

### **DevOps e Infraestructura**

- **Docker** & **Docker Compose** - Containerización
- **Nginx** - Reverse proxy y balanceador
- **Prometheus** + **Grafana** - Monitoreo y métricas
- **GitHub Actions** - CI/CD automatizado

## 🚀 Inicio Rápido

### **Desarrollo Local**

#### 1️⃣ **Clonar y Configurar**

```bash
git clone https://github.com/your-org/conversaai.git
cd conversaai
```

#### 2️⃣ **Backend Setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar base de datos (Docker)
docker-compose up -d postgres redis

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3️⃣ **Frontend Setup**

```bash
cd frontend
npm install

# Configurar variables
cp .env.example .env.local
# Editar .env.local

# Iniciar desarrollo
npm run dev
```

#### 4️⃣ **Acceder a la Aplicación**

- 🌐 **Frontend**: http://localhost:4321
- 🔧 **API**: http://localhost:8000
- 📚 **Docs**: http://localhost:8000/docs
- 📊 **Grafana**: http://localhost:3000

### **Producción**

Ver [📖 Guía de Deployment](docs/DEPLOYMENT.md) para instrucciones completas.

```bash
# Deployment automático
chmod +x scripts/deploy.sh
./scripts/deploy.sh production

# Monitoreo
./scripts/monitor.sh status
```

## 🧪 Testing y Calidad

### **Ejecutar Tests**

```bash
# Backend (80%+ cobertura)
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend
cd frontend
npm run test
npm run test:coverage
```

## 📊 Monitoreo y Observabilidad

### **Scripts de Monitoreo**

```bash
# Estado completo del sistema
./scripts/monitor.sh status

# Verificación rápida de salud
./scripts/monitor.sh check

# Logs en tiempo real
./scripts/monitor.sh logs

# Reiniciar servicios
./scripts/monitor.sh restart
```

### **URLs de Monitoreo**

- 🏥 **Health Check**: `https://yourdomain.com/api/health`
- 📊 **Grafana**: `https://admin.yourdomain.com/grafana`
- 📈 **Prometheus**: `https://admin.yourdomain.com/prometheus`
- 📋 **API Docs**: `https://yourdomain.com/api/docs`

## 🔧 Configuración Crítica

### **Variables de Entorno Principales**

#### **Backend (.env)**

```env
# 🔐 Seguridad (CAMBIAR EN PRODUCCIÓN)
SECRET_KEY=your-super-secret-key-minimum-32-chars
DATABASE_URL=postgresql://user:pass@localhost:5432/chatbot_dev
REDIS_URL=redis://localhost:6379/0

# 🤖 IA y APIs
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# 🔗 Integraciones
WHATSAPP_VERIFY_TOKEN=your-whatsapp-verify-token
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## 🤝 Contribución

### **Proceso de Contribución**

1. 🍴 Fork el proyecto
2. 🌿 Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. ✅ Escribir tests para nuevas funcionalidades
4. 📝 Commit con mensajes descriptivos (`git commit -m 'feat: Add amazing feature'`)
5. 🚀 Push a la rama (`git push origin feature/AmazingFeature`)
6. 🔄 Abrir Pull Request con descripción detallada

### **Estándares de Código**

- **Backend**: PEP 8, type hints obligatorios, docstrings
- **Frontend**: ESLint + Prettier, TypeScript strict mode
- **Tests**: Cobertura mínima 80%, tests para cada PR
- **Commits**: [Conventional Commits](https://conventionalcommits.org/)

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT** - ver [LICENSE](LICENSE) para detalles completos.

## 🆘 Soporte y Comunidad

### **Canales de Soporte**

- 📖 **Documentación**: [docs/](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/conversaai/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/conversaai/discussions)
- 📧 **Email**: support@yourdomain.com

## 🗺️ Roadmap

### **v1.1 - Q2 2024** 🎯

- [ ] 📱 Integración con Facebook Messenger
- [ ] 📸 Integración con Instagram Direct
- [ ] 📝 Sistema de plantillas de respuesta
- [ ] 🔌 API pública para desarrolladores

### **v1.2 - Q3 2024** 🚀

- [ ] 😊 Análisis de sentimientos en tiempo real
- [ ] 🎤 Chatbots con capacidades de voz
- [ ] 🔗 Integración nativa con CRMs populares
- [ ] 🛒 Marketplace de plugins y extensiones

### **v2.0 - Q4 2024** 🌟

- [ ] 🎨 IA multimodal (texto, imagen, voz)
- [ ] ⚡ Automatización de workflows complejos
- [ ] 🛍️ Integración profunda con e-commerce
- [ ] 📱 App móvil nativa (iOS/Android)

## 📈 Estado del Proyecto

| Métrica                | Estado                                                               | Objetivo |
| ---------------------- | -------------------------------------------------------------------- | -------- |
| 🧪 **Cobertura Tests** | ![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen) | 80%+     |
| 🔧 **Build Status**    | ![Build](https://img.shields.io/badge/build-passing-brightgreen)     | ✅       |
| 🐛 **Issues Abiertas** | ![Issues](https://img.shields.io/github/issues/your-org/conversaai)  | < 10     |
| ⭐ **GitHub Stars**    | ![Stars](https://img.shields.io/github/stars/your-org/conversaai)    | 1000+    |
| 📦 **Versión**         | ![Version](https://img.shields.io/badge/version-1.0.0-blue)          | Estable  |

---

<div align="center">

**🚀 Desarrollado con ❤️ por el equipo de ConversaAI**

[🌟 Star en GitHub](https://github.com/ZetahDev/conversaai) • [📖 Documentación](docs/) • [🐛 Reportar Bug](https://github.com/ZetahDev/conversaai/issues) • [💡 Solicitar Feature](https://github.com/ZetahDev/conversaai/discussions)

</div>
