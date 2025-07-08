#!/usr/bin/env python3
"""
Example usage of WeKare Shared S3 Storage functionality

This script demonstrates how to use the S3 storage capabilities
provided by the shared package.

Note: This example assumes the shared package is installed in your Python environment.
If running from within the shared package directory, you may need to adjust imports.
"""

import os
import tempfile
from pathlib import Path

# Import S3 functionality from the shared package
# In a real microservice, you would install the shared package and import like this:
# from shared.storage.s3_client import S3Client, S3Config, get_s3_client
# from shared.storage.s3_client import upload_file_to_s3, download_file_from_s3
# from shared.config.base_config import SharedInfrastructureConfig

# For this example (running from within the shared package directory):
import sys
sys.path.insert(0, '.')
from shared.storage.s3_client import S3Client, S3Config, get_s3_client
from shared.storage.s3_client import upload_file_to_s3, download_file_from_s3
from shared.config.base_config import SharedInfrastructureConfig


def example_1_basic_usage():
    """Example 1: Basic S3 operations with custom configuration"""
    print("🚀 Example 1: Basic S3 operations with custom configuration")
    
    # Create S3 configuration
    config = S3Config(
        bucket_name="my-app-bucket",
        region="us-west-2",
        access_key_id="your-access-key",
        secret_access_key="your-secret-key"
    )
    
    # Create S3 client
    s3_client = S3Client(config)
    
    # Example operations (these would work with real AWS credentials)
    print(f"   📦 Bucket: {s3_client.config.bucket_name}")
    print(f"   🌍 Region: {s3_client.config.region}")
    
    # Create a temporary file for demonstration
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write("Hello, S3! This is a test file.")
        tmp_file_path = tmp_file.name
    
    try:
        # Upload file (would work with real credentials)
        s3_key = "documents/test-file.txt"
        print(f"   📤 Would upload: {tmp_file_path} → s3://{config.bucket_name}/{s3_key}")
        
        # Check if object exists (would work with real credentials)
        print(f"   🔍 Would check existence of: s3://{config.bucket_name}/{s3_key}")
        
        # Download file (would work with real credentials)
        download_path = "downloaded_file.txt"
        print(f"   📥 Would download: s3://{config.bucket_name}/{s3_key} → {download_path}")
        
        # List objects (would work with real credentials)
        print(f"   📋 Would list objects with prefix: documents/")
        
        # Generate presigned URL (would work with real credentials)
        print(f"   🔗 Would generate presigned URL for: s3://{config.bucket_name}/{s3_key}")
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
    print("   ✅ Basic usage example completed\n")


def example_2_shared_config_usage():
    """Example 2: Using shared configuration from environment"""
    print("🚀 Example 2: Using shared configuration from environment")
    
    # Set environment variables (in real usage, these would be set externally)
    os.environ.update({
        "AWS_S3_BUCKET_NAME": "wekare-shared-bucket",
        "AWS_S3_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "your-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "your-secret-access-key"
    })
    
    # Create shared configuration
    shared_config = SharedInfrastructureConfig()
    
    # Create S3 client using shared config
    s3_client = get_s3_client(shared_config)
    
    print(f"   📦 Configured bucket: {s3_client.config.bucket_name}")
    print(f"   🌍 Configured region: {s3_client.config.region}")
    print("   ✅ Shared configuration example completed\n")


def example_3_convenience_functions():
    """Example 3: Using convenience functions for simple operations"""
    print("🚀 Example 3: Using convenience functions for simple operations")
    
    # Set up configuration
    config = S3Config(
        bucket_name="my-convenience-bucket",
        region="us-west-2",
        access_key_id="your-access-key",
        secret_access_key="your-secret-key"
    )
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
        tmp_file.write("Convenience function test content")
        tmp_file_path = tmp_file.name
    
    try:
        # Upload using convenience function
        s3_key = "convenience/test-file.txt"
        print(f"   📤 Would upload using convenience function: {tmp_file_path} → s3://{config.bucket_name}/{s3_key}")
        
        # Download using convenience function
        download_path = "convenience_download.txt"
        print(f"   📥 Would download using convenience function: s3://{config.bucket_name}/{s3_key} → {download_path}")
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)
        
    print("   ✅ Convenience functions example completed\n")


def example_4_advanced_operations():
    """Example 4: Advanced S3 operations"""
    print("🚀 Example 4: Advanced S3 operations")
    
    config = S3Config(
        bucket_name="advanced-operations-bucket",
        region="us-west-2",
        access_key_id="your-access-key",
        secret_access_key="your-secret-key"
    )
    
    s3_client = S3Client(config)
    
    # Advanced operations examples
    print("   🔍 Advanced operations that would be available:")
    print("   • Upload with metadata and content type")
    print("   • Copy objects between S3 locations")
    print("   • Generate presigned URLs for temporary access")
    print("   • List objects with prefix filtering")
    print("   • Upload/download file-like objects (BytesIO)")
    print("   • Batch operations on multiple files")
    print("   ✅ Advanced operations example completed\n")


def example_5_error_handling():
    """Example 5: Error handling and configuration validation"""
    print("🚀 Example 5: Error handling and configuration validation")
    
    try:
        # Try to create config without required bucket name
        shared_config = SharedInfrastructureConfig()
        # This will fail if AWS_S3_BUCKET_NAME is not set
        s3_config = S3Config.from_shared_config(shared_config)
        print("   ⚠️ This would fail without AWS_S3_BUCKET_NAME environment variable")
    except ValueError as e:
        print(f"   ✅ Proper error handling: {e}")
    
    # Example of proper error handling in real usage
    print("   📝 In real usage, you should:")
    print("   • Check configuration before creating S3 client")
    print("   • Handle AWS credential errors gracefully")
    print("   • Validate bucket existence before operations")
    print("   • Use try/except blocks for all S3 operations")
    print("   ✅ Error handling example completed\n")


def main():
    """Run all examples"""
    print("🎯 WeKare Shared S3 Storage - Usage Examples")
    print("=" * 50)
    
    example_1_basic_usage()
    example_2_shared_config_usage()
    example_3_convenience_functions()
    example_4_advanced_operations()
    example_5_error_handling()
    
    print("🎉 All examples completed!")
    print("\n📝 Next steps:")
    print("1. Set your AWS credentials (environment variables or IAM roles)")
    print("2. Configure your S3 bucket name in environment variables")
    print("3. Start using the S3 functionality in your services")
    print("\n📚 For more information, see the README.md file")


if __name__ == "__main__":
    main() 