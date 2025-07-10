# 🚀 Guía de Deployment - ChatBot SAAS

Esta guía te ayudará a desplegar ChatBot SAAS en producción de manera segura y eficiente.

## 📋 Prerrequisitos

### Servidor
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: Mínimo 4GB, recomendado 8GB+
- **CPU**: Mínimo 2 cores, recomendado 4+ cores
- **Disco**: Mínimo 50GB SSD
- **Red**: Conexión estable a internet

### Software
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx (opcional, incluido en Docker)
- Certbot para SSL (opcional)

### Dominios y DNS
- Dominio principal: `yourdomain.com`
- Subdominio API: `api.yourdomain.com` (opcional)
- Subdominio admin: `admin.yourdomain.com`

## 🔧 Configuración Inicial

### 1. Clonar el Repositorio
```bash
git clone https://github.com/your-org/chatbot-saas.git
cd chatbot-saas
```

### 2. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp backend/.env.production.example backend/.env.production

# Editar configuración
nano backend/.env.production
```

**⚠️ IMPORTANTE**: Cambiar todas las variables marcadas como `CHANGE_THIS_*`

### 3. Configurar SSL/TLS
```bash
# Opción 1: Usar Certbot (recomendado)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Opción 2: Certificados propios
mkdir -p ssl
cp your-certificate.crt ssl/yourdomain.crt
cp your-private-key.key ssl/yourdomain.key
```

### 4. Configurar Nginx
```bash
# Editar configuración de Nginx
nano nginx/nginx.conf

# Cambiar 'yourdomain.com' por tu dominio real
sed -i 's/yourdomain.com/tu-dominio.com/g' nginx/nginx.conf
```

## 🚀 Deployment

### Deployment Automático
```bash
# Hacer ejecutable el script
chmod +x scripts/deploy.sh

# Ejecutar deployment
./scripts/deploy.sh production
```

### Deployment Manual

#### 1. Construir Imágenes
```bash
docker-compose -f docker-compose.prod.yml build
```

#### 2. Iniciar Base de Datos
```bash
docker-compose -f docker-compose.prod.yml up -d postgres redis
```

#### 3. Ejecutar Migraciones
```bash
docker-compose -f docker-compose.prod.yml run --rm backend poetry run alembic upgrade head
```

#### 4. Iniciar Todos los Servicios
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### 5. Verificar Estado
```bash
./scripts/monitor.sh status
```

## 📊 Monitoreo

### Verificación de Salud
```bash
# Verificación rápida
./scripts/monitor.sh check

# Estado completo
./scripts/monitor.sh status

# Logs en tiempo real
./scripts/monitor.sh logs
```

### URLs de Monitoreo
- **API Health**: `https://yourdomain.com/api/health`
- **Grafana**: `https://admin.yourdomain.com/grafana`
- **Prometheus**: `https://admin.yourdomain.com/prometheus`

### Métricas Importantes
- **CPU**: < 80%
- **Memoria**: < 80%
- **Disco**: < 80%
- **Tiempo de respuesta API**: < 500ms
- **Uptime**: > 99.9%

## 🔒 Seguridad

### Configuraciones Críticas
1. **Cambiar todas las contraseñas por defecto**
2. **Configurar firewall**:
   ```bash
   ufw allow 22    # SSH
   ufw allow 80    # HTTP
   ufw allow 443   # HTTPS
   ufw enable
   ```
3. **Configurar fail2ban**:
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

### Backup de Seguridad
```bash
# Backup manual
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U chatbot_user chatbot_production > backup.sql

# Backup automático (configurar en crontab)
0 2 * * * /path/to/chatbot-saas/scripts/backup.sh
```

## 🔄 Actualizaciones

### Actualización de Código
```bash
# 1. Hacer backup
./scripts/backup.sh

# 2. Obtener últimos cambios
git pull origin main

# 3. Redesplegar
./scripts/deploy.sh production
```

### Rollback
```bash
# 1. Volver a versión anterior
git checkout <previous-commit>

# 2. Redesplegar
./scripts/deploy.sh production

# 3. Restaurar backup si es necesario
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U chatbot_user chatbot_production < backup.sql
```

## 🐛 Troubleshooting

### Problemas Comunes

#### Servicio no inicia
```bash
# Ver logs específicos
docker-compose -f docker-compose.prod.yml logs backend

# Verificar configuración
docker-compose -f docker-compose.prod.yml config
```

#### Base de datos no conecta
```bash
# Verificar estado de PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Ver logs de la base de datos
docker-compose -f docker-compose.prod.yml logs postgres
```

#### SSL/TLS problemas
```bash
# Verificar certificados
openssl x509 -in ssl/yourdomain.crt -text -noout

# Renovar certificados Let's Encrypt
sudo certbot renew
```

#### Alto uso de recursos
```bash
# Ver uso de recursos por contenedor
docker stats

# Limpiar recursos no utilizados
docker system prune -f
```

### Logs Importantes
- **Backend**: `/var/log/chatbot-saas/app.log`
- **Nginx**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL**: Logs del contenedor
- **Redis**: Logs del contenedor

## 📞 Soporte

### Contactos de Emergencia
- **DevOps**: devops@yourdomain.com
- **Backend**: backend@yourdomain.com
- **Infraestructura**: infra@yourdomain.com

### Escalación
1. **Nivel 1**: Verificar logs y reiniciar servicios
2. **Nivel 2**: Contactar equipo de desarrollo
3. **Nivel 3**: Contactar arquitecto de sistemas

## 📚 Referencias

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Astro Documentation](https://docs.astro.build/)

---

**⚠️ Nota**: Esta documentación debe actualizarse con cada cambio significativo en la infraestructura.
