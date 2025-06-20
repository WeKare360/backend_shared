import os
from typing import Optional
from fastapi import HTTPException, Header
from functools import wraps

class APIKeyManager:
    """Centralized API key management"""
    
    @staticmethod
    def get_service_api_key(service_name: str) -> str:
        """Get API key for specific service from environment"""
        key_map = {
            "profiles": os.getenv("PROFILES_API_KEY", "wekare-team-2024-profiles-api"),
            "referrals": os.getenv("REFERRALS_API_KEY", "wekare-team-2024-referrals-api"),
            "notifications": os.getenv("NOTIFICATIONS_API_KEY", "wekare-team-2024-notifications-api"),
            "insurance": os.getenv("INSURANCE_API_KEY", "wekare-team-2024-insurance-api"),
            "master": os.getenv("MASTER_API_KEY", "wekare-dev-2024")
        }
        return key_map.get(service_name, "")
    
    @staticmethod
    def verify_service_api_key(service_name: str, provided_key: str) -> bool:
        """Verify API key for specific service"""
        expected_key = APIKeyManager.get_service_api_key(service_name)
        master_key = APIKeyManager.get_service_api_key("master")
        
        # Allow both service-specific key and master key
        return provided_key in [expected_key, master_key]
    
    @staticmethod
    def create_api_key_dependency(service_name: str):
        """Create FastAPI dependency for API key verification"""
        def verify_api_key(x_api_key: str = Header(..., description=f"API Key for {service_name} service")):
            if not APIKeyManager.verify_service_api_key(service_name, x_api_key):
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "Invalid API Key",
                        "message": f"Please use the correct API key for {service_name} service",
                        "service": service_name,
                        "expected_header": "X-API-Key",
                        "valid_keys": [
                            APIKeyManager.get_service_api_key(service_name),
                            "master_key_also_accepted"
                        ]
                    }
                )
            return True
        return verify_api_key

# General verify function for backward compatibility
def verify(api_key: str, service_name: str = "master") -> bool:
    """General API key verification function"""
    return APIKeyManager.verify_service_api_key(service_name, api_key)

# Service-specific dependencies
verify_profiles_api_key = APIKeyManager.create_api_key_dependency("profiles")
verify_referrals_api_key = APIKeyManager.create_api_key_dependency("referrals")
verify_notifications_api_key = APIKeyManager.create_api_key_dependency("notifications")
verify_insurance_api_key = APIKeyManager.create_api_key_dependency("insurance")
verify_master_api_key = APIKeyManager.create_api_key_dependency("master")