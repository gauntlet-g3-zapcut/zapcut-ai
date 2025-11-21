"""Brand Images API routes."""
import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.brand import Brand
from app.models.user import User
from app.api.auth import get_current_user
from app.services.image_upload import (
    upload_image_with_metadata,
    delete_image_by_id,
    validate_image_count,
    MAX_BRAND_IMAGES
)
from app.utils.file_validation import validate_image_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brands", tags=["brand-images"])


class UpdateImageMetadataRequest(BaseModel):
    """Request model for updating image metadata."""
    caption: str = ""
    is_primary: bool = False


class ReorderImagesRequest(BaseModel):
    """Request model for reordering images."""
    image_ids: List[str]


@router.post("/{brand_id}/images")
async def upload_brand_images(
    brand_id: str,
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload one or more images to a brand (batch upload).

    Maximum 10 images per brand total.
    """
    logger.info(
        f"Uploading {len(images)} image(s) to brand | "
        f"brand_id={brand_id} | user_id={current_user.id}"
    )

    # Validate brand exists and belongs to user
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Get current images
    current_images = brand.images or []

    # Validate image count
    is_valid, error_msg = validate_image_count(current_images, len(images), "brand")
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Upload images
    uploaded_metadata = []
    failed_uploads = []

    for idx, image_file in enumerate(images):
        try:
            # Validate image file
            image_bytes, file_extension = await validate_image_file(image_file)
            logger.info(f"Image {idx + 1} validated | filename={image_file.filename} | ext={file_extension}")

            # Determine if this should be primary (first image if no existing images)
            is_primary = len(current_images) == 0 and idx == 0

            # Upload to S3 and get metadata
            metadata = upload_image_with_metadata(
                image_bytes=image_bytes,
                entity_id=str(brand.id),
                entity_type="brand",
                file_extension=file_extension,
                filename=image_file.filename,
                is_primary=is_primary
            )

            # Set order
            metadata["order"] = len(current_images) + len(uploaded_metadata)

            uploaded_metadata.append(metadata)
            logger.info(f"Image {idx + 1} uploaded successfully | image_id={metadata['id']}")

        except HTTPException as e:
            logger.error(f"Image {idx + 1} validation failed | filename={image_file.filename} | error={e.detail}")
            failed_uploads.append({
                "filename": image_file.filename,
                "error": e.detail
            })
        except Exception as e:
            logger.error(f"Image {idx + 1} upload failed | filename={image_file.filename} | error={str(e)}")
            failed_uploads.append({
                "filename": image_file.filename,
                "error": f"Upload failed: {str(e)}"
            })

    # Add uploaded images to brand
    if uploaded_metadata:
        brand.images = current_images + uploaded_metadata
        try:
            db.commit()
            db.refresh(brand)
            logger.info(f"Brand updated with {len(uploaded_metadata)} new image(s) | brand_id={brand_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update brand in database | brand_id={brand_id} | error={str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save images to database")

    response = {
        "uploaded_count": len(uploaded_metadata),
        "failed_count": len(failed_uploads),
        "images": uploaded_metadata
    }

    if failed_uploads:
        response["failures"] = failed_uploads

    return response


@router.put("/{brand_id}/images/reorder")
async def reorder_brand_images(
    brand_id: str,
    request: ReorderImagesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder brand images."""
    logger.info(
        f"Reordering images | brand_id={brand_id} | user_id={current_user.id} | "
        f"new_order={request.image_ids}"
    )

    # Validate brand exists and belongs to user
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Get current images
    current_images = brand.images or []

    # Validate all image IDs exist
    current_image_ids = {img.get("id") for img in current_images}
    request_image_ids = set(request.image_ids)

    if current_image_ids != request_image_ids:
        raise HTTPException(
            status_code=400,
            detail="Image ID mismatch. All existing images must be included in the reorder request."
        )

    # Create a map of image_id -> image
    image_map = {img.get("id"): img for img in current_images}

    # Reorder images
    reordered_images = []
    for idx, image_id in enumerate(request.image_ids):
        img = image_map[image_id]
        img["order"] = idx
        reordered_images.append(img)

    # Update brand
    brand.images = reordered_images

    try:
        db.commit()
        db.refresh(brand)
        logger.info(f"Images reordered successfully | brand_id={brand_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update brand in database | brand_id={brand_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reorder images")

    return {
        "message": "Images reordered successfully",
        "images": reordered_images
    }


@router.delete("/{brand_id}/images/{image_id}")
async def delete_brand_image(
    brand_id: str,
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific image from a brand."""
    logger.info(f"Deleting image | brand_id={brand_id} | image_id={image_id} | user_id={current_user.id}")

    # Validate brand exists and belongs to user
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Get current images
    current_images = brand.images or []

    # Find the image to delete
    image_to_delete = None
    remaining_images = []

    for img in current_images:
        if img.get("id") == image_id:
            image_to_delete = img
        else:
            remaining_images.append(img)

    if not image_to_delete:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete from S3
    success = delete_image_by_id(
        entity_id=str(brand.id),
        entity_type="brand",
        image_id=image_id
    )

    if not success:
        logger.warning(f"Failed to delete image from S3, but will remove from database | image_id={image_id}")

    # If deleting primary image, make first remaining image primary
    if image_to_delete.get("is_primary") and remaining_images:
        remaining_images[0]["is_primary"] = True
        logger.info(f"Set new primary image | image_id={remaining_images[0]['id']}")

    # Reorder remaining images
    for idx, img in enumerate(remaining_images):
        img["order"] = idx

    # Update brand
    brand.images = remaining_images

    try:
        db.commit()
        db.refresh(brand)
        logger.info(f"Image deleted successfully | brand_id={brand_id} | image_id={image_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update brand in database | brand_id={brand_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete image from database")

    return {
        "message": "Image deleted successfully",
        "remaining_count": len(remaining_images)
    }


@router.put("/{brand_id}/images/{image_id}")
async def update_brand_image_metadata(
    brand_id: str,
    image_id: str,
    request: UpdateImageMetadataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update image metadata (caption, is_primary)."""
    logger.info(
        f"Updating image metadata | brand_id={brand_id} | image_id={image_id} | "
        f"user_id={current_user.id} | is_primary={request.is_primary}"
    )

    # Validate brand exists and belongs to user
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Get current images
    current_images = brand.images or []

    # Find and update the image
    image_found = False
    updated_image = None
    for img in current_images:
        if img.get("id") == image_id:
            img["caption"] = request.caption

            # If setting this as primary, unset others
            if request.is_primary:
                for other_img in current_images:
                    other_img["is_primary"] = False
                img["is_primary"] = True
            else:
                img["is_primary"] = False

            updated_image = img
            image_found = True
            break

    if not image_found:
        raise HTTPException(status_code=404, detail="Image not found")

    # Ensure at least one image is primary
    has_primary = any(img.get("is_primary") for img in current_images)
    if not has_primary and current_images:
        current_images[0]["is_primary"] = True

    # If we just set a new primary, move it to position 0 and reorder others
    if request.is_primary and updated_image:
        # Remove the updated image from its current position
        current_images = [img for img in current_images if img.get("id") != image_id]
        # Insert it at the beginning
        current_images.insert(0, updated_image)
        # Reorder all images
        for idx, img in enumerate(current_images):
            img["order"] = idx

    # Update brand
    brand.images = current_images

    try:
        db.commit()
        db.refresh(brand)
        logger.info(f"Image metadata updated successfully | brand_id={brand_id} | image_id={image_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update brand in database | brand_id={brand_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update image metadata")

    # Return updated image
    updated_image = next((img for img in current_images if img.get("id") == image_id), None)
    return updated_image
