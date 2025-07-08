# Environment Configuration Guide

This guide provides comprehensive information about configuring the WeKare shared package using environment files.

## Quick Start

1. **Choose your environment file:**
   ```bash
   # For development
   cp examples/.env.development .env
   
   # For testing
   cp examples/.env.testing .env
   
   # For production (customize with real values)
   cp examples/.env.production .env
   ```

2. **Load in your application:**
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   
   from shared.config.base_config import SharedInfrastructureConfig
   config = SharedInfrastructureConfig()
   ```

## Environment File Overview

### `.env.development` - Local Development
- **Purpose**: Local development with external services
- **Database**: Local PostgreSQL instance
- **S3**: Local MinIO instance for S3 compatibility
- **Security**: Development-friendly settings with debug enabled
- **Use case**: Day-to-day development work

### `.env.testing` - Testing Environment
- **Purpose**: Testing environment with test databases
- **Database**: Separate test database
- **S3**: Test bucket with mock credentials
- **Security**: Reduced token expiration for faster testing
- **Use case**: Running test suites

### `.env.production` - Production Environment
- **Purpose**: Production deployment with security guidelines
- **Database**: Production RDS instance
- **S3**: Production S3 bucket
- **Security**: Strong secrets and security recommendations
- **Use case**: Live production deployment

### `.env.docker` - Docker Compose
- **Purpose**: Full local development with Docker services
- **Database**: PostgreSQL container
- **S3**: MinIO container
- **Services**: Includes Redis and other services
- **Use case**: Container-based development

### `.env.ci` - CI/CD Pipelines
- **Purpose**: Continuous integration testing
- **Database**: CI test database
- **S3**: Mock S3 for testing
- **Performance**: Optimized for fast CI runs
- **Use case**: GitHub Actions, GitLab CI, Jenkins

## Configuration Variables

### Core Environment Settings

```bash
# Required for all environments
ENVIRONMENT=development|testing|production
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

### Database Configuration

```bash
# PostgreSQL connection strings
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SYNC_DATABASE_URL=postgresql://user:pass@host:port/db

# Connection pool settings
DB_ECHO=false                # Set to true for SQL query logging
DB_POOL_SIZE=10             # Number of connections in pool
DB_MAX_OVERFLOW=20          # Maximum overflow connections
```

**Examples:**
```bash
# Development (local)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/wekare_dev

# Production (RDS)
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db.amazonaws.com:5432/wekare_prod

# Docker Compose
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/wekare_dev
```

### AWS S3 Configuration

```bash
# Required
AWS_S3_BUCKET_NAME=your-bucket-name

# Authentication (use IAM roles in production)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Regional settings
AWS_S3_REGION=us-east-1
AWS_REGION=us-east-1              # Fallback for S3 region

# Connection settings
AWS_S3_ENDPOINT_URL=http://localhost:9000  # For MinIO/LocalStack
AWS_S3_USE_SSL=true|false         # Default: true
AWS_S3_SIGNATURE_VERSION=s3v4     # Default: s3v4
```

**Examples:**
```bash
# Development with MinIO
AWS_S3_BUCKET_NAME=wekare-dev-bucket
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_USE_SSL=false
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# Production with AWS S3
AWS_S3_BUCKET_NAME=wekare-prod-bucket
AWS_S3_REGION=us-east-1
AWS_S3_USE_SSL=true
# Use IAM roles instead of access keys in production
```

### Security & Authentication

```bash
# JWT Configuration
JWT_SECRET=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# API Keys
MASTER_API_KEY=your-master-api-key

# General AWS
AWS_ACCOUNT_ID=your-aws-account-id
```

## Usage Examples

### Basic Application Setup

```python
# main.py
from dotenv import load_dotenv
load_dotenv()

from shared import SharedInfrastructureConfig
from shared.storage import S3Client
from shared.database import get_database

# Configuration automatically loads from environment
config = SharedInfrastructureConfig()

# Services use the configuration
s3_client = S3Client()
database = get_database()
```

### FastAPI Application

```python
# app.py
from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from shared import SharedInfrastructureConfig, set_global_config

# Set global configuration at startup
config = SharedInfrastructureConfig()
set_global_config(config)

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "environment": config.environment}
```

### Testing Setup

```python
# conftest.py
import pytest
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    load_dotenv(".env.testing")
    
    from shared import SharedInfrastructureConfig, set_global_config
    config = SharedInfrastructureConfig()
    set_global_config(config)
```

## Docker Integration

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    env_file:
      - .env.docker
    depends_on:
      - postgres
      - minio
      - redis
    ports:
      - "8000:8000"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: wekare_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  minio_data:
```

### Dockerfile Environment

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Copy environment file
COPY .env.production .env

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Load environment and start
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      minio:
        image: minio/minio
        env:
          MINIO_ROOT_USER: test-key
          MINIO_ROOT_PASSWORD: test-secret
        ports:
          - 9000:9000
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/wekare_ci_test
          AWS_S3_BUCKET_NAME: wekare-ci-test-bucket
          AWS_ACCESS_KEY_ID: test-key
          AWS_SECRET_ACCESS_KEY: test-secret
          AWS_S3_ENDPOINT_URL: http://localhost:9000
          AWS_S3_USE_SSL: false
          ENVIRONMENT: testing
        run: poetry run pytest
```

### GitLab CI

```yaml
# .gitlab-ci.yml
test:
  stage: test
  image: python:3.11
  
  services:
    - postgres:15
    - minio/minio:latest
  
  variables:
    POSTGRES_DB: wekare_ci_test
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/wekare_ci_test
    AWS_S3_BUCKET_NAME: wekare-ci-test-bucket
    AWS_ACCESS_KEY_ID: test-key
    AWS_SECRET_ACCESS_KEY: test-secret
    AWS_S3_ENDPOINT_URL: http://minio:9000
    AWS_S3_USE_SSL: false
    ENVIRONMENT: testing
  
  script:
    - pip install poetry
    - poetry install
    - poetry run pytest
```

## Environment-Specific Tips

### Development Environment

1. **Use MinIO for S3 compatibility:**
   ```bash
   # Start MinIO locally
   docker run -p 9000:9000 -p 9001:9001 \
     -e MINIO_ROOT_USER=minioadmin \
     -e MINIO_ROOT_PASSWORD=minioadmin \
     minio/minio server /data --console-address ":9001"
   ```

2. **Access MinIO console at:** http://localhost:9001

3. **Enable debug logging:**
   ```bash
   DEBUG=true
   LOG_LEVEL=DEBUG
   DB_ECHO=true
   ```

### Testing Environment

1. **Use separate test database:**
   ```bash
   createdb wekare_test
   ```

2. **Reduce token expiration:**
   ```bash
   JWT_EXPIRE_MINUTES=15
   ```

3. **Enable test mode:**
   ```bash
   WEKARE_TEST_MODE=true
   ```

### Production Environment

1. **Use AWS IAM roles instead of access keys:**
   ```bash
   # Don't set these in production
   # AWS_ACCESS_KEY_ID=...
   # AWS_SECRET_ACCESS_KEY=...
   ```

2. **Use strong secrets:**
   ```bash
   JWT_SECRET=your-super-secure-production-jwt-secret-key-min-256-bits
   ```

3. **Enable SSL:**
   ```bash
   AWS_S3_USE_SSL=true
   ```

4. **Use AWS Secrets Manager:**
   ```python
   import boto3
   
   def get_secret(secret_name):
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId=secret_name)
       return response['SecretString']
   ```

## Security Best Practices

1. **Never commit `.env` files with real credentials**
2. **Use different secrets for each environment**
3. **Rotate secrets regularly**
4. **Use IAM roles in production**
5. **Enable AWS CloudTrail for audit logging**
6. **Use VPC endpoints for S3 access**
7. **Implement least privilege access policies**

## Troubleshooting

### Common Issues

1. **Configuration not loading:**
   ```python
   # Make sure to load dotenv
   from dotenv import load_dotenv
   load_dotenv()
   ```

2. **S3 connection failed:**
   ```bash
   # Check MinIO is running
   curl http://localhost:9000/minio/health/live
   ```

3. **Database connection error:**
   ```bash
   # Check PostgreSQL is running
   pg_isready -h localhost -p 5432
   ```

4. **Missing environment variables:**
   ```python
   # Check what's loaded
   import os
   print(os.environ.get('AWS_S3_BUCKET_NAME'))
   ```

### Debug Configuration

```python
from shared.config.base_config import SharedInfrastructureConfig

config = SharedInfrastructureConfig()
print(f"Environment: {config.environment}")
print(f"S3 Bucket: {config.aws_s3_bucket_name}")
print(f"S3 Region: {config.aws_s3_region}")
print(f"S3 Endpoint: {config.aws_s3_endpoint_url}")
print(f"Database URL: {config.database_url}")
```

## Next Steps

1. Copy the appropriate environment file for your use case
2. Customize the values for your specific setup
3. Load the environment in your application
4. Test the configuration with a simple script
5. Set up your CI/CD pipeline with the appropriate environment

For more examples, see the `examples/configuration_examples.py` file. 