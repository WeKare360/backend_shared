"""
Shared Infrastructure Configuration
Provides base configuration that all WeKare microservices inherit from.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class SharedInfrastructureConfig(BaseSettings):
    """
    Shared infrastructure configuration across all WeKare services.
    
    This configuration is loaded from:
    1. .env.shared.local (local development)
    2. .env.shared.aws (AWS environments)
    3. Environment variables (highest priority)
    """
    
    def __init__(self, **kwargs):
        # Get root directory (where shared config files are located)
        root_dir = Path(__file__).parent.parent.parent
        
        # Load shared environment files (lowest priority)
        shared_local_path = root_dir / ".env.shared.local"
        shared_aws_path = root_dir / ".env.shared.aws"
        
        # Load shared configs
        if shared_local_path.exists():
            load_dotenv(shared_local_path, override=False)
            
        if shared_aws_path.exists():
            load_dotenv(shared_aws_path, override=False)
        
        super().__init__(**kwargs)
    
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
            
            # Security
            "jwt_secret": self.jwt_secret,
            "jwt_algorithm": self.jwt_algorithm,
            "master_api_key": self.master_api_key,
            
            # Application
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
        }


# Global shared config instance
shared_config = SharedInfrastructureConfig()


def get_shared_config() -> SharedInfrastructureConfig:
    """Get the global shared configuration instance"""
    return shared_config 