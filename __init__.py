"""
WeKare Shared Infrastructure Components

This package provides common functionality for WeKare microservices:
- Database connection and base models
- Authentication and authorization utilities  
- Configuration management
- Common domain entities
"""

__version__ = "1.0.0"
__author__ = "WeKare Team"

# Import key components for easy access
from .shared.config.base_config import (
    SharedInfrastructureConfig, 
    ConfigurationBuilder,
    get_shared_config, 
    set_global_config,
    create_development_config,
    create_testing_config,
    create_production_config
)
from .shared.auth.api_keys import (
    APIKeyManager, 
    verify,
    verify_profiles_api_key,
    verify_referrals_api_key, 
    verify_insurance_api_key,
    verify_notifications_api_key,
    verify_master_api_key
)
from .shared.auth.token_verifier import get_token_from_request, verify_token
from .shared.database.connection import DatabaseConnection, get_session, get_database_url
from .shared.database.base import Base, BaseTable, OrganizationMixin
from .shared.database.repository import BaseRepository
from .shared.storage.s3_client import (
    S3Client, 
    S3Config, 
    get_s3_client, 
    upload_file_to_s3, 
    download_file_from_s3
)

# Export all major components
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Configuration
    "SharedInfrastructureConfig",
    "ConfigurationBuilder",
    "get_shared_config",
    "set_global_config",
    "create_development_config",
    "create_testing_config",
    "create_production_config",
    
    # Authentication
    "APIKeyManager",
    "verify",
    "verify_profiles_api_key",
    "verify_referrals_api_key", 
    "verify_insurance_api_key",
    "verify_notifications_api_key",
    "verify_master_api_key",
    "get_token_from_request",
    "verify_token",
    
    # Database
    "DatabaseConnection",
    "get_session",
    "get_database_url",
    "Base",
    "BaseTable", 
    "OrganizationMixin",
    "BaseRepository",
    
    # Storage
    "S3Client",
    "S3Config",
    "get_s3_client",
    "upload_file_to_s3",
    "download_file_from_s3",
]
