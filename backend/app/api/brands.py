"""Brands API routes."""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.brand import Brand
from app.models.user import User
from app.models.creative_bible import CreativeBible
from app.api.auth import get_current_user
from app.services.image_upload import upload_image_to_supabase_s3, delete_image_from_supabase_s3
from app.utils.file_validation import validate_image_file
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("/")
async def list_brands(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all brands for current user."""
    logger.info(f"Fetching brands for user: {current_user.id} (email: {current_user.email})")
    
    try:
        brands = db.query(Brand).filter(Brand.user_id == current_user.id).all()
        logger.info(f"Found {len(brands)} brands for user {current_user.id}")
        
        result = [
            {
                "id": str(brand.id),
                "title": brand.title,
                "description": brand.description,
                "product_image_1_url": brand.product_image_1_url,  # Legacy - for backward compatibility
                "product_image_2_url": brand.product_image_2_url,  # Legacy - for backward compatibility
                "images": brand.images or [],  # New: array of image metadata
                "created_at": brand.created_at,
                "campaign_count": len(brand.campaigns),
            }
            for brand in brands
        ]
        
        logger.info(f"Returning {len(result)} brands")
        return result
    except Exception as e:
        logger.error(f"Error fetching brands for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch brands: {str(e)}")


@router.post("/")
async def create_brand(
    title: str = Form(...),
    description: str = Form(...),
    product_image_1: UploadFile = File(...),
    product_image_2: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new brand with image uploads to Supabase S3."""
    logger.info(f"Creating brand for user: {current_user.id} | title={title}")

    # Step 1: Generate UUID upfront (industry standard approach)
    brand_id = uuid.uuid4()
    logger.info(f"Generated brand UUID: {brand_id}")

    # Step 2: Validate both image files
    try:
        image_1_bytes, image_1_ext = await validate_image_file(product_image_1)
        image_2_bytes, image_2_ext = await validate_image_file(product_image_2)
        logger.info(f"Images validated | image_1={image_1_ext} | image_2={image_2_ext}")
    except HTTPException as e:
        logger.error(f"Image validation failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Image validation failed: {str(e)}")

    # Step 3: Upload image 1 to S3
    try:
        image_1_url = upload_image_to_supabase_s3(
            image_bytes=image_1_bytes,
            brand_id=str(brand_id),
            image_number=1,
            file_extension=image_1_ext
        )
        logger.info(f"Image 1 uploaded | brand_id={brand_id} | url={image_1_url}")
    except Exception as e:
        logger.error(f"Image 1 upload failed | brand_id={brand_id} | error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image 1: {str(e)}"
        )

    # Step 4: Upload image 2 to S3
    try:
        image_2_url = upload_image_to_supabase_s3(
            image_bytes=image_2_bytes,
            brand_id=str(brand_id),
            image_number=2,
            file_extension=image_2_ext
        )
        logger.info(f"Image 2 uploaded | brand_id={brand_id} | url={image_2_url}")
    except Exception as e:
        logger.error(f"Image 2 upload failed | brand_id={brand_id} | error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image 2: {str(e)}"
        )

    # Step 5: Create brand in database with all data (including S3 URLs)
    brand = Brand(
        id=brand_id,
        user_id=current_user.id,
        title=title,
        description=description,
        product_image_1_url=image_1_url,
        product_image_2_url=image_2_url,
        created_at=datetime.utcnow().isoformat()
    )

    try:
        db.add(brand)
        db.commit()
        db.refresh(brand)
        logger.info(f"Brand created in database | brand_id={brand.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error creating brand: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create brand in database")

    logger.info(f"Brand creation completed | brand_id={brand.id}")
    return {
        "id": str(brand.id),
        "title": brand.title,
        "description": brand.description,
        "product_image_1_url": brand.product_image_1_url,
        "product_image_2_url": brand.product_image_2_url,
        "created_at": brand.created_at,
    }


@router.get("/{brand_id}")
async def get_brand(
    brand_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get brand details."""
    logger.info(f"Fetching brand details | brand_id={brand_id} | user_id={current_user.id}")

    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError:
        logger.warning(f"Invalid brand ID format | brand_id={brand_id}")
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        logger.warning(f"Brand not found | brand_id={brand_id} | user_id={current_user.id}")
        raise HTTPException(status_code=404, detail="Brand not found")

    logger.info(
        f"Brand retrieved successfully | brand_id={brand_id} | "
        f"title={brand.title} | campaigns={len(brand.campaigns)} | "
        f"has_image_1={bool(brand.product_image_1_url)} | "
        f"has_image_2={bool(brand.product_image_2_url)}"
    )

    response = {
        "id": str(brand.id),
        "title": brand.title,
        "description": brand.description,
        "product_image_1_url": brand.product_image_1_url,  # Legacy - for backward compatibility
        "product_image_2_url": brand.product_image_2_url,  # Legacy - for backward compatibility
        "images": brand.images or [],  # New: array of image metadata
        "created_at": brand.created_at,
        "campaigns": [
            {
                "id": str(campaign.id),
                "status": campaign.status,
                "created_at": campaign.created_at,
            }
            for campaign in brand.campaigns
        ],
    }

    if brand.product_image_1_url:
        logger.debug(f"Brand image 1 URL | url={brand.product_image_1_url}")
    if brand.product_image_2_url:
        logger.debug(f"Brand image 2 URL | url={brand.product_image_2_url}")

    return response


@router.put("/{brand_id}")
async def update_brand(
    brand_id: str,
    title: str = Form(...),
    description: str = Form(...),
    product_image_1: UploadFile = File(None),
    product_image_2: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a brand with optional image uploads to Supabase S3."""
    logger.info(f"Updating brand | brand_id={brand_id} | user_id={current_user.id}")

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

    # Update title and description
    brand.title = title
    brand.description = description

    warnings = []

    # Update image 1 if provided
    if product_image_1 and product_image_1.filename:
        try:
            # Validate image
            image_1_bytes, image_1_ext = await validate_image_file(product_image_1)
            logger.info(f"Image 1 validated | brand_id={brand_id} | ext={image_1_ext}")

            # Upload to S3 (overwrites existing file with same name)
            image_1_url = upload_image_to_supabase_s3(
                image_bytes=image_1_bytes,
                brand_id=str(brand.id),
                image_number=1,
                file_extension=image_1_ext
            )

            # Update URL in brand
            brand.product_image_1_url = image_1_url
            logger.info(f"Image 1 uploaded | brand_id={brand_id} | url={image_1_url}")

        except HTTPException as e:
            # Validation error - re-raise
            logger.error(f"Image 1 validation failed | brand_id={brand_id} | error={e.detail}")
            raise
        except Exception as e:
            # Upload failed after retries - keep old URL, add warning
            logger.warning(
                f"Image 1 upload failed, keeping old URL | "
                f"brand_id={brand_id} | error={str(e)}"
            )
            warnings.append("Image 1 upload failed. Previous image retained.")

    # Update image 2 if provided
    if product_image_2 and product_image_2.filename:
        try:
            # Validate image
            image_2_bytes, image_2_ext = await validate_image_file(product_image_2)
            logger.info(f"Image 2 validated | brand_id={brand_id} | ext={image_2_ext}")

            # Upload to S3 (overwrites existing file with same name)
            image_2_url = upload_image_to_supabase_s3(
                image_bytes=image_2_bytes,
                brand_id=str(brand.id),
                image_number=2,
                file_extension=image_2_ext
            )

            # Update URL in brand
            brand.product_image_2_url = image_2_url
            logger.info(f"Image 2 uploaded | brand_id={brand_id} | url={image_2_url}")

        except HTTPException as e:
            # Validation error - re-raise
            logger.error(f"Image 2 validation failed | brand_id={brand_id} | error={e.detail}")
            raise
        except Exception as e:
            # Upload failed after retries - keep old URL, add warning
            logger.warning(
                f"Image 2 upload failed, keeping old URL | "
                f"brand_id={brand_id} | error={str(e)}"
            )
            warnings.append("Image 2 upload failed. Previous image retained.")

    # Commit changes to database
    try:
        db.commit()
        db.refresh(brand)
        logger.info(f"Brand updated successfully | brand_id={brand_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update brand in database | brand_id={brand_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update brand in database")

    response = {
        "id": str(brand.id),
        "title": brand.title,
        "description": brand.description,
        "product_image_1_url": brand.product_image_1_url,
        "product_image_2_url": brand.product_image_2_url,
        "created_at": brand.created_at,
    }

    if warnings:
        response["warnings"] = warnings

    return response


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a brand and its associated S3 images."""
    logger.info(f"Deleting brand | brand_id={brand_id} | user_id={current_user.id}")

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

    # Check if brand has campaigns
    if len(brand.campaigns) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete brand with {len(brand.campaigns)} campaign(s). Please delete campaigns first."
        )

    # Extract image URLs before deletion
    image_1_url = brand.product_image_1_url
    image_2_url = brand.product_image_2_url

    try:
        # Step 1: Delete S3 images (don't fail if S3 deletion fails)
        if image_1_url:
            try:
                success = delete_image_from_supabase_s3(image_1_url)
                if success:
                    logger.info(f"Image 1 deleted from S3 | brand_id={brand_id}")
                else:
                    logger.warning(f"Failed to delete image 1 from S3 | brand_id={brand_id} | url={image_1_url}")
            except Exception as e:
                logger.error(f"Error deleting image 1 from S3 | brand_id={brand_id} | error={str(e)}")

        if image_2_url:
            try:
                success = delete_image_from_supabase_s3(image_2_url)
                if success:
                    logger.info(f"Image 2 deleted from S3 | brand_id={brand_id}")
                else:
                    logger.warning(f"Failed to delete image 2 from S3 | brand_id={brand_id} | url={image_2_url}")
            except Exception as e:
                logger.error(f"Error deleting image 2 from S3 | brand_id={brand_id} | error={str(e)}")

        # Step 2: Delete associated creative bibles first (they will cascade delete chat messages)
        creative_bibles = db.query(CreativeBible).filter(CreativeBible.brand_id == brand_uuid).all()
        if creative_bibles:
            logger.info(f"Deleting {len(creative_bibles)} creative bible(s) for brand {brand_id}")
            for creative_bible in creative_bibles:
                db.delete(creative_bible)
            # Flush to ensure creative bibles are deleted before brand deletion
            db.flush()

        # Step 3: Delete the brand from database
        db.delete(brand)
        db.commit()
        logger.info(f"Brand deleted successfully | brand_id={brand.id} | user_id={current_user.id}")
        return {"message": "Brand deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting brand {brand_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete brand: {str(e)}")

