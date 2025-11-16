from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.models.campaign import Campaign
from app.models.generation_job import GenerationJob
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
    """Create a new campaign (video generation must be triggered separately)"""

    # Verify brand exists and belongs to user
    brand = db.query(Brand).filter(
        Brand.id == uuid.UUID(request.brand_id),
        Brand.user_id == current_user.id
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Handle creative_bible_id (may be "default" string or UUID)
    creative_bible_uuid = None
    if request.creative_bible_id and request.creative_bible_id != "default":
        try:
            creative_bible_uuid = uuid.UUID(request.creative_bible_id)
            # Verify it exists
            creative_bible = db.query(CreativeBible).filter(
                CreativeBible.id == creative_bible_uuid,
                CreativeBible.brand_id == uuid.UUID(request.brand_id)
            ).first()
            if not creative_bible:
                raise HTTPException(status_code=404, detail="Creative Bible not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid creative_bible_id format")
    else:
        # Check if a default creative bible already exists
        creative_bible = db.query(CreativeBible).filter(
            CreativeBible.brand_id == uuid.UUID(request.brand_id),
            CreativeBible.name == "default"
        ).first()

        if not creative_bible:
            # Create a default creative bible for this brand
            creative_bible = CreativeBible(
                brand_id=uuid.UUID(request.brand_id),
                name="default",
                creative_bible={},
                reference_image_urls={}
            )
            db.add(creative_bible)
            db.flush()  # Get the ID without committing

        creative_bible_uuid = creative_bible.id

    # Create campaign in database
    campaign = Campaign(
        brand_id=uuid.UUID(request.brand_id),
        creative_bible_id=creative_bible_uuid,
        status="pending",
        generation_stage="not_started",
        generation_progress=0
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    print(f"🚀 CREATE CAMPAIGN + EPIC 5 AUTO-START")
    print(f"   Campaign ID: {campaign.id}")
    print(f"   Brand ID: {request.brand_id}")
    print(f"   Creative Bible ID: {creative_bible_uuid}")
    print(f"   Campaign saved to database")
    print(f"📹 Automatically triggering Epic 5 video generation pipeline...")

    # Automatically trigger Epic 5 TEST MODE video generation
    task_id = None
    try:
        task_result = generate_campaign_video_test_mode.delay(str(campaign.id))
        task_id = task_result.id
        print(f"✅ Epic 5 TEST MODE task queued successfully!")
        print(f"   Celery Task ID: {task_id}")
    except Exception as e:
        print(f"⚠️  Epic 5 task queue error (continuing anyway): {e}")

    return {
        "campaign_id": str(campaign.id),
        "status": "generating",
        "message": "🎬 Epic 5 Video Generation Started! (Auto-triggered)",
        "test_mode": True,
        "epic_5_triggered": True,
        "task_id": task_id
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


@router.post("/{campaign_id}/generate")
async def generate_campaign_video_endpoint(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger Epic 5 video generation for a campaign"""

    print(f"🚀 MANUAL TRIGGER: Epic 5 video generation")
    print(f"   Campaign ID: {campaign_id}")

    try:
        # Trigger Epic 5 TEST MODE video generation task
        generate_campaign_video_test_mode.delay(campaign_id)
        print(f"✅ Epic 5 TEST MODE task queued successfully!")

        return {
            "campaign_id": campaign_id,
            "status": "generating",
            "message": "🎬 Epic 5 Video Generation Started!",
            "test_mode": True
        }
    except Exception as e:
        print(f"❌ Epic 5 task queue error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start video generation: {str(e)}")


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
        "final_video_url": campaign.final_video_url if campaign.status == "completed" else None,
        "logs": campaign.generation_logs if hasattr(campaign, 'generation_logs') and campaign.generation_logs else []
    }


@router.get("/{campaign_id}/task-status/{task_id}")
async def get_task_status(
    campaign_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Celery task status for video generation"""
    from celery.result import AsyncResult
    from app.celery_app import celery_app

    # Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == uuid.UUID(campaign_id)
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get task status from Celery
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
        "campaign_id": campaign_id,
        "task_id": task_id,
        "state": task_result.state,
        "status": task_result.status,
    }

    # Add task-specific info based on state
    if task_result.state == "PENDING":
        response["message"] = "Task is waiting to start..."
        response["progress"] = 0
        response["stage"] = "pending"
    elif task_result.state == "PROGRESS":
        info = task_result.info
        response["progress"] = info.get("progress", 0)
        response["stage"] = info.get("stage", "processing")
        response["message"] = info.get("stage", "Processing...")
    elif task_result.state == "SUCCESS":
        response["progress"] = 100
        response["stage"] = "complete"
        response["message"] = "Video generation complete!"
        response["result"] = task_result.result
        if isinstance(task_result.result, dict):
            response["final_video_url"] = task_result.result.get("final_video_url")
    elif task_result.state == "FAILURE":
        response["progress"] = 0
        response["stage"] = "failed"
        response["message"] = "Video generation failed"
        response["error"] = str(task_result.info)
    else:
        response["message"] = f"Task state: {task_result.state}"
        response["progress"] = 0
        response["stage"] = task_result.state.lower()

    return response


@router.get("/{campaign_id}/generation-jobs")
async def get_generation_jobs(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all generation jobs for a campaign"""
    # Verify campaign exists and user owns it
    campaign = db.query(Campaign).filter(
        Campaign.id == uuid.UUID(campaign_id)
    ).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Query all generation jobs for this campaign
    jobs = db.query(GenerationJob).filter(
        GenerationJob.campaign_id == uuid.UUID(campaign_id)
    ).order_by(GenerationJob.created_at).all()

    # Format results
    return {
        "campaign_id": campaign_id,
        "total_jobs": len(jobs),
        "jobs": [
            {
                "id": str(job.id),
                "job_type": job.job_type,
                "scene_number": job.scene_number,
                "status": job.status,
                "replicate_job_id": job.replicate_job_id,
                "output_url": job.output_url,
                "error_message": job.error_message,
                "input_params": job.input_params,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]
    }

