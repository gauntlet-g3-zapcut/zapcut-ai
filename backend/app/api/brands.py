from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.brand import Brand
from app.models.user import User
from app.api.auth import get_current_user
from app.services.storage import upload_file_to_storage
import uuid

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("/")
async def list_brands(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all brands for current user"""
    brands = db.query(Brand).filter(Brand.user_id == current_user.id).all()
    
    return [
        {
            "id": str(brand.id),
            "title": brand.title,
            "description": brand.description,
            "product_image_1_url": brand.product_image_1_url,
            "product_image_2_url": brand.product_image_2_url,
            "created_at": brand.created_at.isoformat(),
            "campaign_count": len(brand.campaigns),
        }
        for brand in brands
    ]


@router.post("/")
async def create_brand(
    title: str = Form(...),
    description: str = Form(...),
    product_image_1: UploadFile = File(...),
    product_image_2: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new brand"""
    # Upload images to Supabase Storage (with fallback for testing)
    try:
        image_1_path = f"brands/{uuid.uuid4()}/{product_image_1.filename}"
        image_2_path = f"brands/{uuid.uuid4()}/{product_image_2.filename}"
        
        image_1_url = await upload_file_to_storage(
            product_image_1,
            bucket="brands",
            path=image_1_path
        )
        image_2_url = await upload_file_to_storage(
            product_image_2,
            bucket="brands",
            path=image_2_path
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Supabase Storage upload failed: {e}. Using placeholder URLs.", exc_info=True)
        # Fallback to simple placeholder (via.placeholder.com is unreliable)
        image_1_url = "https://placehold.co/400x400/e2e8f0/64748b?text=Product+Image+1"
        image_2_url = "https://placehold.co/400x400/e2e8f0/64748b?text=Product+Image+2"
    
    brand = Brand(
        user_id=current_user.id,
        title=title,
        description=description,
        product_image_1_url=image_1_url,
        product_image_2_url=image_2_url,
    )
    
    db.add(brand)
    db.commit()
    db.refresh(brand)
    
    return {
        "id": str(brand.id),
        "title": brand.title,
        "description": brand.description,
        "product_image_1_url": brand.product_image_1_url,
        "product_image_2_url": brand.product_image_2_url,
        "created_at": brand.created_at.isoformat(),
    }


@router.get("/{brand_id}")
async def get_brand(
    brand_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get brand details"""
    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(brand_id),
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
        "created_at": brand.created_at.isoformat(),
        "campaigns": [
            {
                "id": str(campaign.id),
                "status": campaign.status,
                "created_at": campaign.created_at.isoformat(),
            }
            for campaign in brand.campaigns
        ],
    }


