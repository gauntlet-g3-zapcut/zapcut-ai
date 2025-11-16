from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models.brand import Brand
from app.models.user import User
from app.models.creative_bible import CreativeBible
from app.api.auth import get_current_user
from app.services.storage import upload_file_to_storage
from app.services.openai_service import generate_creative_bible_from_answers
import uuid

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("/")
async def list_brands(
    db: Session = Depends(get_db)
):
    """List all brands (skip auth for development)"""
    brands = db.query(Brand).all()
    
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
        print(f"⚠️  Supabase Storage upload failed: {e}. Using placeholder URLs.")
        # Fallback to simple placeholder (via.placeholder.com is unreliable)
        image_1_url = "https://placehold.co/400x400/e2e8f0/64748b?text=Product+Image+1"
        image_2_url = "https://placehold.co/400x400/e2e8f0/64748b?text=Product+Image+2"
    
    # Get or create a mock user (skip authentication)
    mock_user = db.query(User).filter(User.email == "dev@example.com").first()
    if not mock_user:
        mock_user = User(email="dev@example.com", supabase_uid="mock-user-123")
        db.add(mock_user)
        db.commit()
        db.refresh(mock_user)

    brand = Brand(
        user_id=mock_user.id,
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
    db: Session = Depends(get_db)
):
    """Get brand details"""
    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(brand_id)
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


from typing import Optional
from pydantic import validator
from sqlalchemy.exc import IntegrityError


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
    db: Session = Depends(get_db)
):
    """Create a creative bible from user preferences"""

    try:
        # Get brand
        brand = db.query(Brand).filter(
            Brand.id == uuid.UUID(brand_id)
        ).first()

        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

        # Prepare brand info for OpenAI
        brand_info = {
            "title": brand.title,
            "description": brand.description
        }

        # Convert answers model to dict
        answers_dict = request.answers.dict(exclude_none=True)

        # Generate creative bible from user answers using OpenAI
        print(f"\n🎨 Generating creative bible for brand: {brand.title}")
        print(f"   User preferences: {answers_dict}")

        try:
            creative_bible_data = generate_creative_bible_from_answers(
                answers_dict,
                brand_info
            )
            print(f"   ✅ Creative bible generated")
        except Exception as e:
            print(f"   ❌ OpenAI generation failed: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate creative bible: {str(e)}"
            )

        # Check if creative bible already exists for this brand
        existing_bible = db.query(CreativeBible).filter(
            CreativeBible.brand_id == brand.id
        ).first()

        if existing_bible:
            # Update existing
            existing_bible.creative_bible = creative_bible_data
            existing_bible.conversation_history = answers_dict  # Store answers for compatibility
            db.commit()
            db.refresh(existing_bible)
            creative_bible = existing_bible
            print(f"   ✅ Updated existing creative bible: {creative_bible.id}")
        else:
            # Create new
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
                print(f"   ✅ Created new creative bible: {creative_bible.id}")
            except IntegrityError:
                # Race condition: another request created it
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
                    print(f"   ✅ Updated (race condition) creative bible: {creative_bible.id}")
                else:
                    raise

        return {
            "creative_bible_id": str(creative_bible.id),
            "creative_bible": creative_bible_data
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating creative bible: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create creative bible. Please try again."
        )


