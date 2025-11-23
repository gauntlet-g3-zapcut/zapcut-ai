"""Unit tests for Supabase S3 storage helper."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import io
from botocore.exceptions import ClientError
from app.services.storage import (
    get_s3_client,
    build_public_url,
    upload_bytes,
    delete_object,
    delete_object_by_url
)


class TestGetS3Client:
    """Test S3 client initialization."""
    
    @patch('app.services.storage.boto3')
    @patch('app.services.storage.settings')
    def test_get_s3_client_creates_client(self, mock_settings, mock_boto3):
        """Test that get_s3_client creates a new client when none exists."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co/storage/v1"
        mock_settings.SUPABASE_S3_ACCESS_KEY = "test_access_key"
        mock_settings.SUPABASE_S3_SECRET_KEY = "test_secret_key"
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        # Clear the global cache
        import app.services.storage
        app.services.storage._s3_client = None
        
        client = get_s3_client()
        
        assert client == mock_client
        mock_boto3.client.assert_called_once_with(
            's3',
            endpoint_url="https://test.supabase.co/storage/v1",
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
            region_name='us-east-1'
        )
    
    @patch('app.services.storage.settings')
    def test_get_s3_client_raises_on_missing_credentials(self, mock_settings):
        """Test that get_s3_client raises ValueError when credentials are missing."""
        mock_settings.SUPABASE_S3_ENDPOINT = None
        mock_settings.SUPABASE_S3_ACCESS_KEY = None
        mock_settings.SUPABASE_S3_SECRET_KEY = None
        
        # Clear the global cache
        import app.services.storage
        app.services.storage._s3_client = None
        
        with pytest.raises(ValueError, match="Supabase S3 credentials not configured"):
            get_s3_client()


class TestBuildPublicUrl:
    """Test public URL building."""
    
    @patch('app.services.storage.settings')
    def test_build_public_url_with_storage_path(self, mock_settings):
        """Test building public URL when endpoint contains /storage/v1."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co/storage/v1"
        
        url = build_public_url("videos", "campaign-123/scene-1/video.mp4")
        
        assert url == "https://test.supabase.co/storage/v1/object/public/videos/campaign-123/scene-1/video.mp4"
    
    @patch('app.services.storage.settings')
    def test_build_public_url_without_storage_path(self, mock_settings):
        """Test building public URL when endpoint doesn't contain /storage/v1."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co"
        
        url = build_public_url("videos", "campaign-123/scene-1/video.mp4")
        
        assert url == "https://test.supabase.co/storage/v1/object/public/videos/campaign-123/scene-1/video.mp4"
    
    @patch('app.services.storage.settings')
    def test_build_public_url_strips_trailing_slash(self, mock_settings):
        """Test that trailing slashes are stripped from endpoint."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co/storage/v1/"
        
        url = build_public_url("videos", "video.mp4")
        
        assert url == "https://test.supabase.co/storage/v1/object/public/videos/video.mp4"


class TestUploadBytes:
    """Test upload_bytes function."""
    
    @patch('app.services.storage.get_s3_client')
    @patch('app.services.storage.settings')
    @patch('app.services.storage.io.BytesIO')
    def test_upload_bytes_success(self, mock_bytesio, mock_settings, mock_get_client):
        """Test successful upload."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co/storage/v1"
        mock_settings.SUPABASE_S3_VIDEO_BUCKET = "videos"
        mock_settings.SUPABASE_S3_ACCESS_KEY = "test_key"
        mock_settings.SUPABASE_S3_SECRET_KEY = "test_secret"
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_file = Mock()
        mock_bytesio.return_value = mock_file
        
        # Mock build_public_url
        with patch('app.services.storage.build_public_url', return_value="https://test.supabase.co/storage/v1/object/public/videos/test.mp4"):
            url = upload_bytes("videos", "test.mp4", b"test data", "video/mp4")
        
        assert url == "https://test.supabase.co/storage/v1/object/public/videos/test.mp4"
        mock_client.upload_fileobj.assert_called_once()
        call_args = mock_client.upload_fileobj.call_args
        assert call_args[1]['Bucket'] == "videos"
        assert call_args[1]['Key'] == "test.mp4"
        assert call_args[1]['ExtraArgs']['ContentType'] == "video/mp4"
        assert call_args[1]['ExtraArgs']['ACL'] == "public-read"
    
    @patch('app.services.storage.get_s3_client')
    @patch('app.services.storage.settings')
    @patch('app.services.storage.time.sleep')
    def test_upload_bytes_retries_on_client_error(self, mock_sleep, mock_settings, mock_get_client):
        """Test that upload_bytes retries on ClientError."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co/storage/v1"
        mock_settings.SUPABASE_S3_VIDEO_BUCKET = "videos"
        mock_settings.SUPABASE_S3_ACCESS_KEY = "test_key"
        mock_settings.SUPABASE_S3_SECRET_KEY = "test_secret"
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # First call raises ClientError, second succeeds
        error_response = {
            'Error': {
                'Code': 'ServiceUnavailable',
                'Message': 'Service temporarily unavailable'
            }
        }
        mock_client.upload_fileobj.side_effect = [
            ClientError(error_response, 'upload_fileobj'),
            None  # Success on retry
        ]
        
        with patch('app.services.storage.build_public_url', return_value="https://test.supabase.co/storage/v1/object/public/videos/test.mp4"):
            url = upload_bytes("videos", "test.mp4", b"test data", "video/mp4")
        
        assert url == "https://test.supabase.co/storage/v1/object/public/videos/test.mp4"
        assert mock_client.upload_fileobj.call_count == 2
        mock_sleep.assert_called_once_with(1)  # First retry delay
    
    @patch('app.services.storage.get_s3_client')
    @patch('app.services.storage.settings')
    @patch('app.services.storage.time.sleep')
    def test_upload_bytes_raises_after_max_retries(self, mock_sleep, mock_settings, mock_get_client):
        """Test that upload_bytes raises exception after max retries."""
        mock_settings.SUPABASE_S3_ENDPOINT = "https://test.supabase.co/storage/v1"
        mock_settings.SUPABASE_S3_VIDEO_BUCKET = "videos"
        mock_settings.SUPABASE_S3_ACCESS_KEY = "test_key"
        mock_settings.SUPABASE_S3_SECRET_KEY = "test_secret"
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # All calls raise ClientError
        error_response = {
            'Error': {
                'Code': 'ServiceUnavailable',
                'Message': 'Service temporarily unavailable'
            }
        }
        mock_client.upload_fileobj.side_effect = ClientError(error_response, 'upload_fileobj')
        
        with pytest.raises(Exception, match="Failed to upload to S3 after 3 attempts"):
            upload_bytes("videos", "test.mp4", b"test data", "video/mp4")
        
        assert mock_client.upload_fileobj.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries


class TestDeleteObject:
    """Test delete_object function."""
    
    @patch('app.services.storage.get_s3_client')
    def test_delete_object_success(self, mock_get_client):
        """Test successful deletion."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        result = delete_object("videos", "test.mp4")
        
        assert result is True
        mock_client.delete_object.assert_called_once_with(Bucket="videos", Key="test.mp4")
    
    @patch('app.services.storage.get_s3_client')
    def test_delete_object_handles_client_error(self, mock_get_client):
        """Test that delete_object handles ClientError gracefully."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        error_response = {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'The specified key does not exist'
            }
        }
        mock_client.delete_object.side_effect = ClientError(error_response, 'delete_object')
        
        result = delete_object("videos", "nonexistent.mp4")
        
        assert result is False
    
    def test_delete_object_skips_empty_key(self):
        """Test that delete_object returns False for empty key."""
        result = delete_object("videos", "")
        assert result is False


class TestDeleteObjectByUrl:
    """Test delete_object_by_url function."""
    
    @patch('app.services.storage.delete_object')
    def test_delete_object_by_url_success(self, mock_delete_object):
        """Test successful deletion by URL."""
        mock_delete_object.return_value = True
        
        url = "https://test.supabase.co/storage/v1/object/public/videos/campaign-123/scene-1/video.mp4"
        result = delete_object_by_url(url)
        
        assert result is True
        mock_delete_object.assert_called_once_with("videos", "campaign-123/scene-1/video.mp4")
    
    def test_delete_object_by_url_handles_invalid_url(self):
        """Test that delete_object_by_url handles invalid URLs."""
        result = delete_object_by_url("https://invalid-url.com/file.mp4")
        assert result is False
    
    def test_delete_object_by_url_skips_placeholder(self):
        """Test that delete_object_by_url skips placeholder URLs."""
        result = delete_object_by_url("https://placehold.co/300x200")
        assert result is True

