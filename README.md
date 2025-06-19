# WeKare Shared Infrastructure Components

Shared infrastructure components for WeKare microservices architecture.

## Overview

This package provides common functionality used across all WeKare services:

- **Database Connection & Models** - Shared database utilities and base classes
- **Authentication & Authorization** - JWT token handling, API key validation
- **Configuration Management** - Base configuration classes and environment management
- **Common Domain Entities** - Shared business entities and value objects

## Installation

### For Development (from local source):
```bash
# Install in development mode
pip install -e .

# Or with poetry
poetry install
```

### For Production (from git):
```bash
# Install from git repository
pip install git+https://github.com/yourusername/wekare-backend.git#subdirectory=shared

# Or add to pyproject.toml
[tool.poetry.dependencies]
wekare-shared = {git = "https://github.com/yourusername/wekare-backend.git", subdirectory = "shared"}
```

## Usage

### Database Connection
```python
from shared.database.connection import get_database
from shared.database.base import Base

# Get database connection
database = get_database()
```

### Configuration
```python
from shared.config.base_config import SharedInfrastructureConfig

# Load shared configuration
config = SharedInfrastructureConfig()
print(config.database_url)
```

### Authentication
```python
from shared.auth.token_verifier import verify_jwt_token
from shared.auth.api_keys import validate_api_key

# Verify JWT token
payload = verify_jwt_token(token)

# Validate API key
is_valid = validate_api_key(api_key, "profiles")
```

## Package Structure

```
shared/
├── __init__.py
├── auth/                 # Authentication utilities
│   ├── api_keys.py      # API key validation
│   └── token_verifier.py # JWT token verification
├── config/              # Configuration management
│   ├── base_config.py   # Shared infrastructure config
│   └── __init__.py
├── database/            # Database utilities
│   ├── base.py         # Base database models
│   ├── connection.py   # Database connection management
│   ├── repository.py   # Base repository patterns
│   └── service_db.py   # Service-specific database utilities
├── app/                # Shared FastAPI components
│   ├── domain/         # Shared domain entities
│   └── infra/          # Infrastructure components
├── tests/              # Shared test utilities
└── scripts/            # Shared utility scripts
```

## Version History

- **1.0.0** - Initial release with core infrastructure components
  - Database connection management
  - Base configuration classes  
  - Authentication utilities
  - Common domain entities

## Development

### Running Tests
```bash
poetry run pytest
```

### Building Package
```bash
poetry build
```

### Publishing (Internal)
```bash
# Build wheel
poetry build

# Install locally
pip install dist/wekare_shared-1.0.0-py3-none-any.whl
``` 