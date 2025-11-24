"""Celery tasks for V2 sequential video generation using Veo 3.1 with frame seeding."""
import logging
import random
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
import replicate
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
VIDEO_MODEL = "google/veo-3.1"
VEO_SEGMENT_DURATION = 8  # Each segment is 8 seconds
MAX_RETRIES = 2
RETRY_DELAY_BASE = 60


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


def build_character_block(characters: List[Dict[str, Any]]) -> str:
    """Build detailed character description for video prompts.

    Args:
        characters: List of character dicts with name, description, phone

    Returns:
        Formatted character block string
    """
    if not characters:
        return ""

    # Use only the main character for consistency
    main_char = characters[0]
    name = main_char.get("name", "Character")
    description = main_char.get("description", "")
    phone = main_char.get("phone", "")

    block = f"""MAIN CHARACTER - {name}:
{description}"""

    if phone:
        block += f"\nPhone: {phone}"

    return block


def build_segment_prompt(
    segment: Dict[str, Any],
    character_block: str,
    is_first_segment: bool = False,
    segment_num: int = 1
) -> str:
    """Build video generation prompt for a segment.

    Args:
        segment: Segment dict with visual, action, end_state, app_screen
        character_block: Pre-built character description
        is_first_segment: True for segment 1 (no continuation reference)
        segment_num: Segment number (1-5)

    Returns:
        Video generation prompt string
    """
    # Use new 'visual' field if available, fall back to 'action'
    visual = segment.get("visual", "") or segment.get("action", "")
    action = segment.get("action", "")
    end_state = segment.get("end_state", "")
    app_screen = segment.get("app_screen")

    # Build app instruction if showing phone
    app_instruction = ""
    if app_screen and segment_num >= 2:
        app_instruction = f"""
APP ON PHONE: The character's phone screen shows: {app_screen}
IMPORTANT: App appears ON the phone screen the character is holding, not floating or behind them."""

    if is_first_segment:
        # Segment 1: Hook - no phone, establish character
        prompt = f"""Cinematic viral ad shot. 8 seconds. 16:9 aspect ratio.

{character_block}

SCENE: {visual}

ACTION: {action}

END FRAME: {end_state}

STYLE: High-end mobile ad, natural lighting, shallow depth of field.
CAMERA: Smooth, cinematic. Medium shot or close-up.
IMPORTANT: Character must match description EXACTLY. No phone in this segment."""

    else:
        # Segments 2-5: Continue from provided image
        prompt = f"""Cinematic viral ad shot. 8 seconds. 16:9 aspect ratio.
CONTINUE EXACTLY from the provided starting image - same character, same outfit, same setting.

{character_block}

SCENE: {visual}

ACTION: {action}{app_instruction}

END FRAME: {end_state}

STYLE: High-end mobile ad, natural lighting, shallow depth of field.
CAMERA: Smooth, cinematic. Medium shot or close-up.
CRITICAL: Character appearance, clothing, and phone must be IDENTICAL to starting image."""

    return prompt


def build_webhook_url(campaign_id: str, segment_num: int) -> str:
    """Build webhook URL for sequential video callback."""
    base_url = settings.API_URL or "https://zapcut-api.fly.dev"
    base_url = base_url.rstrip('/')
    return f"{base_url}/webhooks/replicate/sequential?campaign_id={campaign_id}&segment_num={segment_num}"


def update_segment_status(
    campaign_id: str,
    segment_num: int,
    status: str,
    video_url: Optional[str] = None,
    prediction_id: Optional[str] = None,
    last_frame_url: Optional[str] = None,
    error: Optional[str] = None
) -> bool:
    """Update segment status in campaign.video_urls array."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return False

            # Update current_segment tracking
            if status == "generating":
                campaign.current_segment = segment_num

            # Update video_urls array
            video_urls = list(campaign.video_urls or [])
            segment_found = False

            for i, entry in enumerate(video_urls):
                if entry.get("scene_number") == segment_num:
                    updated = dict(entry)
                    updated["video_status"] = status
                    updated["status"] = status  # Also update overall status

                    if video_url:
                        updated["video_url"] = video_url
                    if prediction_id:
                        updated["video_prediction_id"] = prediction_id
                    if last_frame_url:
                        updated["last_frame_url"] = last_frame_url
                    if error:
                        updated["error"] = error

                    video_urls[i] = updated
                    segment_found = True
                    break

            if not segment_found:
                # Create new entry
                video_urls.append({
                    "scene_number": segment_num,
                    "video_status": status,
                    "status": status,
                    "video_url": video_url,
                    "video_prediction_id": prediction_id,
                    "last_frame_url": last_frame_url,
                    "error": error
                })

            campaign.video_urls = video_urls

            if status in ["completed", "failed"]:
                logger.info(
                    f"Segment {segment_num} {status} | campaign={campaign_id} | "
                    f"video_url={video_url}"
                )

            return True

    except Exception as e:
        logger.error(
            f"Failed to update segment {segment_num} status | "
            f"campaign={campaign_id} | error={str(e)}"
        )
        return False


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def start_sequential_pipeline_task(self, campaign_id: str) -> Dict[str, Any]:
    """Start the sequential video pipeline for V2.

    Initializes video_urls array with segment entries and triggers
    generation of segment 1 (with scene image generation first).

    Args:
        campaign_id: Campaign UUID string

    Returns:
        Dict with status
    """
    logger.info(f"Starting sequential video pipeline | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return {"status": "failed", "error": "Campaign not found"}

            story_document = campaign.story_document
            if not story_document:
                return {"status": "failed", "error": "No story_document found"}

            segments = story_document.get("segments", [])
            if not segments:
                return {"status": "failed", "error": "No segments in story_document"}

            # Initialize video_urls with segment entries
            video_urls = []
            for segment in segments:
                seg_num = segment.get("number", 0)
                video_urls.append({
                    "scene_number": seg_num,
                    "video_status": "pending",
                    "status": "pending",
                    "video_url": None,
                    "video_prediction_id": None,
                    "last_frame_url": None,
                    "error": None
                })

            campaign.video_urls = video_urls
            campaign.pipeline_stage = "segment_1_image"
            campaign.current_segment = 0
            db.commit()

            logger.info(
                f"Sequential pipeline initialized | campaign={campaign_id} | "
                f"segments={len(segments)}"
            )

            # Start with generating image for segment 1
            generate_segment_image_task.delay(campaign_id, 1)

            return {"status": "started", "segments": len(segments)}

    except Exception as e:
        logger.error(
            f"Failed to start sequential pipeline | campaign={campaign_id} | error={str(e)}",
            exc_info=True
        )
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_segment_image_task(self, campaign_id: str, segment_num: int) -> Dict[str, Any]:
    """Generate scene image for a segment using Nano Banana.

    For segment 1: Generates starting image from segment action description
    For segments 2-5: Uses previous segment's last frame (no image generation)

    Args:
        campaign_id: Campaign UUID string
        segment_num: Segment number (1-5)

    Returns:
        Dict with status
    """
    logger.info(f"Starting segment {segment_num} image generation | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return {"status": "failed", "error": "Campaign not found"}

            story_document = campaign.story_document
            segments = story_document.get("segments", [])
            characters = story_document.get("characters", [])

            segment = next((s for s in segments if s.get("number") == segment_num), None)
            if not segment:
                return {"status": "failed", "error": f"Segment {segment_num} not found"}

            # For segments 2-5, check if previous segment has last_frame_url
            if segment_num > 1:
                video_urls = campaign.video_urls or []
                prev_segment = next(
                    (v for v in video_urls if v.get("scene_number") == segment_num - 1),
                    None
                )

                if prev_segment and prev_segment.get("last_frame_url"):
                    # Use previous frame, skip to video generation
                    logger.info(
                        f"Segment {segment_num}: using previous frame | campaign={campaign_id}"
                    )
                    generate_segment_video_task.delay(
                        campaign_id,
                        segment_num,
                        prev_segment["last_frame_url"]
                    )
                    return {"status": "skipped", "message": "Using previous segment frame"}

            # Build image prompt from segment visual/action and character description
            character_block = build_character_block(characters)
            # Use 'visual' field if available, fall back to 'action'
            visual = segment.get("visual", "") or segment.get("action", "")
            end_state = segment.get("end_state", "")

            image_prompt = f"""Cinematic film still for viral mobile ad. Photorealistic, 16:9 aspect ratio, 1280x720.

{character_block}

SCENE: {visual}

MOMENT: {end_state}

STYLE: High-end mobile advertisement, natural lighting, shallow depth of field, warm cinematic color grading.
IMPORTANT: Character must match description EXACTLY - same outfit, hair, accessories."""

            # Update status
            update_segment_status(campaign_id, segment_num, "image_generating")

            # Create Replicate prediction for Nano Banana
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

            # Build webhook URL for image callback
            base_url = settings.API_URL or "https://zapcut-api.fly.dev"
            webhook_url = f"{base_url.rstrip('/')}/webhooks/replicate/segment-image?campaign_id={campaign_id}&segment_num={segment_num}"

            logger.info(
                f"Segment {segment_num}: creating Nano Banana prediction | "
                f"prompt={image_prompt[:80]}... | webhook={webhook_url}"
            )

            prediction = client.predictions.create(
                version="google/nano-banana",
                input={
                    "prompt": image_prompt,
                    "width": 1280,
                    "height": 720,
                    "output_format": "png",
                    "output_quality": 95
                },
                webhook=webhook_url
            )

            logger.info(
                f"Segment {segment_num}: image prediction created | "
                f"prediction_id={prediction.id}"
            )

            return {
                "status": "generating",
                "segment_num": segment_num,
                "prediction_id": prediction.id
            }

    except Exception as e:
        error_msg = f"Segment {segment_num} image generation error: {str(e)}"
        logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)

        if self.request.retries < self.max_retries:
            jitter = random.randint(0, 30)
            raise self.retry(exc=e, countdown=RETRY_DELAY_BASE + jitter)

        update_segment_status(campaign_id, segment_num, "failed", error=error_msg)
        return {"status": "failed", "error": error_msg}


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_segment_video_task(
    self,
    campaign_id: str,
    segment_num: int,
    image_url: str
) -> Dict[str, Any]:
    """Generate video for a segment using Veo 3.1 image-to-video.

    Uses the provided image as the starting frame (either generated scene
    image for segment 1, or last frame from previous segment for 2-5).

    Args:
        campaign_id: Campaign UUID string
        segment_num: Segment number (1-5)
        image_url: Starting image URL for image-to-video generation

    Returns:
        Dict with status and prediction info
    """
    logger.info(
        f"Starting segment {segment_num} video generation | campaign={campaign_id} | "
        f"image_url={image_url[:60]}..."
    )

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return {"status": "failed", "error": "Campaign not found"}

            story_document = campaign.story_document
            segments = story_document.get("segments", [])
            characters = story_document.get("characters", [])

            segment = next((s for s in segments if s.get("number") == segment_num), None)
            if not segment:
                return {"status": "failed", "error": f"Segment {segment_num} not found"}

            # Build video prompt
            character_block = build_character_block(characters)
            is_first = (segment_num == 1)
            video_prompt = build_segment_prompt(segment, character_block, is_first, segment_num)

            # Update status
            update_segment_status(campaign_id, segment_num, "generating")
            campaign.pipeline_stage = f"segment_{segment_num}_video"
            db.commit()

            # Get app screenshots for reference_images (optional)
            app_screens = story_document.get("app_screens", [])
            reference_images = [s.get("url") for s in app_screens[:2] if s.get("url")]

            # Create Replicate prediction for Veo 3.1
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            webhook_url = build_webhook_url(campaign_id, segment_num)

            replicate_input = {
                "prompt": video_prompt,
                "image": image_url,  # Starting frame for image-to-video
                "duration": VEO_SEGMENT_DURATION,
                "aspect_ratio": "16:9",
                "resolution": "1080p",
                "generate_audio": True  # Generate context-aware audio from Veo 3.1
            }

            # Add reference images if available (for character/app consistency)
            if reference_images:
                replicate_input["reference_images"] = reference_images[:3]  # Max 3

            logger.info(
                f"Segment {segment_num}: creating Veo 3.1 prediction | "
                f"prompt={video_prompt[:80]}... | duration={VEO_SEGMENT_DURATION}s | "
                f"seed_image={image_url[:80]}... | webhook={webhook_url}"
            )

            prediction = client.predictions.create(
                version=VIDEO_MODEL,
                input=replicate_input,
                webhook=webhook_url
            )

            prediction_id = prediction.id
            logger.info(
                f"Segment {segment_num}: prediction created | prediction_id={prediction_id}"
            )

            # Store prediction_id
            update_segment_status(
                campaign_id,
                segment_num,
                "generating",
                prediction_id=prediction_id
            )

            return {
                "status": "generating",
                "segment_num": segment_num,
                "prediction_id": prediction_id
            }

    except Exception as e:
        error_msg = f"Segment {segment_num} video generation error: {str(e)}"
        logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)

        if self.request.retries < self.max_retries:
            jitter = random.randint(0, 30)
            raise self.retry(exc=e, countdown=RETRY_DELAY_BASE + jitter)

        update_segment_status(campaign_id, segment_num, "failed", error=error_msg)
        return {"status": "failed", "error": error_msg}


def trigger_next_segment_or_assembly(campaign_id: str, completed_segment: int) -> None:
    """Trigger next segment generation or final assembly.

    Called after a segment video completes and frame extraction is done.

    Args:
        campaign_id: Campaign UUID string
        completed_segment: The segment number that just completed
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return

            story_document = campaign.story_document or {}
            total_segments = len(story_document.get("segments", []))

            if completed_segment < total_segments:
                # More segments to generate
                next_segment = completed_segment + 1
                logger.info(
                    f"Segment {completed_segment} complete, triggering segment {next_segment} | "
                    f"campaign={campaign_id}"
                )

                # Get last frame URL from completed segment
                video_urls = campaign.video_urls or []
                completed_entry = next(
                    (v for v in video_urls if v.get("scene_number") == completed_segment),
                    None
                )

                if completed_entry and completed_entry.get("last_frame_url"):
                    # Trigger video generation directly with frame
                    generate_segment_video_task.delay(
                        campaign_id,
                        next_segment,
                        completed_entry["last_frame_url"]
                    )
                else:
                    # Frame extraction failed - fall back to generating scene image
                    logger.warning(
                        f"No last_frame_url for segment {completed_segment}, "
                        f"generating new scene image for segment {next_segment} | "
                        f"campaign={campaign_id}"
                    )
                    # Trigger image generation for the next segment as fallback
                    generate_segment_image_task.delay(campaign_id, next_segment)
            else:
                # All segments complete - check if audio is also ready before assembly
                logger.info(
                    f"All {total_segments} segments complete | campaign={campaign_id}"
                )
                campaign.pipeline_stage = "videos_ready"
                db.commit()

                # Use coordinated assembly - only triggers if audio is also ready
                from app.tasks.video_generation import check_ready_and_assemble
                check_ready_and_assemble(campaign_id)

    except Exception as e:
        logger.error(
            f"Error triggering next segment | campaign={campaign_id} | "
            f"completed={completed_segment} | error={str(e)}",
            exc_info=True
        )
