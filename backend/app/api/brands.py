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
                "product_image_1_url": brand.product_image_1_url,
                "product_image_2_url": brand.product_image_2_url,
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
    """Create a new brand."""
    # TODO: Upload images to storage
    # For now, use placeholder URLs
    image_1_url = f"https://placehold.co/400x400?text={title}+Image+1"
    image_2_url = f"https://placehold.co/400x400?text={title}+Image+2"
    
    brand = Brand(
        user_id=current_user.id,
        title=title,
        description=description,
        product_image_1_url=image_1_url,
        product_image_2_url=image_2_url,
        created_at=datetime.utcnow().isoformat()
    )
    
    db.add(brand)
    db.commit()
    db.refresh(brand)
    
    logger.info(f"Created brand: {brand.id} for user: {current_user.id}")
    
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
    
    return {
        "id": str(brand.id),
        "title": brand.title,
        "description": brand.description,
        "product_image_1_url": brand.product_image_1_url,
        "product_image_2_url": brand.product_image_2_url,
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
    """Update a brand."""
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
    
    # Update images only if new ones are provided
    if product_image_1:
        # TODO: Upload images to storage
        # For now, use placeholder URLs
        brand.product_image_1_url = f"https://placehold.co/400x400?text={title}+Image+1"
    
    if product_image_2:
        # TODO: Upload images to storage
        # For now, use placeholder URLs
        brand.product_image_2_url = f"https://placehold.co/400x400?text={title}+Image+2"
    
    db.commit()
    db.refresh(brand)
    
    logger.info(f"Updated brand: {brand.id} for user: {current_user.id}")
    
    return {
        "id": str(brand.id),
        "title": brand.title,
        "description": brand.description,
        "product_image_1_url": brand.product_image_1_url,
        "product_image_2_url": brand.product_image_2_url,
        "created_at": brand.created_at,
    }


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a brand."""
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
    
    try:
        # Delete associated creative bibles first (they will cascade delete chat messages)
        creative_bibles = db.query(CreativeBible).filter(CreativeBible.brand_id == brand_uuid).all()
        if creative_bibles:
            logger.info(f"Deleting {len(creative_bibles)} creative bible(s) for brand {brand_id}")
            for creative_bible in creative_bibles:
                db.delete(creative_bible)
            # Flush to ensure creative bibles are deleted before brand deletion
            db.flush()
        
        # Now delete the brand
        db.delete(brand)
        db.commit()
        logger.info(f"Deleted brand: {brand.id} for user: {current_user.id}")
        return {"message": "Brand deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting brand {brand_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete brand: {str(e)}")

