# WeKare Shared Package - Environment Configuration Examples

This directory contains sample environment files and examples for configuring the WeKare shared package across different environments.

## 📁 Environment Files

### Quick Start

Choose and copy the appropriate environment file for your use case:

```bash
# Development environment
cp examples/.env.development .env

# Testing environment
cp examples/.env.testing .env

# Production environment (customize with real values)
cp examples/.env.production .env

# Docker Compose environment
cp examples/.env.docker .env

# CI/CD environment
cp examples/.env.ci .env
```

### Environment File Overview

| File | Purpose | Database | S3 | Use Case |
|------|---------|----------|----|---------:|
| `.env.development` | Local development | Local PostgreSQL | Local MinIO | Day-to-day development |
| `.env.testing` | Testing environment | Test database | Test bucket | Running test suites |
| `.env.production` | Production deployment | Production RDS | Production S3 | Live production |
| `.env.docker` | Docker Compose | PostgreSQL container | MinIO container | Container-based development |
| `.env.ci` | CI/CD pipelines | CI test database | Mock S3 | GitHub Actions, GitLab CI |

## 🔧 Configuration Examples

### `configuration_examples.py`

Comprehensive examples showing all configuration methods:

```bash
python examples/configuration_examples.py
```

This script demonstrates:
- Environment variable configuration
- Factory methods for different environments
- Builder pattern for complex configurations
- Programmatic configuration
- Global configuration management

### `environment_example.py`

Interactive script to test environment configurations:

```bash
python examples/environment_example.py development
python examples/environment_example.py testing
python examples/environment_example.py production
python examples/environment_example.py docker
python examples/environment_example.py ci
```

This script:
- Loads the specified environment file
- Creates a configuration object
- Tests S3 and database connections
- Displays configuration summary

## 📋 Environment Variable Reference

### Core Settings

```bash
ENVIRONMENT=development|testing|production
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
```

### Database Configuration

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SYNC_DATABASE_URL=postgresql://user:pass@host:port/db
DB_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### AWS S3 Configuration

```bash
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_ENDPOINT_URL=http://localhost:9000  # For MinIO
AWS_S3_USE_SSL=true
```

### Security & Authentication

```bash
JWT_SECRET=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
MASTER_API_KEY=your-master-api-key
```

## 🚀 Usage Examples

### Basic Application

```python
from dotenv import load_dotenv
load_dotenv()

from shared.config.base_config import SharedInfrastructureConfig
config = SharedInfrastructureConfig()
```

### FastAPI Application

```python
from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from shared import SharedInfrastructureConfig, set_global_config

config = SharedInfrastructureConfig()
set_global_config(config)

app = FastAPI()
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
    set_global_config(SharedInfrastructureConfig())
```

## 🐳 Docker Integration

### Docker Compose Example

```yaml
version: '3.8'
services:
  app:
    build: .
    env_file:
      - .env.docker
    depends_on:
      - postgres
      - minio
```

### Dockerfile Example

```dockerfile
FROM python:3.11-slim
COPY .env.production .env
# ... rest of Dockerfile
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test
      AWS_S3_BUCKET_NAME: test-bucket
      AWS_ACCESS_KEY_ID: test-key
      AWS_SECRET_ACCESS_KEY: test-secret
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: poetry run pytest
```

## 🛠️ Development Setup

### Local Development with MinIO

1. Start MinIO for S3 compatibility:
   ```bash
   docker run -p 9000:9000 -p 9001:9001 \
     -e MINIO_ROOT_USER=minioadmin \
     -e MINIO_ROOT_PASSWORD=minioadmin \
     minio/minio server /data --console-address ":9001"
   ```

2. Copy development environment:
   ```bash
   cp examples/.env.development .env
   ```

3. Test configuration:
   ```bash
   python examples/environment_example.py development
   ```

### Docker Compose Development

1. Copy Docker environment:
   ```bash
   cp examples/.env.docker .env
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

3. Test configuration:
   ```bash
   python examples/environment_example.py docker
   ```

## 🔐 Security Best Practices

### Development
- Use MinIO for local S3 testing
- Enable debug mode for troubleshooting
- Use weak credentials for local development

### Testing
- Use separate test databases
- Mock external services
- Use predictable test data

### Production
- **Never commit real credentials**
- Use AWS IAM roles instead of access keys
- Store secrets in AWS Secrets Manager
- Use strong, unique secrets
- Enable SSL/TLS everywhere
- Implement least privilege access

## 📚 Additional Resources

- **`ENVIRONMENT_CONFIGURATION.md`** - Comprehensive environment configuration guide
- **`configuration_examples.py`** - All configuration methods with examples
- **`environment_example.py`** - Interactive environment testing tool

## 🐛 Troubleshooting

### Common Issues

1. **Configuration not loading**
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Make sure to call this first
   ```

2. **S3 connection failed**
   ```bash
   # Check if MinIO is running
   curl http://localhost:9000/minio/health/live
   ```

3. **Database connection error**
   ```bash
   # Check PostgreSQL status
   pg_isready -h localhost -p 5432
   ```

4. **Environment variables not set**
   ```python
   import os
   print(os.environ.get('AWS_S3_BUCKET_NAME'))  # Check if loaded
   ```

### Debug Configuration

```python
from shared.config.base_config import SharedInfrastructureConfig
config = SharedInfrastructureConfig()
print(f"Environment: {config.environment}")
print(f"S3 Bucket: {config.aws_s3_bucket_name}")
print(f"Database URL: {config.database_url}")
```

## 🎯 Next Steps

1. Choose the appropriate environment file for your use case
2. Copy it to your project root as `.env`
3. Customize the values for your specific setup
4. Test the configuration using the example scripts
5. Integrate with your application code

For detailed information, see the main README and `ENVIRONMENT_CONFIGURATION.md` files. 