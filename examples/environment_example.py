#!/usr/bin/env python3
"""
Environment Configuration Example

This script demonstrates how to use different environment files 
with the WeKare shared package configuration system.
"""

import os
import sys
from pathlib import Path

# Add shared package to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from shared.config.base_config import SharedInfrastructureConfig
from shared.storage.s3_client import S3Client
from shared.database.connection import get_database_url


def load_environment_file(env_name: str) -> None:
    """Load environment file by name."""
    env_file = f".env.{env_name}"
    examples_dir = Path(__file__).parent
    env_path = examples_dir / env_file
    
    if not env_path.exists():
        print(f"❌ Environment file not found: {env_path}")
        print(f"Available files: {list(examples_dir.glob('.env.*'))}")
        return
    
    print(f"📁 Loading environment from: {env_path}")
    load_dotenv(env_path)


def print_configuration_summary(config: SharedInfrastructureConfig) -> None:
    """Print a summary of the loaded configuration."""
    print("\n🔧 Configuration Summary:")
    print(f"  Environment: {config.environment}")
    print(f"  Debug Mode: {config.debug}")
    print(f"  Database URL: {config.database_url}")
    print(f"  S3 Bucket: {config.aws_s3_bucket_name}")
    print(f"  S3 Region: {config.aws_s3_region}")
    print(f"  S3 Endpoint: {config.aws_s3_endpoint_url}")
    print(f"  S3 Use SSL: {config.aws_s3_use_ssl}")
    print(f"  JWT Secret: {config.jwt_secret[:10]}...") if config.jwt_secret else "Not set"


def test_s3_connection(config: SharedInfrastructureConfig) -> None:
    """Test S3 connection with the current configuration."""
    print("\n🔗 Testing S3 Connection:")
    
    try:
        s3_client = S3Client()
        
        # Try to list objects (this will fail if bucket doesn't exist, but that's OK)
        objects = s3_client.list_objects(max_keys=1)
        print(f"  ✅ S3 connection successful! Found {len(objects)} objects")
        
    except Exception as e:
        print(f"  ⚠️  S3 connection failed: {str(e)}")
        print(f"  💡 This is expected if MinIO isn't running or bucket doesn't exist")


def test_database_connection(config: SharedInfrastructureConfig) -> None:
    """Test database connection with the current configuration."""
    print("\n🗄️  Testing Database Connection:")
    
    try:
        # This will test the database URL format
        database_url = get_database_url()
        print(f"  ✅ Database configuration valid!")
        print(f"  💡 URL: {database_url}")
        
    except Exception as e:
        print(f"  ⚠️  Database connection failed: {str(e)}")
        print(f"  💡 This is expected if PostgreSQL isn't running")


def main():
    """Main function to demonstrate environment configuration."""
    print("🚀 WeKare Shared Package - Environment Configuration Example")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python environment_example.py <environment>")
        print("\nAvailable environments:")
        print("  development  - Local development with MinIO")
        print("  testing      - Testing environment")
        print("  production   - Production environment")
        print("  docker       - Docker Compose setup")
        print("  ci           - CI/CD environment")
        print("\nExample: python environment_example.py development")
        return
    
    env_name = sys.argv[1]
    
    # Load the environment file
    load_environment_file(env_name)
    
    # Create configuration
    try:
        config = SharedInfrastructureConfig()
        print_configuration_summary(config)
        
        # Test connections
        test_s3_connection(config)
        test_database_connection(config)
        
        print("\n✅ Configuration test completed!")
        
    except Exception as e:
        print(f"\n❌ Configuration failed: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("  1. Check that all required environment variables are set")
        print("  2. Verify the environment file exists and is valid")
        print("  3. Make sure services (PostgreSQL, MinIO) are running if testing connections")


if __name__ == "__main__":
    main() 