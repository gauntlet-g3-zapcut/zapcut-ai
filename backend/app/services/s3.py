import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid

# Configure S3-compatible client (works with AWS S3, Cloudflare R2, etc.)
s3_config = {
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    "region_name": settings.AWS_REGION,
}

# Add endpoint URL if provided (for Cloudflare R2, MinIO, etc.)
if settings.AWS_ENDPOINT_URL:
    s3_config["endpoint_url"] = settings.AWS_ENDPOINT_URL

s3_client = boto3.client("s3", **s3_config) if settings.AWS_ACCESS_KEY_ID else None


async def upload_file_to_s3(file, key: str) -> str:
    """Upload file to S3-compatible storage and return URL"""
    if not s3_client:
        raise Exception("Storage not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    
    try:
        # Generate unique key if needed
        if not key:
            key = f"uploads/{uuid.uuid4()}/{file.filename}"
        
        # Upload file
        file_content = await file.read()
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=key,
            Body=file_content,
            ContentType=file.content_type,
        )
        
        # Return public URL based on provider
        if settings.R2_PUBLIC_URL:
            # Cloudflare R2 with public domain
            url = f"{settings.R2_PUBLIC_URL}/{key}"
        elif settings.AWS_ENDPOINT_URL:
            # Cloudflare R2 or custom endpoint (fallback to bucket name)
            url = f"https://{settings.AWS_S3_BUCKET}.r2.dev/{key}"
        else:
            # Standard AWS S3
            url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        
        return url
    except ClientError as e:
        raise Exception(f"Failed to upload file to storage: {str(e)}")


def generate_presigned_url(key: str, expiration: int = 3600) -> str:
    """Generate presigned URL for S3 object"""
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
            ExpiresIn=expiration,
        )
        return url
    except ClientError as e:
        raise Exception(f"Failed to generate presigned URL: {str(e)}")


