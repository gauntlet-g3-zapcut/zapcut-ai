"""Campaigns API routes."""
import logging
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.models.campaign import Campaign
from app.api.auth import get_current_user
from app.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class CreateCampaignRequest(BaseModel):
    brand_id: str
    creative_bible_id: str
    status: str = "draft"  # Default to draft, can be "draft" or "pending"


@router.get("/")
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all campaigns for current user across all brands."""
    # Get all brands for the user
    user_brands = db.query(Brand).filter(Brand.user_id == current_user.id).all()
    brand_ids = [brand.id for brand in user_brands]
    
    # Get all campaigns for those brands
    campaigns = db.query(Campaign).filter(Campaign.brand_id.in_(brand_ids)).order_by(Campaign.created_at.desc()).all()
    
    logger.info(f"Found {len(campaigns)} campaigns for user {current_user.id}")
    
    return [
        {
            "id": str(campaign.id),
            "brand_id": str(campaign.brand_id),
            "brand_title": campaign.brand.title,
            "status": campaign.status,
            "final_video_url": campaign.final_video_url,
            "images": campaign.images or [],  # Reference/inspiration images
            "created_at": campaign.created_at,
            "video_urls_count": len(campaign.video_urls) if campaign.video_urls else 0,
        }
        for campaign in campaigns
    ]


@router.post("/")
async def create_campaign(
    request: CreateCampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new campaign and start video generation."""
    logger.info(f"Creating campaign for brand_id: {request.brand_id}, creative_bible_id: {request.creative_bible_id}, user_id: {current_user.id}")
    
    try:
        brand_uuid = uuid.UUID(request.brand_id)
        creative_bible_uuid = uuid.UUID(request.creative_bible_id)
        logger.debug(f"Parsed UUIDs - brand: {brand_uuid}, creative_bible: {creative_bible_uuid}")
    except ValueError as e:
        logger.error(f"Invalid ID format: {e}")
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()
    
    if not brand:
        logger.warning(f"Brand not found: {brand_uuid} for user: {current_user.id}")
        raise HTTPException(status_code=404, detail="Brand not found")
    
    logger.info(f"Found brand: {brand.title} (id: {brand.id})")
    
    creative_bible = db.query(CreativeBible).filter(
        CreativeBible.id == creative_bible_uuid,
        CreativeBible.brand_id == brand.id
    ).first()
    
    if not creative_bible:
        logger.warning(f"Creative Bible not found: {creative_bible_uuid} for brand: {brand.id}")
        raise HTTPException(status_code=404, detail="Creative Bible not found")
    
    logger.info(f"Found creative bible: {creative_bible.name} (id: {creative_bible.id})")
    
    # Get storyline and sora_prompts from creative bible
    storyline_data = creative_bible.creative_bible.get("storyline", {}) if creative_bible.creative_bible else {}
    suno_prompt = creative_bible.creative_bible.get("suno_prompt", "") if creative_bible.creative_bible else ""
    sora_prompts = creative_bible.creative_bible.get("sora_prompts", []) if creative_bible.creative_bible else []
    
    logger.info(f"Storyline data: {len(storyline_data.get('scenes', []))} scenes, suno_prompt: {bool(suno_prompt)}, sora_prompts: {len(sora_prompts)}")
    
    campaign = Campaign(
        brand_id=brand.id,
        creative_bible_id=creative_bible.id,
        storyline=storyline_data,
        sora_prompts=sora_prompts,
        suno_prompt=suno_prompt,
        final_video_url="",
        status=request.status,  # Use status from request (draft or pending)
        audio_status="pending",  # Initialize audio status
        created_at=datetime.utcnow()
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    logger.info(f"Created campaign: {campaign.id} for brand: {request.brand_id}, status: {campaign.status}")

    # Only start video generation if status is "pending" (approved)
    if request.status == "pending":
        # Start video generation using Celery (non-blocking)
        try:
            if settings.REPLICATE_API_TOKEN:
                if settings.REDIS_URL:
                    # Use Celery if Redis is configured
                    from app.tasks.video_generation import start_video_generation_task
                    start_video_generation_task.delay(str(campaign.id))
                    logger.info(f"Enqueued video generation task for campaign: {campaign.id}")
                    message = "Campaign approved. Video generation started."
                else:
                    # Fallback to async task if Redis not configured
                    # Don't pass db session - async task will create its own
                    logger.warning("REDIS_URL not set, falling back to async task")
                    asyncio.create_task(start_video_generation(str(campaign.id)))
                    message = "Campaign approved. Video generation started."
            else:
                logger.warning("REPLICATE_API_TOKEN not set, video generation will not start")
                message = "Campaign created. Video generation will start once API token is configured."
        except Exception as e:
            logger.error(f"Failed to start video generation: {e}", exc_info=True)
            message = "Campaign approved. Video generation will start soon."
    else:
        # Draft campaign - no video generation
        message = "Campaign created as draft. Review storyline to approve and start video generation."

    return {
        "campaign_id": str(campaign.id),
        "status": request.status,
        "message": message
    }


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign details."""
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get creative bible data if available
    creative_bible_data = None
    campaign_preferences = None
    if campaign.creative_bible:
        creative_bible_data = campaign.creative_bible.creative_bible
        campaign_preferences = campaign.creative_bible.campaign_preferences

    return {
        "id": str(campaign.id),
        "brand_id": str(campaign.brand_id),
        "creative_bible_id": str(campaign.creative_bible_id) if campaign.creative_bible_id else None,
        "status": campaign.status,
        "pipeline_version": campaign.pipeline_version or "v0",
        "pipeline_stage": campaign.pipeline_stage,
        "storyline": campaign.storyline,
        "creative_bible": creative_bible_data,
        "campaign_preferences": campaign_preferences,
        "images": campaign.images or [],  # Include campaign images
        "final_video_url": campaign.final_video_url,
        "created_at": campaign.created_at,
    }


@router.get("/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campaign generation status with Phase 1 pipeline tracking.

    Returns detailed status including:
    - pipeline_stage: Current stage in the image-first pipeline
    - Per-scene status for images, upscaling, and videos
    - Progress counts for each stage
    """
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Refresh campaign to get latest data from database (important for webhook updates)
    db.refresh(campaign)

    # Calculate scene progress
    video_urls = campaign.video_urls or []
    storyline = campaign.storyline or {}
    scenes_data = storyline.get("scenes", [])
    total_scenes = len(scenes_data)

    # Get sora_prompts from campaign (legacy) and image_prompts (new)
    sora_prompts = campaign.sora_prompts or []
    image_prompts = campaign.image_prompts or []
    prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in sora_prompts}
    image_prompt_lookup = {p.get("scene_number"): p for p in image_prompts}

    # Build detailed scene status array with Phase 1 fields
    scene_statuses = []
    for i, scene_data in enumerate(scenes_data):
        scene_num = scene_data.get("scene_number", i + 1)
        scene_title = scene_data.get("title", f"Scene {scene_num}")

        # Find matching video_url entry (enhanced structure)
        video_entry = next((v for v in video_urls if v.get("scene_number") == scene_num), None)
        image_prompt_entry = image_prompt_lookup.get(scene_num, {})

        scene_status = {
            "scene_number": scene_num,
            "title": scene_title,
            # Overall status (backward compatible)
            "status": video_entry.get("status", "pending") if video_entry else "pending",
            "video_url": video_entry.get("video_url") if video_entry else None,
            "error": video_entry.get("error") if video_entry else None,
            "sora_prompt": prompt_lookup.get(scene_num),

            # Phase 1: Enhanced prompts
            "image_prompt": video_entry.get("image_prompt") if video_entry else image_prompt_entry.get("image_prompt"),
            "motion_prompt": video_entry.get("motion_prompt") if video_entry else image_prompt_entry.get("motion_prompt"),

            # Phase 1: Image generation status
            "base_image_url": video_entry.get("base_image_url") if video_entry else None,
            "image_status": video_entry.get("image_status", "pending") if video_entry else "pending",

            # Phase 1: Upscaling status
            "upscaled_image_url": video_entry.get("upscaled_image_url") if video_entry else None,
            "upscale_status": video_entry.get("upscale_status", "pending") if video_entry else "pending",

            # Phase 1: Video generation status
            "video_status": video_entry.get("video_status", "pending") if video_entry else "pending",

            # Phase 1: Post-processing status (for future phases)
            "processed_video_url": video_entry.get("processed_video_url") if video_entry else None,
            "processing_status": video_entry.get("processing_status", "pending") if video_entry else "pending",
        }
        scene_statuses.append(scene_status)

    # Calculate summary stats for each stage
    images_completed = len([s for s in scene_statuses if s.get("image_status") == "completed"])
    images_generating = len([s for s in scene_statuses if s.get("image_status") == "generating"])
    upscales_completed = len([s for s in scene_statuses if s.get("upscale_status") == "completed"])
    upscales_generating = len([s for s in scene_statuses if s.get("upscale_status") == "generating"])
    videos_completed = len([s for s in scene_statuses if s.get("video_status") == "completed" or (s.get("status") == "completed" and s.get("video_url"))])
    videos_generating = len([s for s in scene_statuses if s.get("video_status") == "generating" or s.get("status") == "generating"])

    # Legacy counts (backward compatible)
    completed_scenes = len([s for s in scene_statuses if s.get("status") == "completed" and s.get("video_url")])
    generating_scenes = len([s for s in scene_statuses if s.get("status") in ["generating", "retrying"]])
    failed_scenes = len([s for s in scene_statuses if s.get("status") == "failed"])

    # Find current scene being processed
    current_scene = None
    if campaign.status == "processing":
        for scene_status in scene_statuses:
            if scene_status.get("status") in ["generating", "retrying"]:
                current_scene = scene_status.get("scene_number")
                break
        if not current_scene:
            for scene_status in scene_statuses:
                if scene_status.get("status") == "pending":
                    current_scene = scene_status.get("scene_number")
                    break

    return {
        "campaign_id": str(campaign.id),
        "status": campaign.status,
        "pipeline_stage": campaign.pipeline_stage or "pending",  # Phase 1: New field
        "director_mode": campaign.director_mode or "surprise_me",  # Phase 1: New field
        "final_video_url": campaign.final_video_url if campaign.status == "completed" else None,
        "sora_prompts": sora_prompts,
        "image_prompts": image_prompts,  # Phase 1: New field
        "audio": {
            "status": campaign.audio_status or "pending",
            "audio_url": campaign.audio_url,
            "error": campaign.audio_generation_error
        },
        "progress": {
            "current_scene": current_scene,
            "completed_scenes": completed_scenes,
            "total_scenes": total_scenes,
            "generating_scenes": generating_scenes,
            "failed_scenes": failed_scenes,
            "scenes": scene_statuses,
            # Phase 1: Stage-specific progress
            "images": {
                "completed": images_completed,
                "generating": images_generating,
                "total": total_scenes
            },
            "upscales": {
                "completed": upscales_completed,
                "generating": upscales_generating,
                "total": total_scenes
            },
            "videos": {
                "completed": videos_completed,
                "generating": videos_generating,
                "total": total_scenes
            }
        }
    }


class SetPipelineVersionRequest(BaseModel):
    pipeline_version: str  # "v0", "v0.5", "v1", "v2", or "v2p"


@router.patch("/{campaign_id}/pipeline-version")
async def set_pipeline_version(
    campaign_id: str,
    request: SetPipelineVersionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set the pipeline version for a draft campaign.

    Must be called before /approve to select which pipeline to use:
    - v0: Original Sora 2 text-to-video (durations 4/8/12s)
    - v0.5: Veo 3.1 text-to-video (durations 4/6/8s)
    - v1: Image-first parallel (Nano Banana → Real-ESRGAN → Veo 3.1)
    - v2: Story-first sequential (GPT-4o story → voiceover → frame seeding)
    """
    if request.pipeline_version not in ["v0", "v0.5", "v1", "v2", "v2p"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pipeline_version: {request.pipeline_version}. Must be 'v0', 'v0.5', 'v1', 'v2', or 'v2p'"
        )

    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.brand.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if campaign.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Can only set pipeline_version on draft campaigns (current status: {campaign.status})"
        )

    campaign.pipeline_version = request.pipeline_version
    db.commit()

    logger.info(f"Campaign {campaign_id} pipeline_version set to {request.pipeline_version}")

    return {
        "campaign_id": str(campaign.id),
        "pipeline_version": campaign.pipeline_version,
        "message": f"Pipeline version set to {request.pipeline_version}"
    }


@router.post("/{campaign_id}/approve")
async def approve_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a draft campaign and start video generation based on pipeline_version.

    Routes to the appropriate pipeline based on campaign.pipeline_version:
    - v0: Original Sora 2 text-to-video (durations 4/8/12s)
    - v0.5: Veo 3.1 text-to-video (durations 4/6/8s) [DEFAULT]
    - v1: Image-first parallel (Nano Banana → Real-ESRGAN → Veo 3.1)
    - v2: Story-first sequential (GPT-4o story → voiceover → frame seeding)

    Set pipeline_version on the campaign before calling this endpoint,
    or it will default to v0.5.
    """
    logger.info(f"Approving campaign: {campaign_id} for user: {current_user.id}")

    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Verify ownership
    if campaign.brand.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to approve campaign {campaign_id} they don't own")
        raise HTTPException(status_code=403, detail="Not authorized to approve this campaign")

    # Check if campaign is in draft status
    if campaign.status != "draft":
        raise HTTPException(status_code=400, detail=f"Campaign is not in draft status (current status: {campaign.status})")

    # Get pipeline version (default to v0.5 for current Veo 3.1 text-to-video)
    pipeline_version = campaign.pipeline_version or "v0.5"
    logger.info(f"Campaign {campaign_id} using pipeline_version={pipeline_version}")

    # Route to appropriate pipeline
    if pipeline_version in ["v0", "v0.5"]:
        # Both v0 and v0.5 use text-to-video, model selected in task
        return await _start_v0_pipeline(campaign, db)
    elif pipeline_version == "v1":
        return await _start_v1_pipeline(campaign, db)
    elif pipeline_version == "v2":
        return await _start_v2_pipeline(campaign, db)
    elif pipeline_version == "v2p":
        return await _start_v2p_pipeline(campaign, db)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown pipeline_version: {pipeline_version}")


async def _start_v0_pipeline(campaign: Campaign, db: Session) -> dict:
    """Start V0/V0.5 text-to-video pipeline.

    V0 Pipeline: Sora 2 text-to-video (durations 4/8/12s)
    V0.5 Pipeline: Veo 3.1 text-to-video (durations 4/6/8s)

    Both pipelines:
    1. Generate videos via text-to-video (model selected by pipeline_version)
    2. Generate background music (ElevenLabs Music)
    3. Assemble final video with cross-dissolve transitions
    """
    # Preserve the pipeline_version (v0 or v0.5) - don't overwrite
    pipeline_version = campaign.pipeline_version or "v0.5"
    campaign.status = "pending"
    campaign.pipeline_stage = "videos_generating"
    # Don't overwrite pipeline_version if already set
    if not campaign.pipeline_version:
        campaign.pipeline_version = "v0.5"
    db.commit()
    db.refresh(campaign)

    logger.info(f"Campaign {campaign.id} starting {pipeline_version} pipeline")

    try:
        if settings.REPLICATE_API_TOKEN:
            if settings.REDIS_URL:
                from app.tasks.video_generation import start_video_generation_task
                start_video_generation_task.delay(str(campaign.id))
                logger.info(f"Enqueued video generation task ({pipeline_version}) for campaign: {campaign.id}")
                message = f"Campaign approved. {pipeline_version} text-to-video pipeline started."
            else:
                message = "Campaign approved. Pipeline will start once Redis is configured."
        else:
            message = "Campaign approved. Video generation will start once API token is configured."
    except Exception as e:
        logger.error(f"Failed to start {pipeline_version} pipeline: {e}", exc_info=True)
        message = "Campaign approved. Pipeline will start soon."

    return {
        "campaign_id": str(campaign.id),
        "status": "pending",
        "pipeline_version": pipeline_version,
        "pipeline_stage": campaign.pipeline_stage,
        "message": message
    }


async def _start_v1_pipeline(campaign: Campaign, db: Session) -> dict:
    """Start V1 image-first parallel pipeline.

    V1 Pipeline (image-first, parallel):
    1. Generate enhanced prompts (image_prompt + motion_prompt) via GPT-4o
    2. Generate images via Nano Banana (parallel)
    3. Upscale images via Real-ESRGAN (parallel)
    4. Generate videos via Veo 3.1 (image-to-video mode, parallel)
    5. Assemble final video with FFmpeg cross-dissolve transitions
    """
    campaign.status = "pending"
    campaign.pipeline_stage = "pending"
    campaign.pipeline_version = "v1"
    campaign.director_mode = campaign.director_mode or "surprise_me"
    db.commit()
    db.refresh(campaign)

    logger.info(f"Campaign {campaign.id} starting V1 pipeline, director_mode={campaign.director_mode}")

    try:
        if settings.OPENAI_API_KEY and settings.REPLICATE_API_TOKEN:
            if settings.REDIS_URL:
                from app.tasks.prompt_generation import generate_enhanced_prompts_task
                generate_enhanced_prompts_task.delay(str(campaign.id))
                logger.info(f"Enqueued prompt generation task for campaign: {campaign.id}")

                if settings.ELEVENLABS_API_KEY:
                    from app.tasks.audio_generation import generate_audio_task
                    generate_audio_task.delay(str(campaign.id))
                    logger.info(f"Enqueued audio generation task for campaign: {campaign.id}")

                message = "Campaign approved. V1 image-first pipeline started."
            else:
                message = "Campaign approved. Pipeline will start once Redis is configured."
        elif not settings.OPENAI_API_KEY:
            # Fallback to V0 if OpenAI not configured
            logger.warning("OPENAI_API_KEY not set, falling back to V0 pipeline")
            if settings.REPLICATE_API_TOKEN and settings.REDIS_URL:
                from app.tasks.video_generation import start_video_generation_task
                start_video_generation_task.delay(str(campaign.id))
                message = "Campaign approved. Fell back to V0 pipeline (OpenAI not configured)."
            else:
                message = "Campaign approved. Please configure API keys."
        else:
            message = "Campaign approved. Video generation will start once API token is configured."
    except Exception as e:
        logger.error(f"Failed to start V1 pipeline: {e}", exc_info=True)
        message = "Campaign approved. Pipeline will start soon."

    return {
        "campaign_id": str(campaign.id),
        "status": "pending",
        "pipeline_version": "v1",
        "pipeline_stage": campaign.pipeline_stage,
        "director_mode": campaign.director_mode,
        "message": message
    }


async def _start_v2_pipeline(campaign: Campaign, db: Session) -> dict:
    """Start V2 story-first sequential pipeline.

    V2 Pipeline (story-first with visual continuity):
    1. Generate story document (GPT-4o Vision) - Full narrative + 5 segments
    2. Generate voiceover (ElevenLabs TTS) - Full 40-second narration
    3. Generate background music (ElevenLabs Music) - Runs parallel with voiceover
    4. Mix final audio (FFmpeg) - Voiceover + music at 30% volume
    5. Sequential video generation (Veo 3.1):
       - Segment 1: Generate scene image, then video
       - Segments 2-5: Extract last frame, seed next video
    6. Assemble final video with cross-dissolve transitions
    """
    campaign.status = "pending"
    campaign.pipeline_stage = "story_generating"
    campaign.pipeline_version = "v2"
    campaign.director_mode = "surprise_me"
    campaign.voiceover_status = "pending"
    campaign.current_segment = 0
    db.commit()
    db.refresh(campaign)

    logger.info(f"Campaign {campaign.id} starting V2 pipeline")

    try:
        if settings.OPENAI_API_KEY and settings.REPLICATE_API_TOKEN:
            if settings.REDIS_URL:
                from app.tasks.story_generation import generate_story_task
                generate_story_task.delay(str(campaign.id))
                logger.info(f"Enqueued story generation task (V2) for campaign: {campaign.id}")
                message = "Campaign approved. V2 story-first pipeline started."
            else:
                message = "Campaign approved. Pipeline will start once Redis is configured."
        elif not settings.OPENAI_API_KEY:
            message = "Campaign approved. V2 pipeline requires OPENAI_API_KEY."
        else:
            logger.warning("REPLICATE_API_TOKEN not set, video generation will not start")
            message = "Campaign approved. Video generation will start once API token is configured."
    except Exception as e:
        logger.error(f"Failed to start V2 pipeline: {e}", exc_info=True)
        message = "Campaign approved. Pipeline will start soon."

    return {
        "campaign_id": str(campaign.id),
        "status": "pending",
        "pipeline_version": "v2",
        "pipeline_stage": campaign.pipeline_stage,
        "message": message
    }


async def _start_v2p_pipeline(campaign: Campaign, db: Session) -> dict:
    """Start V2P story-first PARALLEL pipeline.

    V2P Pipeline (story-first with parallel generation):
    1. Generate story document (GPT-4o Vision) - Viral ad narrative + 5 segments
    2. Generate voiceover (ElevenLabs TTS) - Full 40-second narration (parallel)
    3. Generate background music (ElevenLabs Music) - Runs parallel
    4. Mix final audio (FFmpeg) - Voiceover + music
    5. PARALLEL video generation:
       - Generate character reference image first
       - Generate all 5 scene images in parallel
       - Generate all 5 videos in parallel (with character ref for consistency)
    6. Assemble final video with cross-dissolve transitions

    Much faster than V2 sequential (~3 min vs ~15 min).
    """
    campaign.status = "pending"
    campaign.pipeline_stage = "story_generating"
    campaign.pipeline_version = "v2p"
    campaign.director_mode = "surprise_me"
    campaign.voiceover_status = "pending"
    campaign.current_segment = 0
    db.commit()
    db.refresh(campaign)

    logger.info(f"Campaign {campaign.id} starting V2P (parallel) pipeline")

    try:
        if settings.OPENAI_API_KEY and settings.REPLICATE_API_TOKEN:
            if settings.REDIS_URL:
                from app.tasks.story_generation import generate_story_task
                generate_story_task.delay(str(campaign.id))
                logger.info(f"Enqueued story generation task (V2P) for campaign: {campaign.id}")
                message = "Campaign approved. V2P parallel pipeline started."
            else:
                message = "Campaign approved. Pipeline will start once Redis is configured."
        elif not settings.OPENAI_API_KEY:
            message = "Campaign approved. V2P pipeline requires OPENAI_API_KEY."
        else:
            logger.warning("REPLICATE_API_TOKEN not set, video generation will not start")
            message = "Campaign approved. Video generation will start once API token is configured."
    except Exception as e:
        logger.error(f"Failed to start V2P pipeline: {e}", exc_info=True)
        message = "Campaign approved. Pipeline will start soon."

    return {
        "campaign_id": str(campaign.id),
        "status": "pending",
        "pipeline_version": "v2p",
        "pipeline_stage": campaign.pipeline_stage,
        "message": message
    }


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a campaign."""
    logger.info(f"Deleting campaign: {campaign_id} for user: {current_user.id}")
    
    try:
        campaign_uuid = uuid.UUID(campaign_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid campaign ID")
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify ownership
    if campaign.brand.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to delete campaign {campaign_id} they don't own")
        raise HTTPException(status_code=403, detail="Not authorized to delete this campaign")
    
    # Delete the campaign
    db.delete(campaign)
    db.commit()
    
    logger.info(f"Campaign {campaign_id} deleted successfully by user {current_user.id}")
    
    return {
        "message": "Campaign deleted successfully",
        "campaign_id": campaign_id
    }


async def generate_single_scene(
    campaign_id: str,
    scene: dict,
    scene_index: int,
    client,
    max_retries: int = 2
):
    """Generate video for a single scene with retry logic."""
    from app.database import get_session_local
    
    scene_num = scene.get("scene_number", scene_index + 1)
    scene_title = scene.get("title", f"Scene {scene_num}")
    scene_description = scene.get("description", "")
    visual_notes = scene.get("visual_notes", "")
    duration = scene.get("duration", 6.0)
    
    # Create comprehensive prompt for Sora
    sora_prompt = f"{scene_title}. {scene_description}. {visual_notes}".strip()
    
    logger.info(f"Starting generation for scene {scene_num} in campaign {campaign_id}")
    
    # Sora 2 only accepts seconds: 4, 8, or 12
    # Map scene duration to nearest allowed value
    scene_duration = int(duration)
    if scene_duration <= 4:
        sora_seconds = 4
    elif scene_duration <= 8:
        sora_seconds = 8
    else:
        sora_seconds = 12
    
    # Update scene status to generating
    update_scene_status(campaign_id, scene_num, "generating", None, None)
    
    # Retry logic
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(f"Retrying scene {scene_num}, attempt {attempt + 1}/{max_retries + 1}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # Run the model in a thread pool to avoid blocking (Replicate client.run is synchronous)
            # This allows multiple scenes to generate in parallel
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                lambda: client.run(
                    "openai/sora-2",
                    input={
                        "prompt": sora_prompt,
                        "seconds": sora_seconds,  # Must be 4, 8, or 12
                        "aspect_ratio": "landscape",  # 16:9 landscape
                    }
                )
            )
            
            # Wait for completion and get video URL
            # Replicate returns a generator or direct URL
            video_url = None
            if isinstance(output, str):
                video_url = output
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0] if isinstance(output[0], str) else str(output[0])
            elif hasattr(output, '__iter__'):
                # Handle generator/iterator
                for item in output:
                    if isinstance(item, str):
                        video_url = item
                        break
                if not video_url:
                    video_url = str(list(output)[0]) if output else None
            else:
                video_url = str(output)
            
            if not video_url:
                raise ValueError(f"No video URL returned from Replicate for scene {scene_num}")
            
            # Update scene status to completed
            update_scene_status(campaign_id, scene_num, "completed", video_url, duration)
            
            logger.info(f"Scene {scene_num} video generated successfully: {video_url}")
            
            return {
                "scene_number": scene_num,
                "video_url": video_url,
                "status": "completed",
                "duration": duration,
                "prompt": sora_prompt
            }
            
        except Exception as scene_error:
            last_error = scene_error
            logger.error(f"Failed to generate video for scene {scene_num} (attempt {attempt + 1}): {scene_error}", exc_info=True)
            
            if attempt < max_retries:
                # Update status to retrying
                update_scene_status(campaign_id, scene_num, "retrying", None, None, str(scene_error))
            else:
                # Final failure
                update_scene_status(campaign_id, scene_num, "failed", None, None, str(scene_error))
                logger.error(f"Scene {scene_num} failed after {max_retries + 1} attempts")
    
    # All retries exhausted
    return {
        "scene_number": scene_num,
        "video_url": None,
        "status": "failed",
        "error": str(last_error),
        "prompt": sora_prompt
    }


def update_scene_status(
    campaign_id: str,
    scene_number: int,
    status: str,
    video_url: str = None,
    duration: float = None,
    error: str = None
):
    """Update the status of a specific scene in the campaign."""
    from app.database import get_session_local
    
    db = get_session_local()()
    try:
        campaign_uuid = uuid.UUID(campaign_id)
        campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
        
        if not campaign:
            logger.error(f"Campaign not found when updating scene {scene_number}: {campaign_id}")
            return
        
        # Get current video_urls or initialize
        scene_video_urls = campaign.video_urls or []
        
        # Find and update the scene entry
        scene_found = False
        for scene_entry in scene_video_urls:
            if scene_entry.get("scene_number") == scene_number:
                scene_entry["status"] = status
                if video_url:
                    scene_entry["video_url"] = video_url
                if duration:
                    scene_entry["duration"] = duration
                if error:
                    scene_entry["error"] = error
                scene_found = True
                break
        
        # If scene not found, add it
        if not scene_found:
            scene_video_urls.append({
                "scene_number": scene_number,
                "video_url": video_url,
                "status": status,
                "duration": duration,
                "error": error
            })
        
        campaign.video_urls = scene_video_urls
        db.commit()
        db.refresh(campaign)  # Ensure changes are visible
        
        # Only log important status changes (completed/failed), not every update
        if status in ["completed", "failed"]:
            logger.info(f"Scene {scene_number} {status} for campaign {campaign_id}")
        
    except Exception as e:
        logger.error(f"Error updating scene {scene_number} status: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def start_video_generation(campaign_id: str, db: Session = None):
    """Start video generation process for a campaign using Replicate Sora 2.
    Generates all videos in parallel.
    NOTE: This is kept as fallback if Redis/Celery is not available."""
    logger.info(f"Starting video generation for campaign: {campaign_id}")
    
    try:
        import replicate
        from app.database import get_session_local
        
        # Create own session if not provided (for fallback mode)
        if db is None:
            db = get_session_local()()
            should_close = True
        else:
            should_close = False
        
        try:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return
            
            # Update status to processing
            campaign.status = "processing"
            db.commit()
            logger.info(f"Updated campaign {campaign_id} status to: processing")
            
            # Get storyline
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            
            logger.info(f"Campaign {campaign_id} has {len(scenes)} scenes to generate")
            
            if not scenes:
                logger.warning(f"No scenes found for campaign {campaign_id}, marking as failed")
                campaign.status = "failed"
                db.commit()
                return
            
            if not settings.REPLICATE_API_TOKEN:
                logger.error(f"REPLICATE_API_TOKEN not configured for campaign {campaign_id}")
                campaign.status = "failed"
                db.commit()
                return
            
            # Initialize Replicate client
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            logger.info(f"Initialized Replicate client for campaign {campaign_id}")
            
            # Initialize all scene entries with "pending" status
            scene_video_urls = []
            for i, scene in enumerate(scenes):
                scene_num = scene.get("scene_number", i + 1)
                scene_video_urls.append({
                    "scene_number": scene_num,
                    "video_url": None,
                    "status": "pending"
                })
            
            campaign.video_urls = scene_video_urls
            db.commit()
            logger.info(f"Initialized {len(scene_video_urls)} scene entries for campaign {campaign_id}")
            
            # Generate all videos in parallel
            logger.info(f"Starting parallel generation of {len(scenes)} videos")
            tasks = [
                generate_single_scene(campaign_id, scene, i, client)
                for i, scene in enumerate(scenes)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and collect sora prompts
            sora_prompts = []
            final_scene_video_urls = []
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scene generation task failed with exception: {result}", exc_info=True)
                    continue
                
                if result:
                    final_scene_video_urls.append({
                        "scene_number": result["scene_number"],
                        "video_url": result.get("video_url"),
                        "status": result["status"],
                        "duration": result.get("duration"),
                        "error": result.get("error")
                    })
                    
                    if result.get("prompt"):
                        sora_prompts.append({
                            "scene_number": result["scene_number"],
                            "prompt": result["prompt"]
                        })
            
            # Sort by scene number
            final_scene_video_urls.sort(key=lambda x: x.get("scene_number", 0))
            
            # Update campaign with final results
            db.refresh(campaign)
            campaign.sora_prompts = sora_prompts
            campaign.video_urls = final_scene_video_urls
            
            # Check if all scenes completed successfully
            completed_count = len([v for v in final_scene_video_urls if v.get("status") == "completed" and v.get("video_url")])
            failed_count = len([v for v in final_scene_video_urls if v.get("status") == "failed"])
            
            if completed_count == len(scenes):
                # All scenes completed
                campaign.status = "completed"
                # Use first video URL as final (TODO: composite all scenes)
                if final_scene_video_urls and final_scene_video_urls[0].get("video_url"):
                    campaign.final_video_url = final_scene_video_urls[0]["video_url"]
                logger.info(f"Campaign {campaign_id} completed with all {completed_count} scenes")
            elif completed_count > 0:
                # Some scenes completed, some failed
                campaign.status = "completed"  # Mark as completed if at least one video exists
                if final_scene_video_urls and final_scene_video_urls[0].get("video_url"):
                    campaign.final_video_url = final_scene_video_urls[0]["video_url"]
                logger.warning(f"Campaign {campaign_id} completed with {completed_count}/{len(scenes)} scenes ({failed_count} failed)")
            else:
                # All scenes failed
                campaign.status = "failed"
                logger.error(f"Campaign {campaign_id} failed - no videos generated")
            
            db.commit()
            logger.info(f"Campaign {campaign_id} final status: {campaign.status}")
        
        except Exception as e:
            logger.error(f"Error in video generation for campaign {campaign_id}: {e}", exc_info=True)
            try:
                if db:
                    db.refresh(campaign)
                    campaign.status = "failed"
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update campaign status: {db_error}", exc_info=True)
    finally:
        if should_close and db:
            db.close()

