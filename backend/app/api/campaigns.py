"""Campaigns API routes."""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.creative_bible import CreativeBible
from app.models.user import User
from app.services.storage import upload_bytes
from app.tasks.video_generation import (
    DEFAULT_GENERATION_MODE,
    DEFAULT_VIDEO_MODEL,
    DEFAULT_VIDEO_RESOLUTION,
    get_generation_settings,
    is_sequential_mode,
    map_duration_to_sora_seconds,
    resolve_model_version,
    resolve_resolution_settings,
    update_scene_status_safe,
    extract_video_url,
    extract_last_frame,
)

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
                    logger.warning("REDIS_URL not set, falling back to async task")
                    asyncio.create_task(start_video_generation(str(campaign.id), db))
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
    """Get campaign generation status."""
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
    
    # Get sora_prompts from campaign
    sora_prompts = campaign.sora_prompts or []
    # Create a lookup dict by scene_number
    prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in sora_prompts}
    
    # Build detailed scene status array
    scene_statuses = []
    for i, scene_data in enumerate(scenes_data):
        scene_num = scene_data.get("scene_number", i + 1)
        scene_title = scene_data.get("title", f"Scene {scene_num}")
        
        # Find matching video_url entry
        video_entry = next((v for v in video_urls if v.get("scene_number") == scene_num), None)
        
        scene_status = {
            "scene_number": scene_num,
            "title": scene_title,
            "status": video_entry.get("status", "pending") if video_entry else "pending",
            "video_url": video_entry.get("video_url") if video_entry else None,
            "error": video_entry.get("error") if video_entry else None,
            "sora_prompt": prompt_lookup.get(scene_num)
        }
        scene_statuses.append(scene_status)
    
    # Calculate summary stats
    completed_scenes = len([s for s in scene_statuses if s.get("status") == "completed" and s.get("video_url")])
    generating_scenes = len([s for s in scene_statuses if s.get("status") in ["generating", "retrying"]])
    failed_scenes = len([s for s in scene_statuses if s.get("status") == "failed"])
    
    # Find current scene being generated (first scene that's generating)
    current_scene = None
    if campaign.status == "processing":
        for scene_status in scene_statuses:
            if scene_status.get("status") in ["generating", "retrying"]:
                current_scene = scene_status.get("scene_number")
                break
        # Fallback: if no generating scenes, use first pending scene
        if not current_scene:
            for scene_status in scene_statuses:
                if scene_status.get("status") == "pending":
                    current_scene = scene_status.get("scene_number")
                    break
    
    return {
        "campaign_id": str(campaign.id),
        "status": campaign.status,
        "final_video_url": campaign.final_video_url if campaign.status == "completed" else None,
        "sora_prompts": sora_prompts,  # Include all sora_prompts
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
            "scenes": scene_statuses  # Detailed per-scene status with video_urls and sora_prompts
        }
    }


@router.post("/{campaign_id}/approve")
async def approve_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a draft campaign and start video generation."""
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

    # Update status to pending
    campaign.status = "pending"
    db.commit()
    db.refresh(campaign)

    logger.info(f"Campaign {campaign_id} status updated to pending")

    # Start video generation
    try:
        if settings.REPLICATE_API_TOKEN:
            if settings.REDIS_URL:
                from app.tasks.video_generation import start_video_generation_task
                start_video_generation_task.delay(str(campaign.id))
                logger.info(f"Enqueued video generation task for campaign: {campaign.id}")
                message = "Campaign approved. Video generation started."
            else:
                logger.warning("REDIS_URL not set, falling back to async task")
                asyncio.create_task(start_video_generation(str(campaign.id), db))
                message = "Campaign approved. Video generation started."
        else:
            logger.warning("REPLICATE_API_TOKEN not set, video generation will not start")
            message = "Campaign approved. Video generation will start once API token is configured."
    except Exception as e:
        logger.error(f"Failed to start video generation: {e}", exc_info=True)
        message = "Campaign approved. Video generation will start soon."

    return {
        "campaign_id": str(campaign.id),
        "status": "pending",
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
    generation_settings: Dict[str, str],
    max_retries: int = 2,
    seed_image_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate video for a single scene with retry logic."""
    scene_num = scene.get("scene_number", scene_index + 1)
    scene_title = scene.get("title", f"Scene {scene_num}")
    scene_description = scene.get("description", "")
    visual_notes = scene.get("visual_notes", "")
    duration = scene.get("duration", 6.0)

    sora_prompt = f"{scene_title}. {scene_description}. {visual_notes}".strip()
    logger.info("Fallback generation started | campaign=%s | scene=%s", campaign_id, scene_num)

    video_model = generation_settings.get("video_model", DEFAULT_VIDEO_MODEL)
    video_resolution = generation_settings.get("video_resolution", DEFAULT_VIDEO_RESOLUTION)
    generation_mode = generation_settings.get("generation_mode", DEFAULT_GENERATION_MODE)
    model_version = resolve_model_version(video_model)
    resolution_settings = resolve_resolution_settings(video_resolution)
    sora_seconds = map_duration_to_sora_seconds(duration)

    # Update status to generating
    update_scene_status_safe(
        campaign_id,
        scene_num,
        "generating",
        target_resolution=video_resolution,
        video_model=video_model,
        seed_image_url=seed_image_url,
    )

    loop = asyncio.get_event_loop()
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(
                    "Fallback retry | campaign=%s | scene=%s | attempt=%s/%s",
                    campaign_id,
                    scene_num,
                    attempt + 1,
                    max_retries + 1,
                )
                await asyncio.sleep(2 ** attempt)

            input_payload: Dict[str, Any] = {
                "prompt": sora_prompt,
                "seconds": sora_seconds,
                "aspect_ratio": "16:9",
                "resolution": video_resolution,
                "output_height": resolution_settings["height"],
                "output_width": resolution_settings["width"],
            }

            if seed_image_url:
                input_payload["init_image"] = seed_image_url
                input_payload["seed_image"] = seed_image_url

            output = await loop.run_in_executor(
                None,
                lambda: client.run(
                    model_version,
                    input=input_payload,
                ),
            )

            video_url = extract_video_url(output)
            if not video_url:
                raise ValueError(f"No video URL returned from Replicate for scene {scene_num}")

            # Download the generated video to upload into our storage bucket for consistency
            with httpx.Client(timeout=60.0) as http_client:
                video_response = http_client.get(video_url)
                video_response.raise_for_status()
                video_bytes = video_response.content

            bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
            storage_key = f"generated/{campaign_id}/scene-{scene_num}/fallback-{uuid.uuid4()}.mp4"
            s3_video_url = upload_bytes(
                bucket_name=bucket_name,
                file_key=storage_key,
                data=video_bytes,
                content_type="video/mp4",
                acl="public-read",
            )

            logger.info(
                "Fallback generation uploaded video | campaign=%s | scene=%s | url=%s",
                campaign_id,
                scene_num,
                s3_video_url,
            )

            new_seed_image_url = None
            if is_sequential_mode(generation_mode):
                frame_bytes = extract_last_frame(video_bytes)
                if frame_bytes:
                    seed_key = f"generated/{campaign_id}/scene-{scene_num}/fallback-seed-{uuid.uuid4()}.png"
                    try:
                        new_seed_image_url = upload_bytes(
                            bucket_name=bucket_name,
                            file_key=seed_key,
                            data=frame_bytes,
                            content_type="image/png",
                            acl="public-read",
                        )
                        logger.info(
                            "Fallback generation uploaded seed image | campaign=%s | scene=%s | key=%s",
                            campaign_id,
                            scene_num,
                            seed_key,
                        )
                    except Exception as seed_error:
                        logger.error(
                            "Fallback seed upload failed | campaign=%s | scene=%s | error=%s",
                            campaign_id,
                            scene_num,
                            seed_error,
                        )

            update_scene_status_safe(
                campaign_id,
                scene_num,
                "completed",
                video_url=s3_video_url,
                duration=duration,
                target_resolution=video_resolution,
                video_model=video_model,
                seed_image_url=new_seed_image_url,
            )

            return {
                "scene_number": scene_num,
                "video_url": s3_video_url,
                "status": "completed",
                "duration": duration,
                "prompt": sora_prompt,
                "seed_image_url": new_seed_image_url,
            }

        except Exception as scene_error:
            last_error = scene_error
            logger.error(
                "Fallback generation error | campaign=%s | scene=%s | attempt=%s | error=%s",
                campaign_id,
                scene_num,
                attempt + 1,
                scene_error,
                exc_info=True,
            )

            if attempt < max_retries:
                update_scene_status_safe(
                    campaign_id,
                    scene_num,
                    "retrying",
                    error=str(scene_error),
                    target_resolution=video_resolution,
                    video_model=video_model,
                )
            else:
                update_scene_status_safe(
                    campaign_id,
                    scene_num,
                    "failed",
                    error=str(scene_error),
                    target_resolution=video_resolution,
                    video_model=video_model,
                )

    return {
        "scene_number": scene_num,
        "video_url": None,
        "status": "failed",
        "error": str(last_error) if last_error else "Unknown error",
        "prompt": sora_prompt,
    }


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
            
            generation_settings = get_generation_settings(campaign)
            generation_mode = generation_settings["generation_mode"]
            video_resolution = generation_settings["video_resolution"]
            video_model = generation_settings["video_model"]
            
            # Initialize Replicate client
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            logger.info(
                "Initialized Replicate client for fallback generation | campaign=%s | mode=%s | model=%s | resolution=%s",
                campaign_id,
                generation_mode,
                video_model,
                video_resolution,
            )
            
            # Initialize scene entries
            scene_video_urls = [
                {
                    "scene_number": scene.get("scene_number", i + 1),
                    "video_url": None,
                    "status": "pending",
                    "retry_count": 0,
                    "target_resolution": video_resolution,
                    "video_model": video_model,
                    "seed_image_url": None,
                }
                for i, scene in enumerate(scenes)
            ]
            campaign.video_urls = scene_video_urls
            db.commit()
            logger.info(f"Initialized {len(scene_video_urls)} scene entries for campaign {campaign_id}")
            
            sora_prompts = []
            final_scene_video_urls = []
            
            if is_sequential_mode(generation_mode):
                logger.info(
                    "Fallback sequential generation of %s scenes | campaign=%s",
                    len(scenes),
                    campaign_id,
                )
                seed_for_next: Optional[str] = None
                for i, scene in enumerate(scenes):
                    try:
                        result = await generate_single_scene(
                            campaign_id,
                            scene,
                            i,
                            client,
                            generation_settings,
                            seed_image_url=seed_for_next,
                        )
                    except Exception as exc:
                        logger.error(
                            "Sequential fallback error | campaign=%s | scene_index=%s | error=%s",
                            campaign_id,
                            i,
                            exc,
                            exc_info=True,
                        )
                        break
                    
                    final_scene_video_urls.append({
                        "scene_number": result.get("scene_number", i + 1),
                        "video_url": result.get("video_url"),
                        "status": result.get("status"),
                        "duration": result.get("duration"),
                        "error": result.get("error"),
                        "target_resolution": video_resolution,
                        "video_model": video_model,
                        "seed_image_url": result.get("seed_image_url"),
                    })
                    
                    if result.get("prompt"):
                        sora_prompts.append({
                            "scene_number": result.get("scene_number", i + 1),
                            "prompt": result["prompt"],
                        })
                    
                    if result.get("status") != "completed":
                        logger.warning(
                            "Sequential fallback stopping after non-completed scene | campaign=%s | scene=%s | status=%s",
                            campaign_id,
                            result.get("scene_number"),
                            result.get("status"),
                        )
                        break
                    
                    seed_for_next = result.get("seed_image_url")
            else:
                logger.info(
                    "Fallback parallel generation of %s scenes | campaign=%s",
                    len(scenes),
                    campaign_id,
                )
                tasks = [
                    generate_single_scene(campaign_id, scene, i, client, generation_settings)
                    for i, scene in enumerate(scenes)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
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
                            "error": result.get("error"),
                            "target_resolution": video_resolution,
                            "video_model": video_model,
                            "seed_image_url": result.get("seed_image_url"),
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

