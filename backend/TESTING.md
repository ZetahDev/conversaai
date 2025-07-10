# 🧪 Testing Guide - ConversaAI

Esta guía explica cómo ejecutar y mantener los tests de ConversaAI.

## 📋 Configuración de Testing

### Dependencias Requeridas

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov pytest-asyncio httpx coverage
```

### Estructura de Tests

```
backend/tests/
├── __init__.py
├── conftest.py              # Configuración global de pytest
├── test_main.py            # Tests del módulo principal
├── test_config.py          # Tests de configuración
├── test_auth.py            # Tests de autenticación
├── test_chatbots.py        # Tests de chatbots
├── test_integrations.py    # Tests de integraciones
└── fixtures/               # Datos de prueba
```

## 🚀 Ejecutar Tests

### Opción 1: Script Automatizado (Recomendado)

```bash
# Desde el directorio backend/
python run_tests.py
```

### Opción 2: Comandos Manuales

```bash
# Tests básicos
pytest tests/ -v

# Tests con coverage
pytest tests/ --cov=app --cov-report=term-missing

# Tests con coverage y reporte HTML
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Tests específicos
pytest tests/test_main.py -v

# Tests con marcadores
pytest -m "unit" -v          # Solo tests unitarios
pytest -m "integration" -v   # Solo tests de integración
pytest -m "not slow" -v      # Excluir tests lentos
```

## 📊 Coverage Reports

### Tipos de Reportes

1. **Terminal**: Muestra coverage en la consola
2. **HTML**: Reporte interactivo en `htmlcov/index.html`
3. **XML**: Para integración con Codecov (`coverage.xml`)

### Objetivos de Coverage

- **Mínimo**: 80%
- **Objetivo**: 90%+
- **Crítico**: 95%+ para módulos core

### Ver Reporte HTML

```bash
# Generar y abrir reporte HTML
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## 🏷️ Marcadores de Tests

### Marcadores Disponibles

- `@pytest.mark.unit` - Tests unitarios rápidos
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.slow` - Tests que tardan más de 1 segundo
- `@pytest.mark.api` - Tests de endpoints API
- `@pytest.mark.auth` - Tests de autenticación
- `@pytest.mark.service` - Tests de servicios

### Uso de Marcadores

```python
import pytest

@pytest.mark.unit
def test_fast_function():
    assert True

@pytest.mark.integration
@pytest.mark.slow
def test_database_integration():
    # Test que requiere BD
    pass
```

## 🔧 Configuración Avanzada

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
addopts = 
    -v
    --cov=app
    --cov-branch
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    api: API tests
```

### Fixtures Comunes

```python
# En conftest.py
@pytest.fixture
def client():
    """Cliente de prueba para FastAPI"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

@pytest.fixture
def test_user():
    """Usuario de prueba"""
    return {
        "email": "test@example.com",
        "password": "testpass123"
    }
```

## 🚀 CI/CD Integration

### GitHub Actions

Los tests se ejecutan automáticamente en GitHub Actions:

- ✅ En cada push a `main`
- ✅ En cada pull request
- ✅ Coverage se sube a Codecov
- ✅ Badges se actualizan automáticamente

### Comandos CI

```bash
# Comando usado en CI
pytest tests/ \
  --cov=app \
  --cov-branch \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v
```

## 📝 Escribir Tests

### Estructura de Test

```python
"""
Tests para [módulo]
"""
import pytest
from app.module import function_to_test


class TestModuleName:
    """Tests para ModuleName"""
    
    def test_function_success(self):
        """Test caso exitoso"""
        result = function_to_test("valid_input")
        assert result == "expected_output"
    
    def test_function_error(self):
        """Test caso de error"""
        with pytest.raises(ValueError):
            function_to_test("invalid_input")
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test función asíncrona"""
        result = await async_function()
        assert result is not None
```

### Best Practices

1. **Nombres Descriptivos**: `test_create_user_with_valid_email`
2. **Un Assert por Test**: Cada test debe verificar una cosa
3. **Arrange-Act-Assert**: Estructura clara
4. **Mocks para Dependencias**: No depender de servicios externos
5. **Datos de Prueba**: Usar fixtures para datos consistentes

## 🐛 Debugging Tests

### Ejecutar Test Específico

```bash
# Test específico
pytest tests/test_main.py::TestMainEndpoints::test_health_check -v

# Con debugging
pytest tests/test_main.py::test_function -v -s --pdb
```

### Ver Output Completo

```bash
# Mostrar prints y logs
pytest tests/ -v -s

# Mostrar warnings
pytest tests/ -v --disable-warnings
```

## 📈 Métricas de Calidad

### Coverage por Módulo

- `app/core/`: 95%+
- `app/api/`: 90%+
- `app/services/`: 90%+
- `app/models/`: 85%+
- `app/integrations/`: 80%+

### Performance

- Tests unitarios: < 100ms cada uno
- Tests de integración: < 1s cada uno
- Suite completa: < 30s

## 🔗 Enlaces Útiles

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Codecov Dashboard](https://codecov.io/gh/ZetahDev/conversaai)

---

**🤖 ConversaAI - Testing con calidad empresarial**
