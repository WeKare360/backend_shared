"""
Test Configuration for WeKare Services
Handles test mode settings and mock authentication
"""

import os
from typing import Optional, Dict, Any
from uuid import UUID

# Test Environment Settings
TEST_MODE = os.getenv("WEKARE_TEST_MODE", "false").lower() == "true"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:getgoing@localhost:5433/wekare_test")

# Test Organization and Users
TEST_ORG_ID = UUID("12345678-1234-5678-9abc-123456789012")
TEST_USER_IDS = {
    "admin": UUID("11111111-1111-1111-1111-111111111111"),
    "provider": UUID("22222222-2222-2222-2222-222222222222"),
    "patient": UUID("33333333-3333-3333-3333-333333333333")
}

# Test API Keys (for testing purposes)
TEST_API_KEYS = {
    "admin": "test-api-key-admin-123456789",
    "provider": "test-api-key-provider-123456789", 
    "patient": "test-api-key-patient-123456789",
    "default": "test-api-key-default-123456789"
}

class TestUser:
    """Mock user for testing"""
    def __init__(self, user_type: str = "admin"):
        self.id = TEST_USER_IDS.get(user_type, TEST_USER_IDS["admin"])
        self.organization_id = TEST_ORG_ID
        self.cognito_user_id = f"test-cognito-{user_type}-123"
        self.cognito_username = f"{user_type}@wekaretest.com"
        self.role = user_type
        self.is_active = True
        self.email_verified = True

def get_test_user(user_type: str = "admin") -> TestUser:
    """Get a test user"""
    return TestUser(user_type)

def get_test_api_key(user_type: str = "default") -> str:
    """Get a test API key"""
    return TEST_API_KEYS.get(user_type, TEST_API_KEYS["default"])

def is_test_mode() -> bool:
    """Check if we're in test mode"""
    return TEST_MODE

def get_test_database_url() -> str:
    """Get test database URL"""
    return TEST_DATABASE_URL

def mock_auth_dependency():
    """Mock authentication dependency for testing"""
    if TEST_MODE:
        return get_test_user("admin")
    else:
        raise Exception("Mock auth should only be used in test mode")

# Test Configuration
TEST_CONFIG = {
    "database_url": TEST_DATABASE_URL,
    "test_mode": TEST_MODE,
    "organization_id": str(TEST_ORG_ID),
    "api_keys": TEST_API_KEYS,
    "users": {k: str(v) for k, v in TEST_USER_IDS.items()}
} 