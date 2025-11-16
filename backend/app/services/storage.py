"""
Supabase Storage service for file uploads
Uses Supabase Storage S3-compatible API via boto3
"""
from app.config import settings
import uuid
from typing import Optional
from fastapi import UploadFile
from urllib.parse import quote

# Initialize S3 client for Supabase Storage (S3-compatible)
# Lazy import boto3 to avoid conflict with local queue module
s3_client = None
supabase_client = None

try:
    # Use S3-compatible API if endpoint is configured
    if settings.SUPABASE_S3_ENDPOINT:
        # Lazy import boto3 to avoid conflict with local queue module
        # Handle the queue module conflict by loading stdlib queue directly
        try:
            import sys
            import os
            import importlib.util
            
            # Save reference to local queue module if it exists
            local_queue_backup = None
            if 'queue' in sys.modules:
                local_queue_backup = sys.modules['queue']
                # Remove local queue from sys.modules temporarily
                del sys.modules['queue']
            
            # Find Python's standard library queue.py file
            stdlib_queue_file = None
            for path in sys.path:
                if os.path.isdir(path) and 'site-packages' not in path:
                    test_file = os.path.join(path, 'queue.py')
                    if os.path.exists(test_file):
                        stdlib_queue_file = test_file
                        break
            
            # Load standard library queue module directly from file
            # This bypasses Python's normal import mechanism
            if stdlib_queue_file:
                spec = importlib.util.spec_from_file_location('queue', stdlib_queue_file)
                if spec and spec.loader:
                    stdlib_queue = importlib.util.module_from_spec(spec)
                    # Load the module - this puts it in sys.modules
                    spec.loader.exec_module(stdlib_queue)
                    # Verify it's the stdlib version
                    if not hasattr(stdlib_queue, 'LifoQueue'):
                        raise ImportError("Failed to load standard library queue module")
                    # Ensure it's in sys.modules as 'queue'
                    sys.modules['queue'] = stdlib_queue
            
            # Now import boto3 - it will use the stdlib queue already in sys.modules
            import boto3
            from botocore.exceptions import ClientError
            
            # Note: stdlib queue remains in sys.modules for boto3's use
            # The local queue directory can coexist, but boto3 uses stdlib version
            
            # Extract project ref from endpoint or use access key if provided
            # Endpoint format: https://{project_ref}.storage.supabase.co/storage/v1/s3
            access_key = settings.SUPABASE_S3_ACCESS_KEY
            secret_key = settings.SUPABASE_S3_SECRET_KEY
            
            # If access key/secret not explicitly set, try to derive from service role key
            if not access_key and settings.SUPABASE_URL:
                # Extract project ref from SUPABASE_URL
                project_ref = settings.SUPABASE_URL.replace('https://', '').replace('http://', '').split('.')[0]
                access_key = project_ref
            
            if not secret_key:
                secret_key = settings.SUPABASE_SERVICE_ROLE_KEY
            
            if access_key and secret_key:
                s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.SUPABASE_S3_ENDPOINT,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name='us-east-1'  # Supabase Storage doesn't require specific region
                )
                print("✅ Supabase Storage S3 client initialized")
            else:
                print("⚠️  Supabase Storage S3 not configured (missing credentials)")
        except ImportError as e:
            print(f"⚠️  boto3 not installed - S3 API unavailable: {e}")
        except Exception as e:
            print(f"⚠️  Failed to initialize S3 client: {e}")
    
    # Also initialize Python client as fallback (or if S3 endpoint not set)
    if not s3_client:
        try:
            from supabase import create_client, Client
            
            if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
                supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                if not settings.SUPABASE_S3_ENDPOINT:
                    print("✅ Supabase Storage client initialized (Python client)")
        except ImportError:
            pass  # Supabase package not installed, that's okay if using S3 API
        except Exception as e:
            print(f"⚠️  Failed to initialize Supabase Python client: {e}")
            
except Exception as e:
    print(f"⚠️  Supabase Storage initialization failed: {e}")


async def upload_file_to_storage(
    file: UploadFile,
    bucket: str = "uploads",
    path: Optional[str] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Upload file to Supabase Storage and return public URL
    
    Args:
        file: FastAPI UploadFile object
        bucket: Storage bucket name (default: "uploads")
        path: Optional file path in bucket (if None, generates unique path)
        content_type: Optional content type (defaults to file.content_type)
    
    Returns:
        Public URL of uploaded file
    
    Raises:
        Exception: If storage is not configured or upload fails
    """
    if not s3_client and not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_S3_ENDPOINT or SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        # Generate unique path if not provided
        if not path:
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
            path = f"{uuid.uuid4()}{'.' + file_ext if file_ext else ''}"
        
        # Read file content
        file_content = await file.read()
        
        # Use provided content_type or file's content_type
        content_type_to_use = content_type or file.content_type or 'application/octet-stream'
        
        # Use S3-compatible API if available
        if s3_client:
            try:
                from botocore.exceptions import ClientError
                s3_client.put_object(
                    Bucket=bucket,
                    Key=path,
                    Body=file_content,
                    ContentType=content_type_to_use
                )
                
                # Generate public URL
                # Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{path}
                encoded_path = quote(path, safe='/')
                public_url = (
                    f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{encoded_path}"
                )
                
                return public_url
            except Exception as e:
                # Handle both ClientError and other exceptions
                error_type = type(e).__name__
                raise Exception(f"Failed to upload file to Supabase Storage ({error_type}): {str(e)}")
        
        # Fallback to Supabase Python client
        if not supabase_client:
            raise Exception("Storage client not initialized")
        
        upload_options = {'content-type': content_type_to_use}
        
        response = supabase_client.storage.from_(bucket).upload(
            path=path,
            file=file_content,
            file_options=upload_options if upload_options else None
        )
        
        # Check for errors in response
        if isinstance(response, dict):
            if 'error' in response and response['error']:
                error_msg = response['error'] if isinstance(response['error'], str) else str(response['error'])
                raise Exception(f"Supabase Storage upload error: {error_msg}")
        elif hasattr(response, 'error') and response.error:
            error_msg = response.error if isinstance(response.error, str) else str(response.error)
            raise Exception(f"Supabase Storage upload error: {error_msg}")
        
        if isinstance(response, dict) and 'data' in response and response['data'] is None:
            if 'error' in response:
                error_msg = response['error'] if isinstance(response['error'], str) else str(response['error'])
                raise Exception(f"Supabase Storage upload error: {error_msg}")
        
        # Generate public URL
        encoded_path = quote(path, safe='/')
        public_url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{encoded_path}"
        )
        
        return public_url
        
    except Exception as e:
        raise Exception(f"Failed to upload file to storage: {str(e)}")


def generate_signed_url(
    bucket: str,
    path: str,
    expiration: int = 3600
) -> str:
    """
    Generate a signed URL for private bucket access
    
    Args:
        bucket: Storage bucket name
        path: File path in bucket
        expiration: URL expiration time in seconds (default: 3600)
    
    Returns:
        Signed URL valid for expiration seconds
    """
    if not s3_client and not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_S3_ENDPOINT or SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        # Use S3-compatible API if available
        if s3_client:
            try:
                from botocore.exceptions import ClientError
                signed_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': path},
                    ExpiresIn=expiration
                )
                return signed_url
            except Exception as e:
                error_type = type(e).__name__
                raise Exception(f"Failed to generate signed URL ({error_type}): {str(e)}")
        
        # Fallback to Supabase Python client
        if not supabase_client:
            raise Exception("Storage client not initialized")
        
        response = supabase_client.storage.from_(bucket).create_signed_url(
            path=path,
            expires_in=expiration
        )
        
        if hasattr(response, 'error') and response.error:
            error_msg = response.error if isinstance(response.error, str) else str(response.error)
            raise Exception(f"Failed to generate signed URL: {error_msg}")
        
        # Response format varies - could be dict with 'signedURL' or response object
        if isinstance(response, dict):
            if 'signedURL' in response:
                return response['signedURL']
            elif 'signed_url' in response:
                return response['signed_url']
        elif hasattr(response, 'signedURL'):
            return response.signedURL
        elif hasattr(response, 'signed_url'):
            return response.signed_url
        elif isinstance(response, str):
            # Sometimes the response might be the URL directly
            return response
        else:
            raise Exception(f"Unexpected response format from create_signed_url: {type(response)}")
            
    except Exception as e:
        if "Unexpected response format" in str(e) or "Failed to generate signed URL" in str(e):
            raise
        raise Exception(f"Failed to generate signed URL: {str(e)}")


async def upload_bytes_to_storage(
    data: bytes,
    bucket: str,
    path: str,
    content_type: Optional[str] = None
) -> str:
    """
    Upload bytes data to Supabase Storage and return public URL
    
    Args:
        data: Bytes data to upload
        bucket: Storage bucket name
        path: File path in bucket
        content_type: Optional content type (e.g., "video/mp4", "audio/mpeg")
    
    Returns:
        Public URL of uploaded file
    
    Raises:
        Exception: If storage is not configured or upload fails
    """
    if not s3_client and not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_S3_ENDPOINT or SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        content_type_to_use = content_type or 'application/octet-stream'
        
        # Use S3-compatible API if available
        if s3_client:
            try:
                from botocore.exceptions import ClientError
                s3_client.put_object(
                    Bucket=bucket,
                    Key=path,
                    Body=data,
                    ContentType=content_type_to_use
                )
                
                # Generate public URL
                encoded_path = quote(path, safe='/')
                public_url = (
                    f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{encoded_path}"
                )
                
                return public_url
            except Exception as e:
                error_type = type(e).__name__
                raise Exception(f"Failed to upload bytes to Supabase Storage ({error_type}): {str(e)}")
        
        # Fallback to Supabase Python client
        if not supabase_client:
            raise Exception("Storage client not initialized")
        
        upload_options = {'content-type': content_type_to_use}
        
        response = supabase_client.storage.from_(bucket).upload(
            path=path,
            file=data,
            file_options=upload_options if upload_options else None
        )
        
        # Check for errors in response
        if isinstance(response, dict):
            if 'error' in response and response['error']:
                error_msg = response['error'] if isinstance(response['error'], str) else str(response['error'])
                raise Exception(f"Supabase Storage upload error: {error_msg}")
        elif hasattr(response, 'error') and response.error:
            error_msg = response.error if isinstance(response.error, str) else str(response.error)
            raise Exception(f"Supabase Storage upload error: {error_msg}")
        
        if isinstance(response, dict) and 'data' in response and response['data'] is None:
            if 'error' in response:
                error_msg = response['error'] if isinstance(response['error'], str) else str(response['error'])
                raise Exception(f"Supabase Storage upload error: {error_msg}")
        
        # Generate public URL
        encoded_path = quote(path, safe='/')
        public_url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{encoded_path}"
        )
        
        return public_url
        
    except Exception as e:
        raise Exception(f"Failed to upload bytes to storage: {str(e)}")


async def delete_file_from_storage(
    bucket: str,
    path: str
) -> bool:
    """
    Delete a file from Supabase Storage
    
    Args:
        bucket: Storage bucket name
        path: File path in bucket
    
    Returns:
        True if successful
    
    Raises:
        Exception: If deletion fails
    """
    if not s3_client and not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_S3_ENDPOINT or SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        # Use S3-compatible API if available
        if s3_client:
            try:
                from botocore.exceptions import ClientError
                s3_client.delete_object(Bucket=bucket, Key=path)
                return True
            except Exception as e:
                error_type = type(e).__name__
                raise Exception(f"Failed to delete file ({error_type}): {str(e)}")
        
        # Fallback to Supabase Python client
        if not supabase_client:
            raise Exception("Storage client not initialized")
        
        response = supabase_client.storage.from_(bucket).remove([path])
        
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Failed to delete file: {response.error}")
        
        return True
        
    except Exception as e:
        raise Exception(f"Failed to delete file from storage: {str(e)}")

