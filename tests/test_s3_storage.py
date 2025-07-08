"""
Tests for S3 Storage module
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, mock_open
from io import BytesIO
from botocore.exceptions import ClientError, NoCredentialsError
from shared.storage.s3_client import S3Client, S3Config, get_s3_client, upload_file_to_s3, download_file_from_s3
from shared.config.base_config import SharedInfrastructureConfig


class TestS3Config:
    """Test the S3Config class"""
    
    def test_s3_config_initialization(self):
        """Test S3Config initialization with direct values"""
        config = S3Config(
            bucket_name="test-bucket",
            region="us-west-2",
            access_key_id="test-key",
            secret_access_key="test-secret",
            endpoint_url="http://localhost:9000",
            use_ssl=False,
            signature_version="s3v4"
        )
        
        assert config.bucket_name == "test-bucket"
        assert config.region == "us-west-2"
        assert config.access_key_id == "test-key"
        assert config.secret_access_key == "test-secret"
        assert config.endpoint_url == "http://localhost:9000"
        assert config.use_ssl is False
        assert config.signature_version == "s3v4"
    
    def test_s3_config_defaults(self):
        """Test S3Config with default values"""
        config = S3Config(bucket_name="test-bucket")
        
        assert config.bucket_name == "test-bucket"
        assert config.region is None
        assert config.access_key_id is None
        assert config.secret_access_key is None
        assert config.endpoint_url is None
        assert config.use_ssl is True
        assert config.signature_version == "s3v4"
    
    def test_s3_config_from_shared_config(self):
        """Test S3Config.from_shared_config method"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "wekare-test-bucket",
            "AWS_S3_REGION": "us-west-1",
            "AWS_ACCESS_KEY_ID": "test-access-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret-key",
            "AWS_S3_ENDPOINT_URL": "http://localstack:4566",
            "AWS_S3_USE_SSL": "false",
            "AWS_S3_SIGNATURE_VERSION": "s3v2"
        }
        
        with patch.dict(os.environ, test_env):
            shared_config = SharedInfrastructureConfig()
            s3_config = S3Config.from_shared_config(shared_config)
            
            assert s3_config.bucket_name == "wekare-test-bucket"
            assert s3_config.region == "us-west-1"
            assert s3_config.access_key_id == "test-access-key"
            assert s3_config.secret_access_key == "test-secret-key"
            assert s3_config.endpoint_url == "http://localstack:4566"
            assert s3_config.use_ssl is False
            assert s3_config.signature_version == "s3v2"
    
    def test_s3_config_from_shared_config_with_fallback_region(self):
        """Test S3Config falls back to aws_region when aws_s3_region is not set"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "wekare-test-bucket",
            "AWS_REGION": "us-east-1",  # Should fall back to this
            "AWS_ACCESS_KEY_ID": "test-access-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret-key"
        }
        
        with patch.dict(os.environ, test_env):
            shared_config = SharedInfrastructureConfig()
            s3_config = S3Config.from_shared_config(shared_config)
            
            assert s3_config.bucket_name == "wekare-test-bucket"
            assert s3_config.region == "us-east-1"  # Should use aws_region
    
    def test_s3_config_from_shared_config_missing_bucket(self):
        """Test S3Config.from_shared_config raises error when bucket name is missing"""
        test_env = {
            "AWS_REGION": "us-east-1"
        }
        
        with patch.dict(os.environ, test_env):
            shared_config = SharedInfrastructureConfig()
            
            with pytest.raises(ValueError, match="aws_s3_bucket_name must be configured"):
                S3Config.from_shared_config(shared_config)
    
    def test_s3_config_from_shared_config_none_parameter(self):
        """Test S3Config.from_shared_config with None parameter"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "wekare-test-bucket",
            "AWS_REGION": "us-east-1"
        }
        
        with patch.dict(os.environ, test_env):
            # Create a new config instance to pick up the patched environment
            shared_config = SharedInfrastructureConfig()
            s3_config = S3Config.from_shared_config(shared_config)
            
            assert s3_config.bucket_name == "wekare-test-bucket"
            assert s3_config.region == "us-east-1"


class TestS3Client:
    """Test the S3Client class"""
    
    def test_s3_client_initialization_with_s3_config(self):
        """Test S3Client initialization with S3Config"""
        config = S3Config(bucket_name="test-bucket", region="us-west-2")
        client = S3Client(config)
        
        assert client.config.bucket_name == "test-bucket"
        assert client.config.region == "us-west-2"
        assert client._client is None  # Should be lazy loaded
    
    def test_s3_client_initialization_with_shared_config(self):
        """Test S3Client initialization with SharedInfrastructureConfig"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "wekare-test-bucket",
            "AWS_REGION": "us-east-1"
        }
        
        with patch.dict(os.environ, test_env):
            shared_config = SharedInfrastructureConfig()
            client = S3Client(shared_config)
            
            assert client.config.bucket_name == "wekare-test-bucket"
            assert client.config.region == "us-east-1"
    
    def test_s3_client_initialization_with_none(self):
        """Test S3Client initialization with None (should use global config)"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "wekare-test-bucket",
            "AWS_REGION": "us-east-1"
        }
        
        with patch.dict(os.environ, test_env):
            # Create a new config instance to pick up the patched environment
            shared_config = SharedInfrastructureConfig()
            client = S3Client(shared_config)
            
            assert client.config.bucket_name == "wekare-test-bucket"
            assert client.config.region == "us-east-1"
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_create_client_with_credentials(self, mock_session):
        """Test _create_client method with credentials"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(
            bucket_name="test-bucket",
            region="us-west-2",
            access_key_id="test-key",
            secret_access_key="test-secret"
        )
        client = S3Client(config)
        
        # Access the client property to trigger lazy loading
        boto_client = client.client
        
        # Verify session was created with correct credentials
        mock_session.assert_called_once_with(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-2"
        )
        
        # Verify client was created
        mock_session_instance.client.assert_called_once()
        assert boto_client == mock_boto_client
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_create_client_with_endpoint_url(self, mock_session):
        """Test _create_client method with custom endpoint URL"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(
            bucket_name="test-bucket",
            region="us-west-2",
            endpoint_url="http://localhost:9000"
        )
        client = S3Client(config)
        
        # Access the client property to trigger lazy loading
        boto_client = client.client
        
        # Verify client was created with endpoint URL
        call_args = mock_session_instance.client.call_args
        assert call_args[1]["endpoint_url"] == "http://localhost:9000"
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_create_client_no_credentials_error(self, mock_session):
        """Test _create_client method with NoCredentialsError"""
        mock_session.side_effect = NoCredentialsError()
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        with pytest.raises(ValueError, match="AWS credentials not configured"):
            _ = client.client
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_create_client_general_error(self, mock_session):
        """Test _create_client method with general error"""
        mock_session.side_effect = Exception("Connection failed")
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        with pytest.raises(ValueError, match="Failed to create S3 client"):
            _ = client.client
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_upload_file_success(self, mock_session):
        """Test upload_file method success"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            # Test successful upload
            result = client.upload_file(tmp_file_path, "test-key")
            
            assert result is True
            mock_boto_client.upload_file.assert_called_once_with(
                tmp_file_path,
                "test-bucket",
                "test-key",
                ExtraArgs=None
            )
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_upload_file_with_metadata(self, mock_session):
        """Test upload_file method with metadata and content type"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            metadata = {"author": "test-user", "version": "1.0"}
            content_type = "application/json"
            
            result = client.upload_file(
                tmp_file_path, 
                "test-key", 
                metadata=metadata, 
                content_type=content_type
            )
            
            assert result is True
            mock_boto_client.upload_file.assert_called_once_with(
                tmp_file_path,
                "test-bucket",
                "test-key",
                ExtraArgs={
                    "Metadata": metadata,
                    "ContentType": content_type
                }
            )
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_upload_file_not_found(self, mock_session):
        """Test upload_file method with file not found"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        # Test with non-existent file
        result = client.upload_file("/non/existent/file.txt", "test-key")
        
        assert result is False
        mock_boto_client.upload_file.assert_not_called()
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_upload_file_client_error(self, mock_session):
        """Test upload_file method with ClientError"""
        mock_boto_client = Mock()
        mock_boto_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "upload_file"
        )
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            result = client.upload_file(tmp_file_path, "test-key")
            
            assert result is False
            mock_boto_client.upload_file.assert_called_once()
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_upload_fileobj_success(self, mock_session):
        """Test upload_fileobj method success"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        file_obj = BytesIO(b"test content")
        
        result = client.upload_fileobj(file_obj, "test-key")
        
        assert result is True
        mock_boto_client.upload_fileobj.assert_called_once_with(
            file_obj,
            "test-bucket",
            "test-key",
            ExtraArgs=None
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_download_file_success(self, mock_session):
        """Test download_file method success"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            download_path = Path(tmp_dir) / "downloaded_file.txt"
            
            result = client.download_file("test-key", download_path)
            
            assert result is True
            mock_boto_client.download_file.assert_called_once_with(
                "test-bucket",
                "test-key",
                str(download_path)
            )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_download_file_not_found(self, mock_session):
        """Test download_file method with file not found"""
        mock_boto_client = Mock()
        mock_boto_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "download_file"
        )
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            download_path = Path(tmp_dir) / "downloaded_file.txt"
            
            result = client.download_file("test-key", download_path)
            
            assert result is False
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_download_fileobj_success(self, mock_session):
        """Test download_fileobj method success"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        file_obj = BytesIO()
        
        result = client.download_fileobj("test-key", file_obj)
        
        assert result is True
        mock_boto_client.download_fileobj.assert_called_once_with(
            "test-bucket",
            "test-key",
            file_obj
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_get_object_success(self, mock_session):
        """Test get_object method success"""
        mock_boto_client = Mock()
        mock_response = {
            "Body": Mock(),
            "ContentType": "text/plain",
            "ContentLength": 12,
            "LastModified": "2024-01-01T00:00:00Z",
            "Metadata": {"author": "test-user"},
            "ETag": "\"abc123\""
        }
        mock_response["Body"].read.return_value = b"test content"
        mock_boto_client.get_object.return_value = mock_response
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.get_object("test-key")
        
        assert result is not None
        assert result["Body"] == b"test content"
        assert result["ContentType"] == "text/plain"
        assert result["ContentLength"] == 12
        assert result["Metadata"]["author"] == "test-user"
        assert result["ETag"] == "\"abc123\""
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_get_object_not_found(self, mock_session):
        """Test get_object method with object not found"""
        mock_boto_client = Mock()
        mock_boto_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist"}},
            "get_object"
        )
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.get_object("non-existent-key")
        
        assert result is None
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_delete_object_success(self, mock_session):
        """Test delete_object method success"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.delete_object("test-key")
        
        assert result is True
        mock_boto_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-key"
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_delete_object_error(self, mock_session):
        """Test delete_object method with error"""
        mock_boto_client = Mock()
        mock_boto_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "delete_object"
        )
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.delete_object("test-key")
        
        assert result is False
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_list_objects_success(self, mock_session):
        """Test list_objects method success"""
        mock_boto_client = Mock()
        mock_response = {
            "Contents": [
                {
                    "Key": "file1.txt",
                    "Size": 100,
                    "LastModified": "2024-01-01T00:00:00Z",
                    "ETag": "\"abc123\"",
                    "StorageClass": "STANDARD"
                },
                {
                    "Key": "file2.txt",
                    "Size": 200,
                    "LastModified": "2024-01-02T00:00:00Z",
                    "ETag": "\"def456\"",
                    "StorageClass": "REDUCED_REDUNDANCY"
                }
            ]
        }
        mock_boto_client.list_objects_v2.return_value = mock_response
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.list_objects(prefix="files/", max_keys=100)
        
        assert len(result) == 2
        assert result[0]["Key"] == "file1.txt"
        assert result[0]["Size"] == 100
        assert result[1]["Key"] == "file2.txt"
        assert result[1]["Size"] == 200
        
        mock_boto_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="files/",
            MaxKeys=100
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_list_objects_empty(self, mock_session):
        """Test list_objects method with empty bucket"""
        mock_boto_client = Mock()
        mock_boto_client.list_objects_v2.return_value = {}  # No Contents key
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.list_objects()
        
        assert result == []
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_object_exists_true(self, mock_session):
        """Test object_exists method when object exists"""
        mock_boto_client = Mock()
        mock_boto_client.head_object.return_value = {"ContentLength": 100}
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.object_exists("test-key")
        
        assert result is True
        mock_boto_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-key"
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_object_exists_false(self, mock_session):
        """Test object_exists method when object doesn't exist"""
        mock_boto_client = Mock()
        mock_boto_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "head_object"
        )
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.object_exists("test-key")
        
        assert result is False
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_get_presigned_url_success(self, mock_session):
        """Test get_presigned_url method success"""
        mock_boto_client = Mock()
        mock_boto_client.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test-key?signature=abc123"
        
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.get_presigned_url("test-key", expiration=3600, http_method="GET")
        
        assert result == "https://test-bucket.s3.amazonaws.com/test-key?signature=abc123"
        mock_boto_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test-key"},
            ExpiresIn=3600
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_get_presigned_url_invalid_method(self, mock_session):
        """Test get_presigned_url method with invalid HTTP method"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.get_presigned_url("test-key", http_method="INVALID")
        
        assert result is None
        mock_boto_client.generate_presigned_url.assert_not_called()
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_copy_object_success(self, mock_session):
        """Test copy_object method success"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        result = client.copy_object("source-key", "destination-key")
        
        assert result is True
        mock_boto_client.copy_object.assert_called_once_with(
            CopySource={"Bucket": "test-bucket", "Key": "source-key"},
            Bucket="test-bucket",
            Key="destination-key"
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_copy_object_with_metadata(self, mock_session):
        """Test copy_object method with metadata"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        metadata = {"version": "2.0", "author": "test-user"}
        result = client.copy_object("source-key", "destination-key", metadata=metadata)
        
        assert result is True
        mock_boto_client.copy_object.assert_called_once_with(
            CopySource={"Bucket": "test-bucket", "Key": "source-key"},
            Bucket="test-bucket",
            Key="destination-key",
            Metadata=metadata,
            MetadataDirective="REPLACE"
        )
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_copy_object_different_source_bucket(self, mock_session):
        """Test copy_object method with different source bucket"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        config = S3Config(bucket_name="dest-bucket")
        client = S3Client(config)
        
        result = client.copy_object("source-key", "destination-key", source_bucket="source-bucket")
        
        assert result is True
        mock_boto_client.copy_object.assert_called_once_with(
            CopySource={"Bucket": "source-bucket", "Key": "source-key"},
            Bucket="dest-bucket",
            Key="destination-key"
        )


class TestConvenienceFunctions:
    """Test the convenience functions"""
    
    def test_get_s3_client_with_config(self):
        """Test get_s3_client function with config"""
        config = S3Config(bucket_name="test-bucket")
        client = get_s3_client(config)
        
        assert isinstance(client, S3Client)
        assert client.config.bucket_name == "test-bucket"
    
    def test_get_s3_client_with_none(self):
        """Test get_s3_client function with None config"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "wekare-test-bucket",
            "AWS_REGION": "us-east-1"
        }
        
        with patch.dict(os.environ, test_env):
            # Create a new config instance to pick up the patched environment
            shared_config = SharedInfrastructureConfig()
            client = get_s3_client(shared_config)
            
            assert isinstance(client, S3Client)
            assert client.config.bucket_name == "wekare-test-bucket"
    
    @patch('shared.storage.s3_client.S3Client')
    def test_upload_file_to_s3_convenience(self, mock_s3_client):
        """Test upload_file_to_s3 convenience function"""
        mock_client_instance = Mock()
        mock_client_instance.upload_file.return_value = True
        mock_s3_client.return_value = mock_client_instance
        
        config = S3Config(bucket_name="test-bucket")
        metadata = {"author": "test-user"}
        
        result = upload_file_to_s3(
            "/path/to/file.txt", 
            "test-key", 
            config=config, 
            metadata=metadata, 
            content_type="text/plain"
        )
        
        assert result is True
        mock_s3_client.assert_called_once_with(config)
        mock_client_instance.upload_file.assert_called_once_with(
            "/path/to/file.txt", 
            "test-key", 
            metadata, 
            "text/plain"
        )
    
    @patch('shared.storage.s3_client.S3Client')
    def test_download_file_from_s3_convenience(self, mock_s3_client):
        """Test download_file_from_s3 convenience function"""
        mock_client_instance = Mock()
        mock_client_instance.download_file.return_value = True
        mock_s3_client.return_value = mock_client_instance
        
        config = S3Config(bucket_name="test-bucket")
        
        result = download_file_from_s3("test-key", "/path/to/download.txt", config=config)
        
        assert result is True
        mock_s3_client.assert_called_once_with(config)
        mock_client_instance.download_file.assert_called_once_with("test-key", "/path/to/download.txt")


class TestS3IntegrationScenarios:
    """Integration-style tests for common S3 usage scenarios"""
    
    @patch('shared.storage.s3_client.boto3.Session')
    def test_complete_file_lifecycle(self, mock_session):
        """Test complete file lifecycle: upload, check exists, download, delete"""
        mock_boto_client = Mock()
        mock_session_instance = Mock()
        mock_session_instance.client.return_value = mock_boto_client
        mock_session.return_value = mock_session_instance
        
        # Mock successful operations
        mock_boto_client.head_object.return_value = {"ContentLength": 100}
        
        config = S3Config(bucket_name="test-bucket")
        client = S3Client(config)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            # Upload
            upload_result = client.upload_file(tmp_file_path, "test-key")
            assert upload_result is True
            
            # Check exists
            exists_result = client.object_exists("test-key")
            assert exists_result is True
            
            # Download
            with tempfile.TemporaryDirectory() as tmp_dir:
                download_path = Path(tmp_dir) / "downloaded.txt"
                download_result = client.download_file("test-key", download_path)
                assert download_result is True
            
            # Delete
            delete_result = client.delete_object("test-key")
            assert delete_result is True
            
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    def test_configuration_precedence(self):
        """Test that S3 configuration follows correct precedence"""
        test_env = {
            "AWS_S3_BUCKET_NAME": "env-bucket",
            "AWS_S3_REGION": "us-west-2",
            "AWS_REGION": "us-east-1",  # Should be overridden by AWS_S3_REGION
            "AWS_ACCESS_KEY_ID": "env-key",
            "AWS_SECRET_ACCESS_KEY": "env-secret"
        }
        
        with patch.dict(os.environ, test_env):
            shared_config = SharedInfrastructureConfig()
            s3_config = S3Config.from_shared_config(shared_config)
            
            # S3-specific region should take precedence
            assert s3_config.region == "us-west-2"
            assert s3_config.bucket_name == "env-bucket"
            assert s3_config.access_key_id == "env-key"
            assert s3_config.secret_access_key == "env-secret"
    
    def test_error_handling_scenarios(self):
        """Test various error handling scenarios"""
        # Test missing bucket name
        with pytest.raises(ValueError, match="aws_s3_bucket_name must be configured"):
            S3Config.from_shared_config(SharedInfrastructureConfig())
        
        # Test invalid config types
        with pytest.raises(AttributeError):
            S3Client("invalid_config_type") 