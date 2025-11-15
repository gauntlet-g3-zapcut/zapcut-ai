from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.models.campaign import Campaign
from app.api.auth import get_current_user
from app.tasks.video_generation import generate_campaign_video
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
    """Create a new campaign and start video generation"""
    # Get brand
    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(request.brand_id),
        Brand.user_id == current_user.id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get creative bible
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == uuid.UUID(request.creative_bible_id),
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    # Create campaign
    campaign = Campaign(
        brand_id=brand.id,
        creative_bible_id=creative_bible.id,
        storyline={},
        sora_prompts=[],
        suno_prompt="",
        final_video_url="",
        status="pending"
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Start video generation task
    generate_campaign_video.delay(str(campaign.id))
    
    return {
        "campaign_id": str(campaign.id),
        "status": "pending",
        "message": "Campaign created. Video generation started."
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
        "final_video_url": campaign.final_video_url if campaign.status == "completed" else None
    }

