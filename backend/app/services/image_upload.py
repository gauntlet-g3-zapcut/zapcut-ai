"""Image upload service for Supabase S3 storage."""
import io
import logging
import time
import uuid
from typing import Optional, Dict, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s

# Image limits
MAX_BRAND_IMAGES = 10
MAX_CAMPAIGN_IMAGES = 20


def get_content_type(file_extension: str) -> str:
    """Map file extension to MIME type.

    Args:
        file_extension: File extension (e.g., 'jpg', 'png')

    Returns:
        MIME type string
    """
    extension_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp'
    }
    return extension_map.get(file_extension.lower(), 'image/jpeg')


def upload_image_to_supabase_s3(
    image_bytes: bytes,
    brand_id: str,
    image_number: int,
    file_extension: str
) -> str:
    """Upload image file to Supabase S3 storage with retry logic.

    Args:
        image_bytes: The image file bytes to upload
        brand_id: Brand ID for file naming
        image_number: Image number (1 or 2)
        file_extension: File extension (jpg, png, webp)

    Returns:
        Public URL of the uploaded image file

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
            # Initialize S3 client for Supabase
            logger.info(
                f"Initializing S3 client | endpoint={settings.SUPABASE_S3_ENDPOINT} | "
                f"access_key_prefix={settings.SUPABASE_S3_ACCESS_KEY[:8]}... | "
                f"region=us-east-1"
            )
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.SUPABASE_S3_ENDPOINT,
                aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
                aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
                region_name='us-east-1'
            )

            # Test: Try to list buckets to see what's available
            try:
                buckets_response = s3_client.list_buckets()
                available_buckets = [b['Name'] for b in buckets_response.get('Buckets', [])]
                logger.info(f"Available S3 buckets: {available_buckets}")
            except Exception as list_error:
                logger.warning(f"Could not list buckets: {str(list_error)}")

            # Bucket and file configuration
            bucket_name = 'brand-images'
            file_key = f"{brand_id}_image_{image_number}.{file_extension}"
            content_type = get_content_type(file_extension)

            logger.info(
                f"Uploading image to S3 | brand={brand_id} | "
                f"image_number={image_number} | size={len(image_bytes)} bytes | "
                f"bucket={bucket_name} | file_key={file_key} | content_type={content_type} | "
                f"attempt={attempt + 1}/{MAX_RETRIES}"
            )

            # Upload image bytes
            image_file = io.BytesIO(image_bytes)
            s3_client.upload_fileobj(
                image_file,
                Bucket=bucket_name,
                Key=file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'
                }
            )

            # Construct public URL
            endpoint = settings.SUPABASE_S3_ENDPOINT.rstrip('/')
            if '/storage/v1' in endpoint:
                base_url = endpoint.split('/storage/v1')[0]
            else:
                base_url = endpoint

            image_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{file_key}"

            logger.info(
                f"Image uploaded successfully | brand={brand_id} | "
                f"image_number={image_number} | url={image_url}"
            )

            return image_url

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            last_error = e

            logger.error(
                f"S3 upload error | brand={brand_id} | image_number={image_number} | "
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
                f"Unexpected error uploading image | brand={brand_id} | "
                f"image_number={image_number} | attempt={attempt + 1}/{MAX_RETRIES} | "
                f"error={str(e)}"
            )

            # Retry if not the last attempt
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying upload in {delay}s...")
                time.sleep(delay)

    # All retries failed
    error_msg = f"Failed to upload image after {MAX_RETRIES} attempts: {str(last_error)}"
    logger.error(f"Upload failed permanently | brand={brand_id} | image_number={image_number}")
    raise Exception(error_msg)


def delete_image_from_supabase_s3(image_url: str) -> bool:
    """Delete image file from Supabase S3 storage.

    Args:
        image_url: Full public URL of the image to delete

    Returns:
        True if deletion succeeded, False otherwise
    """
    if not image_url:
        logger.warning("No image URL provided for deletion")
        return False

    # Skip placeholder URLs
    if 'placehold.co' in image_url:
        logger.info(f"Skipping deletion of placeholder URL: {image_url}")
        return True

    try:
        # Extract bucket and key from URL
        # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{key}
        if '/storage/v1/object/public/' not in image_url:
            logger.warning(f"Invalid Supabase S3 URL format: {image_url}")
            return False

        parts = image_url.split('/storage/v1/object/public/')
        if len(parts) != 2:
            logger.warning(f"Could not parse S3 URL: {image_url}")
            return False

        path_parts = parts[1].split('/', 1)
        if len(path_parts) != 2:
            logger.warning(f"Could not extract bucket and key from URL: {image_url}")
            return False

        bucket_name = path_parts[0]
        file_key = path_parts[1]

        if not all([
            settings.SUPABASE_S3_ENDPOINT,
            settings.SUPABASE_S3_ACCESS_KEY,
            settings.SUPABASE_S3_SECRET_KEY
        ]):
            logger.error("Supabase S3 credentials not configured for deletion")
            return False

        # Initialize S3 client
        logger.debug(f"Initializing S3 client for deletion | endpoint={settings.SUPABASE_S3_ENDPOINT}")
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.SUPABASE_S3_ENDPOINT,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
            region_name='us-east-1'
        )

        logger.info(f"Deleting image from S3 | bucket={bucket_name} | key={file_key}")
        # Delete the object
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)

        logger.info(f"Image deleted successfully from S3 | bucket={bucket_name} | key={file_key}")
        return True

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        logger.error(
            f"S3 deletion error | url={image_url} | code={error_code} | error={error_msg}"
        )
        return False

    except Exception as e:
        logger.error(f"Unexpected error deleting image | url={image_url} | error={str(e)}")
        return False


def upload_image_with_metadata(
    image_bytes: bytes,
    entity_id: str,
    entity_type: str,
    file_extension: str,
    filename: str,
    caption: Optional[str] = None,
    is_primary: bool = False
) -> Dict:
    """Upload image and return metadata object.

    Args:
        image_bytes: The image file bytes to upload
        entity_id: Brand ID or Campaign ID
        entity_type: "brand" or "campaign"
        file_extension: File extension (jpg, png, webp)
        filename: Original filename
        caption: Optional caption for the image
        is_primary: Whether this is the primary image

    Returns:
        Dictionary containing image metadata

    Raises:
        ValueError: If S3 credentials not configured or invalid entity_type
        Exception: If upload fails after all retries
    """
    if entity_type not in ["brand", "campaign"]:
        raise ValueError(f"Invalid entity_type: {entity_type}. Must be 'brand' or 'campaign'")

    if not all([
        settings.SUPABASE_S3_ENDPOINT,
        settings.SUPABASE_S3_ACCESS_KEY,
        settings.SUPABASE_S3_SECRET_KEY
    ]):
        raise ValueError("Supabase S3 credentials not configured")

    # Generate unique image ID
    image_id = str(uuid.uuid4())

    # Determine bucket name based on entity type
    bucket_name = f"{entity_type}-images"

    # New S3 structure: {entity_id}/{image_id}.{ext}
    file_key = f"{entity_id}/{image_id}.{file_extension}"
    content_type = get_content_type(file_extension)

    # Retry loop
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.SUPABASE_S3_ENDPOINT,
                aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
                aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
                region_name='us-east-1'
            )

            logger.info(
                f"Uploading image to S3 | entity_type={entity_type} | entity_id={entity_id} | "
                f"image_id={image_id} | size={len(image_bytes)} bytes | "
                f"bucket={bucket_name} | file_key={file_key} | attempt={attempt + 1}/{MAX_RETRIES}"
            )

            # Upload image bytes
            image_file = io.BytesIO(image_bytes)
            s3_client.upload_fileobj(
                image_file,
                Bucket=bucket_name,
                Key=file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'
                }
            )

            # Construct public URL
            endpoint = settings.SUPABASE_S3_ENDPOINT.rstrip('/')
            if '/storage/v1' in endpoint:
                base_url = endpoint.split('/storage/v1')[0]
            else:
                base_url = endpoint

            image_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{file_key}"

            # Create metadata object
            metadata = {
                "id": image_id,
                "url": image_url,
                "filename": filename,
                "uploaded_at": datetime.utcnow().isoformat(),
                "size_bytes": len(image_bytes),
                "order": 0,  # Will be set by caller
                "caption": caption or "",
                "is_primary": is_primary
            }

            logger.info(
                f"Image uploaded successfully | entity_type={entity_type} | "
                f"entity_id={entity_id} | image_id={image_id} | url={image_url}"
            )

            return metadata

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            last_error = e

            logger.error(
                f"S3 upload error | entity_type={entity_type} | entity_id={entity_id} | "
                f"attempt={attempt + 1}/{MAX_RETRIES} | code={error_code} | error={error_msg}"
            )

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying upload in {delay}s...")
                time.sleep(delay)

        except Exception as e:
            last_error = e
            logger.error(
                f"Unexpected error uploading image | entity_type={entity_type} | "
                f"entity_id={entity_id} | attempt={attempt + 1}/{MAX_RETRIES} | error={str(e)}"
            )

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying upload in {delay}s...")
                time.sleep(delay)

    # All retries failed
    error_msg = f"Failed to upload image after {MAX_RETRIES} attempts: {str(last_error)}"
    logger.error(f"Upload failed permanently | entity_type={entity_type} | entity_id={entity_id}")
    raise Exception(error_msg)


def delete_image_by_id(
    entity_id: str,
    entity_type: str,
    image_id: str
) -> bool:
    """Delete specific image by its UUID from S3.

    Args:
        entity_id: Brand ID or Campaign ID
        entity_type: "brand" or "campaign"
        image_id: Image UUID

    Returns:
        True if deletion succeeded, False otherwise
    """
    if entity_type not in ["brand", "campaign"]:
        logger.error(f"Invalid entity_type: {entity_type}")
        return False

    try:
        if not all([
            settings.SUPABASE_S3_ENDPOINT,
            settings.SUPABASE_S3_ACCESS_KEY,
            settings.SUPABASE_S3_SECRET_KEY
        ]):
            logger.error("Supabase S3 credentials not configured for deletion")
            return False

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.SUPABASE_S3_ENDPOINT,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
            region_name='us-east-1'
        )

        bucket_name = f"{entity_type}-images"

        # Try to delete with common extensions
        # We don't know the extension, so try all common ones
        extensions = ['jpg', 'jpeg', 'png', 'webp']
        deleted = False

        for ext in extensions:
            file_key = f"{entity_id}/{image_id}.{ext}"
            try:
                logger.info(f"Attempting to delete | bucket={bucket_name} | key={file_key}")
                s3_client.delete_object(Bucket=bucket_name, Key=file_key)
                logger.info(f"Image deleted successfully | bucket={bucket_name} | key={file_key}")
                deleted = True
                break  # Success, no need to try other extensions
            except ClientError as e:
                # If file doesn't exist, that's okay, try next extension
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if error_code == 'NoSuchKey':
                    continue
                else:
                    logger.error(f"Error deleting {file_key}: {e}")

        return deleted

    except Exception as e:
        logger.error(
            f"Unexpected error deleting image | entity_type={entity_type} | "
            f"entity_id={entity_id} | image_id={image_id} | error={str(e)}"
        )
        return False


def validate_image_count(
    current_images: List[Dict],
    additional_count: int,
    entity_type: str
) -> tuple[bool, Optional[str]]:
    """Validate that adding images won't exceed the limit.

    Args:
        current_images: List of existing image metadata objects
        additional_count: Number of images to add
        entity_type: "brand" or "campaign"

    Returns:
        Tuple of (is_valid, error_message)
    """
    max_images = MAX_BRAND_IMAGES if entity_type == "brand" else MAX_CAMPAIGN_IMAGES
    current_count = len(current_images)
    new_total = current_count + additional_count

    if new_total > max_images:
        error_msg = (
            f"Cannot add {additional_count} image(s). "
            f"{entity_type.capitalize()} already has {current_count} image(s), "
            f"and the maximum is {max_images}."
        )
        return False, error_msg

    return True, None
