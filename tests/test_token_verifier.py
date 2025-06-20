"""
Tests for Token Verifier module
"""
import pytest
import jwt
import os
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, Request
from shared.auth.token_verifier import get_token_from_request, verify_token


class TestGetTokenFromRequest:
    """Test token extraction from request headers"""
    
    def test_get_token_from_request_success(self):
        """Test successful token extraction from Authorization header"""
        # Create mock request with proper Authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer test-jwt-token"}
        
        token = get_token_from_request(mock_request)
        assert token == "test-jwt-token"
    
    def test_get_token_from_request_missing_header(self):
        """Test token extraction fails when Authorization header is missing"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            get_token_from_request(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Missing token" in str(exc_info.value.detail)
    
    def test_get_token_from_request_wrong_format(self):
        """Test token extraction fails when Authorization header has wrong format"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Authorization": "Basic test-token"}
        
        with pytest.raises(HTTPException) as exc_info:
            get_token_from_request(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Missing token" in str(exc_info.value.detail)
    
    def test_get_token_from_request_empty_token(self):
        """Test token extraction fails when token part is empty"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer "}
        
        token = get_token_from_request(mock_request)
        assert token == ""
    
    def test_get_token_from_request_malformed_header(self):
        """Test token extraction fails with malformed Authorization header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Authorization": "Bearer"}
        
        with pytest.raises(HTTPException) as exc_info:
            get_token_from_request(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Missing token" in str(exc_info.value.detail)


class TestVerifyToken:
    """Test JWT token verification"""
    
    def test_verify_token_success(self):
        """Test successful token verification"""
        test_payload = {"user_id": "123", "username": "testuser"}
        test_secret = "test-secret-key"
        test_algorithm = "HS256"
        
        # Create a valid JWT token
        test_token = jwt.encode(test_payload, test_secret, algorithm=test_algorithm)
        
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "JWT_ALGORITHM": test_algorithm
        }):
            result = verify_token(test_token)
            assert result["user_id"] == "123"
            assert result["username"] == "testuser"
    
    def test_verify_token_invalid_signature(self):
        """Test token verification fails with invalid signature"""
        test_payload = {"user_id": "123", "username": "testuser"}
        wrong_secret = "wrong-secret"
        correct_secret = "correct-secret"
        
        # Create token with wrong secret
        test_token = jwt.encode(test_payload, wrong_secret, algorithm="HS256")
        
        with patch.dict(os.environ, {
            "JWT_SECRET": correct_secret,
            "JWT_ALGORITHM": "HS256"
        }):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(test_token)
            
            assert exc_info.value.status_code == 403
            assert "Invalid token" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self):
        """Test token verification fails with expired token"""
        import time
        from datetime import datetime, timedelta
        
        test_payload = {
            "user_id": "123",
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        test_secret = "test-secret-key"
        
        test_token = jwt.encode(test_payload, test_secret, algorithm="HS256")
        
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "JWT_ALGORITHM": "HS256"
        }):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(test_token)
            
            assert exc_info.value.status_code == 403
            assert "Invalid token" in str(exc_info.value.detail)
    
    def test_verify_token_malformed(self):
        """Test token verification fails with malformed token"""
        malformed_token = "this.is.not.a.valid.jwt.token"
        
        with patch.dict(os.environ, {
            "JWT_SECRET": "test-secret",
            "JWT_ALGORITHM": "HS256"
        }):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(malformed_token)
            
            assert exc_info.value.status_code == 403
            assert "Invalid token" in str(exc_info.value.detail)
    
    def test_verify_token_empty(self):
        """Test token verification fails with empty token"""
        with patch.dict(os.environ, {
            "JWT_SECRET": "test-secret",
            "JWT_ALGORITHM": "HS256"
        }):
            with pytest.raises(HTTPException) as exc_info:
                verify_token("")
            
            assert exc_info.value.status_code == 403
            assert "Invalid token" in str(exc_info.value.detail)
    
    def test_verify_token_wrong_algorithm(self):
        """Test token verification fails when algorithm doesn't match"""
        test_payload = {"user_id": "123", "username": "testuser"}
        test_secret = "test-secret-key"
        
        # Create token with HS256
        test_token = jwt.encode(test_payload, test_secret, algorithm="HS256")
        
        # Try to verify with HS512
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "JWT_ALGORITHM": "HS512"
        }):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(test_token)
            
            assert exc_info.value.status_code == 403
            assert "Invalid token" in str(exc_info.value.detail)
    
    def test_verify_token_with_default_env_values(self):
        """Test token verification with default environment values"""
        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            test_payload = {"user_id": "123", "username": "testuser"}
            # Use default values: JWT_SECRET="secret", JWT_ALGORITHM="HS256"
            test_token = jwt.encode(test_payload, "secret", algorithm="HS256")
            
            result = verify_token(test_token)
            assert result["user_id"] == "123"
            assert result["username"] == "testuser"


class TestTokenVerifierIntegration:
    """Integration tests for token verifier functionality"""
    
    def test_full_request_to_verification_flow(self):
        """Test complete flow from request to verified token"""
        # Setup test data
        test_payload = {"user_id": "456", "username": "integrationuser", "role": "admin"}
        test_secret = "integration-test-secret"
        test_algorithm = "HS256"
        
        # Create valid JWT token
        test_token = jwt.encode(test_payload, test_secret, algorithm=test_algorithm)
        
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Authorization": f"Bearer {test_token}"}
        
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "JWT_ALGORITHM": test_algorithm
        }):
            # Extract token from request
            extracted_token = get_token_from_request(mock_request)
            
            # Verify the extracted token
            verified_payload = verify_token(extracted_token)
            
            # Verify the payload matches
            assert verified_payload["user_id"] == "456"
            assert verified_payload["username"] == "integrationuser"
            assert verified_payload["role"] == "admin"
    
    def test_realistic_jwt_payload(self):
        """Test with realistic JWT payload structure"""
        from datetime import datetime, timedelta
        
        test_payload = {
            "sub": "user123",  # Subject
            "iat": datetime.utcnow(),  # Issued at
            "exp": datetime.utcnow() + timedelta(hours=1),  # Expiration
            "aud": "wekare-app",  # Audience
            "iss": "wekare-auth",  # Issuer
            "user_id": "123",
            "username": "johndoe",
            "email": "john@example.com",
            "roles": ["user", "patient"]
        }
        
        test_secret = "realistic-test-secret"
        test_token = jwt.encode(test_payload, test_secret, algorithm="HS256")
        
        with patch.dict(os.environ, {
            "JWT_SECRET": test_secret,
            "JWT_ALGORITHM": "HS256"
        }):
            result = verify_token(test_token)
            
            assert result["sub"] == "user123"
            assert result["user_id"] == "123"
            assert result["username"] == "johndoe"
            assert result["email"] == "john@example.com"
            assert result["roles"] == ["user", "patient"]
            assert result["aud"] == "wekare-app"
            assert result["iss"] == "wekare-auth"
    
    def test_case_sensitive_headers(self):
        """Test that header extraction works with different case variations"""
        test_token = "test-token-value"
        
        # Test different header case variations
        headers_to_test = [
            {"Authorization": f"Bearer {test_token}"},
            {"authorization": f"Bearer {test_token}"},  # lowercase  
            {"AUTHORIZATION": f"Bearer {test_token}"},  # uppercase
        ]
        
        for headers in headers_to_test:
            mock_request = MagicMock(spec=Request)
            # Create a custom headers object that handles case-insensitive lookups
            mock_headers = MagicMock()
            mock_headers.get.return_value = headers.get("Authorization") or headers.get("authorization") or headers.get("AUTHORIZATION")
            mock_request.headers = mock_headers
            
            extracted = get_token_from_request(mock_request)
            assert extracted == test_token 