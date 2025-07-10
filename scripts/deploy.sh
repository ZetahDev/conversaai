#!/bin/bash

# Script de deployment para ConversaAI
# Uso: ./scripts/deploy.sh [environment]

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
ENVIRONMENT=${1:-production}
PROJECT_NAME="chatbot-saas"
BACKUP_DIR="/var/backups/$PROJECT_NAME"
LOG_FILE="/var/log/$PROJECT_NAME/deploy.log"

# Funciones de utilidad
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Verificar prerrequisitos
check_prerequisites() {
    log "Verificando prerrequisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
    fi
    
    # Verificar archivo de entorno
    if [ ! -f ".env.$ENVIRONMENT" ]; then
        error "Archivo .env.$ENVIRONMENT no encontrado"
    fi
    
    # Verificar permisos
    if [ ! -w "." ]; then
        error "No tienes permisos de escritura en el directorio actual"
    fi
    
    success "Prerrequisitos verificados"
}

# Crear backup de la base de datos
backup_database() {
    log "Creando backup de la base de datos..."
    
    # Crear directorio de backup si no existe
    mkdir -p "$BACKUP_DIR"
    
    # Nombre del archivo de backup
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Crear backup
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U chatbot_user chatbot_production > "$BACKUP_FILE"; then
        success "Backup creado: $BACKUP_FILE"
    else
        warning "No se pudo crear el backup de la base de datos"
    fi
}

# Detener servicios
stop_services() {
    log "Deteniendo servicios..."
    
    if docker-compose -f docker-compose.prod.yml down; then
        success "Servicios detenidos"
    else
        warning "Algunos servicios no se pudieron detener correctamente"
    fi
}

# Construir imágenes
build_images() {
    log "Construyendo imágenes Docker..."
    
    # Backend
    log "Construyendo imagen del backend..."
    if docker-compose -f docker-compose.prod.yml build backend; then
        success "Imagen del backend construida"
    else
        error "Error construyendo imagen del backend"
    fi
    
    # Frontend
    log "Construyendo imagen del frontend..."
    if docker-compose -f docker-compose.prod.yml build frontend; then
        success "Imagen del frontend construida"
    else
        error "Error construyendo imagen del frontend"
    fi
}

# Ejecutar migraciones
run_migrations() {
    log "Ejecutando migraciones de base de datos..."
    
    # Iniciar solo la base de datos
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    
    # Esperar a que la base de datos esté lista
    log "Esperando a que la base de datos esté lista..."
    sleep 10
    
    # Ejecutar migraciones
    if docker-compose -f docker-compose.prod.yml run --rm backend poetry run alembic upgrade head; then
        success "Migraciones ejecutadas correctamente"
    else
        error "Error ejecutando migraciones"
    fi
}

# Iniciar servicios
start_services() {
    log "Iniciando servicios..."
    
    if docker-compose -f docker-compose.prod.yml up -d; then
        success "Servicios iniciados"
    else
        error "Error iniciando servicios"
    fi
}

# Verificar salud de los servicios
health_check() {
    log "Verificando salud de los servicios..."
    
    # Esperar un momento para que los servicios se inicien
    sleep 30
    
    # Verificar backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        success "Backend está funcionando"
    else
        error "Backend no responde"
    fi
    
    # Verificar frontend
    if curl -f http://localhost > /dev/null 2>&1; then
        success "Frontend está funcionando"
    else
        warning "Frontend no responde (puede estar iniciando)"
    fi
    
    # Verificar base de datos
    if docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U chatbot_user > /dev/null 2>&1; then
        success "Base de datos está funcionando"
    else
        error "Base de datos no responde"
    fi
}

# Limpiar recursos no utilizados
cleanup() {
    log "Limpiando recursos no utilizados..."
    
    # Limpiar imágenes no utilizadas
    docker image prune -f
    
    # Limpiar volúmenes no utilizados
    docker volume prune -f
    
    success "Limpieza completada"
}

# Mostrar logs
show_logs() {
    log "Mostrando logs de los servicios..."
    docker-compose -f docker-compose.prod.yml logs --tail=50
}

# Función principal
main() {
    log "=== Iniciando deployment de $PROJECT_NAME en $ENVIRONMENT ==="
    
    # Verificar prerrequisitos
    check_prerequisites
    
    # Crear backup
    backup_database
    
    # Detener servicios
    stop_services
    
    # Construir imágenes
    build_images
    
    # Ejecutar migraciones
    run_migrations
    
    # Iniciar servicios
    start_services
    
    # Verificar salud
    health_check
    
    # Limpiar
    cleanup
    
    success "=== Deployment completado exitosamente ==="
    
    log "URLs disponibles:"
    log "  - Frontend: https://yourdomain.com"
    log "  - API: https://yourdomain.com/api"
    log "  - Docs: https://yourdomain.com/api/docs"
    log "  - Grafana: https://admin.yourdomain.com/grafana"
    log "  - Prometheus: https://admin.yourdomain.com/prometheus"
    
    # Mostrar logs recientes
    show_logs
}

# Manejo de señales
trap 'error "Deployment interrumpido"' INT TERM

# Ejecutar función principal
main "$@"
