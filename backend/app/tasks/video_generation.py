"""Celery tasks for video generation."""
import logging
import random
import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
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
DEFAULT_GENERATION_MODE = "parallel"
DEFAULT_VIDEO_RESOLUTION = "1080p"
DEFAULT_VIDEO_MODEL = settings.REPLICATE_DEFAULT_VIDEO_MODEL or "google-veo-3-1"

RESOLUTION_DIMENSIONS: Dict[str, Dict[str, int]] = {
    "720p": {"width": 1280, "height": 720},
    "1080p": {"width": 1920, "height": 1080},
}

def _video_model_version_map() -> Dict[str, str]:
    """Map friendly video model keys to Replicate version identifiers."""
    return {
        "google-veo-3-1": settings.REPLICATE_VEO_3_1_VERSION or "google/veo-3.1",
        "kling-2-1": settings.REPLICATE_KLING_2_1_VERSION or "kling/kling-2.1",
        "minimax-video-01": settings.REPLICATE_MINIMAX_VIDEO_01_VERSION or "minimax/video-01",
    }


def get_generation_settings(campaign: Campaign) -> Dict[str, str]:
    """Resolve generation settings stored on the creative bible for a campaign."""
    preferences: Dict[str, Any] = {}
    try:
        if campaign.creative_bible and campaign.creative_bible.campaign_preferences:
            preferences = campaign.creative_bible.campaign_preferences or {}
    except AttributeError:
        preferences = {}

    generation_mode = str(preferences.get("generation_mode", DEFAULT_GENERATION_MODE)).lower()
    video_resolution = str(preferences.get("video_resolution", DEFAULT_VIDEO_RESOLUTION)).lower()
    video_model = str(preferences.get("video_model", DEFAULT_VIDEO_MODEL)).lower()

    if generation_mode not in {"parallel", "sequential"}:
        generation_mode = DEFAULT_GENERATION_MODE

    if video_resolution not in RESOLUTION_DIMENSIONS:
        video_resolution = DEFAULT_VIDEO_RESOLUTION

    version_map = _video_model_version_map()
    if video_model not in version_map:
        video_model = DEFAULT_VIDEO_MODEL

    return {
        "generation_mode": generation_mode,
        "video_resolution": video_resolution,
        "video_model": video_model,
    }


def resolve_model_version(model_key: str) -> str:
    """Return Replicate version string for the given model key."""
    version_map = _video_model_version_map()
    return version_map.get(model_key, version_map.get(DEFAULT_VIDEO_MODEL, "google/veo-3.1"))


def resolve_resolution_settings(resolution: str) -> Dict[str, int]:
    """Return width/height configuration for a given resolution key."""
    return RESOLUTION_DIMENSIONS.get(resolution, RESOLUTION_DIMENSIONS[DEFAULT_VIDEO_RESOLUTION])


def is_sequential_mode(generation_mode: str) -> bool:
    """Helper to determine if sequential generation is requested."""
    return generation_mode.lower() == "sequential"


def extract_last_frame(video_bytes: bytes) -> Optional[bytes]:
    """Extract the final frame from a video using ffmpeg, returning PNG bytes.

    Returns:
        PNG bytes of the final frame, or None if extraction fails.
    """
    if not video_bytes:
        return None

    video_path = None
    image_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_file.write(video_bytes)
            video_path = video_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as image_file:
            image_path = image_file.name

        # Extract a frame very close to the end of the video
        command = [
            "ffmpeg",
            "-y",  # overwrite if exists
            "-sseof",
            "-0.1",
            "-i",
            video_path,
            "-vframes",
            "1",
            image_path,
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if result.returncode != 0:
            logger.error(
                "ffmpeg failed to extract last frame | returncode=%s | stderr=%s",
                result.returncode,
                result.stderr.decode("utf-8", errors="ignore"),
            )
            return None

        if not os.path.exists(image_path):
            return None

        with open(image_path, "rb") as image_file:
            return image_file.read()
    except FileNotFoundError:
        logger.warning("ffmpeg not available on system; cannot extract seed frame for sequential mode.")
        return None
    except Exception as exc:
        logger.error("Failed to extract last frame from video: %s", exc, exc_info=True)
        return None
    finally:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


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
            
            generation_settings = get_generation_settings(campaign)
            generation_mode = generation_settings["generation_mode"]
            video_resolution = generation_settings["video_resolution"]
            model_key = generation_settings["video_model"]
            model_version = resolve_model_version(model_key)
            resolution_settings = resolve_resolution_settings(video_resolution)
            
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
            seed_image_url = None

            scene_video_urls = campaign.video_urls or []
            scene_entry = next(
                (entry for entry in scene_video_urls if entry.get("scene_number") == scene_number),
                None,
            )
            if scene_entry:
                seed_image_url = scene_entry.get("seed_image_url")
            
            # Create new prediction
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            webhook_url = build_webhook_url(campaign_id, scene_number)
            
            logger.info(
                f"Scene {scene_number}: retrying prediction | campaign={campaign_id} | "
                f"model={model_version} | resolution={video_resolution} | duration={sora_seconds}s"
            )
            
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
            
            prediction = client.predictions.create(
                version=model_version,
                input=input_payload,
                webhook=webhook_url
            )
            
            prediction_id = prediction.id
            logger.info(
                f"Scene {scene_number}: retry prediction created | campaign={campaign_id} | "
                f"prediction_id={prediction_id} | model={model_version}"
            )
            
            # Update scene status to generating with new prediction_id
            update_scene_status_safe(
                campaign_id,
                scene_number,
                "generating",
                prediction_id=prediction_id,
                target_resolution=video_resolution,
                video_model=model_key,
                seed_image_url=seed_image_url,
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
    retry_count: Optional[int] = None,
    target_resolution: Optional[str] = None,
    video_model: Optional[str] = None,
    seed_image_url: Optional[str] = None,
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
                    if target_resolution:
                        updated_entry["target_resolution"] = target_resolution
                    if video_model:
                        updated_entry["video_model"] = video_model
                    if seed_image_url:
                        updated_entry["seed_image_url"] = seed_image_url
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
                    "retry_count": retry_count if retry_count is not None else 0,
                    "target_resolution": target_resolution,
                    "video_model": video_model,
                    "seed_image_url": seed_image_url,
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
    sora_prompt: Optional[str] = None,
    model_key: Optional[str] = None,
    video_resolution: Optional[str] = None,
    seed_image_url: Optional[str] = None,
    generation_mode: Optional[str] = None,
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
    
    generation_mode = (generation_mode or DEFAULT_GENERATION_MODE).lower()
    model_key = (model_key or DEFAULT_VIDEO_MODEL).lower()
    video_resolution = (video_resolution or DEFAULT_VIDEO_RESOLUTION).lower()
    sora_seconds = map_duration_to_sora_seconds(duration)
    resolution_settings = resolve_resolution_settings(video_resolution)
    model_version = resolve_model_version(model_key)
    
    # Update status to generating with metadata
    update_scene_status_safe(
        campaign_id,
        scene_num,
        "generating",
        target_resolution=video_resolution,
        video_model=model_key,
        seed_image_url=seed_image_url,
    )
    
    try:
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
        # Build webhook URL
        webhook_url = build_webhook_url(campaign_id, scene_num)
        
        logger.info(
            "Scene %s: creating prediction | campaign=%s | model=%s | resolution=%s | seconds=%s | webhook=%s",
            scene_num,
            campaign_id,
            model_version,
            video_resolution,
            sora_seconds,
            webhook_url,
        )
        
        # Create prediction with webhook callback
        input_payload: Dict[str, Any] = {
            "prompt": sora_prompt,
            "seconds": sora_seconds,
            "aspect_ratio": "16:9",
            "resolution": video_resolution,
            "output_height": resolution_settings["height"],
            "output_width": resolution_settings["width"],
        }

        if seed_image_url:
            # Downstream models may use init_image/seed_image naming. Provide both for compatibility.
            input_payload["init_image"] = seed_image_url
            input_payload["seed_image"] = seed_image_url

        prediction = client.predictions.create(
            version=model_version,
            input=input_payload,
            webhook=webhook_url
        )
        
        # Store prediction_id and return immediately (webhook will handle completion)
        prediction_id = prediction.id
        logger.info(
            "Scene %s: prediction created | campaign=%s | prediction_id=%s | model=%s",
            scene_num,
            campaign_id,
            prediction_id,
            model_version,
        )
        
        # Update scene with prediction_id
        update_scene_status_safe(
            campaign_id,
            scene_num,
            "generating",
            prediction_id=prediction_id,
            target_resolution=video_resolution,
            video_model=model_key,
            seed_image_url=seed_image_url,
        )
        
        # Return immediately - webhook will update status when complete
        return {
            "scene_number": scene_num,
            "video_url": None,
            "status": "generating",
            "prediction_id": prediction_id,
            "duration": duration,
            "prompt": sora_prompt,
            "video_model": model_key,
            "target_resolution": video_resolution,
            "generation_mode": generation_mode,
            "seed_image_url": seed_image_url,
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scene {scene_num}: error creating prediction | error={error_msg}", exc_info=True)
        update_scene_status_safe(
            campaign_id,
            scene_num,
            "failed",
            error=error_msg,
            target_resolution=video_resolution,
            video_model=model_key,
            seed_image_url=seed_image_url,
        )
        
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
            
            # Get scenes and user-selected generation settings
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            generation_settings = get_generation_settings(campaign)
            generation_mode = generation_settings["generation_mode"]
            video_resolution = generation_settings["video_resolution"]
            model_key = generation_settings["video_model"]
            
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
                    "retry_count": 0,
                    "target_resolution": video_resolution,
                    "video_model": model_key,
                    "seed_image_url": None,
                }
                for i, scene in enumerate(scenes)
            ]
            campaign.video_urls = scene_video_urls
            db.commit()
            
            # Get stored prompts
            stored_sora_prompts = campaign.sora_prompts or []
            prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in stored_sora_prompts}
            
            logger.info(f"Enqueuing {len(scenes)} tasks | campaign={campaign_id} | prompts={len(prompt_lookup)}")
            
            if is_sequential_mode(generation_mode):
                logger.info(
                    "Sequential generation selected | campaign=%s | model=%s | resolution=%s",
                    campaign_id,
                    model_key,
                    video_resolution,
                )
                if scenes:
                    first_scene = scenes[0]
                    result = generate_single_scene_task.delay(
                        campaign_id,
                        first_scene,
                        0,
                        prompt_lookup.get(first_scene.get("scene_number", 1)),
                        model_key,
                        video_resolution,
                        None,
                        generation_mode,
                    )
                    campaign.task_group_id = result.id
                    db.commit()
                    logger.info(
                        "First sequential task enqueued | campaign=%s | scene=%s | celery_id=%s",
                        campaign_id,
                        first_scene.get("scene_number", 1),
                        result.id,
                    )
            else:
                logger.info(
                    "Parallel generation selected | campaign=%s | model=%s | resolution=%s",
                    campaign_id,
                    model_key,
                    video_resolution,
                )
                # Enqueue all scene tasks in parallel
                job = group(
                    generate_single_scene_task.s(
                        campaign_id,
                        scene,
                        i,
                        prompt_lookup.get(scene.get("scene_number", i + 1)),
                        model_key,
                        video_resolution,
                        None,
                        generation_mode,
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


def trigger_next_scene_after_completion(
    campaign_id: str,
    completed_scene_number: int,
    seed_image_url: Optional[str] = None,
) -> None:
    """Trigger next sequential scene after the previous one completes."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error("Trigger next scene: campaign not found | campaign=%s", campaign_id)
                return

            generation_settings = get_generation_settings(campaign)
            generation_mode = generation_settings["generation_mode"]

            if not is_sequential_mode(generation_mode):
                return

            storyline = campaign.storyline or {}
            scenes: List[Dict[str, Any]] = storyline.get("scenes", [])

            if not scenes:
                return

            ordered_scenes = sorted(scenes, key=lambda s: s.get("scene_number", 0))
            current_index = next(
                (idx for idx, scene in enumerate(ordered_scenes) if scene.get("scene_number") == completed_scene_number),
                None,
            )

            if current_index is None or current_index + 1 >= len(ordered_scenes):
                logger.info(
                    "Sequential flow complete or unable to locate next scene | campaign=%s | completed_scene=%s",
                    campaign_id,
                    completed_scene_number,
                )
                return

            next_scene = ordered_scenes[current_index + 1]
            next_scene_number = next_scene.get("scene_number", current_index + 2)

            video_urls = campaign.video_urls or []
            next_entry = next(
                (entry for entry in video_urls if entry.get("scene_number") == next_scene_number),
                None,
            )

            if not next_entry:
                logger.warning(
                    "Sequential flow: missing next scene entry | campaign=%s | next_scene=%s",
                    campaign_id,
                    next_scene_number,
                )
                return

            if next_entry.get("status") not in {"pending", None}:
                logger.info(
                    "Sequential flow: next scene already started | campaign=%s | next_scene=%s | status=%s",
                    campaign_id,
                    next_scene_number,
                    next_entry.get("status"),
                )
                return

            if not seed_image_url:
                completed_entry = next(
                    (entry for entry in video_urls if entry.get("scene_number") == completed_scene_number),
                    None,
                )
                if completed_entry:
                    seed_image_url = completed_entry.get("seed_image_url")

            stored_sora_prompts = campaign.sora_prompts or []
            prompt_lookup = {p.get("scene_number"): p.get("prompt") for p in stored_sora_prompts}

            model_key = generation_settings["video_model"]
            video_resolution = generation_settings["video_resolution"]

            result = generate_single_scene_task.delay(
                campaign_id,
                next_scene,
                current_index + 1,
                prompt_lookup.get(next_scene_number),
                model_key,
                video_resolution,
                seed_image_url,
                generation_mode,
            )

            campaign.task_group_id = result.id
            db.commit()

            logger.info(
                "Sequential flow: next scene enqueued | campaign=%s | next_scene=%s | celery_id=%s",
                campaign_id,
                next_scene_number,
                result.id,
            )
    except Exception as exc:
        logger.error(
            "Failed to enqueue next sequential scene | campaign=%s | error=%s",
            campaign_id,
            exc,
            exc_info=True,
        )
