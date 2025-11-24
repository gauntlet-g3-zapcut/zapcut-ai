"""Celery tasks for video generation."""
import logging
import random
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

# Constants - Video Models
# v0: Sora 2 (original)
SORA_MODEL = "openai/sora-2"
SORA_DURATION_OPTIONS = [4, 8, 12]  # Sora supports 4, 8, or 12 seconds

# v0.5+: Veo 3.1 (current default)
VEO_MODEL = "google/veo-3.1"
VEO_DURATION_OPTIONS = [4, 6, 8]  # Veo 3.1 supports 4, 6, or 8 seconds

# Default to Veo 3.1 for backward compatibility
VIDEO_MODEL = VEO_MODEL

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


def map_duration_to_veo_seconds(duration: float) -> int:
    """Map scene duration to nearest Veo 3.1-compatible value (4, 6, or 8)."""
    duration_int = int(duration)
    if duration_int <= 4:
        return 4
    elif duration_int <= 6:
        return 6
    else:
        return 8  # Veo 3.1 max is 8 seconds


def map_duration_to_sora_seconds(duration: float) -> int:
    """Map scene duration to nearest Sora-compatible value (4, 8, or 12)."""
    duration_int = int(duration)
    if duration_int <= 4:
        return 4
    elif duration_int <= 8:
        return 8
    else:
        return 12  # Sora max is 12 seconds


def get_model_config(pipeline_version: str) -> tuple:
    """Get model and duration mapper based on pipeline version.

    Returns:
        Tuple of (model_name, duration_mapper_func)
    """
    if pipeline_version == "v0":
        return SORA_MODEL, map_duration_to_sora_seconds
    else:
        # v0.5, v1, v2 all use Veo 3.1
        return VEO_MODEL, map_duration_to_veo_seconds


def build_video_prompt(scene_title: str, scene_description: str, visual_notes: str) -> str:
    """Build video generation prompt from scene components."""
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


def check_ready_and_assemble(campaign_id: str) -> bool:
    """Check if both videos and audio are ready, then trigger assembly.

    This function implements event-driven coordination:
    - Called when videos complete OR when audio mixing completes
    - Only triggers assembly when BOTH are ready
    - Prevents race conditions where assembly runs without audio

    For V2 pipeline: Checks final_audio_url (mixed voiceover + music)
    For V0/V0.5/V1: Checks audio_url (music only)

    Args:
        campaign_id: Campaign UUID string

    Returns:
        True if assembly was triggered, False otherwise
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.warning(f"Campaign not found for assembly check | campaign={campaign_id}")
                return False

            # Check if videos are ready
            storyline = campaign.storyline or {}
            story_document = campaign.story_document or {}

            # V2 uses story_document.segments, V0/V0.5/V1 use storyline.scenes
            total_scenes = len(story_document.get("segments", [])) or len(storyline.get("scenes", []))

            video_urls = campaign.video_urls or []
            completed_videos = [
                v for v in video_urls
                if (v.get("status") == "completed" or v.get("video_status") == "completed")
                and v.get("video_url")
            ]
            videos_ready = len(completed_videos) >= total_scenes and total_scenes > 0

            # Check if audio is ready
            # V2: Use final_audio_url (mixed voiceover + music)
            # V0/V0.5/V1: Use audio_url (music only)
            pipeline_version = campaign.pipeline_version or "v0.5"

            if pipeline_version == "v2":
                # V2 needs final_audio_url (mixed audio)
                audio_ready = campaign.final_audio_url is not None
                audio_source = "final_audio_url"
            else:
                # V0/V0.5/V1 need audio_url with completed status
                audio_ready = (
                    campaign.audio_url is not None and
                    campaign.audio_status == "completed"
                )
                audio_source = "audio_url"

            logger.info(
                f"Assembly check | campaign={campaign_id} | pipeline={pipeline_version} | "
                f"videos_ready={videos_ready} ({len(completed_videos)}/{total_scenes}) | "
                f"audio_ready={audio_ready} (source={audio_source})"
            )

            if videos_ready and audio_ready:
                # Both ready - trigger assembly
                if campaign.pipeline_stage not in ["assembling", "completed"]:
                    logger.info(f"Both videos and audio ready, triggering assembly | campaign={campaign_id}")
                    campaign.pipeline_stage = "assembling"
                    db.commit()

                    # Trigger assembly task
                    assemble_videos_basic_task.delay(campaign_id)
                    return True
                else:
                    logger.info(f"Assembly already in progress or completed | campaign={campaign_id}")
                    return False
            elif videos_ready:
                logger.info(f"Videos ready, waiting for audio | campaign={campaign_id}")
                # Update stage to indicate waiting
                if campaign.pipeline_stage == "videos_generating":
                    campaign.pipeline_stage = "videos_ready"
                    db.commit()
                return False
            elif audio_ready:
                logger.info(f"Audio ready, waiting for videos | campaign={campaign_id}")
                return False
            else:
                logger.debug(f"Neither videos nor audio ready yet | campaign={campaign_id}")
                return False

    except Exception as e:
        logger.error(f"Error in assembly check | campaign={campaign_id} | error={str(e)}", exc_info=True)
        return False


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
            stored_prompts = campaign.sora_prompts or []  # Field name kept for DB compatibility
            prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in stored_prompts}
            video_prompt = prompt_lookup.get(scene_number)

            if not video_prompt:
                # Build prompt from scene data
                scene_title = scene_data.get("title", f"Scene {scene_number}")
                scene_description = scene_data.get("description", "")
                visual_notes = scene_data.get("visual_notes", "")
                video_prompt = build_video_prompt(scene_title, scene_description, visual_notes)

            duration = scene_data.get("duration", 6.0)
            veo_seconds = map_duration_to_veo_seconds(duration)

            # Create new prediction
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            webhook_url = build_webhook_url(campaign_id, scene_number)

            logger.info(
                f"Scene {scene_number}: retrying prediction | campaign={campaign_id} | "
                f"prompt={video_prompt[:80]}... | duration={veo_seconds}s"
            )

            prediction = client.predictions.create(
                version=VIDEO_MODEL,
                input={
                    "prompt": video_prompt,
                    "duration": veo_seconds,
                    "aspect_ratio": "16:9",
                    "resolution": "1080p",
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
    """Safely update scene status with proper error handling and minimal logging.

    IMPORTANT: This function uses SELECT FOR UPDATE to prevent race conditions
    when multiple webhooks or tasks try to update the same campaign simultaneously.
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            # CRITICAL: Use SELECT FOR UPDATE to prevent race conditions
            # This ensures only one process can modify video_urls at a time
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()
            
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
    video_prompt: Optional[str] = None,
    image_url: Optional[str] = None,  # Image URL for image-to-video mode
    pipeline_version: Optional[str] = None  # Pipeline version for model selection
) -> Dict[str, Any]:
    """Create Replicate prediction with webhook callback (fire-and-forget).

    Args:
        campaign_id: Campaign UUID string
        scene_data: Dict with scene_number, title, description, visual_notes, duration
        scene_index: 0-based scene index
        video_prompt: Text prompt for video generation (motion_prompt for image-to-video)
        image_url: Optional image URL for image-to-video mode (v1+ pipelines)
        pipeline_version: Pipeline version (v0=Sora, v0.5+=Veo 3.1)
    """
    scene_num = scene_data.get("scene_number", scene_index + 1)
    scene_title = scene_data.get("title", f"Scene {scene_num}")
    scene_description = scene_data.get("description", "")
    visual_notes = scene_data.get("visual_notes", "")
    duration = scene_data.get("duration", 6.0)

    # Build or use provided prompt
    if not video_prompt:
        video_prompt = build_video_prompt(scene_title, scene_description, visual_notes)
        logger.warning(f"Scene {scene_num}: using fallback prompt")
    else:
        logger.info(f"Scene {scene_num}: using stored prompt ({len(video_prompt)} chars)")

    # Get model and duration mapper based on pipeline version
    model_name, duration_mapper = get_model_config(pipeline_version or "v0.5")
    video_seconds = duration_mapper(duration)

    # Update status to generating (use video_status field for new pipeline)
    update_scene_status_safe(campaign_id, scene_num, "generating")

    # Also update video_status field for new pipeline tracking
    _update_video_status(campaign_id, scene_num, "generating")

    try:
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

        # Build webhook URL
        webhook_url = build_webhook_url(campaign_id, scene_num)

        # Build Replicate input - use image-to-video mode if image_url provided
        replicate_input = {
            "prompt": video_prompt,
            "duration": video_seconds,
            "aspect_ratio": "16:9",
            "resolution": "1080p",
            "generate_audio": True,  # Generate context-aware audio from Veo 3.1
        }

        if image_url:
            # Image-to-video mode (v1+ pipelines)
            replicate_input["image"] = image_url
            logger.info(
                f"Scene {scene_num}: creating {model_name} IMAGE-TO-VIDEO prediction | "
                f"prompt={video_prompt[:80]}... | duration={video_seconds}s | "
                f"image={image_url[:60]}... | webhook={webhook_url}"
            )
        else:
            # Text-to-video mode (v0, v0.5)
            logger.info(
                f"Scene {scene_num}: creating {model_name} TEXT-TO-VIDEO prediction | "
                f"prompt={video_prompt[:80]}... | duration={video_seconds}s | webhook={webhook_url}"
            )

        # Create prediction with webhook callback
        prediction = client.predictions.create(
            version=model_name,
            input=replicate_input,
            webhook=webhook_url
        )

        # Store prediction_id and return immediately (webhook will handle completion)
        prediction_id = prediction.id
        logger.info(f"Scene {scene_num}: prediction created | prediction_id={prediction_id} | webhook={webhook_url}")

        # Update scene with prediction_id
        update_scene_status_safe(campaign_id, scene_num, "generating", prediction_id=prediction_id)
        _update_video_status(campaign_id, scene_num, "generating", prediction_id=prediction_id)

        # Return immediately - webhook will update status when complete
        return {
            "scene_number": scene_num,
            "video_url": None,
            "status": "generating",
            "prediction_id": prediction_id,
            "duration": duration,
            "prompt": video_prompt,
            "image_url": image_url
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scene {scene_num}: error creating prediction | error={error_msg}", exc_info=True)
        update_scene_status_safe(campaign_id, scene_num, "failed", error=error_msg)
        _update_video_status(campaign_id, scene_num, "failed", error=error_msg)

        # Use Celery's retry mechanism with jitter to avoid synchronized retries
        if self.request.retries < self.max_retries:
            # Base delay + random jitter (0-30s) to spread out retries
            base_delay = 60 * (self.request.retries + 1)
            jitter = random.randint(0, 30)
            retry_delay = base_delay + jitter
            logger.info(f"Scene {scene_num}: retrying ({self.request.retries + 1}/{self.max_retries}) in {retry_delay}s")
            raise self.retry(exc=e, countdown=retry_delay)

        return {
            "scene_number": scene_num,
            "video_url": None,
            "status": "failed",
            "error": error_msg,
            "prompt": video_prompt
        }


def _update_video_status(
    campaign_id: str,
    scene_num: int,
    status: str,
    prediction_id: Optional[str] = None,
    error: Optional[str] = None
) -> bool:
    """Update video_status field in the new video_urls structure.

    IMPORTANT: This function uses SELECT FOR UPDATE to prevent race conditions
    when multiple tasks try to update the same campaign simultaneously.
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            # CRITICAL: Use SELECT FOR UPDATE to prevent race conditions
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                return False

            video_urls = list(campaign.video_urls or [])
            for i, scene_entry in enumerate(video_urls):
                if scene_entry.get("scene_number") == scene_num:
                    updated = dict(scene_entry)
                    updated["video_status"] = status
                    if prediction_id:
                        updated["video_prediction_id"] = prediction_id
                    if error:
                        updated["error"] = error
                    video_urls[i] = updated
                    break

            campaign.video_urls = video_urls
            return True
    except Exception as e:
        logger.error(f"Failed to update video_status for scene {scene_num} | campaign={campaign_id} | error={str(e)}")
        return False


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
            
            # Get stored prompts (field name kept as sora_prompts for DB compatibility)
            stored_prompts = campaign.sora_prompts or []
            prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in stored_prompts}

            # Get pipeline version for model selection
            pipeline_version = campaign.pipeline_version or "v0.5"
            model_name, _ = get_model_config(pipeline_version)

            logger.info(f"Enqueuing {len(scenes)} {model_name} tasks | campaign={campaign_id} | pipeline={pipeline_version} | prompts={len(prompt_lookup)}")

            # Stagger scene tasks to avoid Replicate rate limits
            SCENE_STAGGER_DELAY = 15  # seconds between each scene submission

            task_signatures = []
            for i, scene in enumerate(scenes):
                sig = generate_single_scene_task.s(
                    campaign_id,
                    scene,
                    i,
                    prompt_lookup.get(scene.get("scene_number", i + 1)),
                    None,  # image_url (not used for v0/v0.5 text-to-video)
                    pipeline_version  # Pass pipeline version for model selection
                )
                # Apply countdown to stagger: scene 0 = 0s, scene 1 = 15s, scene 2 = 30s, etc.
                sig = sig.set(countdown=i * SCENE_STAGGER_DELAY)
                task_signatures.append(sig)

            job = group(task_signatures)
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


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def assemble_videos_basic_task(self, campaign_id: str) -> Dict[str, Any]:
    """Assemble all scene videos into a final video using FFmpeg xfade cross-dissolve.

    This is the Phase 1 basic assembly task:
    1. Downloads all completed scene videos from S3
    2. Uses FFmpeg xfade filter for 0.5s cross-dissolve transitions
    3. Downloads and mixes audio track if available
    4. Uploads assembled video to S3
    5. Updates campaign.final_video_url

    Args:
        campaign_id: Campaign UUID string

    Returns:
        Dict with status and final video URL
    """
    import os
    import tempfile
    import subprocess
    import httpx

    logger.info(f"Starting video assembly | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return {"status": "failed", "error": "Campaign not found"}

            # Update pipeline stage
            campaign.pipeline_stage = "assembling"
            db.commit()

            # Get all completed scene videos
            video_urls = campaign.video_urls or []

            # Debug: Log all video_urls entries to understand the state
            logger.info(
                f"Video URLs state before assembly | campaign={campaign_id} | "
                f"total_entries={len(video_urls)}"
            )
            for v in video_urls:
                logger.info(
                    f"  Scene {v.get('scene_number')}: status={v.get('status')} "
                    f"video_status={v.get('video_status')} "
                    f"has_video_url={bool(v.get('video_url'))} "
                    f"has_last_frame={bool(v.get('last_frame_url'))}"
                )

            completed_scenes = [
                v for v in video_urls
                if (v.get("status") == "completed" or v.get("video_status") == "completed")
                and v.get("video_url")
            ]

            if len(completed_scenes) < 2:
                logger.warning(f"Not enough scenes to assemble | campaign={campaign_id} | scenes={len(completed_scenes)}")
                if len(completed_scenes) == 1:
                    # Single scene - use it as final video
                    campaign.final_video_url = completed_scenes[0]["video_url"]
                    campaign.pipeline_stage = "completed"
                    campaign.status = "completed"
                    db.commit()
                    return {"status": "success", "final_video_url": campaign.final_video_url}
                return {"status": "failed", "error": "No completed scenes to assemble"}

            # Sort by scene_number (all pipelines now use consistent naming)
            completed_scenes.sort(key=lambda x: x.get("scene_number", 0))

            # Log which scenes will be assembled
            scene_nums = [s.get("scene_number", "?") for s in completed_scenes]
            logger.info(
                f"Assembling {len(completed_scenes)} scenes | campaign={campaign_id} | "
                f"scene_numbers={scene_nums}"
            )

            # Create temp directory for downloads and processing
            with tempfile.TemporaryDirectory() as temp_dir:
                input_files = []

                # Download all scene videos
                for scene in completed_scenes:
                    scene_num = scene.get("scene_number", 0)
                    video_url = scene.get("video_url")

                    if not video_url:
                        continue

                    input_path = os.path.join(temp_dir, f"scene_{scene_num:02d}.mp4")

                    logger.info(f"Downloading scene {scene_num} | url={video_url[:60]}...")

                    try:
                        with httpx.Client(timeout=120.0) as client:
                            response = client.get(video_url)
                            response.raise_for_status()
                            with open(input_path, 'wb') as f:
                                f.write(response.content)
                        input_files.append(input_path)
                        logger.info(f"Downloaded scene {scene_num} | size={os.path.getsize(input_path)} bytes")
                    except Exception as e:
                        logger.error(f"Failed to download scene {scene_num} | error={str(e)}")
                        continue

                if len(input_files) < 2:
                    logger.error(f"Not enough videos downloaded | campaign={campaign_id}")
                    if len(input_files) == 1:
                        # Use single downloaded video as final
                        with open(input_files[0], 'rb') as f:
                            video_bytes = f.read()
                        from app.services.storage import upload_bytes
                        bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
                        file_key = f"generated/{campaign_id}/final/assembled.mp4"
                        final_url = upload_bytes(bucket_name, file_key, video_bytes, 'video/mp4', 'public-read')
                        campaign.final_video_url = final_url
                        campaign.pipeline_stage = "completed"
                        campaign.status = "completed"
                        db.commit()
                        return {"status": "success", "final_video_url": final_url}
                    return {"status": "failed", "error": "Failed to download videos"}

                output_path = os.path.join(temp_dir, "final_assembled.mp4")

                # Build FFmpeg command with xfade cross-dissolve transitions
                # Strategy: Sequential xfade filter chain
                ffmpeg_success = _run_ffmpeg_xfade_assembly(input_files, output_path, transition_duration=0.5)

                if not ffmpeg_success or not os.path.exists(output_path):
                    logger.error(f"FFmpeg assembly failed | campaign={campaign_id}")
                    # Fallback: simple concat without transitions
                    ffmpeg_success = _run_ffmpeg_concat_fallback(input_files, output_path, temp_dir)

                if not ffmpeg_success or not os.path.exists(output_path):
                    campaign.pipeline_stage = "failed"
                    db.commit()
                    return {"status": "failed", "error": "FFmpeg assembly failed"}

                # Check for audio track and mix if available
                # V2 Pipeline: Use final_audio_url (mixed voiceover + music) if available
                # V1 Pipeline: Fall back to audio_url (music only)
                final_audio_url = campaign.final_audio_url  # V2: Mixed voiceover + music
                audio_url = campaign.audio_url  # V1: Music only
                audio_status = campaign.audio_status
                final_output_path = output_path

                # Priority: V2 final_audio_url > V1 audio_url
                effective_audio_url = final_audio_url or audio_url
                audio_ready = (
                    (final_audio_url is not None) or
                    (audio_url and audio_status == "completed")
                )

                if effective_audio_url and audio_ready:
                    logger.info(
                        f"Audio track available, mixing audio | campaign={campaign_id} | "
                        f"is_v2={final_audio_url is not None} | audio_url={effective_audio_url[:60]}..."
                    )

                    # Download audio track
                    audio_path = os.path.join(temp_dir, "soundtrack.mp3")
                    try:
                        with httpx.Client(timeout=60.0) as client:
                            response = client.get(effective_audio_url)
                            response.raise_for_status()
                            with open(audio_path, 'wb') as f:
                                f.write(response.content)
                        logger.info(f"Downloaded audio track | size={os.path.getsize(audio_path)} bytes")

                        # Mix audio with video
                        mixed_output_path = os.path.join(temp_dir, "final_with_audio.mp4")
                        mix_success = _mix_audio_with_video(output_path, audio_path, mixed_output_path)

                        if mix_success and os.path.exists(mixed_output_path):
                            final_output_path = mixed_output_path
                            logger.info(f"Audio mixed successfully | campaign={campaign_id}")
                        else:
                            logger.warning(f"Audio mixing failed, using video without audio | campaign={campaign_id}")
                    except Exception as audio_error:
                        logger.warning(f"Failed to download/mix audio, using video without audio | campaign={campaign_id} | error={str(audio_error)}")
                else:
                    logger.info(f"No audio track available or not completed | campaign={campaign_id} | audio_status={audio_status}")

                # Upload assembled video to S3
                logger.info(f"Uploading assembled video | campaign={campaign_id} | size={os.path.getsize(final_output_path)} bytes")

                with open(final_output_path, 'rb') as f:
                    video_bytes = f.read()

                from app.services.storage import upload_bytes
                bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
                file_key = f"generated/{campaign_id}/final/assembled.mp4"

                final_url = upload_bytes(
                    bucket_name=bucket_name,
                    file_key=file_key,
                    data=video_bytes,
                    content_type='video/mp4',
                    acl='public-read'
                )

                logger.info(f"Assembled video uploaded | campaign={campaign_id} | url={final_url}")

                # Update campaign
                campaign.final_video_url = final_url
                campaign.pipeline_stage = "completed"
                campaign.status = "completed"
                db.commit()

                return {
                    "status": "success",
                    "campaign_id": campaign_id,
                    "final_video_url": final_url,
                    "scenes_assembled": len(input_files)
                }

    except Exception as e:
        logger.error(f"Video assembly failed | campaign={campaign_id} | error={str(e)}", exc_info=True)

        try:
            with db_session() as db:
                campaign_uuid = uuid.UUID(campaign_id)
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    campaign.pipeline_stage = "failed"
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update campaign status | error={str(db_error)}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "failed", "error": str(e)}


def _run_ffmpeg_xfade_assembly(input_files: list, output_path: str, transition_duration: float = 0.5) -> bool:
    """Run FFmpeg with xfade filter for cross-dissolve transitions (video + audio).

    Uses a filter chain for both video and audio:
    Video: [0:v][1:v]xfade=transition=fade:duration=0.5:offset=T1[v01]; ...
    Audio: [0:a][1:a]acrossfade=d=0.5:c1=tri:c2=tri[a01]; ...

    Veo 3.1 generates context-aware audio (ambient sounds, SFX) with each video.
    This function preserves and crossfades that audio for seamless transitions.

    Args:
        input_files: List of input video file paths (sorted by scene order)
        output_path: Output file path
        transition_duration: Duration of each cross-dissolve in seconds

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    if len(input_files) < 2:
        return False

    try:
        # Get durations of each input video
        durations = []
        for input_file in input_files:
            duration = _get_video_duration(input_file)
            durations.append(duration if duration else 6.0)  # Default 6s

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Add all inputs
        for input_file in input_files:
            cmd.extend(["-i", input_file])

        # Build xfade filter chain for VIDEO
        video_filter_parts = []
        accumulated_duration = 0.0

        for i in range(len(input_files) - 1):
            # Calculate offset for this transition
            if i == 0:
                offset = durations[0] - transition_duration
                video_filter_parts.append(
                    f"[0:v][1:v]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[v{i}]"
                )
            else:
                offset = accumulated_duration + durations[i] - transition_duration
                video_filter_parts.append(
                    f"[v{i-1}][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[v{i}]"
                )

            accumulated_duration = offset + transition_duration

        # Build acrossfade filter chain for AUDIO (Veo-generated ambient audio)
        # acrossfade crossfades between two audio streams
        audio_filter_parts = []
        audio_accumulated = 0.0

        for i in range(len(input_files) - 1):
            if i == 0:
                # First pair: pad first audio to its duration, then crossfade with second
                audio_offset = durations[0] - transition_duration
                # Use adelay + amix approach for proper timing
                audio_filter_parts.append(
                    f"[0:a]atrim=0:{durations[0]},asetpts=PTS-STARTPTS[a0t]"
                )
                audio_filter_parts.append(
                    f"[1:a]atrim=0:{durations[1]},asetpts=PTS-STARTPTS,adelay={int((audio_offset)*1000)}|{int((audio_offset)*1000)}[a1d]"
                )
                audio_filter_parts.append(
                    f"[a0t][a1d]amix=inputs=2:duration=longest:dropout_transition=0,volume=2[a{i}]"
                )
                audio_accumulated = audio_offset + durations[1]
            else:
                # Subsequent pairs: delay next audio and mix
                next_delay = audio_accumulated - transition_duration
                audio_filter_parts.append(
                    f"[{i+1}:a]atrim=0:{durations[i+1]},asetpts=PTS-STARTPTS,adelay={int(next_delay*1000)}|{int(next_delay*1000)}[a{i+1}d]"
                )
                audio_filter_parts.append(
                    f"[a{i-1}][a{i+1}d]amix=inputs=2:duration=longest:dropout_transition=0,volume=2[a{i}]"
                )
                audio_accumulated = next_delay + durations[i+1]

        # Final output labels
        final_video_label = f"v{len(input_files) - 2}"
        final_audio_label = f"a{len(input_files) - 2}"

        # Combine all filters
        all_filter_parts = video_filter_parts + audio_filter_parts
        filter_complex = ";".join(all_filter_parts)

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", f"[{final_video_label}]",
            "-map", f"[{final_audio_label}]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.1",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ])

        logger.info(f"Running FFmpeg xfade assembly with audio | files={len(input_files)}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg xfade with audio failed | stderr={result.stderr[:500]}")
            # Fall back to video-only assembly
            return _run_ffmpeg_xfade_video_only(input_files, output_path, transition_duration, durations)

        logger.info("FFmpeg xfade assembly with audio successful")
        return True

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg xfade timed out")
        return False
    except Exception as e:
        logger.error(f"FFmpeg xfade error | error={str(e)}")
        return False


def _run_ffmpeg_xfade_video_only(input_files: list, output_path: str, transition_duration: float, durations: list) -> bool:
    """Fallback: xfade video only (no audio) if audio crossfade fails.

    Some Veo videos may not have audio tracks. This handles that case gracefully.
    """
    import subprocess

    try:
        cmd = ["ffmpeg", "-y"]

        for input_file in input_files:
            cmd.extend(["-i", input_file])

        # Video-only filter chain
        filter_parts = []
        accumulated_duration = 0.0

        for i in range(len(input_files) - 1):
            if i == 0:
                offset = durations[0] - transition_duration
                filter_parts.append(
                    f"[0:v][1:v]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[v{i}]"
                )
            else:
                offset = accumulated_duration + durations[i] - transition_duration
                filter_parts.append(
                    f"[v{i-1}][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[v{i}]"
                )
            accumulated_duration = offset + transition_duration

        final_label = f"v{len(input_files) - 2}"
        filter_complex = ";".join(filter_parts)

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", f"[{final_label}]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.1",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            output_path
        ])

        logger.info(f"Running FFmpeg xfade video-only fallback | files={len(input_files)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg xfade video-only failed | stderr={result.stderr[:500]}")
            return False

        logger.info("FFmpeg xfade video-only fallback successful")
        return True

    except Exception as e:
        logger.error(f"FFmpeg xfade video-only error | error={str(e)}")
        return False


def _run_ffmpeg_concat_fallback(input_files: list, output_path: str, temp_dir: str) -> bool:
    """Fallback: Simple concat without transitions using concat demuxer.

    Args:
        input_files: List of input video file paths
        output_path: Output file path
        temp_dir: Temp directory for concat list file

    Returns:
        True if successful, False otherwise
    """
    import subprocess
    import os

    try:
        # Create concat list file
        concat_list_path = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list_path, 'w') as f:
            for input_file in input_files:
                f.write(f"file '{input_file}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",  # Force widely compatible pixel format
            "-profile:v", "high",
            "-level", "4.1",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            output_path
        ]

        logger.info(f"Running FFmpeg concat fallback | files={len(input_files)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg concat fallback failed | stderr={result.stderr[:500]}")
            return False

        logger.info("FFmpeg concat fallback successful")
        return True

    except Exception as e:
        logger.error(f"FFmpeg concat fallback error | error={str(e)}")
        return False


def _get_video_duration(file_path: str) -> Optional[float]:
    """Get video duration using ffprobe.

    Args:
        file_path: Path to video file

    Returns:
        Duration in seconds, or None if failed
    """
    import subprocess

    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return float(result.stdout.strip())
        return None

    except Exception:
        return None


def _mix_audio_with_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """Mix audio track with video using FFmpeg.

    For V2/V2P pipeline, this mixes THREE audio sources:
    1. Veo ambient audio (from video) - context sounds, SFX at 20% volume
    2. Voiceover + music (from audio_path) - already mixed, at 100% volume

    The Veo audio adds ambient sounds that make the video feel more natural
    while the voiceover+music provides the main audio track.

    Args:
        video_path: Path to input video file (may have Veo audio)
        audio_path: Path to audio file (voiceover + music mix)
        output_path: Path for output video with mixed audio

    Returns:
        True if successful, False otherwise
    """
    import subprocess

    try:
        # Get video duration to match audio length
        video_duration = _get_video_duration(video_path)
        if not video_duration:
            video_duration = 30.0  # Default fallback

        fade_duration = min(2.0, video_duration * 0.1)  # 2s or 10% of video

        # Check if video has an audio stream
        has_video_audio = _check_video_has_audio(video_path)

        if has_video_audio:
            # Mix Veo ambient audio (20% volume) with voiceover+music (100% volume)
            logger.info(f"Video has Veo audio, mixing 3-way | video_duration={video_duration}s")

            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,  # Input 0: video with Veo audio
                "-i", audio_path,  # Input 1: voiceover + music
                "-filter_complex",
                # Veo ambient audio: reduce to 20% volume (background ambient sounds)
                f"[0:a]volume=0.2[veo];"
                # Voiceover+music: trim to video length, full volume, fade out at end
                f"[1:a]atrim=0:{video_duration},asetpts=PTS-STARTPTS,"
                f"afade=t=out:st={video_duration - fade_duration}:d={fade_duration}[main];"
                # Mix Veo ambient + voiceover+music
                f"[veo][main]amix=inputs=2:duration=first:dropout_transition=2,volume=1.5[aout]",
                "-map", "0:v",  # Take video from first input
                "-map", "[aout]",  # Take mixed audio
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-profile:v", "high",
                "-level", "4.1",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-shortest",
                output_path
            ]
        else:
            # No Veo audio - just use voiceover+music
            logger.info(f"No Veo audio in video, using voiceover+music only | video_duration={video_duration}s")

            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex",
                f"[1:a]atrim=0:{video_duration},asetpts=PTS-STARTPTS,"
                f"afade=t=out:st={video_duration - fade_duration}:d={fade_duration}[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-profile:v", "high",
                "-level", "4.1",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-shortest",
                output_path
            ]

        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg audio mix failed | stderr={result.stderr[:500]}")
            return False

        logger.info("FFmpeg audio mix successful")
        return True

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg audio mix timed out")
        return False
    except Exception as e:
        logger.error(f"FFmpeg audio mix error | error={str(e)}")
        return False


def _check_video_has_audio(video_path: str) -> bool:
    """Check if video file has an audio stream using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        True if video has audio stream, False otherwise
    """
    import subprocess

    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        # If output contains "audio", video has audio stream
        has_audio = "audio" in result.stdout.lower()
        logger.debug(f"Video audio check | path={video_path} | has_audio={has_audio}")
        return has_audio

    except Exception as e:
        logger.warning(f"Could not check video audio | error={str(e)}")
        return False  # Assume no audio if check fails
