"""Brands API routes."""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.brand import Brand
from app.models.user import User
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

