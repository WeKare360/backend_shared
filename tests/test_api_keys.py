"""
Tests for API Keys module
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from shared.auth.api_keys import (
    APIKeyManager, 
    verify, 
    verify_profiles_api_key,
    verify_referrals_api_key,
    verify_notifications_api_key,
    verify_insurance_api_key,
    verify_master_api_key
)


class TestAPIKeyManager:
    """Test the APIKeyManager class"""
    
    def test_get_service_api_key_defaults(self):
        """Test getting service API keys with default values"""
        # Test default values without environment variables
        with patch.dict(os.environ, {}, clear=True):
            assert APIKeyManager.get_service_api_key("profiles") == "wekare-team-2024-profiles-api"
            assert APIKeyManager.get_service_api_key("referrals") == "wekare-team-2024-referrals-api"
            assert APIKeyManager.get_service_api_key("notifications") == "wekare-team-2024-notifications-api"
            assert APIKeyManager.get_service_api_key("insurance") == "wekare-team-2024-insurance-api"
            assert APIKeyManager.get_service_api_key("master") == "wekare-dev-2024"
            assert APIKeyManager.get_service_api_key("unknown") == ""
    
    def test_get_service_api_key_from_env(self):
        """Test getting service API keys from environment variables"""
        test_env = {
            "PROFILES_API_KEY": "test-profiles-key",
            "REFERRALS_API_KEY": "test-referrals-key", 
            "NOTIFICATIONS_API_KEY": "test-notifications-key",
            "INSURANCE_API_KEY": "test-insurance-key",
            "MASTER_API_KEY": "test-master-key"
        }
        
        with patch.dict(os.environ, test_env):
            assert APIKeyManager.get_service_api_key("profiles") == "test-profiles-key"
            assert APIKeyManager.get_service_api_key("referrals") == "test-referrals-key"
            assert APIKeyManager.get_service_api_key("notifications") == "test-notifications-key"
            assert APIKeyManager.get_service_api_key("insurance") == "test-insurance-key"
            assert APIKeyManager.get_service_api_key("master") == "test-master-key"
    
    def test_verify_service_api_key_with_correct_key(self):
        """Test API key verification with correct service key"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            assert APIKeyManager.verify_service_api_key("profiles", "test-profiles-key") is True
    
    def test_verify_service_api_key_with_master_key(self):
        """Test API key verification with master key"""
        test_env = {
            "PROFILES_API_KEY": "test-profiles-key",
            "MASTER_API_KEY": "test-master-key"
        }
        
        with patch.dict(os.environ, test_env):
            # Master key should work for any service
            assert APIKeyManager.verify_service_api_key("profiles", "test-master-key") is True
    
    def test_verify_service_api_key_with_wrong_key(self):
        """Test API key verification with wrong key"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            assert APIKeyManager.verify_service_api_key("profiles", "wrong-key") is False
    
    def test_verify_service_api_key_with_wrong_service_key(self):
        """Test API key verification with key from different service"""
        test_env = {
            "PROFILES_API_KEY": "test-profiles-key",
            "REFERRALS_API_KEY": "test-referrals-key"
        }
        
        with patch.dict(os.environ, test_env):
            # Referrals key should not work for profiles service
            assert APIKeyManager.verify_service_api_key("profiles", "test-referrals-key") is False
    
    def test_create_api_key_dependency_success(self):
        """Test creating FastAPI dependency that passes validation"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            dependency = APIKeyManager.create_api_key_dependency("profiles")
            # Should not raise exception
            result = dependency("test-profiles-key")
            assert result is True
    
    def test_create_api_key_dependency_failure(self):
        """Test creating FastAPI dependency that fails validation"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            dependency = APIKeyManager.create_api_key_dependency("profiles")
            
            with pytest.raises(HTTPException) as exc_info:
                dependency("wrong-key")
            
            assert exc_info.value.status_code == 401
            assert "Invalid API Key" in str(exc_info.value.detail)
            assert "profiles" in str(exc_info.value.detail)


class TestVerifyFunction:
    """Test the general verify function"""
    
    def test_verify_with_master_key(self):
        """Test verify function with master key"""
        test_env = {"MASTER_API_KEY": "test-master-key"}
        
        with patch.dict(os.environ, test_env):
            assert verify("test-master-key") is True
            assert verify("test-master-key", "master") is True
    
    def test_verify_with_wrong_key(self):
        """Test verify function with wrong key"""
        test_env = {"MASTER_API_KEY": "test-master-key"}
        
        with patch.dict(os.environ, test_env):
            assert verify("wrong-key") is False
            assert verify("wrong-key", "master") is False
    
    def test_verify_with_service_key(self):
        """Test verify function with service-specific key"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            assert verify("test-profiles-key", "profiles") is True
            assert verify("wrong-key", "profiles") is False


class TestServiceDependencies:
    """Test the pre-created service dependencies"""
    
    def test_verify_profiles_api_key_success(self):
        """Test profiles API key dependency success"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            result = verify_profiles_api_key("test-profiles-key")
            assert result is True
    
    def test_verify_profiles_api_key_failure(self):
        """Test profiles API key dependency failure"""
        test_env = {"PROFILES_API_KEY": "test-profiles-key"}
        
        with patch.dict(os.environ, test_env):
            with pytest.raises(HTTPException) as exc_info:
                verify_profiles_api_key("wrong-key")
            
            assert exc_info.value.status_code == 401
            assert "profiles" in str(exc_info.value.detail)
    
    def test_verify_referrals_api_key_success(self):
        """Test referrals API key dependency success"""
        test_env = {"REFERRALS_API_KEY": "test-referrals-key"}
        
        with patch.dict(os.environ, test_env):
            result = verify_referrals_api_key("test-referrals-key")
            assert result is True
    
    def test_verify_notifications_api_key_success(self):
        """Test notifications API key dependency success"""
        test_env = {"NOTIFICATIONS_API_KEY": "test-notifications-key"}
        
        with patch.dict(os.environ, test_env):
            result = verify_notifications_api_key("test-notifications-key")
            assert result is True
    
    def test_verify_insurance_api_key_success(self):
        """Test insurance API key dependency success"""
        test_env = {"INSURANCE_API_KEY": "test-insurance-key"}
        
        with patch.dict(os.environ, test_env):
            result = verify_insurance_api_key("test-insurance-key")
            assert result is True
    
    def test_verify_master_api_key_success(self):
        """Test master API key dependency success"""
        test_env = {"MASTER_API_KEY": "test-master-key"}
        
        with patch.dict(os.environ, test_env):
            result = verify_master_api_key("test-master-key")
            assert result is True
    
    def test_all_dependencies_accept_master_key(self):
        """Test that all service dependencies accept master key"""
        test_env = {"MASTER_API_KEY": "test-master-key"}
        
        with patch.dict(os.environ, test_env):
            # All services should accept master key
            assert verify_profiles_api_key("test-master-key") is True
            assert verify_referrals_api_key("test-master-key") is True
            assert verify_notifications_api_key("test-master-key") is True
            assert verify_insurance_api_key("test-master-key") is True
            assert verify_master_api_key("test-master-key") is True


class TestAPIKeyIntegration:
    """Integration tests for API key functionality"""
    
    def test_realistic_scenario_with_multiple_services(self):
        """Test realistic scenario with multiple services and keys"""
        test_env = {
            "PROFILES_API_KEY": "prod-profiles-2024-key", 
            "REFERRALS_API_KEY": "prod-referrals-2024-key",
            "INSURANCE_API_KEY": "prod-insurance-2024-key",
            "NOTIFICATIONS_API_KEY": "prod-notifications-2024-key",
            "MASTER_API_KEY": "prod-master-2024-key"
        }
        
        with patch.dict(os.environ, test_env):
            # Test service-specific keys work only for their service
            assert APIKeyManager.verify_service_api_key("profiles", "prod-profiles-2024-key") is True
            assert APIKeyManager.verify_service_api_key("profiles", "prod-referrals-2024-key") is False
            
            # Test master key works for all services
            assert APIKeyManager.verify_service_api_key("profiles", "prod-master-2024-key") is True
            assert APIKeyManager.verify_service_api_key("referrals", "prod-master-2024-key") is True
            assert APIKeyManager.verify_service_api_key("insurance", "prod-master-2024-key") is True
            assert APIKeyManager.verify_service_api_key("notifications", "prod-master-2024-key") is True
    
    def test_error_detail_format(self):
        """Test that error details have expected format"""
        test_env = {"PROFILES_API_KEY": "test-key"}
        
        with patch.dict(os.environ, test_env):
            dependency = APIKeyManager.create_api_key_dependency("profiles")
            
            with pytest.raises(HTTPException) as exc_info:
                dependency("wrong-key")
            
            error_detail = exc_info.value.detail
            assert isinstance(error_detail, dict)
            assert "error" in error_detail
            assert "message" in error_detail
            assert "service" in error_detail
            assert "expected_header" in error_detail
            assert "valid_keys" in error_detail
            assert error_detail["service"] == "profiles"
            assert error_detail["expected_header"] == "X-API-Key" 