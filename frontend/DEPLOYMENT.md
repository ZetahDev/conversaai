# 🚀 Deployment Guide - ChatBot SAAS Frontend

Esta guía te ayudará a deployar el frontend de ChatBot SAAS de manera segura y eficiente.

## 📋 Prerrequisitos

### Desarrollo
- Node.js 18+ 
- npm 9+
- Git

### Producción
- Servidor web (Nginx, Apache, o CDN)
- Certificado SSL/TLS
- Dominio configurado
- Backend API funcionando

## 🔧 Configuración de Entornos

### 1. Variables de Entorno

Copia y configura los archivos de entorno:

```bash
# Para desarrollo
cp .env.example .env

# Para producción
cp .env.production .env.production
```

### 2. Variables Críticas para Producción

**⚠️ IMPORTANTE: Configura estas variables antes del deployment:**

```env
# API Configuration
PUBLIC_API_URL=https://api.tudominio.com
PUBLIC_APP_URL=https://tudominio.com

# Security
PUBLIC_ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
PUBLIC_PASSWORD_MIN_LENGTH=12
PUBLIC_LOGIN_MAX_ATTEMPTS=3

# External Services
PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_tu-clave-real
PUBLIC_GA_TRACKING_ID=G-XXXXXXXXXX
PUBLIC_SENTRY_DSN=https://tu-sentry-dsn@sentry.io/proyecto
```

## 🏗️ Proceso de Build

### Desarrollo
```bash
npm run deploy:dev
```

### Staging
```bash
npm run deploy:staging
```

### Producción
```bash
npm run deploy:prod
```

## 🔒 Checklist de Seguridad

### Antes del Deployment

- [ ] **Variables de entorno configuradas**
- [ ] **HTTPS habilitado**
- [ ] **Certificado SSL válido**
- [ ] **CORS configurado correctamente**
- [ ] **Rate limiting activado**
- [ ] **Headers de seguridad configurados**
- [ ] **Audit de dependencias pasado**
- [ ] **Tests ejecutados exitosamente**

### Headers de Seguridad Requeridos

Configura estos headers en tu servidor web:

```nginx
# Nginx configuration
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.tudominio.com;";
```

## 🌐 Deployment por Plataforma

### Vercel

1. **Conectar repositorio:**
   ```bash
   npm install -g vercel
   vercel login
   vercel
   ```

2. **Configurar variables de entorno en Vercel Dashboard**

3. **Configurar dominio personalizado**

### Netlify

1. **Build settings:**
   - Build command: `npm run build`
   - Publish directory: `dist`

2. **Configurar redirects en `netlify.toml`:**
   ```toml
   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

### AWS S3 + CloudFront

1. **Build y upload:**
   ```bash
   npm run deploy:prod
   aws s3 sync dist/ s3://tu-bucket --delete
   ```

2. **Configurar CloudFront distribution**

3. **Configurar Route 53 para dominio**

### Servidor Propio (Nginx)

1. **Configuración de Nginx:**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name tudominio.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       root /var/www/chatbot-saas/dist;
       index index.html;
       
       # SPA routing
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       # Security headers
       include /etc/nginx/security-headers.conf;
       
       # Gzip compression
       gzip on;
       gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   }
   ```

## 📊 Monitoreo y Logging

### 1. Error Tracking (Sentry)

```javascript
// Configurado automáticamente si PUBLIC_SENTRY_DSN está definido
```

### 2. Analytics (Google Analytics)

```javascript
// Configurado automáticamente si PUBLIC_GA_TRACKING_ID está definido
```

### 3. Performance Monitoring

El sistema incluye monitoreo automático de:
- Core Web Vitals (LCP, FID, CLS)
- Tiempo de carga de página
- Errores de JavaScript
- Métricas de API

## 🔄 CI/CD Pipeline

### GitHub Actions

Crea `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run security audit
      run: npm audit --audit-level=high
    
    - name: Run tests
      run: npm test
    
    - name: Build for production
      run: npm run deploy:prod
      env:
        PUBLIC_API_URL: ${{ secrets.API_URL }}
        PUBLIC_STRIPE_PUBLISHABLE_KEY: ${{ secrets.STRIPE_KEY }}
        PUBLIC_SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
    
    - name: Deploy to server
      # Agregar step de deployment específico
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Build falla:**
   ```bash
   npm run clean
   npm install
   npm run deploy:prod
   ```

2. **Variables de entorno no se cargan:**
   - Verificar que empiecen con `PUBLIC_`
   - Reiniciar el proceso de build

3. **Errores de CORS:**
   - Verificar `PUBLIC_ALLOWED_ORIGINS`
   - Configurar headers en el servidor

4. **Problemas de routing:**
   - Configurar redirects para SPA
   - Verificar configuración del servidor web

### Logs y Debugging

```bash
# Ver logs de build
npm run deploy:prod 2>&1 | tee build.log

# Verificar variables de entorno
node -e "console.log(process.env)" | grep PUBLIC_

# Test de conectividad con API
curl -I https://api.tudominio.com/health
```

## 📈 Optimización de Performance

### 1. Compresión
- Habilitar Gzip/Brotli en servidor
- Configurar cache headers apropiados

### 2. CDN
- Usar CloudFront, Cloudflare, o similar
- Configurar cache de assets estáticos

### 3. Monitoring
- Configurar alertas para errores
- Monitorear métricas de performance

## 🔐 Backup y Rollback

### Backup
```bash
# Backup de configuración
cp .env.production .env.production.backup.$(date +%Y%m%d)

# Backup de build
tar -czf dist-backup-$(date +%Y%m%d).tar.gz dist/
```

### Rollback
```bash
# Rollback a versión anterior
git checkout HEAD~1
npm run deploy:prod
```

## 📞 Soporte

Si encuentras problemas durante el deployment:

1. Revisa los logs de build
2. Verifica la configuración de variables de entorno
3. Consulta la documentación del proveedor de hosting
4. Contacta al equipo de desarrollo

---

**⚠️ Recordatorio:** Nunca hagas deployment a producción sin probar primero en staging.
