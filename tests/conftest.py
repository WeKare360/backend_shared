"""
Pytest configuration and fixtures for shared package tests
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_async_session():
    """Create a mock AsyncSession for database testing"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def clean_environment():
    """Provide a clean environment for testing configuration"""
    original_env = os.environ.copy()
    # Clear all environment variables
    os.environ.clear()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_environment():
    """Provide test environment variables"""
    test_env = {
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
        "JWT_SECRET": "test-jwt-secret-key",
        "JWT_ALGORITHM": "HS256",
        "MASTER_API_KEY": "test-master-key",
        "PROFILES_API_KEY": "test-profiles-key",
        "REFERRALS_API_KEY": "test-referrals-key",
        "INSURANCE_API_KEY": "test-insurance-key",
        "NOTIFICATIONS_API_KEY": "test-notifications-key",
        "ENVIRONMENT": "test",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO"
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
def mock_database_connection():
    """Create a mock database connection"""
    mock_conn = MagicMock()
    mock_conn.engine = AsyncMock()
    mock_conn.session_factory = MagicMock()
    mock_conn.database_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    
    # Mock connection methods
    mock_conn.connect = AsyncMock()
    mock_conn.disconnect = AsyncMock()
    mock_conn.get_session = AsyncMock()
    mock_conn.check_connection = AsyncMock(return_value=True)
    mock_conn.execute_raw_query = AsyncMock()
    
    return mock_conn


@pytest.fixture
def sample_jwt_payload():
    """Provide a sample JWT payload for testing"""
    from datetime import datetime, timedelta
    
    return {
        "sub": "user123",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "aud": "wekare-app",
        "iss": "wekare-auth",
        "user_id": "123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"]
    }


@pytest.fixture
def mock_model_instance():
    """Create a mock model instance for repository testing"""
    from uuid import uuid4
    from datetime import datetime
    
    mock_instance = MagicMock()
    mock_instance.id = uuid4()
    mock_instance.created_at = datetime.utcnow()
    mock_instance.updated_at = datetime.utcnow()
    mock_instance.name = "Test Item"
    mock_instance.description = "Test Description"
    
    return mock_instance


# Async fixtures for database testing
@pytest.fixture
async def async_mock_session():
    """Create an async mock session"""
    session = AsyncMock(spec=AsyncSession)
    
    # Setup common mock behavior
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    
    return session


# Configuration for pytest-asyncio
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# Test data fixtures
@pytest.fixture
def sample_api_keys():
    """Sample API keys for testing"""
    return {
        "profiles": "test-profiles-api-key-2024",
        "referrals": "test-referrals-api-key-2024", 
        "insurance": "test-insurance-api-key-2024",
        "notifications": "test-notifications-api-key-2024",
        "master": "test-master-api-key-2024"
    }


@pytest.fixture
def sample_database_config():
    """Sample database configuration for testing"""
    return {
        "database_url": "postgresql+asyncpg://test:test@localhost:5432/test_db",
        "sync_database_url": "postgresql://test:test@localhost:5432/test_db",
        "db_echo": False,
        "db_pool_size": 5,
        "db_max_overflow": 10
    }


@pytest.fixture
def sample_aws_config():
    """Sample AWS configuration for testing"""
    return {
        "aws_region": "us-east-2",
        "aws_account_id": "123456789012",
        "aws_cloudwatch_log_group": "/aws/ecs/test-app",
        "aws_load_balancer_url": "https://test-alb.us-east-2.elb.amazonaws.com"
    } 