"""
Shared Infrastructure Configuration
Provides base configuration that all WeKare microservices inherit from.

This configuration system supports multiple initialization methods:
1. Environment variables (most flexible)
2. Custom env files (optional)
3. Direct parameters (programmatic)
4. Configuration builder pattern
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger("shared.config")


class SharedInfrastructureConfig(BaseSettings):
    """
    Shared infrastructure configuration across all WeKare services.
    
    This configuration can be loaded from:
    1. Environment variables (highest priority)
    2. Custom .env files (if specified)
    3. Direct parameters (programmatic configuration)
    
    The configuration no longer depends on external files by default,
    making it easier to develop and deploy.
    """
    
    def __init__(self, 
                 env_files: Optional[List[Union[str, Path]]] = None,
                 load_shared_env_files: bool = False,
                 custom_env_path: Optional[Union[str, Path]] = None,
                 **kwargs):
        """
        Initialize configuration with flexible loading options.
        
        Args:
            env_files: List of specific .env files to load (optional)
            load_shared_env_files: Whether to load legacy .env.shared.* files (default: False)
            custom_env_path: Custom directory to look for .env files (optional)
            **kwargs: Direct configuration parameters
        """
        
        # Load environment files if specified
        if env_files:
            self._load_env_files(env_files)
        
        # Load legacy shared environment files if requested
        if load_shared_env_files:
            self._load_legacy_shared_env_files(custom_env_path)
        
        # Initialize with any direct parameters
        super().__init__(**kwargs)
        
        logger.info("🔧 Configuration initialized", 
                   environment=self.environment,
                   debug=self.debug,
                   aws_region=self.aws_region,
                   has_s3_bucket=bool(self.aws_s3_bucket_name))
    
    def _load_env_files(self, env_files: List[Union[str, Path]]):
        """Load specified environment files"""
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                load_dotenv(env_path, override=False)
                logger.info("📂 Loaded env file", path=str(env_path))
            else:
                logger.warning("⚠️ Env file not found", path=str(env_path))
    
    def _load_legacy_shared_env_files(self, custom_env_path: Optional[Union[str, Path]] = None):
        """Load legacy shared environment files for backward compatibility"""
        if custom_env_path:
            base_dir = Path(custom_env_path)
        else:
            # Default to looking in parent directories (legacy behavior)
            base_dir = Path(__file__).parent.parent.parent
        
        shared_local_path = base_dir / ".env.shared.local"
        shared_aws_path = base_dir / ".env.shared.aws"
        
        for env_path in [shared_local_path, shared_aws_path]:
            if env_path.exists():
                load_dotenv(env_path, override=False)
                logger.info("📂 Loaded legacy env file", path=str(env_path))
    
    # ==============================================
    # DATABASE CONFIGURATION (SHARED)
    # ==============================================
    database_url: str = "postgresql+asyncpg://postgres:getgoing@localhost:5433/wekare_test"
    sync_database_url: str = "postgresql://postgres:getgoing@localhost:5433/wekare_test"
    
    # Database connection settings
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # ==============================================
    # AWS INFRASTRUCTURE (SHARED)
    # ==============================================
    aws_region: str = "us-east-2"
    aws_default_region: str = "us-east-2"
    aws_account_id: str = "613778970767"
    aws_cloudwatch_log_group: Optional[str] = None
    aws_load_balancer_url: Optional[str] = None
    
    # S3 Configuration
    aws_s3_bucket_name: Optional[str] = None
    aws_s3_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_endpoint_url: Optional[str] = None  # For local development/testing
    aws_s3_use_ssl: bool = True
    aws_s3_signature_version: str = "s3v4"
    
    # ==============================================
    # SECURITY & AUTHENTICATION (SHARED)
    # ==============================================
    jwt_secret: str = "dev_jwt_secret_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # Master API key for inter-service communication
    master_api_key: str = "wekare-dev-2024"
    
    # ==============================================
    # APPLICATION SETTINGS (SHARED)
    # ==============================================
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    pythonpath: str = ".:/app"
    
    # ==============================================
    # EXTERNAL SERVICES (SHARED DEFAULTS)
    # ==============================================
    sendgrid_from_email: str = "noreply@wekare.com"
    twilio_phone_number: str = "+1234567890"
    
    class Config:
        env_file_encoding = 'utf-8'
        case_sensitive = False
        # Allow extra fields for service-specific overrides
        extra = "allow"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() in ["development", "dev", "local"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() in ["production", "prod"]
    
    @property
    def is_aws_environment(self) -> bool:
        """Check if running in AWS environment"""
        return bool(self.aws_cloudwatch_log_group or self.aws_load_balancer_url)
    
    def get_database_url(self, service_name: Optional[str] = None) -> str:
        """Get database URL (simplified for compatibility)"""
        return self.database_url
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            # Database
            "database_url": self.database_url,
            "sync_database_url": self.sync_database_url,
            
            # AWS
            "aws_region": self.aws_region,
            "aws_account_id": self.aws_account_id,
            
            # S3
            "aws_s3_bucket_name": self.aws_s3_bucket_name,
            "aws_s3_region": self.aws_s3_region,
            "aws_s3_use_ssl": self.aws_s3_use_ssl,
            
            # Security
            "jwt_secret": self.jwt_secret,
            "jwt_algorithm": self.jwt_algorithm,
            "master_api_key": self.master_api_key,
            
            # Application
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
        }
    
    def has_s3_config(self) -> bool:
        """Check if S3 configuration is available"""
        return bool(self.aws_s3_bucket_name)
    
    def get_s3_config_dict(self) -> Dict[str, Any]:
        """Get S3-specific configuration as dictionary"""
        return {
            "bucket_name": self.aws_s3_bucket_name,
            "region": self.aws_s3_region or self.aws_region,
            "access_key_id": self.aws_access_key_id,
            "secret_access_key": self.aws_secret_access_key,
            "endpoint_url": self.aws_s3_endpoint_url,
            "use_ssl": self.aws_s3_use_ssl,
            "signature_version": self.aws_s3_signature_version,
        }
    
    @classmethod
    def from_env_file(cls, env_file: Union[str, Path], **kwargs) -> "SharedInfrastructureConfig":
        """
        Create configuration from a single environment file.
        
        Args:
            env_file: Path to the .env file
            **kwargs: Additional configuration parameters
        """
        return cls(env_files=[env_file], **kwargs)
    
    @classmethod
    def from_env_files(cls, env_files: List[Union[str, Path]], **kwargs) -> "SharedInfrastructureConfig":
        """
        Create configuration from multiple environment files.
        
        Args:
            env_files: List of .env file paths
            **kwargs: Additional configuration parameters
        """
        return cls(env_files=env_files, **kwargs)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], **kwargs) -> "SharedInfrastructureConfig":
        """
        Create configuration from a dictionary.
        
        Args:
            config_dict: Configuration values as dictionary
            **kwargs: Additional configuration parameters
        """
        return cls(**{**config_dict, **kwargs})
    
    @classmethod
    def for_development(cls, 
                       s3_bucket: Optional[str] = None,
                       s3_endpoint_url: str = "http://localhost:9000",
                       **kwargs) -> "SharedInfrastructureConfig":
        """
        Create development configuration with sensible defaults.
        
        Args:
            s3_bucket: S3 bucket name for development (optional)
            s3_endpoint_url: S3 endpoint for local testing (default: MinIO)
            **kwargs: Additional configuration parameters
        """
        dev_config = {
            "environment": "development",
            "debug": True,
            "log_level": "DEBUG",
            "aws_s3_endpoint_url": s3_endpoint_url,
            "aws_s3_use_ssl": False,
        }
        
        if s3_bucket:
            dev_config["aws_s3_bucket_name"] = s3_bucket
            dev_config["aws_s3_region"] = "us-east-1"  # Default for development
        
        return cls(**{**dev_config, **kwargs})
    
    @classmethod
    def for_testing(cls, 
                   test_s3_bucket: str = "test-bucket",
                   **kwargs) -> "SharedInfrastructureConfig":
        """
        Create testing configuration with test-specific defaults.
        
        Args:
            test_s3_bucket: S3 bucket name for testing
            **kwargs: Additional configuration parameters
        """
        test_config = {
            "environment": "testing",
            "debug": True,
            "log_level": "DEBUG",
            "database_url": "postgresql+asyncpg://postgres:test@localhost:5433/wekare_test",
            "aws_s3_bucket_name": test_s3_bucket,
            "aws_s3_region": "us-east-1",
            "aws_s3_endpoint_url": "http://localhost:9000",
            "aws_s3_use_ssl": False,
            "jwt_secret": "test-jwt-secret",
            "master_api_key": "test-master-key",
        }
        
        return cls(**{**test_config, **kwargs})
    
    @classmethod
    def for_production(cls, 
                      required_s3_bucket: str,
                      required_s3_region: str = "us-east-2",
                      **kwargs) -> "SharedInfrastructureConfig":
        """
        Create production configuration with production-specific defaults.
        
        Args:
            required_s3_bucket: S3 bucket name (required for production)
            required_s3_region: S3 region (default: us-east-2)
            **kwargs: Additional configuration parameters
        """
        prod_config = {
            "environment": "production",
            "debug": False,
            "log_level": "INFO",
            "aws_s3_bucket_name": required_s3_bucket,
            "aws_s3_region": required_s3_region,
            "aws_s3_use_ssl": True,
        }
        
        return cls(**{**prod_config, **kwargs})
    
    @classmethod
    def with_legacy_files(cls, 
                         custom_env_path: Optional[Union[str, Path]] = None,
                         **kwargs) -> "SharedInfrastructureConfig":
        """
        Create configuration that loads legacy .env.shared.* files for backward compatibility.
        
        Args:
            custom_env_path: Custom directory to look for .env files (optional)
            **kwargs: Additional configuration parameters
        """
        return cls(load_shared_env_files=True, custom_env_path=custom_env_path, **kwargs)


class ConfigurationBuilder:
    """
    Builder pattern for creating configurations in a fluent way.
    
    Example:
        config = (ConfigurationBuilder()
                 .for_environment("development")
                 .with_s3("my-dev-bucket", endpoint="http://localhost:9000")
                 .with_database("postgresql://localhost:5432/mydb")
                 .build())
    """
    
    def __init__(self):
        self._config_params = {}
        self._env_files = []
    
    def for_environment(self, env: str) -> "ConfigurationBuilder":
        """Set the environment type"""
        self._config_params["environment"] = env
        if env.lower() in ["development", "dev", "local"]:
            self._config_params.update({
                "debug": True,
                "log_level": "DEBUG"
            })
        elif env.lower() in ["production", "prod"]:
            self._config_params.update({
                "debug": False,
                "log_level": "INFO"
            })
        return self
    
    def with_s3(self, 
                bucket_name: str,
                region: Optional[str] = None,
                endpoint: Optional[str] = None,
                use_ssl: Optional[bool] = None) -> "ConfigurationBuilder":
        """Configure S3 settings"""
        self._config_params["aws_s3_bucket_name"] = bucket_name
        if region:
            self._config_params["aws_s3_region"] = region
        if endpoint:
            self._config_params["aws_s3_endpoint_url"] = endpoint
        if use_ssl is not None:
            self._config_params["aws_s3_use_ssl"] = use_ssl
        return self
    
    def with_database(self, database_url: str) -> "ConfigurationBuilder":
        """Configure database URL"""
        self._config_params["database_url"] = database_url
        return self
    
    def with_aws_region(self, region: str) -> "ConfigurationBuilder":
        """Set AWS region"""
        self._config_params["aws_region"] = region
        return self
    
    def with_jwt_config(self, secret: str, algorithm: str = "HS256") -> "ConfigurationBuilder":
        """Configure JWT settings"""
        self._config_params["jwt_secret"] = secret
        self._config_params["jwt_algorithm"] = algorithm
        return self
    
    def with_env_file(self, env_file: Union[str, Path]) -> "ConfigurationBuilder":
        """Add an environment file to load"""
        self._env_files.append(env_file)
        return self
    
    def with_custom_params(self, **params) -> "ConfigurationBuilder":
        """Add custom configuration parameters"""
        self._config_params.update(params)
        return self
    
    def build(self) -> SharedInfrastructureConfig:
        """Build the final configuration"""
        if self._env_files:
            return SharedInfrastructureConfig(env_files=self._env_files, **self._config_params)
        else:
            return SharedInfrastructureConfig(**self._config_params)


# Flexible global configuration management
_global_config: Optional[SharedInfrastructureConfig] = None


def set_global_config(config: SharedInfrastructureConfig) -> None:
    """Set the global configuration instance"""
    global _global_config
    _global_config = config
    logger.info("🌍 Global configuration updated")


def get_shared_config() -> SharedInfrastructureConfig:
    """
    Get the global shared configuration instance.
    
    If no global config has been set, creates a default instance
    using environment variables only (no external files).
    """
    global _global_config
    if _global_config is None:
        _global_config = SharedInfrastructureConfig()
        logger.info("🌍 Created default global configuration")
    return _global_config


def reset_global_config() -> None:
    """Reset the global configuration (useful for testing)"""
    global _global_config
    _global_config = None
    logger.info("🔄 Global configuration reset")


# Legacy compatibility - create shared_config without external file dependencies
shared_config = SharedInfrastructureConfig()


# Convenience functions for common configuration patterns
def create_development_config(s3_bucket: Optional[str] = None) -> SharedInfrastructureConfig:
    """Create a development configuration with sensible defaults"""
    return SharedInfrastructureConfig.for_development(s3_bucket=s3_bucket)


def create_testing_config(test_s3_bucket: str = "test-bucket") -> SharedInfrastructureConfig:
    """Create a testing configuration"""
    return SharedInfrastructureConfig.for_testing(test_s3_bucket=test_s3_bucket)


def create_production_config(s3_bucket: str, s3_region: str = "us-east-2") -> SharedInfrastructureConfig:
    """Create a production configuration"""
    return SharedInfrastructureConfig.for_production(
        required_s3_bucket=s3_bucket, 
        required_s3_region=s3_region
    ) 