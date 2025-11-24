"""Celery tasks for image generation (Nano Banana) and upscaling (Real-ESRGAN)."""
import logging
import random
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional
import replicate
from celery import group
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# Model constants
IMAGE_MODEL = "google/nano-banana"  # Nano Banana for image generation
UPSCALE_MODEL = "nightmareai/real-esrgan"  # Real-ESRGAN for upscaling
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720  # 16:9 for Veo
UPSCALE_FACTOR = 2  # 2x upscale: 1280x720 -> 2560x1440

# Stagger delay between scene submissions to avoid rate limits
SCENE_STAGGER_DELAY = 10  # seconds


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


def build_image_webhook_url(campaign_id: str, scene_num: int) -> str:
    """Build webhook URL for image generation callback."""
    base_url = settings.API_URL or "https://zapcut-api.fly.dev"
    base_url = base_url.rstrip('/')
    return f"{base_url}/webhooks/replicate/image?campaign_id={campaign_id}&scene_num={scene_num}"


def build_upscale_webhook_url(campaign_id: str, scene_num: int) -> str:
    """Build webhook URL for upscale callback."""
    base_url = settings.API_URL or "https://zapcut-api.fly.dev"
    base_url = base_url.rstrip('/')
    return f"{base_url}/webhooks/replicate/upscale?campaign_id={campaign_id}&scene_num={scene_num}"


def update_scene_image_status(
    campaign_id: str,
    scene_number: int,
    field: str,
    value: Any,
    additional_updates: Optional[Dict[str, Any]] = None
) -> bool:
    """Update a specific field in the scene's video_urls entry.

    IMPORTANT: This function uses SELECT FOR UPDATE to prevent race conditions
    when multiple Celery tasks try to update the same campaign simultaneously.

    Args:
        campaign_id: Campaign UUID string
        scene_number: Scene number to update
        field: Field name to update
        value: New value for the field
        additional_updates: Dict of additional field:value pairs to update

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            # CRITICAL: Use SELECT FOR UPDATE to prevent race conditions
            # This ensures only one task can modify video_urls at a time
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).with_for_update().first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return False

            # Create new list to trigger SQLAlchemy change detection
            video_urls = list(campaign.video_urls or [])
            scene_found = False

            for i, scene_entry in enumerate(video_urls):
                if scene_entry.get("scene_number") == scene_number:
                    # Create a new dict with updated values
                    updated_entry = dict(scene_entry)
                    updated_entry[field] = value

                    if additional_updates:
                        updated_entry.update(additional_updates)

                    video_urls[i] = updated_entry
                    scene_found = True
                    break

            if not scene_found:
                logger.warning(f"Scene {scene_number} not found in video_urls | campaign={campaign_id}")
                return False

            campaign.video_urls = video_urls
            db.commit()

            return True

    except Exception as e:
        logger.error(f"Failed to update scene {scene_number} {field} | campaign={campaign_id} | error={str(e)}")
        return False


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_single_image_task(
    self,
    campaign_id: str,
    scene_num: int,
    image_prompt: str
) -> Dict[str, Any]:
    """Create Replicate prediction for Nano Banana image generation with webhook callback.

    Args:
        campaign_id: Campaign UUID string
        scene_num: Scene number
        image_prompt: The image generation prompt

    Returns:
        Dict with status and prediction info
    """
    logger.info(f"Scene {scene_num}: starting image generation | campaign={campaign_id}")

    # Update status to generating
    update_scene_image_status(campaign_id, scene_num, "image_status", "generating")

    try:
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        webhook_url = build_image_webhook_url(campaign_id, scene_num)

        logger.info(
            f"Scene {scene_num}: creating Nano Banana prediction | "
            f"prompt={image_prompt[:80]}... | webhook={webhook_url}"
        )

        # Create prediction with webhook callback
        prediction = client.predictions.create(
            version=IMAGE_MODEL,
            input={
                "prompt": image_prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "output_format": "png",
                "output_quality": 95,
            },
            webhook=webhook_url
        )

        prediction_id = prediction.id
        logger.info(f"Scene {scene_num}: image prediction created | prediction_id={prediction_id}")

        # Update scene with prediction_id
        update_scene_image_status(
            campaign_id, scene_num,
            "image_status", "generating",
            {"image_prediction_id": prediction_id}
        )

        return {
            "scene_number": scene_num,
            "status": "generating",
            "prediction_id": prediction_id,
            "prompt": image_prompt
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scene {scene_num}: error creating image prediction | error={error_msg}", exc_info=True)

        update_scene_image_status(
            campaign_id, scene_num,
            "image_status", "failed",
            {"error": f"Image generation failed: {error_msg}"}
        )

        # Retry with jitter
        if self.request.retries < self.max_retries:
            jitter = random.randint(0, 30)
            retry_delay = 60 * (self.request.retries + 1) + jitter
            logger.info(f"Scene {scene_num}: retrying image gen in {retry_delay}s")
            raise self.retry(exc=e, countdown=retry_delay)

        return {
            "scene_number": scene_num,
            "status": "failed",
            "error": error_msg
        }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def upscale_single_image_task(
    self,
    campaign_id: str,
    scene_num: int,
    base_image_url: str
) -> Dict[str, Any]:
    """Create Replicate prediction for Real-ESRGAN upscaling with webhook callback.

    Args:
        campaign_id: Campaign UUID string
        scene_num: Scene number
        base_image_url: URL of the base image to upscale

    Returns:
        Dict with status and prediction info
    """
    logger.info(f"Scene {scene_num}: starting upscaling | campaign={campaign_id}")

    # Update status to upscaling
    update_scene_image_status(campaign_id, scene_num, "upscale_status", "generating")

    try:
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        webhook_url = build_upscale_webhook_url(campaign_id, scene_num)

        logger.info(
            f"Scene {scene_num}: creating Real-ESRGAN prediction | "
            f"image_url={base_image_url[:60]}... | scale={UPSCALE_FACTOR}x | webhook={webhook_url}"
        )

        # Create prediction with webhook callback
        prediction = client.predictions.create(
            version=UPSCALE_MODEL,
            input={
                "image": base_image_url,
                "scale": UPSCALE_FACTOR,
                "face_enhance": False,  # No face enhancement for ad content
            },
            webhook=webhook_url
        )

        prediction_id = prediction.id
        logger.info(f"Scene {scene_num}: upscale prediction created | prediction_id={prediction_id}")

        # Update scene with prediction_id
        update_scene_image_status(
            campaign_id, scene_num,
            "upscale_status", "generating",
            {"upscale_prediction_id": prediction_id}
        )

        return {
            "scene_number": scene_num,
            "status": "generating",
            "prediction_id": prediction_id
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scene {scene_num}: error creating upscale prediction | error={error_msg}", exc_info=True)

        update_scene_image_status(
            campaign_id, scene_num,
            "upscale_status", "failed",
            {"error": f"Upscale failed: {error_msg}"}
        )

        # Retry with jitter
        if self.request.retries < self.max_retries:
            jitter = random.randint(0, 30)
            retry_delay = 60 * (self.request.retries + 1) + jitter
            logger.info(f"Scene {scene_num}: retrying upscale in {retry_delay}s")
            raise self.retry(exc=e, countdown=retry_delay)

        # Fallback: trigger video generation with base image (non-upscaled)
        logger.warning(f"Scene {scene_num}: upscale failed, using base image for video | campaign={campaign_id}")
        try:
            with db_session() as db:
                campaign_uuid = uuid.UUID(campaign_id)
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    video_urls = campaign.video_urls or []
                    scene_entry = next(
                        (s for s in video_urls if s.get("scene_number") == scene_num),
                        None
                    )
                    if scene_entry:
                        base_url = scene_entry.get("base_image_url")
                        motion_prompt = scene_entry.get("motion_prompt", "")
                        if base_url:
                            from app.tasks.video_generation import generate_single_scene_task
                            generate_single_scene_task.delay(
                                campaign_id,
                                {"scene_number": scene_num, "duration": 6.0},
                                scene_num - 1,
                                motion_prompt,
                                base_url  # Use base image as fallback
                            )
        except Exception as fallback_error:
            logger.error(f"Scene {scene_num}: fallback to base image failed | error={str(fallback_error)}")

        return {
            "scene_number": scene_num,
            "status": "failed",
            "error": error_msg
        }


@celery_app.task(bind=True, max_retries=1, default_retry_delay=60)
def start_image_generation_task(self, campaign_id: str) -> None:
    """Start image generation for all scenes in a campaign.

    This task:
    1. Updates pipeline_stage to "images_generating"
    2. Enqueues image generation tasks for all scenes (staggered)

    Args:
        campaign_id: Campaign UUID string
    """
    logger.info(f"Starting image generation | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return

            # Update pipeline stage
            campaign.pipeline_stage = "images_generating"
            campaign.status = "processing"
            db.commit()

            # Get image prompts
            image_prompts = campaign.image_prompts or []

            if not image_prompts:
                logger.error(f"No image prompts found | campaign={campaign_id}")
                campaign.pipeline_stage = "failed"
                campaign.status = "failed"
                db.commit()
                return

            if not settings.REPLICATE_API_TOKEN:
                logger.error(f"REPLICATE_API_TOKEN not configured | campaign={campaign_id}")
                campaign.pipeline_stage = "failed"
                campaign.status = "failed"
                db.commit()
                return

            logger.info(f"Enqueuing {len(image_prompts)} image generation tasks | campaign={campaign_id}")

            # Update all scenes to pending image status
            video_urls = campaign.video_urls or []
            for scene_entry in video_urls:
                scene_entry["image_status"] = "pending"
            campaign.video_urls = video_urls
            db.commit()

            # Enqueue image generation tasks with stagger
            task_signatures = []
            for i, prompt_data in enumerate(image_prompts):
                scene_num = prompt_data.get("scene_number", i + 1)
                image_prompt = prompt_data.get("image_prompt", "")

                sig = generate_single_image_task.s(campaign_id, scene_num, image_prompt)
                sig = sig.set(countdown=i * SCENE_STAGGER_DELAY)
                task_signatures.append(sig)

            job = group(task_signatures)
            result = job.apply_async()

            logger.info(
                f"Image generation tasks enqueued | campaign={campaign_id} | "
                f"task_group_id={result.id} | scenes={len(task_signatures)}"
            )

    except Exception as e:
        logger.error(f"Failed to start image generation | campaign={campaign_id} | error={str(e)}", exc_info=True)
        try:
            with db_session() as db:
                campaign_uuid = uuid.UUID(campaign_id)
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    campaign.pipeline_stage = "failed"
                    campaign.status = "failed"
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update campaign status | campaign={campaign_id} | error={str(db_error)}")
