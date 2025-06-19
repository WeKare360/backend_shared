from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import List, Optional
from uuid import UUID
import hashlib
import os
from pydantic import BaseModel

security = HTTPBearer()

class CognitoUser(BaseModel):
    """Cognito User model"""
    user_id: str
    username: str
    email: str
    organization_id: str
    attributes: dict = {}

# Test user for development/testing
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

def is_test_mode() -> bool:
    """Check if we're running in test mode"""
    return os.getenv("WEKARE_TEST_MODE", "false").lower() == "true"

def user_pool_id_to_uuid(user_pool_id: str) -> UUID:
    """
    Convert user pool ID to deterministic UUID
    
    This creates a consistent UUID from the user pool ID that will always
    be the same for the same user pool, ensuring data consistency.
    
    Args:
        user_pool_id: Cognito User Pool ID (e.g., 'us-east-1_ABC123DEF')
        
    Returns:
        UUID object generated from the user pool ID
    """
    # Create a deterministic UUID from user pool ID using MD5 hash
    hash_object = hashlib.md5(user_pool_id.encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    
    # Format as UUID (insert hyphens in standard UUID positions)
    uuid_string = f"{hex_dig[:8]}-{hex_dig[8:12]}-{hex_dig[12:16]}-{hex_dig[16:20]}-{hex_dig[20:32]}"
    
    return UUID(uuid_string)

async def get_current_user(
    x_api_key: str = Header(..., description="API Key for authentication")
) -> CognitoUser:
    """
    Get current user - returns test user in test mode, otherwise would validate with Cognito
    """
    # Verify API key first
    if x_api_key != "wekare-team-2024-profiles-api":
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid API Key",
                "message": "Please use the correct team API key",
                "required_header": "X-API-Key: wekare-team-2024-profiles-api"
            }
        )
    
    # In test mode, return test user
    if is_test_mode():
        return TEST_COGNITO_USER
    
    # In production, this would validate JWT token with Cognito
    # For now, return test user for development
    return TEST_COGNITO_USER

def get_test_user() -> CognitoUser:
    """Get the test user for seeding and testing purposes"""
    return TEST_COGNITO_USER

# Optional: Helper function to get organization UUID directly
def get_organization_uuid_from_user_pool(user_pool_id: str) -> str:
    """
    Helper function to get organization UUID from user pool ID
    
    Args:
        user_pool_id: Cognito User Pool ID
        
    Returns:
        Organization UUID as string
    """
    return str(user_pool_id_to_uuid(user_pool_id))

# Optional: Validation function for organization access
def validate_organization_access(current_user: CognitoUser, required_org_id: str) -> bool:
    """
    Validate that the current user has access to the specified organization
    
    Args:
        current_user: CognitoUser object
        required_org_id: Organization ID to validate access for
        
    Returns:
        True if user has access, False otherwise
    """
    return current_user.organization_id == required_org_id