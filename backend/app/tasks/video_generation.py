"""Celery tasks for video generation."""
import logging
import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any
import replicate
from celery import group
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
SORA_DURATION_OPTIONS = [4, 8, 12]
PREDICTION_TIMEOUT_MINUTES = 15  # For reconciliation
RECONCILIATION_CHECK_INTERVAL = 300  # seconds (5 minutes)
WEBHOOK_VERIFICATION_ENABLED = True


class ReplicateError(Exception):
    """Custom exception for Replicate API errors."""
    pass


@contextmanager
def db_session():
    """Context manager for database sessions with guaranteed cleanup."""
    db = get_session_local()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def map_duration_to_sora_seconds(duration: float) -> int:
    """Map scene duration to nearest Sora-compatible value (4, 8, or 12)."""
    duration_int = int(duration)
    if duration_int <= 4:
        return 4
    elif duration_int <= 8:
        return 8
    else:
        return 12


def build_sora_prompt(scene_title: str, scene_description: str, visual_notes: str) -> str:
    """Build Sora prompt from scene components."""
    return f"{scene_title}. {scene_description}. {visual_notes}".strip()


def extract_video_url(output: Any) -> Optional[str]:
    """Extract video URL from Replicate output (handles various formats)."""
    if isinstance(output, str):
        return output
    elif isinstance(output, list) and len(output) > 0:
        item = output[0]
        return item if isinstance(item, str) else str(item)
    elif hasattr(output, '__iter__') and not isinstance(output, str):
        for item in output:
            if isinstance(item, str):
                return item
        return str(list(output)[0]) if output else None
    else:
        return str(output) if output else None


def build_webhook_url(campaign_id: str, scene_num: int) -> str:
    """Build webhook URL for Replicate callback."""
    base_url = settings.API_URL or "https://zapcut-api.fly.dev"
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    return f"{base_url}/webhooks/replicate?campaign_id={campaign_id}&scene_num={scene_num}"


def retry_scene_prediction(campaign_id: str, scene_number: int) -> bool:
    """Retry a failed scene prediction by creating a new Replicate prediction."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                logger.error(f"Campaign not found for retry: {campaign_id}")
                return False
            
            # Get scene data
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            scene_data = next(
                (s for s in scenes if s.get("scene_number") == scene_number),
                None
            )
            
            if not scene_data:
                logger.error(f"Scene {scene_number} not found in storyline | campaign={campaign_id}")
                return False
            
            # Get stored prompts
            stored_sora_prompts = campaign.sora_prompts or []
            prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in stored_sora_prompts}
            sora_prompt = prompt_lookup.get(scene_number)
            
            if not sora_prompt:
                # Build prompt from scene data
                scene_title = scene_data.get("title", f"Scene {scene_number}")
                scene_description = scene_data.get("description", "")
                visual_notes = scene_data.get("visual_notes", "")
                sora_prompt = build_sora_prompt(scene_title, scene_description, visual_notes)
            
            duration = scene_data.get("duration", 6.0)
            sora_seconds = map_duration_to_sora_seconds(duration)
            
            # Create new prediction
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            webhook_url = build_webhook_url(campaign_id, scene_number)
            
            logger.info(
                f"Scene {scene_number}: retrying prediction | campaign={campaign_id} | "
                f"prompt={sora_prompt[:80]}... | duration={sora_seconds}s"
            )
            
            prediction = client.predictions.create(
                version="openai/sora-2",
                input={
                    "prompt": sora_prompt,
                    "seconds": sora_seconds,
                    "aspect_ratio": "landscape",
                },
                webhook=webhook_url
            )
            
            prediction_id = prediction.id
            logger.info(
                f"Scene {scene_number}: retry prediction created | campaign={campaign_id} | "
                f"prediction_id={prediction_id}"
            )
            
            # Update scene status to generating with new prediction_id
            update_scene_status_safe(
                campaign_id,
                scene_number,
                "generating",
                prediction_id=prediction_id
            )
            
            return True
            
    except Exception as e:
        logger.error(
            f"Failed to retry scene {scene_number} | campaign={campaign_id} | error={str(e)}",
            exc_info=True
        )
        return False


def update_scene_status_safe(
    campaign_id: str,
    scene_number: int,
    status: str,
    video_url: Optional[str] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None,
    prediction_id: Optional[str] = None,
    retry_count: Optional[int] = None
) -> bool:
    """Safely update scene status with proper error handling and minimal logging."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            # Create a NEW list instead of modifying in place
            # This ensures SQLAlchemy detects the change to the JSON field
            existing_video_urls = campaign.video_urls or []
            scene_video_urls = []
            scene_found = False
            
            for scene_entry in existing_video_urls:
                if scene_entry.get("scene_number") == scene_number:
                    # Create a new dict with updated values (don't modify in place)
                    updated_entry = dict(scene_entry)  # Copy existing entry
                    updated_entry["status"] = status
                    if video_url:
                        updated_entry["video_url"] = video_url
                    if duration:
                        updated_entry["duration"] = duration
                    if error:
                        updated_entry["error"] = error
                    if prediction_id:
                        updated_entry["prediction_id"] = prediction_id
                    # Preserve or update retry_count
                    if retry_count is not None:
                        updated_entry["retry_count"] = retry_count
                    elif "retry_count" not in updated_entry:
                        updated_entry["retry_count"] = 0
                    scene_video_urls.append(updated_entry)
                    scene_found = True
                else:
                    # Keep other scenes unchanged (but still create new list)
                    scene_video_urls.append(scene_entry)
            
            if not scene_found:
                # Create new scene entry
                scene_entry = {
                    "scene_number": scene_number,
                    "video_url": video_url,
                    "status": status,
                    "duration": duration,
                    "error": error,
                    "retry_count": retry_count if retry_count is not None else 0
                }
                if prediction_id:
                    scene_entry["prediction_id"] = prediction_id
                scene_video_urls.append(scene_entry)
            else:
                # Update retry_count if provided
                if retry_count is not None:
                    scene_video_urls[-1]["retry_count"] = retry_count
            
            # Assign the NEW list - SQLAlchemy will detect this as a change
            campaign.video_urls = scene_video_urls
            
            # Only log important status changes
            if status in ["completed", "failed"]:
                if status == "completed" and video_url:
                    logger.info(
                        f"Scene {scene_number} {status} | campaign={campaign_id} | "
                        f"video_url={video_url}"
                    )
                else:
                    logger.info(f"Scene {scene_number} {status} | campaign={campaign_id}")
            
            return True
    except Exception as e:
        logger.error(f"Failed to update scene {scene_number} | campaign={campaign_id} | error={str(e)}")
        return False


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_single_scene_task(
    self,
    campaign_id: str,
    scene_data: Dict[str, Any],
    scene_index: int,
    sora_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Create Replicate prediction with webhook callback (fire-and-forget)."""
    scene_num = scene_data.get("scene_number", scene_index + 1)
    scene_title = scene_data.get("title", f"Scene {scene_num}")
    scene_description = scene_data.get("description", "")
    visual_notes = scene_data.get("visual_notes", "")
    duration = scene_data.get("duration", 6.0)
    
    # Build or use provided prompt
    if not sora_prompt:
        sora_prompt = build_sora_prompt(scene_title, scene_description, visual_notes)
        logger.warning(f"Scene {scene_num}: using fallback prompt")
    else:
        logger.info(f"Scene {scene_num}: using stored prompt ({len(sora_prompt)} chars)")
    
    sora_seconds = map_duration_to_sora_seconds(duration)
    
    # Update status to generating
    update_scene_status_safe(campaign_id, scene_num, "generating")
    
    try:
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
        # Build webhook URL
        webhook_url = build_webhook_url(campaign_id, scene_num)
        
        logger.info(f"Scene {scene_num}: creating prediction with webhook | prompt={sora_prompt[:80]}... | duration={sora_seconds}s | webhook={webhook_url}")
        
        # Create prediction with webhook callback
        prediction = client.predictions.create(
            version="openai/sora-2",
            input={
                "prompt": sora_prompt,
                "seconds": sora_seconds,
                "aspect_ratio": "landscape",
            },
            webhook=webhook_url
        )
        
        # Store prediction_id and return immediately (webhook will handle completion)
        prediction_id = prediction.id
        logger.info(f"Scene {scene_num}: prediction created | prediction_id={prediction_id} | webhook={webhook_url}")
        
        # Update scene with prediction_id
        update_scene_status_safe(campaign_id, scene_num, "generating", prediction_id=prediction_id)
        
        # Return immediately - webhook will update status when complete
        return {
            "scene_number": scene_num,
            "video_url": None,
            "status": "generating",
            "prediction_id": prediction_id,
            "duration": duration,
            "prompt": sora_prompt
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scene {scene_num}: error creating prediction | error={error_msg}", exc_info=True)
        update_scene_status_safe(campaign_id, scene_num, "failed", error=error_msg)
        
        # Use Celery's retry mechanism
        if self.request.retries < self.max_retries:
            logger.info(f"Scene {scene_num}: retrying ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            "scene_number": scene_num,
            "video_url": None,
            "status": "failed",
            "error": error_msg,
            "prompt": sora_prompt
        }


@celery_app.task
def start_video_generation_task(campaign_id: str) -> None:
    """Start video generation for a campaign - enqueues scene tasks in parallel (fire-and-forget)."""
    logger.info(f"Starting video generation | campaign={campaign_id}")
    
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return
            
            # Update status
            campaign.status = "processing"
            db.commit()
            
            # Get scenes
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            
            if not scenes:
                logger.warning(f"No scenes found | campaign={campaign_id}")
                campaign.status = "failed"
                db.commit()
                return
            
            if not settings.REPLICATE_API_TOKEN:
                logger.error(f"REPLICATE_API_TOKEN not configured | campaign={campaign_id}")
                campaign.status = "failed"
                db.commit()
                return
            
            # Initialize scene entries
            scene_video_urls = [
                {
                    "scene_number": scene.get("scene_number", i + 1),
                    "video_url": None,
                    "status": "pending",
                    "retry_count": 0
                }
                for i, scene in enumerate(scenes)
            ]
            campaign.video_urls = scene_video_urls
            db.commit()
            
            # Get stored prompts
            stored_sora_prompts = campaign.sora_prompts or []
            prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in stored_sora_prompts}
            
            logger.info(f"Enqueuing {len(scenes)} tasks | campaign={campaign_id} | prompts={len(prompt_lookup)}")
            
            # Enqueue all scene tasks in parallel
            job = group(
                generate_single_scene_task.s(
                    campaign_id,
                    scene,
                    i,
                    prompt_lookup.get(scene.get("scene_number", i + 1))
                )
                for i, scene in enumerate(scenes)
            )
            result = job.apply_async()
            
            # Store task group ID for reference (fire-and-forget - don't wait for results)
            campaign.task_group_id = result.id
            db.commit()
            
            logger.info(f"Campaign tasks enqueued | campaign={campaign_id} | task_group_id={result.id}")
            # Webhooks will handle status updates when scenes complete
            
            # Start audio generation in parallel
            if settings.ELEVENLABS_API_KEY:
                from app.tasks.audio_generation import generate_audio_task
                generate_audio_task.delay(campaign_id)
                logger.info(f"Audio generation task enqueued | campaign={campaign_id}")
            else:
                logger.warning(f"ELEVENLABS_API_KEY not configured, skipping audio generation | campaign={campaign_id}")
    
    except Exception as e:
        logger.error(f"Campaign generation error | campaign={campaign_id} | error={str(e)}", exc_info=True)
        try:
            with db_session() as db:
                campaign_uuid = uuid.UUID(campaign_id)
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    campaign.status = "failed"
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update campaign status | campaign={campaign_id} | error={str(db_error)}")
