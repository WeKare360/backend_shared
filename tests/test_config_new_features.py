"""
Tests for new configuration features
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from shared.config.base_config import (
    SharedInfrastructureConfig,
    ConfigurationBuilder,
    create_development_config,
    create_testing_config,
    create_production_config,
    set_global_config,
    get_shared_config,
    reset_global_config
)


class TestNewConfigurationFeatures:
    """Test the new configuration features"""
    
    def test_factory_method_for_development(self):
        """Test development factory method"""
        config = SharedInfrastructureConfig.for_development(
            s3_bucket="dev-bucket",
            s3_endpoint_url="http://localhost:9000"
        )
        
        assert config.environment == "development"
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.aws_s3_bucket_name == "dev-bucket"
        assert config.aws_s3_endpoint_url == "http://localhost:9000"
        assert config.aws_s3_use_ssl is False
        assert config.aws_s3_region == "us-east-1"
    
    def test_factory_method_for_testing(self):
        """Test testing factory method"""
        config = SharedInfrastructureConfig.for_testing(test_s3_bucket="test-bucket")
        
        assert config.environment == "testing"
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.aws_s3_bucket_name == "test-bucket"
        assert config.aws_s3_endpoint_url == "http://localhost:9000"
        assert config.aws_s3_use_ssl is False
        assert config.jwt_secret == "test-jwt-secret"
        assert config.master_api_key == "test-master-key"
    
    def test_factory_method_for_production(self):
        """Test production factory method"""
        config = SharedInfrastructureConfig.for_production(
            required_s3_bucket="prod-bucket",
            required_s3_region="us-west-2"
        )
        
        assert config.environment == "production"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.aws_s3_bucket_name == "prod-bucket"
        assert config.aws_s3_region == "us-west-2"
        assert config.aws_s3_use_ssl is True
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        dev_config = create_development_config("dev-bucket")
        test_config = create_testing_config("test-bucket")
        prod_config = create_production_config("prod-bucket", "us-east-1")
        
        assert dev_config.aws_s3_bucket_name == "dev-bucket"
        assert test_config.aws_s3_bucket_name == "test-bucket"
        assert prod_config.aws_s3_bucket_name == "prod-bucket"
        assert prod_config.aws_s3_region == "us-east-1"
    
    def test_configuration_builder_pattern(self):
        """Test configuration builder pattern"""
        config = (ConfigurationBuilder()
                 .for_environment("development")
                 .with_s3("builder-bucket", region="us-west-2", endpoint="http://localhost:9000")
                 .with_database("postgresql://localhost:5432/test")
                 .with_aws_region("us-west-2")
                 .with_jwt_config("builder-secret", "HS384")
                 .with_custom_params(custom_field="custom_value")
                 .build())
        
        assert config.environment == "development"
        assert config.debug is True
        assert config.aws_s3_bucket_name == "builder-bucket"
        assert config.aws_s3_region == "us-west-2"
        assert config.aws_s3_endpoint_url == "http://localhost:9000"
        assert config.database_url == "postgresql://localhost:5432/test"
        assert config.aws_region == "us-west-2"
        assert config.jwt_secret == "builder-secret"
        assert config.jwt_algorithm == "HS384"
        assert getattr(config, 'custom_field') == "custom_value"
    
    def test_from_env_file(self):
        """Test loading from environment file"""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp_env:
            tmp_env.write("""
AWS_S3_BUCKET_NAME=env-file-bucket
AWS_S3_REGION=us-west-1
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=WARNING
""")
            tmp_env_path = tmp_env.name
        
        try:
            config = SharedInfrastructureConfig.from_env_file(tmp_env_path)
            
            assert config.aws_s3_bucket_name == "env-file-bucket"
            assert config.aws_s3_region == "us-west-1"
            assert config.environment == "staging"
            assert config.debug is False
            assert config.log_level == "WARNING"
        finally:
            os.unlink(tmp_env_path)
    
    def test_from_dict(self):
        """Test creating config from dictionary"""
        config_dict = {
            "aws_s3_bucket_name": "dict-bucket",
            "aws_s3_region": "eu-west-1",
            "environment": "production",
            "debug": False,
            "custom_setting": "dict-value"
        }
        
        config = SharedInfrastructureConfig.from_dict(config_dict)
        
        assert config.aws_s3_bucket_name == "dict-bucket"
        assert config.aws_s3_region == "eu-west-1"
        assert config.environment == "production"
        assert config.debug is False
        assert getattr(config, 'custom_setting') == "dict-value"
    
    def test_global_configuration_management(self):
        """Test global configuration management"""
        # Reset to clean state
        reset_global_config()
        
        # Create and set global config
        global_config = SharedInfrastructureConfig.for_development(s3_bucket="global-bucket")
        set_global_config(global_config)
        
        # Retrieve global config
        retrieved_config = get_shared_config()
        assert retrieved_config is global_config
        assert retrieved_config.aws_s3_bucket_name == "global-bucket"
        
        # Reset and test auto-creation
        reset_global_config()
        auto_config = get_shared_config()
        assert isinstance(auto_config, SharedInfrastructureConfig)
        assert auto_config is not global_config
    
    def test_has_s3_config_method(self):
        """Test has_s3_config method"""
        # Clear environment to ensure clean test state
        with patch.dict(os.environ, {}, clear=True):
            config_with_s3 = SharedInfrastructureConfig(aws_s3_bucket_name="test-bucket")
            config_without_s3 = SharedInfrastructureConfig()
            
            assert config_with_s3.has_s3_config() is True
            assert config_without_s3.has_s3_config() is False
    
    def test_get_s3_config_dict_method(self):
        """Test get_s3_config_dict method"""
        config = SharedInfrastructureConfig(
            aws_s3_bucket_name="test-bucket",
            aws_s3_region="us-west-2",
            aws_region="us-east-1",  # Should be used as fallback
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_s3_endpoint_url="http://localhost:9000",
            aws_s3_use_ssl=False,
            aws_s3_signature_version="s3v2"
        )
        
        s3_dict = config.get_s3_config_dict()
        
        assert s3_dict["bucket_name"] == "test-bucket"
        assert s3_dict["region"] == "us-west-2"  # S3 region takes precedence
        assert s3_dict["access_key_id"] == "test-key"
        assert s3_dict["secret_access_key"] == "test-secret"
        assert s3_dict["endpoint_url"] == "http://localhost:9000"
        assert s3_dict["use_ssl"] is False
        assert s3_dict["signature_version"] == "s3v2"
    
    def test_get_s3_config_dict_with_fallback_region(self):
        """Test get_s3_config_dict with fallback to aws_region"""
        # Clear environment to ensure clean test state
        with patch.dict(os.environ, {}, clear=True):
            config = SharedInfrastructureConfig(
                aws_s3_bucket_name="test-bucket",
                aws_region="us-east-1",  # Should be used as fallback
                # aws_s3_region not set
            )
            
            s3_dict = config.get_s3_config_dict()
            assert s3_dict["region"] == "us-east-1"  # Should fall back to aws_region
    
    def test_flexible_initialization_parameters(self):
        """Test flexible initialization parameters"""
        # Clear environment to ensure clean test state
        with patch.dict(os.environ, {}, clear=True):
            # Test with env_files parameter
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp_env:
                tmp_env.write("AWS_S3_BUCKET_NAME=param-bucket\n")
                tmp_env_path = tmp_env.name
            
            try:
                config = SharedInfrastructureConfig(
                    env_files=[tmp_env_path],
                    environment="custom",
                    debug=False
                )
                
                assert config.aws_s3_bucket_name == "param-bucket"
                assert config.environment == "custom"
                assert config.debug is False
            finally:
                os.unlink(tmp_env_path)
    
    def test_env_file_not_exists_handling(self):
        """Test graceful handling of non-existent env files"""
        # Should not raise error for non-existent files
        config = SharedInfrastructureConfig(env_files=["/non/existent/file.env"])
        assert isinstance(config, SharedInfrastructureConfig)
    
    def test_builder_with_env_file(self):
        """Test builder pattern with env files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp_env:
            tmp_env.write("AWS_S3_BUCKET_NAME=builder-env-bucket\n")
            tmp_env_path = tmp_env.name
        
        try:
            config = (ConfigurationBuilder()
                     .with_env_file(tmp_env_path)
                     .for_environment("development")
                     .with_s3("override-bucket")  # Should override env file
                     .build())
            
            assert config.aws_s3_bucket_name == "override-bucket"  # Direct params override env file
            assert config.environment == "development"
        finally:
            os.unlink(tmp_env_path)


class TestConfigurationCompatibility:
    """Test backward compatibility"""
    
    def test_default_initialization_still_works(self):
        """Test that default initialization still works"""
        # Clear environment to ensure clean test state
        with patch.dict(os.environ, {}, clear=True):
            config = SharedInfrastructureConfig()
            assert isinstance(config, SharedInfrastructureConfig)
            assert config.environment == "development"
    
    def test_environment_variable_override_still_works(self):
        """Test that environment variable override still works"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "env-var-bucket",
            "ENVIRONMENT": "production",
            "DEBUG": "false"
        }
        
        with patch.dict(os.environ, test_env):
            config = SharedInfrastructureConfig()
            
            assert config.aws_s3_bucket_name == "env-var-bucket"
            assert config.environment == "production"
            assert config.debug is False
    
    def test_legacy_shared_config_variable(self):
        """Test that legacy shared_config variable still works"""
        from shared.config.base_config import shared_config
        assert isinstance(shared_config, SharedInfrastructureConfig) 