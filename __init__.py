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
from .config.base_config import SharedInfrastructureConfig, get_shared_config
from .auth.api_keys import (
    APIKeyManager, 
    verify,
    verify_profiles_api_key,
    verify_referrals_api_key, 
    verify_insurance_api_key,
    verify_notifications_api_key,
    verify_master_api_key
)
from .auth.token_verifier import get_token_from_request, verify_token
from .database.connection import DatabaseConnection, get_session, get_database_url
from .database.base import Base, BaseTable, OrganizationMixin
from .database.repository import BaseRepository

# Export all major components
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Configuration
    "SharedInfrastructureConfig",
    "get_shared_config",
    
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
]
