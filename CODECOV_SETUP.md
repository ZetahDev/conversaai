# 📊 Configuración de Codecov para ConversaAI

Esta guía te ayudará a configurar Codecov completamente para obtener coverage tracking y bundle analysis.

## 🔑 **Paso 1: Configurar Token en GitHub**

### 1.1 Ir a GitHub Secrets
1. Ve a: https://github.com/ZetahDev/conversaai/settings/secrets/actions
2. Click en "New repository secret"

### 1.2 Agregar el Token
- **Name**: `CODECOV_TOKEN`
- **Secret**: `4bfa41b3-d0c1-492e-9521-e2363ec969e7`

## 🚀 **Paso 2: Verificar la Configuración**

### 2.1 Archivos Configurados
- ✅ `.github/workflows/ci.yml` - Pipeline CI/CD
- ✅ `codecov.yml` - Configuración de Codecov
- ✅ `backend/pytest.ini` - Tests con coverage
- ✅ `frontend/astro.config.mjs` - Bundle analysis

### 2.2 URLs de Badges
Una vez configurado, estos badges funcionarán:

```markdown
[![Build Status](https://github.com/ZetahDev/conversaai/workflows/🚀%20ConversaAI%20CI/CD%20Pipeline/badge.svg)](https://github.com/ZetahDev/conversaai/actions)
[![Coverage](https://codecov.io/gh/ZetahDev/conversaai/branch/main/graph/badge.svg)](https://codecov.io/gh/ZetahDev/conversaai)
```

## 🧪 **Paso 3: Ejecutar el Pipeline**

### 3.1 Trigger Automático
El pipeline se ejecutará automáticamente cuando:
- Hagas push a `main`
- Abras un Pull Request
- Hagas push a `develop`

### 3.2 Trigger Manual
```bash
# Hacer un commit para activar el pipeline
git add .
git commit -m "🔧 Configure Codecov integration"
git push origin main
```

## 📊 **Paso 4: Verificar Resultados**

### 4.1 GitHub Actions
- Ve a: https://github.com/ZetahDev/conversaai/actions
- Verifica que el workflow "🚀 ConversaAI CI/CD Pipeline" se ejecute

### 4.2 Codecov Dashboard
- Ve a: https://codecov.io/gh/ZetahDev/conversaai
- Verifica que aparezcan los reportes de coverage

### 4.3 Bundle Analysis
- En Codecov, ve a la pestaña "Bundles"
- Verifica que aparezca "conversaai-frontend"

## 🎯 **Objetivos de Coverage**

### Backend
- **Mínimo**: 80%
- **Objetivo**: 90%+
- **Crítico**: 95%+ para módulos core

### Frontend
- **Bundle Size**: < 500KB
- **Chunk Analysis**: Optimización automática
- **Performance**: Tracking de regresiones

## 🔧 **Comandos Útiles**

### Backend Testing
```bash
cd backend
python run_tests.py
```

### Frontend Building
```bash
cd frontend
npm install
npm run build
```

### Coverage Local
```bash
# Backend
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend bundle analysis se ejecuta automáticamente en build
```

## 🐛 **Troubleshooting**

### Error: "CODECOV_TOKEN not found"
- Verifica que agregaste el secret en GitHub
- Asegúrate de que el nombre sea exactamente `CODECOV_TOKEN`

### Error: "Upload failed"
- Verifica que el token sea correcto
- Revisa los logs en GitHub Actions

### Badge no se actualiza
- Espera unos minutos después del primer push
- Verifica que el workflow se haya ejecutado exitosamente

## 📈 **Métricas Esperadas**

### Después de la Primera Ejecución
- ✅ Coverage badge funcionando
- ✅ Build status badge funcionando
- ✅ Reportes en Codecov dashboard
- ✅ Bundle analysis disponible

### Métricas de Calidad
- 🎯 Coverage: 80%+
- 🚀 Build time: < 5 minutos
- 📦 Bundle size: Optimizado
- 🔍 Security: Sin vulnerabilidades

## 🔗 **Enlaces Importantes**

- **GitHub Actions**: https://github.com/ZetahDev/conversaai/actions
- **Codecov Dashboard**: https://codecov.io/gh/ZetahDev/conversaai
- **Coverage Reports**: Se generan automáticamente
- **Bundle Analysis**: https://codecov.io/gh/ZetahDev/conversaai/bundles

---

## ✅ **Checklist de Configuración**

- [ ] Token agregado en GitHub Secrets
- [ ] Primer push realizado
- [ ] Workflow ejecutado exitosamente
- [ ] Coverage report visible en Codecov
- [ ] Badges funcionando en README
- [ ] Bundle analysis disponible

**🎉 Una vez completado este checklist, ConversaAI tendrá un sistema de CI/CD profesional con coverage tracking completo!**
