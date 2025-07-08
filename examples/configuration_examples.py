#!/usr/bin/env python3
"""
WeKare Shared Package - Configuration Examples

This script demonstrates the various ways clients can configure
the shared package for different environments and use cases.

The new configuration system is flexible and doesn't require
external files, making it perfect for both development and production.
"""

import os
import tempfile
from pathlib import Path

# For this example (running from within the shared package directory):
import sys
sys.path.insert(0, '.')

# Import the improved configuration system
from shared.config.base_config import (
    SharedInfrastructureConfig,
    ConfigurationBuilder,
    create_development_config,
    create_testing_config,
    create_production_config,
    set_global_config,
    get_shared_config
)

# Import S3 functionality
from shared.storage.s3_client import S3Client, S3Config


def example_1_environment_variables():
    """Example 1: Simple configuration using environment variables (most common)"""
    print("🚀 Example 1: Environment Variables Configuration")
    
    # Set environment variables (in real usage, these would be set externally)
    os.environ.update({
        "AWS_S3_BUCKET_NAME": "my-service-bucket",
        "AWS_S3_REGION": "us-west-2",
        "AWS_ACCESS_KEY_ID": "your-access-key",
        "AWS_SECRET_ACCESS_KEY": "your-secret-key",
        "ENVIRONMENT": "development",
        "DEBUG": "true"
    })
    
    # Create configuration (automatically picks up environment variables)
    config = SharedInfrastructureConfig()
    
    print(f"   📦 S3 Bucket: {config.aws_s3_bucket_name}")
    print(f"   🌍 Region: {config.aws_s3_region}")
    print(f"   🔧 Environment: {config.environment}")
    print(f"   🐛 Debug: {config.debug}")
    
    # Use with S3
    s3_client = S3Client(config)
    print(f"   ✅ S3 Client configured for bucket: {s3_client.config.bucket_name}")
    print()


def example_2_factory_methods():
    """Example 2: Using factory methods for different environments"""
    print("🚀 Example 2: Factory Methods for Different Environments")
    
    # Development configuration
    dev_config = SharedInfrastructureConfig.for_development(
        s3_bucket="dev-bucket",
        s3_endpoint_url="http://localhost:9000"  # MinIO for local dev
    )
    print(f"   🔧 Dev - S3 Bucket: {dev_config.aws_s3_bucket_name}")
    print(f"   🔧 Dev - Endpoint: {dev_config.aws_s3_endpoint_url}")
    print(f"   🔧 Dev - SSL: {dev_config.aws_s3_use_ssl}")
    
    # Testing configuration
    test_config = SharedInfrastructureConfig.for_testing(
        test_s3_bucket="test-bucket"
    )
    print(f"   🧪 Test - S3 Bucket: {test_config.aws_s3_bucket_name}")
    print(f"   🧪 Test - Environment: {test_config.environment}")
    
    # Production configuration
    prod_config = SharedInfrastructureConfig.for_production(
        required_s3_bucket="prod-bucket",
        required_s3_region="us-east-1"
    )
    print(f"   🚀 Prod - S3 Bucket: {prod_config.aws_s3_bucket_name}")
    print(f"   🚀 Prod - SSL: {prod_config.aws_s3_use_ssl}")
    print(f"   🚀 Prod - Debug: {prod_config.debug}")
    print()


def example_3_builder_pattern():
    """Example 3: Using the builder pattern for fluent configuration"""
    print("🚀 Example 3: Configuration Builder Pattern")
    
    # Build configuration fluently
    config = (ConfigurationBuilder()
              .for_environment("development")
              .with_s3("my-dev-bucket", 
                      region="us-west-2", 
                      endpoint="http://localhost:9000",
                      use_ssl=False)
              .with_database("postgresql://localhost:5432/myapp_dev")
              .with_aws_region("us-west-2")
              .with_jwt_config("dev-secret", "HS256")
              .with_custom_params(
                  custom_setting="my-value",
                  service_name="my-service"
              )
              .build())
    
    print(f"   🏗️ Built - S3 Bucket: {config.aws_s3_bucket_name}")
    print(f"   🏗️ Built - Database: {config.database_url}")
    print(f"   🏗️ Built - JWT Secret: {config.jwt_secret}")
    print(f"   🏗️ Built - Custom: {getattr(config, 'custom_setting', 'N/A')}")
    print()


def example_4_env_file_configuration():
    """Example 4: Loading configuration from .env files"""
    print("🚀 Example 4: Environment File Configuration")
    
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as tmp_env:
        tmp_env.write("""
# Sample .env file for WeKare service
AWS_S3_BUCKET_NAME=env-file-bucket
AWS_S3_REGION=us-east-2
AWS_ACCESS_KEY_ID=env-access-key
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
JWT_SECRET=env-jwt-secret
""")
        tmp_env_path = tmp_env.name
    
    try:
        # Load configuration from .env file
        config = SharedInfrastructureConfig.from_env_file(tmp_env_path)
        
        print(f"   📄 From .env - S3 Bucket: {config.aws_s3_bucket_name}")
        print(f"   📄 From .env - Environment: {config.environment}")
        print(f"   📄 From .env - Debug: {config.debug}")
        print(f"   📄 From .env - Log Level: {config.log_level}")
        
    finally:
        # Clean up
        os.unlink(tmp_env_path)
    
    print()


def example_5_programmatic_configuration():
    """Example 5: Programmatic configuration with direct parameters"""
    print("🚀 Example 5: Programmatic Configuration")
    
    # Create configuration programmatically
    config = SharedInfrastructureConfig(
        # S3 settings
        aws_s3_bucket_name="programmatic-bucket",
        aws_s3_region="us-west-1",
        aws_s3_endpoint_url="https://s3.us-west-1.amazonaws.com",
        aws_s3_use_ssl=True,
        
        # Application settings
        environment="production",
        debug=False,
        log_level="WARNING",
        
        # Database settings
        database_url="postgresql://prod-db:5432/myapp",
        
        # Custom settings
        my_custom_setting="custom-value"
    )
    
    print(f"   💻 Programmatic - S3 Bucket: {config.aws_s3_bucket_name}")
    print(f"   💻 Programmatic - Environment: {config.environment}")
    print(f"   💻 Programmatic - Custom: {getattr(config, 'my_custom_setting', 'N/A')}")
    print()


def example_6_global_configuration():
    """Example 6: Global configuration management"""
    print("🚀 Example 6: Global Configuration Management")
    
    # Set a global configuration
    global_config = SharedInfrastructureConfig.for_development(
        s3_bucket="global-dev-bucket"
    )
    set_global_config(global_config)
    
    # Any component can now get the global config
    retrieved_config = get_shared_config()
    print(f"   🌍 Global - S3 Bucket: {retrieved_config.aws_s3_bucket_name}")
    
    # S3 client will automatically use global config if no config provided
    s3_client = S3Client()  # No config parameter needed!
    print(f"   🌍 S3 Client uses global bucket: {s3_client.config.bucket_name}")
    print()


def example_7_s3_specific_configuration():
    """Example 7: S3-specific configuration patterns"""
    print("🚀 Example 7: S3-Specific Configuration Patterns")
    
    # Method 1: S3Config factory methods
    dev_s3_config = S3Config.for_development("dev-bucket")
    test_s3_config = S3Config.for_testing("test-bucket")
    prod_s3_config = S3Config.for_production("prod-bucket", "us-east-1")
    
    print(f"   🔧 Dev S3 - Endpoint: {dev_s3_config.endpoint_url}")
    print(f"   🧪 Test S3 - SSL: {test_s3_config.use_ssl}")
    print(f"   🚀 Prod S3 - Region: {prod_s3_config.region}")
    
    # Method 2: Direct S3Config creation
    custom_s3_config = S3Config(
        bucket_name="custom-bucket",
        region="eu-west-1",
        access_key_id="custom-key",
        secret_access_key="custom-secret",
        endpoint_url="https://custom-s3-endpoint.com",
        use_ssl=True
    )
    
    # Use with S3 client
    s3_client = S3Client(custom_s3_config)
    print(f"   🛠️ Custom S3 - Bucket: {s3_client.config.bucket_name}")
    print()


def example_8_legacy_compatibility():
    """Example 8: Legacy compatibility for existing deployments"""
    print("🚀 Example 8: Legacy Compatibility")
    
    # For existing deployments that rely on .env.shared.* files
    # This looks for .env.shared.local and .env.shared.aws in parent directories
    try:
        legacy_config = SharedInfrastructureConfig.with_legacy_files()
        print(f"   📜 Legacy - Would load from .env.shared.* files if they exist")
        print(f"   📜 Legacy - S3 Bucket: {legacy_config.aws_s3_bucket_name or 'Not configured'}")
    except Exception as e:
        print(f"   📜 Legacy - No legacy files found (expected): {type(e).__name__}")
    
    print()


def example_9_configuration_validation():
    """Example 9: Configuration validation and error handling"""
    print("🚀 Example 9: Configuration Validation")
    
    # Valid configuration
    valid_config = SharedInfrastructureConfig.for_development(s3_bucket="valid-bucket")
    print(f"   ✅ Valid - Has S3 config: {valid_config.has_s3_config()}")
    
    # Configuration without S3 bucket
    no_s3_config = SharedInfrastructureConfig(environment="development")
    print(f"   ❌ No S3 - Has S3 config: {no_s3_config.has_s3_config()}")
    
    # Try to create S3 client with invalid config
    try:
        S3Client(no_s3_config)
    except ValueError as e:
        print(f"   ⚠️ Expected error: {str(e)[:60]}...")
    
    print()


def example_10_real_world_usage():
    """Example 10: Real-world usage patterns for different scenarios"""
    print("🚀 Example 10: Real-World Usage Patterns")
    
    print("   🏠 Local Development:")
    local_config = (ConfigurationBuilder()
                   .for_environment("development")
                   .with_s3("my-local-bucket", endpoint="http://localhost:9000", use_ssl=False)
                   .build())
    print(f"      - S3 Endpoint: {local_config.aws_s3_endpoint_url}")
    
    print("   🔬 Testing Environment:")
    test_config = create_testing_config("test-bucket")
    print(f"      - Environment: {test_config.environment}")
    
    print("   🌟 Staging Environment:")
    staging_config = SharedInfrastructureConfig(
        environment="staging",
        aws_s3_bucket_name="staging-bucket",
        aws_s3_region="us-east-2",
        debug=False,
        log_level="INFO"
    )
    print(f"      - Debug mode: {staging_config.debug}")
    
    print("   🚀 Production Environment:")
    prod_config = create_production_config("prod-bucket", "us-east-1")
    print(f"      - SSL enabled: {prod_config.aws_s3_use_ssl}")
    
    print()


def main():
    """Run all configuration examples"""
    print("🎯 WeKare Shared Package - Configuration Examples")
    print("=" * 60)
    
    example_1_environment_variables()
    example_2_factory_methods()
    example_3_builder_pattern()
    example_4_env_file_configuration()
    example_5_programmatic_configuration()
    example_6_global_configuration()
    example_7_s3_specific_configuration()
    example_8_legacy_compatibility()
    example_9_configuration_validation()
    example_10_real_world_usage()
    
    print("🎉 All configuration examples completed!")
    print("\n📝 Key Benefits of the New Configuration System:")
    print("✅ No dependency on external files for development")
    print("✅ Multiple initialization methods for flexibility")
    print("✅ Clear error messages with helpful suggestions")
    print("✅ Builder pattern for fluent configuration")
    print("✅ Factory methods for common environments")
    print("✅ Backward compatibility with legacy systems")
    print("✅ Easy S3 configuration for all environments")
    print("\n📚 Choose the method that best fits your use case!")


if __name__ == "__main__":
    main() 