"""
Test Cognito Authentication for Local Development and Integration Testing
This module provides a test implementation of Cognito authentication that uses
a known test user for development and testing purposes.
"""
from typing import Optional
from fastapi import HTTPException, Header
from pydantic import BaseModel

class CognitoUser(BaseModel):
    """Test Cognito User model"""
    user_id: str
    username: str
    email: str
    organization_id: str
    attributes: dict = {}

# Test user matching our seeded data
TEST_COGNITO_USER = CognitoUser(
    user_id="test-user-cognito-123456",
    username="test-user@wekare.com",
    email="test-user@wekare.com",
    organization_id="550e8400-e29b-41d4-a716-446655440001",
    attributes={
        "given_name": "Test",
        "family_name": "User",
        "phone_number": "+1-555-123-4567"
    }
)

async def get_current_user(
    x_api_key: str = Header(..., description="API Key for authentication")
) -> CognitoUser:
    """
    Test implementation of get_current_user that returns our test user
    when the correct API key is provided.
    
    For testing purposes, this bypasses actual Cognito authentication
    and returns a known test user.
    """
    # Verify API key
    if x_api_key != "wekare-team-2024-profiles-api":
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid API Key",
                "message": "Please use the correct team API key",
                "required_header": "X-API-Key: wekare-team-2024-profiles-api"
            }
        )
    
    # Return test user for integration testing
    return TEST_COGNITO_USER

def get_test_user() -> CognitoUser:
    """Get the test user for seeding and testing purposes"""
    return TEST_COGNITO_USER 