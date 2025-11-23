"""File validation utilities for image uploads."""
import io
import logging
from typing import Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}

# Magic bytes for image file type validation
MAGIC_BYTES = {
    'jpg': [b'\xFF\xD8\xFF'],
    'png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],
    'webp': [b'RIFF', b'WEBP']  # WebP has RIFF...WEBP
}


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename.

    Args:
        filename: Original filename

    Returns:
        Lowercase file extension without dot

    Raises:
        HTTPException: If no extension found
    """
    if not filename or '.' not in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. File must have an extension."
        )

    extension = filename.rsplit('.', 1)[1].lower()
    return extension


def validate_file_extension(extension: str) -> None:
    """Validate file extension is allowed.

    Args:
        extension: File extension to validate

    Raises:
        HTTPException: If extension not allowed
    """
    logger.debug(f"Validating file extension | extension={extension}")
    if extension not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file extension rejected | extension={extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS).upper()} images are allowed."
        )
    logger.debug(f"File extension valid | extension={extension}")


def validate_mime_type(content_type: str) -> None:
    """Validate MIME type is allowed.

    Args:
        content_type: MIME type from file upload

    Raises:
        HTTPException: If MIME type not allowed
    """
    logger.debug(f"Validating MIME type | content_type={content_type}")
    if content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Invalid MIME type rejected | content_type={content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME type '{content_type}'. Only JPEG, PNG, and WebP images are allowed."
        )
    logger.debug(f"MIME type valid | content_type={content_type}")


def validate_file_size(file_bytes: bytes) -> None:
    """Validate file size is within limits.

    Args:
        file_bytes: File content as bytes

    Raises:
        HTTPException: If file too large
    """
    file_size = len(file_bytes)
    logger.debug(f"Validating file size | size={file_size} bytes ({file_size / (1024 * 1024):.2f}MB)")
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        logger.warning(f"File size exceeds limit | size={actual_mb:.2f}MB | max={max_mb:.1f}MB")
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {max_mb:.1f}MB (uploaded: {actual_mb:.1f}MB)."
        )
    logger.debug(f"File size valid | size={file_size} bytes")


def validate_magic_bytes(file_bytes: bytes, extension: str) -> None:
    """Validate file magic bytes match the extension.

    Args:
        file_bytes: File content as bytes
        extension: Expected file extension

    Raises:
        HTTPException: If magic bytes don't match extension
    """
    logger.debug(f"Validating magic bytes | extension={extension}")
    if extension not in MAGIC_BYTES:
        # Skip validation for unknown extensions
        logger.debug(f"Skipping magic bytes validation for unknown extension | extension={extension}")
        return

    magic_signatures = MAGIC_BYTES[extension]

    # Check if file starts with any of the valid magic bytes
    for magic in magic_signatures:
        if file_bytes.startswith(magic):
            logger.debug(f"Magic bytes valid | extension={extension} | matched={magic.hex()}")
            return

    # Special case for WebP - check both RIFF and WEBP markers
    if extension == 'webp':
        if file_bytes.startswith(b'RIFF') and b'WEBP' in file_bytes[:12]:
            logger.debug(f"Magic bytes valid | extension=webp | format=RIFF/WEBP")
            return

    logger.warning(f"Magic bytes invalid | extension={extension} | first_bytes={file_bytes[:8].hex()}")
    raise HTTPException(
        status_code=400,
        detail=f"File is corrupted or not a valid {extension.upper()} image."
    )


def validate_image_content(file_bytes: bytes) -> None:
    """Validate file is actually an image by attempting to open it.

    Args:
        file_bytes: File content as bytes

    Raises:
        HTTPException: If file cannot be opened as an image
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # Verify it's a valid image
        logger.info(f"Image validated | format={image.format} | size={image.size}")
    except Exception as e:
        logger.error(f"Image validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="File is corrupted or not a valid image."
        )


async def validate_image_file(file: UploadFile) -> Tuple[bytes, str]:
    """Validate uploaded image file.

    Performs comprehensive validation:
    1. File size check (max 10MB)
    2. Extension check (jpg, jpeg, png, webp only)
    3. MIME type check
    4. Magic bytes validation
    5. Image content validation (using Pillow)

    Args:
        file: FastAPI UploadFile object

    Returns:
        Tuple of (image_bytes, file_extension)

    Raises:
        HTTPException: If validation fails at any step
    """
    logger.info(f"Starting file validation | filename={file.filename} | content_type={file.content_type}")

    # Read file content
    try:
        file_bytes = await file.read()
        logger.debug(f"File read successfully | size={len(file_bytes)} bytes")
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded file."
        )
    finally:
        # Reset file pointer for potential re-reading
        await file.seek(0)

    # Validate file size
    validate_file_size(file_bytes)

    # Extract and validate extension
    extension = get_file_extension(file.filename)
    validate_file_extension(extension)

    # Validate MIME type
    if file.content_type:
        validate_mime_type(file.content_type)
    else:
        logger.warning(f"No content type provided for file: {file.filename}")

    # Validate magic bytes
    validate_magic_bytes(file_bytes, extension)

    # Validate image content with Pillow
    validate_image_content(file_bytes)

    logger.info(
        f"File validation successful | filename={file.filename} | "
        f"size={len(file_bytes)} bytes | extension={extension}"
    )

    return file_bytes, extension
