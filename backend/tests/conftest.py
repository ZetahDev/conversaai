"""
Configuración de pytest para los tests
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import security_manager
from app.models.user import User, UserRole, UserStatus
from app.models.company import Company, CompanyStatus, CompanyType

# Base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_company(db_session):
    """Create a test company."""
    company = Company(
        id="test-company-1",
        name="Test Company",
        slug="test-company",
        email="test@company.com",
        status=CompanyStatus.ACTIVE,
        company_type=CompanyType.STARTUP
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company

@pytest.fixture
def test_user(db_session, test_company):
    """Create a test user."""
    user = User(
        id="test-user-1",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash=security_manager.get_password_hash("TestPassword123!"),
        role=UserRole.COMPANY_ADMIN,
        status=UserStatus.ACTIVE,
        company_id=test_company.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_superadmin(db_session, test_company):
    """Create a test superadmin user."""
    user = User(
        id="test-superadmin-1",
        email="admin@example.com",
        first_name="Super",
        last_name="Admin",
        password_hash=security_manager.get_password_hash("SuperAdmin123!"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        company_id=test_company.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    access_token = security_manager.create_access_token(
        data={"sub": test_user.id, "email": test_user.email, "role": test_user.role.value}
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def superadmin_headers(test_superadmin):
    """Create authentication headers for superadmin user."""
    access_token = security_manager.create_access_token(
        data={"sub": test_superadmin.id, "email": test_superadmin.email, "role": test_superadmin.role.value}
    )
    return {"Authorization": f"Bearer {access_token}"}

# Datos de prueba comunes
@pytest.fixture
def sample_chatbot_data():
    """Sample chatbot data for testing."""
    return {
        "name": "Test Chatbot",
        "description": "A test chatbot",
        "greeting_message": "Hello! How can I help you?",
        "fallback_message": "I don't understand. Can you rephrase?",
        "personality": "helpful",
        "primary_ai_provider": "gemini_flash_lite"
    }

@pytest.fixture
def sample_integration_data():
    """Sample integration data for testing."""
    return {
        "name": "Test WhatsApp Integration",
        "integration_type": "whatsapp",
        "config": {
            "phone_number_id": "123456789",
            "access_token": "test_token"
        }
    }

@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing."""
    return {
        "title": "Test Notification",
        "message": "This is a test notification",
        "type": "info",
        "priority": "medium"
    }
