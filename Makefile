# Makefile para ChatBot SAAS

.PHONY: help install dev build test clean docker-build docker-up docker-down migrate seed lint format

# Variables
BACKEND_DIR = backend
FRONTEND_DIR = frontend
DOCKER_COMPOSE = docker-compose
PYTHON = python3
PIP = pip3
NODE = node
NPM = npm

# Colores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Mostrar ayuda
	@echo "$(BLUE)ChatBot SAAS - Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Instalación
install: ## Instalar todas las dependencias
	@echo "$(YELLOW)Instalando dependencias del backend...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m venv venv
	cd $(BACKEND_DIR) && source venv/bin/activate && $(PIP) install -r requirements.txt
	@echo "$(YELLOW)Instalando dependencias del frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✓ Dependencias instaladas$(NC)"

install-backend: ## Instalar dependencias del backend
	@echo "$(YELLOW)Instalando dependencias del backend...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m venv venv
	cd $(BACKEND_DIR) && source venv/bin/activate && $(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Backend instalado$(NC)"

install-frontend: ## Instalar dependencias del frontend
	@echo "$(YELLOW)Instalando dependencias del frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✓ Frontend instalado$(NC)"

# Desarrollo
dev: ## Iniciar entorno de desarrollo completo
	@echo "$(YELLOW)Iniciando entorno de desarrollo...$(NC)"
	$(DOCKER_COMPOSE) up -d postgres redis minio qdrant
	@echo "$(GREEN)✓ Servicios de base iniciados$(NC)"
	@echo "$(YELLOW)Inicia el backend y frontend en terminales separadas:$(NC)"
	@echo "$(BLUE)Backend:$(NC) make dev-backend"
	@echo "$(BLUE)Frontend:$(NC) make dev-frontend"

dev-backend: ## Iniciar solo el backend en desarrollo
	@echo "$(YELLOW)Iniciando backend...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Iniciar solo el frontend en desarrollo
	@echo "$(YELLOW)Iniciando frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run dev

dev-services: ## Iniciar solo los servicios (DB, Redis, etc.)
	@echo "$(YELLOW)Iniciando servicios de desarrollo...$(NC)"
	$(DOCKER_COMPOSE) up -d postgres redis minio qdrant
	@echo "$(GREEN)✓ Servicios iniciados$(NC)"

# Build
build: ## Construir aplicación para producción
	@echo "$(YELLOW)Construyendo aplicación...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "$(GREEN)✓ Aplicación construida$(NC)"

build-frontend: ## Construir solo el frontend
	@echo "$(YELLOW)Construyendo frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "$(GREEN)✓ Frontend construido$(NC)"

# Testing
test: ## Ejecutar todos los tests
	@echo "$(YELLOW)Ejecutando tests...$(NC)"
	make test-backend
	make test-frontend
	@echo "$(GREEN)✓ Todos los tests completados$(NC)"

test-backend: ## Ejecutar tests del backend
	@echo "$(YELLOW)Ejecutando tests del backend...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && pytest
	@echo "$(GREEN)✓ Tests del backend completados$(NC)"

test-frontend: ## Ejecutar tests del frontend
	@echo "$(YELLOW)Ejecutando tests del frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) test
	@echo "$(GREEN)✓ Tests del frontend completados$(NC)"

test-coverage: ## Ejecutar tests con coverage
	@echo "$(YELLOW)Ejecutando tests con coverage...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && pytest --cov=app --cov-report=html
	@echo "$(GREEN)✓ Coverage generado en backend/htmlcov/$(NC)"

# Linting y formateo
lint: ## Ejecutar linting en todo el proyecto
	@echo "$(YELLOW)Ejecutando linting...$(NC)"
	make lint-backend
	make lint-frontend
	@echo "$(GREEN)✓ Linting completado$(NC)"

lint-backend: ## Ejecutar linting del backend
	@echo "$(YELLOW)Linting backend...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && flake8 app/
	cd $(BACKEND_DIR) && source venv/bin/activate && mypy app/
	@echo "$(GREEN)✓ Backend linting completado$(NC)"

lint-frontend: ## Ejecutar linting del frontend
	@echo "$(YELLOW)Linting frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run lint
	@echo "$(GREEN)✓ Frontend linting completado$(NC)"

format: ## Formatear código
	@echo "$(YELLOW)Formateando código...$(NC)"
	make format-backend
	make format-frontend
	@echo "$(GREEN)✓ Código formateado$(NC)"

format-backend: ## Formatear código del backend
	@echo "$(YELLOW)Formateando backend...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && black app/
	cd $(BACKEND_DIR) && source venv/bin/activate && isort app/
	@echo "$(GREEN)✓ Backend formateado$(NC)"

format-frontend: ## Formatear código del frontend
	@echo "$(YELLOW)Formateando frontend...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run format
	@echo "$(GREEN)✓ Frontend formateado$(NC)"

# Base de datos
migrate: ## Ejecutar migraciones de base de datos
	@echo "$(YELLOW)Ejecutando migraciones...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Migraciones ejecutadas$(NC)"

migrate-create: ## Crear nueva migración
	@echo "$(YELLOW)Creando nueva migración...$(NC)"
	@read -p "Nombre de la migración: " name; \
	cd $(BACKEND_DIR) && source venv/bin/activate && alembic revision --autogenerate -m "$$name"
	@echo "$(GREEN)✓ Migración creada$(NC)"

migrate-rollback: ## Rollback de la última migración
	@echo "$(YELLOW)Haciendo rollback...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && alembic downgrade -1
	@echo "$(GREEN)✓ Rollback completado$(NC)"

seed: ## Poblar base de datos con datos de prueba
	@echo "$(YELLOW)Poblando base de datos...$(NC)"
	cd $(BACKEND_DIR) && source venv/bin/activate && python -m app.scripts.seed_data
	@echo "$(GREEN)✓ Base de datos poblada$(NC)"

# Docker
docker-build: ## Construir imágenes Docker
	@echo "$(YELLOW)Construyendo imágenes Docker...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Imágenes construidas$(NC)"

docker-up: ## Iniciar todos los servicios con Docker
	@echo "$(YELLOW)Iniciando servicios con Docker...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Servicios iniciados$(NC)"
	@echo "$(BLUE)Backend:$(NC) http://localhost:8000"
	@echo "$(BLUE)Frontend:$(NC) http://localhost:4321"
	@echo "$(BLUE)Flower:$(NC) http://localhost:5555"
	@echo "$(BLUE)MinIO:$(NC) http://localhost:9001"

docker-down: ## Detener todos los servicios Docker
	@echo "$(YELLOW)Deteniendo servicios Docker...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Servicios detenidos$(NC)"

docker-logs: ## Ver logs de Docker
	$(DOCKER_COMPOSE) logs -f

docker-clean: ## Limpiar contenedores y volúmenes Docker
	@echo "$(YELLOW)Limpiando Docker...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✓ Docker limpiado$(NC)"

# Utilidades
clean: ## Limpiar archivos temporales
	@echo "$(YELLOW)Limpiando archivos temporales...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name "*.log" -delete
	cd $(FRONTEND_DIR) && rm -rf node_modules/.cache
	cd $(FRONTEND_DIR) && rm -rf .astro
	@echo "$(GREEN)✓ Archivos temporales limpiados$(NC)"

status: ## Mostrar estado de los servicios
	@echo "$(BLUE)Estado de los servicios:$(NC)"
	$(DOCKER_COMPOSE) ps

logs: ## Ver logs de todos los servicios
	$(DOCKER_COMPOSE) logs -f --tail=100

shell-backend: ## Abrir shell en el contenedor del backend
	$(DOCKER_COMPOSE) exec backend bash

shell-db: ## Abrir shell en la base de datos
	$(DOCKER_COMPOSE) exec postgres psql -U chatbot_user -d chatbot_db

backup-db: ## Crear backup de la base de datos
	@echo "$(YELLOW)Creando backup de la base de datos...$(NC)"
	$(DOCKER_COMPOSE) exec postgres pg_dump -U chatbot_user chatbot_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup creado$(NC)"

# Deployment
deploy-staging: ## Deploy a staging
	@echo "$(YELLOW)Desplegando a staging...$(NC)"
	# Aquí irían los comandos de deploy a staging
	@echo "$(GREEN)✓ Deploy a staging completado$(NC)"

deploy-production: ## Deploy a producción
	@echo "$(RED)⚠️  Deploy a producción$(NC)"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "$(YELLOW)Desplegando a producción...$(NC)"
	# Aquí irían los comandos de deploy a producción
	@echo "$(GREEN)✓ Deploy a producción completado$(NC)"

# Información
info: ## Mostrar información del proyecto
	@echo "$(BLUE)ChatBot SAAS - Información del proyecto$(NC)"
	@echo ""
	@echo "$(YELLOW)Estructura:$(NC)"
	@echo "  Backend:  FastAPI + PostgreSQL + Redis"
	@echo "  Frontend: Astro + React + TailwindCSS"
	@echo "  Queue:    Celery + Redis"
	@echo "  Storage:  MinIO/S3"
	@echo "  Vector:   Pinecone/Qdrant"
	@echo ""
	@echo "$(YELLOW)URLs de desarrollo:$(NC)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:4321"
	@echo "  Docs:     http://localhost:8000/docs"
	@echo "  Flower:   http://localhost:5555"
	@echo "  MinIO:    http://localhost:9001"
	@echo ""
	@echo "$(YELLOW)Comandos útiles:$(NC)"
	@echo "  make dev          - Iniciar desarrollo"
	@echo "  make test         - Ejecutar tests"
	@echo "  make lint         - Linting"
	@echo "  make docker-up    - Docker completo"
