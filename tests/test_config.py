"""
Tests for Configuration module
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from shared.config.base_config import SharedInfrastructureConfig, get_shared_config


class TestSharedInfrastructureConfig:
    """Test the SharedInfrastructureConfig class"""
    
    def test_config_initialization_with_defaults(self):
        """Test configuration initialization with default values"""
        # Clear environment to test defaults
        with patch.dict(os.environ, {}, clear=True):
            config = SharedInfrastructureConfig()
            
            # Test default values
            assert config.database_url == "postgresql+asyncpg://postgres:getgoing@localhost:5433/wekare_test"
            assert config.sync_database_url == "postgresql://postgres:getgoing@localhost:5433/wekare_test"
            assert config.aws_region == "us-east-2"
            assert config.aws_account_id == "613778970767"
            assert config.jwt_secret == "dev_jwt_secret_key_change_in_production"
            assert config.jwt_algorithm == "HS256"
            assert config.jwt_expire_minutes == 30
            assert config.master_api_key == "wekare-dev-2024"
            assert config.environment == "development"
            assert config.debug is True
            assert config.log_level == "INFO"
    
    def test_config_from_environment_variables(self):
        """Test configuration loading from environment variables"""
        test_env = {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@prod-db:5432/prod_db",
            "AWS_REGION": "us-west-2", 
            "AWS_ACCOUNT_ID": "123456789012",
            "JWT_SECRET": "production-secret-key",
            "JWT_ALGORITHM": "HS512",
            "JWT_EXPIRE_MINUTES": "60",
            "MASTER_API_KEY": "prod-master-key-2024",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "ERROR"
        }
        
        with patch.dict(os.environ, test_env):
            config = SharedInfrastructureConfig()
            
            assert config.database_url == "postgresql+asyncpg://user:pass@prod-db:5432/prod_db"
            assert config.aws_region == "us-west-2"
            assert config.aws_account_id == "123456789012"
            assert config.jwt_secret == "production-secret-key"
            assert config.jwt_algorithm == "HS512"
            assert config.jwt_expire_minutes == 60
            assert config.master_api_key == "prod-master-key-2024"
            assert config.environment == "production"
            assert config.debug is False
            assert config.log_level == "ERROR"
    
    @patch('pathlib.Path.exists')
    @patch('shared.config.base_config.load_dotenv')
    def test_env_file_loading(self, mock_load_dotenv, mock_exists):
        """Test that legacy .env files are loaded when explicitly requested"""
        # Mock that both env files exist
        mock_exists.return_value = True
        
        # Test that regular config doesn't load legacy files by default
        config = SharedInfrastructureConfig()
        assert mock_load_dotenv.call_count == 0
        
        # Test that legacy config loader works
        legacy_config = SharedInfrastructureConfig.with_legacy_files()
        
        # Verify load_dotenv was called for both files
        assert mock_load_dotenv.call_count == 2
        
        # Check the paths that were attempted to be loaded
        call_args = [call[0][0] for call in mock_load_dotenv.call_args_list]
        
        # Should contain paths ending with .env.shared.local and .env.shared.aws
        local_env_found = any(str(path).endswith('.env.shared.local') for path in call_args)
        aws_env_found = any(str(path).endswith('.env.shared.aws') for path in call_args)
        
        assert local_env_found, "Should attempt to load .env.shared.local"
        assert aws_env_found, "Should attempt to load .env.shared.aws"
    
    @patch('pathlib.Path.exists')
    @patch('shared.config.base_config.load_dotenv')
    def test_env_file_not_exists(self, mock_load_dotenv, mock_exists):
        """Test behavior when .env files don't exist"""
        # Mock that env files don't exist
        mock_exists.return_value = False
        
        config = SharedInfrastructureConfig()
        
        # load_dotenv should not be called if files don't exist
        mock_load_dotenv.assert_not_called()
    
    def test_is_development_property(self):
        """Test is_development property"""
        test_cases = [
            ("development", True),
            ("dev", True),
            ("local", True),
            ("DEVELOPMENT", True),  # Case insensitive
            ("production", False),
            ("staging", False),
            ("test", False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"ENVIRONMENT": env_value}):
                config = SharedInfrastructureConfig()
                assert config.is_development == expected, f"Failed for environment: {env_value}"
    
    def test_is_production_property(self):
        """Test is_production property"""
        test_cases = [
            ("production", True),
            ("prod", True),
            ("PRODUCTION", True),  # Case insensitive
            ("development", False),
            ("staging", False),
            ("test", False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"ENVIRONMENT": env_value}):
                config = SharedInfrastructureConfig()
                assert config.is_production == expected, f"Failed for environment: {env_value}"
    
    def test_is_aws_environment_property(self):
        """Test is_aws_environment property"""
        # Test with no AWS indicators
        with patch.dict(os.environ, {}, clear=True):
            config = SharedInfrastructureConfig()
            assert config.is_aws_environment is False
        
        # Test with cloudwatch log group
        with patch.dict(os.environ, {"AWS_CLOUDWATCH_LOG_GROUP": "/aws/ecs/wekare"}):
            config = SharedInfrastructureConfig()
            assert config.is_aws_environment is True
        
        # Test with load balancer URL
        with patch.dict(os.environ, {"AWS_LOAD_BALANCER_URL": "https://wekare-alb.us-east-2.elb.amazonaws.com"}):
            config = SharedInfrastructureConfig()
            assert config.is_aws_environment is True
        
        # Test with both
        with patch.dict(os.environ, {
            "AWS_CLOUDWATCH_LOG_GROUP": "/aws/ecs/wekare",
            "AWS_LOAD_BALANCER_URL": "https://wekare-alb.us-east-2.elb.amazonaws.com"
        }):
            config = SharedInfrastructureConfig()
            assert config.is_aws_environment is True
    
    def test_get_database_url_method(self):
        """Test get_database_url method"""
        test_db_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        
        with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
            config = SharedInfrastructureConfig()
            
            # Should return the same URL regardless of service name
            assert config.get_database_url() == test_db_url
            assert config.get_database_url("profiles") == test_db_url
            assert config.get_database_url("referrals") == test_db_url
    
    def test_to_dict_method(self):
        """Test to_dict method returns expected structure"""
        test_env = {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
            "SYNC_DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "AWS_REGION": "us-west-1",
            "AWS_ACCOUNT_ID": "999999999999",
            "JWT_SECRET": "test-secret",
            "JWT_ALGORITHM": "HS384",
            "MASTER_API_KEY": "test-master",
            "ENVIRONMENT": "test",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }
        
        with patch.dict(os.environ, test_env):
            config = SharedInfrastructureConfig()
            config_dict = config.to_dict()
            
            expected_keys = [
                "database_url", "sync_database_url", "aws_region", "aws_account_id",
                "jwt_secret", "jwt_algorithm", "master_api_key", "environment", 
                "debug", "log_level"
            ]
            
            for key in expected_keys:
                assert key in config_dict, f"Missing key: {key}"
            
            assert config_dict["database_url"] == test_env["DATABASE_URL"]
            assert config_dict["aws_region"] == test_env["AWS_REGION"]
            assert config_dict["jwt_secret"] == test_env["JWT_SECRET"]
            assert config_dict["environment"] == test_env["ENVIRONMENT"]
    
    def test_config_extra_fields_allowed(self):
        """Test that extra fields are allowed in configuration"""
        test_env = {
            "CUSTOM_FIELD": "custom_value",
            "SERVICE_SPECIFIC_SETTING": "service_value"
        }
        
        with patch.dict(os.environ, test_env):
            # Should not raise validation error with extra fields
            # This just tests that no exception is raised during initialization
            config = SharedInfrastructureConfig()
            
            # If we get here without exception, the test passes
            assert config is not None
    
    def test_database_connection_settings(self):
        """Test database connection specific settings"""
        test_env = {
            "DB_ECHO": "true",
            "DB_POOL_SIZE": "20",
            "DB_MAX_OVERFLOW": "30"
        }
        
        with patch.dict(os.environ, test_env):
            config = SharedInfrastructureConfig()
            
            assert config.db_echo is True
            assert config.db_pool_size == 20
            assert config.db_max_overflow == 30


class TestGetSharedConfig:
    """Test the get_shared_config function"""
    
    def test_get_shared_config_returns_instance(self):
        """Test that get_shared_config returns a SharedInfrastructureConfig instance"""
        config = get_shared_config()
        assert isinstance(config, SharedInfrastructureConfig)
    
    def test_get_shared_config_singleton_behavior(self):
        """Test that get_shared_config returns the same instance (singleton pattern)"""
        config1 = get_shared_config()
        config2 = get_shared_config()
        
        # Should be the same instance
        assert config1 is config2
    
    def test_shared_config_module_variable(self):
        """Test that the module-level shared_config variable works"""
        from shared.config.base_config import shared_config, reset_global_config
        
        assert isinstance(shared_config, SharedInfrastructureConfig)
        
        # Reset global config to ensure clean state
        reset_global_config()
        
        # After reset, get_shared_config() creates a new instance
        global_config = get_shared_config()
        assert isinstance(global_config, SharedInfrastructureConfig)
        
        # The module-level shared_config is a separate instance for backward compatibility
        assert shared_config is not global_config


class TestConfigurationIntegration:
    """Integration tests for configuration functionality"""
    
    def test_realistic_development_config(self):
        """Test realistic development configuration"""
        dev_env = {
            "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/wekare_dev",
            "SYNC_DATABASE_URL": "postgresql://postgres:password@localhost:5432/wekare_dev",
            "ENVIRONMENT": "development",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "JWT_SECRET": "dev-secret-do-not-use-in-production",
            "MASTER_API_KEY": "dev-master-key-2024"
        }
        
        with patch.dict(os.environ, dev_env):
            config = SharedInfrastructureConfig()
            
            assert config.is_development is True
            assert config.is_production is False
            assert config.is_aws_environment is False
            assert config.debug is True
            assert config.log_level == "DEBUG"
    
    def test_realistic_production_config(self):
        """Test realistic production configuration"""
        prod_env = {
            "DATABASE_URL": "postgresql+asyncpg://wekare_user:secure_password@prod-db.amazonaws.com:5432/wekare_prod",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "JWT_SECRET": "super-secure-production-secret-key",
            "MASTER_API_KEY": "prod-master-key-2024-secure",
            "AWS_REGION": "us-east-1",
            "AWS_ACCOUNT_ID": "613778970767",
            "AWS_CLOUDWATCH_LOG_GROUP": "/aws/ecs/wekare-prod",
            "AWS_LOAD_BALANCER_URL": "https://wekare-prod-alb.us-east-1.elb.amazonaws.com"
        }
        
        with patch.dict(os.environ, prod_env):
            config = SharedInfrastructureConfig()
            
            assert config.is_development is False
            assert config.is_production is True
            assert config.is_aws_environment is True
            assert config.debug is False
            assert config.log_level == "INFO"
            assert config.aws_region == "us-east-1"
    
    def test_config_with_missing_optional_fields(self):
        """Test configuration with only required fields"""
        minimal_env = {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test"
        }
        
        with patch.dict(os.environ, minimal_env, clear=True):
            # Should not raise error with minimal configuration
            config = SharedInfrastructureConfig()
            
            # Should have defaults for optional fields
            assert config.environment == "development"
            assert config.debug is True
            assert config.jwt_algorithm == "HS256" 