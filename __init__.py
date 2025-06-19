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

# Import key modules for easy access
from . import auth
from . import config
from . import database

# Expose commonly used classes
from .config.base_config import SharedInfrastructureConfig
from .database.connection import get_database_url, get_session, db
from .database.base import Base

__all__ = [
    "auth",
    "config", 
    "database",
    "SharedInfrastructureConfig",
    "get_database_url",
    "get_session",
    "db",
    "Base",
    "__version__",
]
