# WeKare Shared Infrastructure Components

Shared infrastructure components for WeKare microservices architecture.

## Overview

This package provides common functionality used across all WeKare services:

- **Database Connection & Models** - Shared database utilities and base classes
- **Authentication & Authorization** - JWT token handling, API key validation
- **Configuration Management** - Base configuration classes and environment management
- **Storage & File Management** - AWS S3 integration with read/write capabilities
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

The new flexible configuration system supports multiple initialization methods and doesn't require external files:

#### Method 1: Environment Variables (Recommended)
```python
from shared.config.base_config import SharedInfrastructureConfig

# Automatically loads from environment variables
config = SharedInfrastructureConfig()
print(config.aws_s3_bucket_name)
```

#### Method 2: Factory Methods for Different Environments
```python
from shared.config.base_config import (
    SharedInfrastructureConfig,
    create_development_config,
    create_testing_config,
    create_production_config
)

# Development with local S3 (MinIO)
dev_config = SharedInfrastructureConfig.for_development(
    s3_bucket="my-dev-bucket",
    s3_endpoint_url="http://localhost:9000"
)

# Testing configuration
test_config = create_testing_config("test-bucket")

# Production configuration  
prod_config = create_production_config("prod-bucket", "us-east-1")
```

#### Method 3: Builder Pattern (Fluent API)
```python
from shared.config.base_config import ConfigurationBuilder

config = (ConfigurationBuilder()
          .for_environment("development")
          .with_s3("my-bucket", region="us-west-2", endpoint="http://localhost:9000")
          .with_database("postgresql://localhost:5432/myapp")
          .with_jwt_config("dev-secret")
          .build())
```

#### Method 4: Programmatic Configuration
```python
config = SharedInfrastructureConfig(
    aws_s3_bucket_name="my-bucket",
    aws_s3_region="us-west-2",
    environment="development",
    debug=True
)
```

#### Method 5: Global Configuration
```python
from shared.config.base_config import set_global_config, get_shared_config

# Set once in your application startup
config = SharedInfrastructureConfig.for_development(s3_bucket="app-bucket")
set_global_config(config)

# Use anywhere in your application
config = get_shared_config()
```

#### S3 Configuration Environment Variables
```bash
# Required
AWS_S3_BUCKET_NAME=your-bucket-name

# Optional (with defaults)
AWS_S3_REGION=us-east-2                    # Falls back to AWS_REGION
AWS_ACCESS_KEY_ID=your-access-key          # Or use IAM roles
AWS_SECRET_ACCESS_KEY=your-secret-key      # Or use IAM roles
AWS_S3_ENDPOINT_URL=http://localhost:9000  # For local testing (MinIO/LocalStack)
AWS_S3_USE_SSL=true                        # Default: true
AWS_S3_SIGNATURE_VERSION=s3v4              # Default: s3v4
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

### S3 Storage
```python
from shared.storage.s3_client import S3Client, S3Config, get_s3_client
from shared.storage.s3_client import upload_file_to_s3, download_file_from_s3

# Method 1: Using S3Client directly
s3_client = get_s3_client()  # Uses shared configuration
success = s3_client.upload_file("local_file.txt", "path/in/s3/file.txt")
success = s3_client.download_file("path/in/s3/file.txt", "downloaded_file.txt")

# Method 2: Using convenience functions
success = upload_file_to_s3("local_file.txt", "path/in/s3/file.txt")
success = download_file_from_s3("path/in/s3/file.txt", "downloaded_file.txt")

# Method 3: Using custom configuration
custom_config = S3Config(
    bucket_name="my-bucket",
    region="us-west-2",
    access_key_id="your-key",
    secret_access_key="your-secret"
)
s3_client = S3Client(custom_config)

# Advanced operations
objects = s3_client.list_objects(prefix="documents/")
exists = s3_client.object_exists("path/in/s3/file.txt")
presigned_url = s3_client.get_presigned_url("path/in/s3/file.txt", expiration=3600)
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
├── storage/             # Storage utilities
│   ├── s3_client.py    # AWS S3 client with read/write operations
│   └── __init__.py
├── app/                # Shared FastAPI components
│   ├── domain/         # Shared domain entities
│   └── infra/          # Infrastructure components
├── tests/              # Shared test utilities
└── scripts/            # Shared utility scripts
```

## Version History

- **1.2.0** - Major configuration system improvements
  - **No external file dependencies** - Works out-of-the-box for development
  - **Multiple initialization methods** - Environment variables, factory methods, builder pattern, programmatic
  - **Flexible S3 configuration** - Easy setup for dev/test/prod environments
  - **Global configuration management** - Set once, use everywhere
  - **Better error messages** - Clear guidance when configuration is missing
  - **Backward compatibility** - All existing code continues to work

- **1.1.0** - Added S3 storage capabilities
  - AWS S3 client with comprehensive read/write operations
  - S3 configuration management
  - Upload/download file operations
  - Object listing, existence checking, and presigned URLs
  - Metadata and content type support
  - Convenience functions for easy integration
  
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