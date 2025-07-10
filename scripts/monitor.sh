#!/bin/bash

# Script de monitoreo para ConversaAI
# Uso: ./scripts/monitor.sh [check|status|logs|restart]

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
PROJECT_NAME="chatbot-saas"
COMPOSE_FILE="docker-compose.prod.yml"
HEALTH_ENDPOINTS=(
    "http://localhost:8000/health"
    "http://localhost"
)

# Funciones de utilidad
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Verificar estado de los servicios
check_services() {
    log "Verificando estado de los servicios..."
    
    # Obtener estado de los contenedores
    SERVICES=$(docker-compose -f $COMPOSE_FILE ps --services)
    
    for service in $SERVICES; do
        STATUS=$(docker-compose -f $COMPOSE_FILE ps -q $service | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
        
        case $STATUS in
            "running")
                success "$service: ✓ Ejecutándose"
                ;;
            "exited")
                error "$service: ✗ Detenido"
                ;;
            "restarting")
                warning "$service: ⟳ Reiniciando"
                ;;
            "not_found")
                error "$service: ✗ No encontrado"
                ;;
            *)
                warning "$service: ? Estado desconocido ($STATUS)"
                ;;
        esac
    done
}

# Verificar endpoints de salud
check_health() {
    log "Verificando endpoints de salud..."
    
    for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
        if curl -f -s --max-time 10 "$endpoint" > /dev/null; then
            success "$endpoint: ✓ Respondiendo"
        else
            error "$endpoint: ✗ No responde"
        fi
    done
}

# Verificar recursos del sistema
check_resources() {
    log "Verificando recursos del sistema..."
    
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
        warning "CPU: ${CPU_USAGE}% (Alto)"
    else
        success "CPU: ${CPU_USAGE}%"
    fi
    
    # Memoria
    MEMORY_INFO=$(free | grep Mem)
    MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
    MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
    MEMORY_PERCENT=$(echo "scale=1; $MEMORY_USED * 100 / $MEMORY_TOTAL" | bc)
    
    if (( $(echo "$MEMORY_PERCENT > 80" | bc -l) )); then
        warning "Memoria: ${MEMORY_PERCENT}% (Alta)"
    else
        success "Memoria: ${MEMORY_PERCENT}%"
    fi
    
    # Disco
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 80 ]; then
        warning "Disco: ${DISK_USAGE}% (Alto)"
    else
        success "Disco: ${DISK_USAGE}%"
    fi
}

# Verificar logs de errores
check_logs() {
    log "Verificando logs de errores recientes..."
    
    # Buscar errores en logs del backend
    ERROR_COUNT=$(docker-compose -f $COMPOSE_FILE logs --tail=100 backend 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        warning "Se encontraron $ERROR_COUNT errores en logs del backend"
        docker-compose -f $COMPOSE_FILE logs --tail=10 backend | grep -i "error\|exception\|failed" || true
    else
        success "No se encontraron errores recientes en logs"
    fi
}

# Verificar conectividad de base de datos
check_database() {
    log "Verificando conectividad de base de datos..."
    
    if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U chatbot_user > /dev/null 2>&1; then
        success "Base de datos: ✓ Conectada"
        
        # Verificar número de conexiones
        CONNECTIONS=$(docker-compose -f $COMPOSE_FILE exec -T postgres psql -U chatbot_user -d chatbot_production -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs)
        log "Conexiones activas: $CONNECTIONS"
    else
        error "Base de datos: ✗ No conectada"
    fi
}

# Verificar Redis
check_redis() {
    log "Verificando Redis..."
    
    if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
        success "Redis: ✓ Conectado"
        
        # Verificar memoria usada
        REDIS_MEMORY=$(docker-compose -f $COMPOSE_FILE exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        log "Memoria Redis: $REDIS_MEMORY"
    else
        error "Redis: ✗ No conectado"
    fi
}

# Mostrar estado completo
show_status() {
    log "=== Estado del sistema $PROJECT_NAME ==="
    
    check_services
    echo
    check_health
    echo
    check_resources
    echo
    check_database
    echo
    check_redis
    echo
    check_logs
    
    log "=== Fin del reporte ==="
}

# Mostrar logs en tiempo real
show_logs() {
    log "Mostrando logs en tiempo real (Ctrl+C para salir)..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Reiniciar servicios
restart_services() {
    log "Reiniciando servicios..."
    
    read -p "¿Estás seguro de que quieres reiniciar todos los servicios? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f $COMPOSE_FILE restart
        success "Servicios reiniciados"
        
        # Esperar y verificar
        sleep 30
        check_health
    else
        log "Reinicio cancelado"
    fi
}

# Verificación rápida
quick_check() {
    log "=== Verificación rápida ==="
    
    # Verificar servicios críticos
    CRITICAL_SERVICES=("backend" "postgres" "redis")
    ALL_OK=true
    
    for service in "${CRITICAL_SERVICES[@]}"; do
        STATUS=$(docker-compose -f $COMPOSE_FILE ps -q $service | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
        
        if [ "$STATUS" != "running" ]; then
            error "$service no está ejecutándose"
            ALL_OK=false
        fi
    done
    
    # Verificar endpoint principal
    if ! curl -f -s --max-time 5 "http://localhost:8000/health" > /dev/null; then
        error "API no responde"
        ALL_OK=false
    fi
    
    if [ "$ALL_OK" = true ]; then
        success "✓ Todos los servicios críticos están funcionando"
        exit 0
    else
        error "✗ Algunos servicios críticos tienen problemas"
        exit 1
    fi
}

# Función principal
main() {
    case "${1:-status}" in
        "check"|"quick")
            quick_check
            ;;
        "status"|"")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "restart")
            restart_services
            ;;
        "help"|"-h"|"--help")
            echo "Uso: $0 [check|status|logs|restart|help]"
            echo ""
            echo "Comandos:"
            echo "  check    - Verificación rápida de servicios críticos"
            echo "  status   - Estado completo del sistema (por defecto)"
            echo "  logs     - Mostrar logs en tiempo real"
            echo "  restart  - Reiniciar todos los servicios"
            echo "  help     - Mostrar esta ayuda"
            ;;
        *)
            error "Comando desconocido: $1"
            echo "Usa '$0 help' para ver los comandos disponibles"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
