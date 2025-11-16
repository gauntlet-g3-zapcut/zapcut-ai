"""
Supabase Storage service for file uploads
Replaces S3 service with Supabase Storage (S3-compatible)
"""
from app.config import settings
import uuid
from typing import Optional
from fastapi import UploadFile

# Lazy import to avoid startup failures
supabase_client = None

try:
    from supabase import create_client, Client
    
    # Initialize Supabase client for storage operations
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        print("✅ Supabase Storage client initialized")
    else:
        print("⚠️  Supabase Storage not configured (missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY)")
except ImportError:
    print("⚠️  Supabase package not installed - storage operations will fail")
except Exception as e:
    print(f"⚠️  Supabase Storage initialization failed: {e}")
else:
    print("⚠️  Supabase Storage not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")


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
    if not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        # Generate unique path if not provided
        if not path:
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
            path = f"{uuid.uuid4()}{'.' + file_ext if file_ext else ''}"
        
        # Read file content
        file_content = await file.read()
        
        # Use provided content_type or file's content_type
        upload_options = {}
        if content_type:
            upload_options['content-type'] = content_type
        elif file.content_type:
            upload_options['content-type'] = file.content_type
        
        # Upload to Supabase Storage
        # The Python client upload method returns a StorageFileUploadResponse
        # which may have error attribute or raise exceptions
        try:
            response = supabase_client.storage.from_(bucket).upload(
                path=path,
                file=file_content,
                file_options=upload_options if upload_options else None
            )
            
            # Check for errors in response (Python client may return error in response)
            if hasattr(response, 'error') and response.error:
                error_msg = response.error if isinstance(response.error, str) else str(response.error)
                raise Exception(f"Supabase Storage upload error: {error_msg}")
            
        except Exception as upload_error:
            # Re-raise with more context if it's not already our exception
            if "Supabase Storage upload error" in str(upload_error):
                raise
            raise Exception(f"Supabase Storage upload failed: {str(upload_error)}")
        
        # Generate public URL
        # Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{path}
        # URL encode the path to handle special characters
        from urllib.parse import quote
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
    if not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
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
    if not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        upload_options = {}
        if content_type:
            upload_options['content-type'] = content_type
        
        # Upload to Supabase Storage
        try:
            response = supabase_client.storage.from_(bucket).upload(
                path=path,
                file=data,
                file_options=upload_options if upload_options else None
            )
            
            # Check for errors in response
            if hasattr(response, 'error') and response.error:
                error_msg = response.error if isinstance(response.error, str) else str(response.error)
                raise Exception(f"Supabase Storage upload error: {error_msg}")
            
        except Exception as upload_error:
            if "Supabase Storage upload error" in str(upload_error):
                raise
            raise Exception(f"Supabase Storage upload failed: {str(upload_error)}")
        
        # Generate public URL
        from urllib.parse import quote
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
    if not supabase_client:
        raise Exception(
            "Storage not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    try:
        response = supabase_client.storage.from_(bucket).remove([path])
        
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Failed to delete file: {response.error}")
        
        return True
        
    except Exception as e:
        raise Exception(f"Failed to delete file from storage: {str(e)}")

