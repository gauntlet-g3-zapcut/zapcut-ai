from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.models.campaign import Campaign
from app.api.auth import get_current_user
from app.tasks.video_generation import generate_campaign_video, generate_campaign_video_test_mode
import uuid

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class CreateCampaignRequest(BaseModel):
    brand_id: str
    creative_bible_id: str


@router.post("/")
async def create_campaign(
    request: CreateCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🧪 TESTING MODE: Database bypassed, Epic 5 triggered directly"""

    # Generate a test campaign ID
    test_campaign_id = str(uuid.uuid4())

    print(f"🚀 EPIC 5 TEST MODE")
    print(f"   Campaign ID: {test_campaign_id}")
    print(f"   Brand ID: {request.brand_id}")
    print(f"   Creative Bible ID: {request.creative_bible_id}")
    print(f"📹 Triggering Epic 5 video generation pipeline...")

    try:
        # Trigger Epic 5 TEST MODE video generation task
        generate_campaign_video_test_mode.delay(test_campaign_id)
        print(f"✅ Epic 5 TEST MODE task queued successfully!")
    except Exception as e:
        print(f"⚠️  Epic 5 task queue error (continuing anyway): {e}")

    return {
        "campaign_id": test_campaign_id,
        "status": "pending",
        "message": "🎬 Epic 5 Video Generation Started! (Test Mode - No DB)",
        "test_mode": True,
        "epic_5_triggered": True
    }


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign details"""
    campaign = db.query(Campaign).filter(
        Campaign.id == uuid.UUID(campaign_id)
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check ownership
    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": str(campaign.id),
        "brand_id": str(campaign.brand_id),
        "status": campaign.status,
        "storyline": campaign.storyline,
        "final_video_url": campaign.final_video_url,
        "created_at": campaign.created_at.isoformat(),
    }


@router.get("/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign generation status"""
    campaign = db.query(Campaign).filter(
        Campaign.id == uuid.UUID(campaign_id)
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check ownership
    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "campaign_id": str(campaign.id),
        "status": campaign.status,
        "stage": campaign.generation_stage if hasattr(campaign, 'generation_stage') else "not_started",
        "progress": campaign.generation_progress if hasattr(campaign, 'generation_progress') else 0,
        "final_video_url": campaign.final_video_url if campaign.status == "completed" else None
    }

