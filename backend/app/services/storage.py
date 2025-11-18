"""Reusable Supabase S3 storage helper."""
import io
import logging
import time
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s

# Memoized S3 client instance
_s3_client: Optional[boto3.client] = None


def get_s3_client():
    """Get or create memoized Supabase S3 client."""
    global _s3_client
    
    if _s3_client is None:
        if not all([
            settings.SUPABASE_S3_ENDPOINT,
            settings.SUPABASE_S3_ACCESS_KEY,
            settings.SUPABASE_S3_SECRET_KEY
        ]):
            raise ValueError("Supabase S3 credentials not configured")
        
        _s3_client = boto3.client(
            's3',
            endpoint_url=settings.SUPABASE_S3_ENDPOINT,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
            region_name='us-east-1'
        )
    
    return _s3_client


def build_public_url(bucket_name: str, file_key: str) -> str:
    """Build public URL for a Supabase S3 object.
    
    Args:
        bucket_name: S3 bucket name
        file_key: S3 object key
        
    Returns:
        Public URL string
    """
    endpoint = settings.SUPABASE_S3_ENDPOINT.rstrip('/')
    
    # If endpoint contains /storage/v1, extract the base URL
    if '/storage/v1' in endpoint:
        base_url = endpoint.split('/storage/v1')[0]
    else:
        # If endpoint is just the base URL, use it directly
        base_url = endpoint
    
    # Construct public URL
    # Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{key}
    return f"{base_url}/storage/v1/object/public/{bucket_name}/{file_key}"


def upload_bytes(
    bucket_name: str,
    file_key: str,
    data: bytes,
    content_type: str,
    acl: str = 'public-read'
) -> str:
    """Upload bytes to Supabase S3 storage with retry logic.
    
    Args:
        bucket_name: S3 bucket name
        file_key: S3 object key (file path)
        data: The file bytes to upload
        content_type: MIME type (e.g., 'video/mp4', 'audio/mpeg')
        acl: Access control level (default: 'public-read')
        
    Returns:
        Public URL of the uploaded file
        
    Raises:
        ValueError: If S3 credentials not configured
        Exception: If upload fails after all retries
    """
    if not all([
        settings.SUPABASE_S3_ENDPOINT,
        settings.SUPABASE_S3_ACCESS_KEY,
        settings.SUPABASE_S3_SECRET_KEY
    ]):
        raise ValueError("Supabase S3 credentials not configured")
    
    # Retry loop
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            s3_client = get_s3_client()
            
            logger.info(
                f"Uploading to S3 | bucket={bucket_name} | "
                f"key={file_key} | size={len(data)} bytes | "
                f"content_type={content_type} | attempt={attempt + 1}/{MAX_RETRIES}"
            )
            
            # Upload bytes
            data_file = io.BytesIO(data)
            s3_client.upload_fileobj(
                data_file,
                Bucket=bucket_name,
                Key=file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': acl
                }
            )
            
            # Build public URL
            public_url = build_public_url(bucket_name, file_key)
            
            logger.info(
                f"Upload successful | bucket={bucket_name} | "
                f"key={file_key} | url={public_url}"
            )
            
            return public_url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            last_error = e
            
            logger.error(
                f"S3 upload error | bucket={bucket_name} | key={file_key} | "
                f"attempt={attempt + 1}/{MAX_RETRIES} | code={error_code} | error={error_msg}"
            )
            
            # Retry if not the last attempt
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying upload in {delay}s...")
                time.sleep(delay)
            
        except Exception as e:
            last_error = e
            logger.error(
                f"Unexpected error uploading to S3 | bucket={bucket_name} | "
                f"key={file_key} | attempt={attempt + 1}/{MAX_RETRIES} | "
                f"error={str(e)}"
            )
            
            # Retry if not the last attempt
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying upload in {delay}s...")
                time.sleep(delay)
    
    # All retries failed
    error_msg = f"Failed to upload to S3 after {MAX_RETRIES} attempts: {str(last_error)}"
    logger.error(f"Upload failed permanently | bucket={bucket_name} | key={file_key}")
    raise Exception(error_msg)


def delete_object(bucket_name: str, file_key: str) -> bool:
    """Delete object from Supabase S3 storage.
    
    Args:
        bucket_name: S3 bucket name
        file_key: S3 object key
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    if not file_key:
        logger.warning("No file key provided for deletion")
        return False
    
    # Skip placeholder URLs
    if 'placehold.co' in file_key:
        logger.info(f"Skipping deletion of placeholder: {file_key}")
        return True
    
    try:
        s3_client = get_s3_client()
        
        logger.info(f"Deleting from S3 | bucket={bucket_name} | key={file_key}")
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        
        logger.info(f"Deletion successful | bucket={bucket_name} | key={file_key}")
        return True
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        logger.error(
            f"S3 deletion error | bucket={bucket_name} | key={file_key} | "
            f"code={error_code} | error={error_msg}"
        )
        return False
        
    except Exception as e:
        logger.error(
            f"Unexpected error deleting from S3 | bucket={bucket_name} | "
            f"key={file_key} | error={str(e)}"
        )
        return False


def delete_object_by_url(url: str) -> bool:
    """Delete object from Supabase S3 storage by public URL.
    
    Args:
        url: Full public URL of the object to delete
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    if not url:
        logger.warning("No URL provided for deletion")
        return False
    
    # Skip placeholder URLs
    if 'placehold.co' in url:
        logger.info(f"Skipping deletion of placeholder URL: {url}")
        return True
    
    try:
        # Extract bucket and key from URL
        # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{key}
        if '/storage/v1/object/public/' not in url:
            logger.warning(f"Invalid Supabase S3 URL format: {url}")
            return False
        
        parts = url.split('/storage/v1/object/public/')
        if len(parts) != 2:
            logger.warning(f"Could not parse S3 URL: {url}")
            return False
        
        path_parts = parts[1].split('/', 1)
        if len(path_parts) != 2:
            logger.warning(f"Could not extract bucket and key from URL: {url}")
            return False
        
        bucket_name = path_parts[0]
        file_key = path_parts[1]
        
        return delete_object(bucket_name, file_key)
        
    except Exception as e:
        logger.error(f"Error parsing URL for deletion | url={url} | error={str(e)}")
        return False

