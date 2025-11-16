"""Brands API routes."""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.brand import Brand
from app.models.user import User
from app.models.creative_bible import CreativeBible
from app.api.auth import get_current_user
from app.services.storage import upload_file_to_storage
from app.services.openai_service import generate_creative_bible_from_answers

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
    # Upload images to Supabase Storage
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

class AnswersModel(BaseModel):
    style: Optional[str] = None
    audience: Optional[str] = None
    emotion: Optional[str] = None
    pacing: Optional[str] = None
    colors: Optional[str] = None

    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None"""
        if isinstance(v, str) and not v.strip():
            return None
        return v


class CreateCreativeBibleRequest(BaseModel):
    answers: AnswersModel

    @validator('answers')
    def validate_has_answers(cls, v):
        """Ensure at least one answer is provided"""
        values_dict = v.dict()
        if not any(values_dict.values()):
            raise ValueError('At least one answer must be provided')
        return v


@router.post("/{brand_id}/creative-bible")
async def create_creative_bible(
    brand_id: str,
    request: CreateCreativeBibleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a creative bible from user preferences"""

    print(f"\n{'='*80}")
    print(f"🎨 CREATE CREATIVE BIBLE - Request received")
    print(f"{'='*80}")
    print(f"   Brand ID: {brand_id}")
    print(f"   Answers: {request.answers.dict(exclude_none=True)}")
    print(f"{'='*80}\n")

    try:
        # Get brand
        print(f"📋 Step 1: Looking up brand with ID: {brand_id}")
        brand = db.query(Brand).filter(
            Brand.id == uuid.UUID(brand_id),
            Brand.user_id == current_user.id
        ).first()

        if not brand:
            print(f"❌ ERROR: Brand not found for ID: {brand_id}")
            raise HTTPException(status_code=404, detail="Brand not found")

        print(f"✅ Brand found: {brand.title} (ID: {brand.id})")

        # Prepare brand info for OpenAI
        brand_info = {
            "title": brand.title,
            "description": brand.description
        }

        # Convert answers model to dict
        answers_dict = request.answers.dict(exclude_none=True)

        # Generate creative bible from user answers using OpenAI
        print(f"\n📋 Step 2: Generating creative bible from user answers")
        print(f"   Brand: {brand.title}")
        print(f"   User preferences: {answers_dict}")

        try:
            print(f"   🤖 Calling OpenAI to generate creative bible...")
            creative_bible_data = generate_creative_bible_from_answers(
                answers_dict,
                brand_info
            )
            print(f"   ✅ OpenAI generation successful")
            print(f"   Generated data keys: {list(creative_bible_data.keys())}")
        except Exception as e:
            print(f"   ❌ ERROR: OpenAI generation failed")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   Exception message: {str(e)}")
            import traceback
            print(f"   Traceback:\n{traceback.format_exc()}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate creative bible: {str(e)}"
            )

        # Check if creative bible already exists for this brand
        print(f"\n📋 Step 3: Checking for existing creative bible")
        existing_bible = db.query(CreativeBible).filter(
            CreativeBible.brand_id == brand.id
        ).first()

        if existing_bible:
            print(f"   ℹ️  Found existing creative bible: {existing_bible.id}")
        else:
            print(f"   ℹ️  No existing creative bible found, will create new one")

        if existing_bible:
            # Update existing
            print(f"   📝 Updating existing creative bible...")
            existing_bible.creative_bible = creative_bible_data
            existing_bible.conversation_history = answers_dict  # Store answers for compatibility
            try:
                db.commit()
                db.refresh(existing_bible)
                creative_bible = existing_bible
                print(f"   ✅ Successfully updated creative bible: {creative_bible.id}")
            except Exception as e:
                print(f"   ❌ ERROR: Failed to update existing creative bible")
                print(f"   Exception: {str(e)}")
                db.rollback()
                raise
        else:
            # Create new
            print(f"   📝 Creating new creative bible...")
            creative_bible = CreativeBible(
                brand_id=brand.id,
                name=f"{brand.title} Creative Bible",
                creative_bible=creative_bible_data,
                conversation_history=answers_dict,  # Store answers for compatibility
                reference_image_urls={}
            )

            try:
                db.add(creative_bible)
                db.commit()
                db.refresh(creative_bible)
                print(f"   ✅ Successfully created new creative bible: {creative_bible.id}")
            except IntegrityError as e:
                # Race condition: another request created it
                print(f"   ⚠️  IntegrityError (race condition detected): {str(e)}")
                print(f"   🔄 Attempting to update existing record instead...")
                db.rollback()
                existing_bible = db.query(CreativeBible).filter(
                    CreativeBible.brand_id == brand.id
                ).first()
                if existing_bible:
                    existing_bible.creative_bible = creative_bible_data
                    existing_bible.conversation_history = answers_dict
                    db.commit()
                    db.refresh(existing_bible)
                    creative_bible = existing_bible
                    print(f"   ✅ Successfully updated (after race condition) creative bible: {creative_bible.id}")
                else:
                    print(f"   ❌ ERROR: Race condition but no existing bible found")
                    raise

        print(f"\n✅ SUCCESS: Creative bible operation completed")
        print(f"   Creative Bible ID: {creative_bible.id}")
        print(f"{'='*80}\n")

        return {
            "creative_bible_id": str(creative_bible.id),
            "creative_bible": creative_bible_data
        }

    except HTTPException as http_ex:
        print(f"\n❌ HTTP EXCEPTION in create_creative_bible")
        print(f"   Status: {http_ex.status_code}")
        print(f"   Detail: {http_ex.detail}")
        print(f"{'='*80}\n")
        raise
    except Exception as e:
        db.rollback()
        print(f"\n❌ UNEXPECTED ERROR in create_creative_bible")
        print(f"   Exception type: {type(e).__name__}")
        print(f"   Exception message: {str(e)}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        print(f"{'='*80}\n")
        raise HTTPException(
            status_code=500,
            detail="Failed to create creative bible. Please try again."
        )
