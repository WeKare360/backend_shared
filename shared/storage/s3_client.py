"""
AWS S3 Storage Client for WeKare Shared Infrastructure

Provides a comprehensive S3 client with read/write capabilities, 
configurable settings, and proper error handling.
"""

import os
import boto3
from typing import Optional, Dict, Any, BinaryIO, Union, List
from botocore.exceptions import ClientError, NoCredentialsError
from dataclasses import dataclass
from pathlib import Path
import logging
import structlog
from shared.config.base_config import SharedInfrastructureConfig

# Set up logging
logger = structlog.get_logger("shared.storage.s3_client")

@dataclass
class S3Config:
    """S3 Configuration dataclass"""
    bucket_name: str
    region: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    use_ssl: bool = True
    signature_version: str = "s3v4"
    
    @classmethod
    def from_shared_config(cls, config: Optional[SharedInfrastructureConfig] = None) -> "S3Config":
        """Create S3Config from SharedInfrastructureConfig"""
        if config is None:
            from shared.config.base_config import get_shared_config
            config = get_shared_config()
            
        if not config.aws_s3_bucket_name:
            raise ValueError(
                "aws_s3_bucket_name must be configured. "
                "Set AWS_S3_BUCKET_NAME environment variable or use a configuration method like "
                "SharedInfrastructureConfig.for_development(s3_bucket='your-bucket')"
            )
            
        return cls(
            bucket_name=config.aws_s3_bucket_name,
            region=config.aws_s3_region or config.aws_region,
            access_key_id=config.aws_access_key_id,
            secret_access_key=config.aws_secret_access_key,
            endpoint_url=config.aws_s3_endpoint_url,
            use_ssl=config.aws_s3_use_ssl,
            signature_version=config.aws_s3_signature_version
        )
    
    @classmethod
    def for_development(cls, 
                       bucket_name: str,
                       endpoint_url: str = "http://localhost:9000",
                       region: str = "us-east-1") -> "S3Config":
        """Create S3Config for development with local S3 (MinIO) defaults"""
        return cls(
            bucket_name=bucket_name,
            region=region,
            endpoint_url=endpoint_url,
            use_ssl=False,
            signature_version="s3v4"
        )
    
    @classmethod
    def for_testing(cls, bucket_name: str = "test-bucket") -> "S3Config":
        """Create S3Config for testing"""
        return cls(
            bucket_name=bucket_name,
            region="us-east-1",
            endpoint_url="http://localhost:9000",
            use_ssl=False,
            signature_version="s3v4"
        )
    
    @classmethod
    def for_production(cls, 
                      bucket_name: str,
                      region: str = "us-east-2",
                      access_key_id: Optional[str] = None,
                      secret_access_key: Optional[str] = None) -> "S3Config":
        """Create S3Config for production"""
        return cls(
            bucket_name=bucket_name,
            region=region,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            use_ssl=True,
            signature_version="s3v4"
        )

class S3Client:
    """
    AWS S3 Client with comprehensive read/write capabilities
    
    Provides methods for uploading, downloading, listing, and managing S3 objects
    with proper error handling and logging.
    """
    
    def __init__(self, config: Union[S3Config, SharedInfrastructureConfig, None] = None):
        """Initialize S3 client with configuration"""
        if config is None:
            self.config = S3Config.from_shared_config()
        elif isinstance(config, SharedInfrastructureConfig):
            self.config = S3Config.from_shared_config(config)
        else:
            self.config = config
            
        self._client = None
        self._session = None
        
        logger.info("🪣 S3Client initialized", 
                   bucket=self.config.bucket_name,
                   region=self.config.region,
                   has_custom_endpoint=bool(self.config.endpoint_url))
    
    @property
    def client(self):
        """Lazy initialization of boto3 S3 client"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self):
        """Create boto3 S3 client with configuration"""
        try:
            # Create session with credentials if provided
            session_kwargs = {}
            if self.config.access_key_id and self.config.secret_access_key:
                session_kwargs.update({
                    "aws_access_key_id": self.config.access_key_id,
                    "aws_secret_access_key": self.config.secret_access_key
                })
                
            if self.config.region:
                session_kwargs["region_name"] = self.config.region
                
            self._session = boto3.Session(**session_kwargs)
            
            # Create S3 client
            client_kwargs = {
                "service_name": "s3",
                "use_ssl": self.config.use_ssl,
                "config": boto3.session.Config(
                    signature_version=self.config.signature_version
                )
            }
            
            if self.config.endpoint_url:
                client_kwargs["endpoint_url"] = self.config.endpoint_url
                
            client = self._session.client(**client_kwargs)
            
            logger.info("✅ S3 client created successfully", 
                       bucket=self.config.bucket_name,
                       region=self.config.region)
            
            return client
            
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            raise ValueError("AWS credentials not configured. Please set access keys or use IAM roles.")
        except Exception as e:
            logger.error("❌ Failed to create S3 client", error=str(e))
            raise ValueError(f"Failed to create S3 client: {str(e)}")
    
    def upload_file(self, file_path: Union[str, Path], s3_key: str, 
                   metadata: Optional[Dict[str, str]] = None,
                   content_type: Optional[str] = None) -> bool:
        """
        Upload a file to S3
        
        Args:
            file_path: Path to the local file to upload
            s3_key: S3 key (path) where the file will be stored
            metadata: Optional metadata to attach to the object
            content_type: Optional content type for the object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error("❌ File not found", file_path=str(file_path))
                return False
                
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata
            if content_type:
                extra_args["ContentType"] = content_type
                
            logger.info("📤 Uploading file to S3", 
                       file_path=str(file_path),
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
                       
            self.client.upload_file(
                str(file_path),
                self.config.bucket_name,
                s3_key,
                ExtraArgs=extra_args if extra_args else None
            )
            
            logger.info("✅ File uploaded successfully", 
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
            return True
            
        except FileNotFoundError:
            logger.error("❌ File not found", file_path=str(file_path))
            return False
        except ClientError as e:
            logger.error("❌ S3 upload failed", error=str(e), s3_key=s3_key)
            return False
        except Exception as e:
            logger.error("❌ Unexpected error during upload", error=str(e))
            return False
    
    def upload_fileobj(self, file_obj: BinaryIO, s3_key: str,
                      metadata: Optional[Dict[str, str]] = None,
                      content_type: Optional[str] = None) -> bool:
        """
        Upload a file-like object to S3
        
        Args:
            file_obj: File-like object to upload
            s3_key: S3 key (path) where the file will be stored
            metadata: Optional metadata to attach to the object
            content_type: Optional content type for the object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata
            if content_type:
                extra_args["ContentType"] = content_type
                
            logger.info("📤 Uploading file object to S3", 
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
                       
            self.client.upload_fileobj(
                file_obj,
                self.config.bucket_name,
                s3_key,
                ExtraArgs=extra_args if extra_args else None
            )
            
            logger.info("✅ File object uploaded successfully", 
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
            return True
            
        except ClientError as e:
            logger.error("❌ S3 upload failed", error=str(e), s3_key=s3_key)
            return False
        except Exception as e:
            logger.error("❌ Unexpected error during upload", error=str(e))
            return False
    
    def download_file(self, s3_key: str, local_path: Union[str, Path]) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 key (path) of the file to download
            local_path: Local path where the file will be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            local_path = Path(local_path)
            
            # Create parent directories if they don't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info("📥 Downloading file from S3", 
                       s3_key=s3_key,
                       local_path=str(local_path),
                       bucket=self.config.bucket_name)
                       
            self.client.download_file(
                self.config.bucket_name,
                s3_key,
                str(local_path)
            )
            
            logger.info("✅ File downloaded successfully", 
                       s3_key=s3_key,
                       local_path=str(local_path))
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.error("❌ File not found in S3", s3_key=s3_key)
            else:
                logger.error("❌ S3 download failed", error=str(e), s3_key=s3_key)
            return False
        except Exception as e:
            logger.error("❌ Unexpected error during download", error=str(e))
            return False
    
    def download_fileobj(self, s3_key: str, file_obj: BinaryIO) -> bool:
        """
        Download a file from S3 to a file-like object
        
        Args:
            s3_key: S3 key (path) of the file to download
            file_obj: File-like object to write to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("📥 Downloading file object from S3", 
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
                       
            self.client.download_fileobj(
                self.config.bucket_name,
                s3_key,
                file_obj
            )
            
            logger.info("✅ File object downloaded successfully", 
                       s3_key=s3_key)
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.error("❌ File not found in S3", s3_key=s3_key)
            else:
                logger.error("❌ S3 download failed", error=str(e), s3_key=s3_key)
            return False
        except Exception as e:
            logger.error("❌ Unexpected error during download", error=str(e))
            return False
    
    def get_object(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get object from S3 with metadata
        
        Args:
            s3_key: S3 key (path) of the object
            
        Returns:
            Dict with object data and metadata, None if not found
        """
        try:
            logger.info("🔍 Getting object from S3", 
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
                       
            response = self.client.get_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            
            result = {
                "Body": response["Body"].read(),
                "ContentType": response.get("ContentType"),
                "ContentLength": response.get("ContentLength"),
                "LastModified": response.get("LastModified"),
                "Metadata": response.get("Metadata", {}),
                "ETag": response.get("ETag")
            }
            
            logger.info("✅ Object retrieved successfully", 
                       s3_key=s3_key,
                       size=result["ContentLength"])
            return result
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning("⚠️ Object not found in S3", s3_key=s3_key)
            else:
                logger.error("❌ Failed to get object", error=str(e), s3_key=s3_key)
            return None
        except Exception as e:
            logger.error("❌ Unexpected error getting object", error=str(e))
            return None
    
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3
        
        Args:
            s3_key: S3 key (path) of the object to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🗑️ Deleting object from S3", 
                       s3_key=s3_key,
                       bucket=self.config.bucket_name)
                       
            self.client.delete_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            
            logger.info("✅ Object deleted successfully", s3_key=s3_key)
            return True
            
        except ClientError as e:
            logger.error("❌ Failed to delete object", error=str(e), s3_key=s3_key)
            return False
        except Exception as e:
            logger.error("❌ Unexpected error deleting object", error=str(e))
            return False
    
    def list_objects(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket
        
        Args:
            prefix: Prefix to filter objects by
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object metadata dictionaries
        """
        try:
            logger.info("📋 Listing objects in S3", 
                       prefix=prefix,
                       max_keys=max_keys,
                       bucket=self.config.bucket_name)
                       
            response = self.client.list_objects_v2(
                Bucket=self.config.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    objects.append({
                        "Key": obj["Key"],
                        "Size": obj["Size"],
                        "LastModified": obj["LastModified"],
                        "ETag": obj["ETag"],
                        "StorageClass": obj.get("StorageClass", "STANDARD")
                    })
            
            logger.info("✅ Listed objects successfully", 
                       count=len(objects),
                       prefix=prefix)
            return objects
            
        except ClientError as e:
            logger.error("❌ Failed to list objects", error=str(e), prefix=prefix)
            return []
        except Exception as e:
            logger.error("❌ Unexpected error listing objects", error=str(e))
            return []
    
    def object_exists(self, s3_key: str) -> bool:
        """
        Check if an object exists in S3
        
        Args:
            s3_key: S3 key (path) of the object to check
            
        Returns:
            bool: True if object exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error("❌ Error checking object existence", error=str(e), s3_key=s3_key)
                return False
        except Exception as e:
            logger.error("❌ Unexpected error checking object existence", error=str(e))
            return False
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600, 
                         http_method: str = "GET") -> Optional[str]:
        """
        Generate a presigned URL for S3 object access
        
        Args:
            s3_key: S3 key (path) of the object
            expiration: Time in seconds for the URL to remain valid
            http_method: HTTP method for the URL (GET, PUT, etc.)
            
        Returns:
            Presigned URL string or None if failed
        """
        try:
            method_map = {
                "GET": "get_object",
                "PUT": "put_object",
                "DELETE": "delete_object"
            }
            
            client_method = method_map.get(http_method.upper())
            if not client_method:
                logger.error("❌ Unsupported HTTP method", method=http_method)
                return None
            
            logger.info("🔗 Generating presigned URL", 
                       s3_key=s3_key,
                       method=http_method,
                       expiration=expiration)
                       
            url = self.client.generate_presigned_url(
                client_method,
                Params={"Bucket": self.config.bucket_name, "Key": s3_key},
                ExpiresIn=expiration
            )
            
            logger.info("✅ Presigned URL generated successfully", s3_key=s3_key)
            return url
            
        except ClientError as e:
            logger.error("❌ Failed to generate presigned URL", error=str(e), s3_key=s3_key)
            return None
        except Exception as e:
            logger.error("❌ Unexpected error generating presigned URL", error=str(e))
            return None
    
    def copy_object(self, source_key: str, destination_key: str, 
                   source_bucket: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Copy an object within S3
        
        Args:
            source_key: Source S3 key
            destination_key: Destination S3 key
            source_bucket: Source bucket (defaults to current bucket)
            metadata: New metadata for the copied object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if source_bucket is None:
                source_bucket = self.config.bucket_name
                
            copy_source = {
                "Bucket": source_bucket,
                "Key": source_key
            }
            
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata
                extra_args["MetadataDirective"] = "REPLACE"
                
            logger.info("📋 Copying object in S3", 
                       source_key=source_key,
                       destination_key=destination_key,
                       source_bucket=source_bucket,
                       dest_bucket=self.config.bucket_name)
                       
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=self.config.bucket_name,
                Key=destination_key,
                **extra_args
            )
            
            logger.info("✅ Object copied successfully", 
                       source_key=source_key,
                       destination_key=destination_key)
            return True
            
        except ClientError as e:
            logger.error("❌ Failed to copy object", error=str(e), 
                        source_key=source_key, destination_key=destination_key)
            return False
        except Exception as e:
            logger.error("❌ Unexpected error copying object", error=str(e))
            return False


# Convenience functions for easy access
def get_s3_client(config: Optional[Union[S3Config, SharedInfrastructureConfig]] = None) -> S3Client:
    """Get an S3 client instance"""
    return S3Client(config)

def upload_file_to_s3(file_path: Union[str, Path], s3_key: str, 
                     config: Optional[Union[S3Config, SharedInfrastructureConfig]] = None,
                     metadata: Optional[Dict[str, str]] = None,
                     content_type: Optional[str] = None) -> bool:
    """Convenience function to upload a file to S3"""
    client = get_s3_client(config)
    return client.upload_file(file_path, s3_key, metadata, content_type)

def download_file_from_s3(s3_key: str, local_path: Union[str, Path],
                         config: Optional[Union[S3Config, SharedInfrastructureConfig]] = None) -> bool:
    """Convenience function to download a file from S3"""
    client = get_s3_client(config)
    return client.download_file(s3_key, local_path) 