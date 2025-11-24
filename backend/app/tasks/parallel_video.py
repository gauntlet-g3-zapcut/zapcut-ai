"""Celery tasks for V2 PARALLEL video generation using Veo 3.1 with reference images.

This is Option B: Generate character reference first, then all segments in parallel.
Much faster than sequential (~3 min vs ~15 min) with good consistency via reference images.

Pipeline:
1. Generate character reference image (establishes the look)
2. Generate all 5 scene images in parallel
3. Generate all 5 videos in parallel (each with character reference)
4. Assemble when all complete
"""
import logging
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
import replicate
from celery import group
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
VIDEO_MODEL = "google/veo-3.1"
IMAGE_MODEL = "google/nano-banana"  # For character reference and scene images
VEO_SEGMENT_DURATION = 8
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


def build_character_reference_prompt(characters: List[Dict[str, Any]]) -> str:
    """Build prompt for generating character reference image.

    Creates a neutral pose reference that can be used across all segments.
    """
    if not characters:
        return "Young professional person, neutral expression, simple background"

    main_char = characters[0]
    description = main_char.get("description", "")
    name = main_char.get("name", "Character")

    return f"""Portrait photograph for character reference sheet. Clean white/neutral background.

CHARACTER: {name}
{description}

POSE: Standing or seated, facing camera at slight angle, neutral/pleasant expression.
STYLE: High-quality portrait photo, soft natural lighting, shallow depth of field.
PURPOSE: This is a reference image - character should be clearly visible and recognizable.
FRAMING: Medium shot, head to waist, character fills most of frame."""


def build_scene_image_prompt(
    segment: Dict[str, Any],
    characters: List[Dict[str, Any]],
    segment_num: int
) -> str:
    """Build prompt for generating a scene image for a specific segment.

    When reference images are provided (character ref + app screenshots),
    the prompt instructs the model to blend them into the scene.
    """
    main_char = characters[0] if characters else {}
    char_name = main_char.get("name", "Character")
    char_description = main_char.get("description", "")
    char_phone = main_char.get("phone", "smartphone")

    visual = segment.get("visual", "") or segment.get("action", "")
    end_state = segment.get("end_state", "")
    app_screen = segment.get("app_screen")

    # Add phone instruction for segments 2-5
    phone_instruction = ""
    reference_instruction = ""
    if segment_num >= 2 and app_screen:
        phone_instruction = f"""
PHONE: Character holds {char_phone}. The phone screen clearly displays the app interface from the reference images.
The app UI is shown ON the phone screen, not floating or separate. Match the exact app UI from reference."""
        reference_instruction = """
REFERENCE IMAGES: Use the provided reference images to:
1. Match the character's face and appearance from the character reference
2. Display the EXACT app interface from the app screenshots on the phone screen
3. Blend these elements naturally into the cinematic scene"""
    elif segment_num == 1:
        phone_instruction = "\nNO PHONE in this shot - character doesn't have phone yet."
        reference_instruction = """
REFERENCE IMAGE: Match the character's face and appearance from the character reference."""

    return f"""Cinematic film still for viral mobile ad. Photorealistic, 16:9 aspect ratio.

MAIN CHARACTER - {char_name}:
{char_description}

SCENE: {visual}

MOMENT: {end_state}{phone_instruction}{reference_instruction}

STYLE: High-end mobile advertisement, natural lighting, shallow depth of field, warm cinematic color grading.
CRITICAL: Character must match the reference image EXACTLY - same face, outfit, hair, accessories."""


def build_video_prompt(
    segment: Dict[str, Any],
    characters: List[Dict[str, Any]],
    segment_num: int
) -> str:
    """Build prompt for generating video from scene image."""
    main_char = characters[0] if characters else {}
    char_name = main_char.get("name", "Character")
    char_description = main_char.get("description", "")
    char_phone = main_char.get("phone", "smartphone")

    visual = segment.get("visual", "") or segment.get("action", "")
    action = segment.get("action", "")
    end_state = segment.get("end_state", "")
    app_screen = segment.get("app_screen")

    # Add app instruction for segments with phone
    app_instruction = ""
    if segment_num >= 2 and app_screen:
        app_instruction = f"""
APP ON PHONE: The {char_phone} screen shows: {app_screen}
IMPORTANT: App stays visible ON the phone screen throughout."""

    return f"""Cinematic viral ad shot. 8 seconds. 16:9 aspect ratio.
Generate video continuing from the provided starting image.

MAIN CHARACTER - {char_name}:
{char_description}

SCENE: {visual}

ACTION: {action}{app_instruction}

END FRAME: {end_state}

STYLE: High-end mobile ad, natural lighting, cinematic.
CAMERA: Smooth motion, medium shot or close-up.
CRITICAL: Character appearance must stay IDENTICAL to starting image - same person, outfit, setting."""


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def start_parallel_pipeline_task(self, campaign_id: str) -> Dict[str, Any]:
    """Start the parallel V2 video pipeline.

    Step 1: Generate character reference image
    Then triggers parallel generation of all scene images.

    Args:
        campaign_id: Campaign UUID string

    Returns:
        Dict with status
    """
    logger.info(f"Starting PARALLEL video pipeline | campaign={campaign_id}")

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
            characters = story_document.get("characters", [])

            if not segments:
                return {"status": "failed", "error": "No segments in story_document"}

            # Initialize video_urls with all segment entries
            video_urls = []
            for segment in segments:
                seg_num = segment.get("number", 0)
                video_urls.append({
                    "scene_number": seg_num,
                    "video_status": "pending",
                    "status": "pending",
                    "video_url": None,
                    "scene_image_url": None,
                    "video_prediction_id": None,
                    "error": None
                })

            campaign.video_urls = video_urls
            campaign.pipeline_stage = "generating_character_ref"
            campaign.pipeline_version = "v2p"
            db.commit()

            logger.info(
                f"Parallel pipeline initialized | campaign={campaign_id} | "
                f"segments={len(segments)}"
            )

            # Step 1: Generate character reference image
            generate_character_reference_task.delay(campaign_id)

            return {"status": "started", "segments": len(segments), "mode": "parallel"}

    except Exception as e:
        logger.error(
            f"Failed to start parallel pipeline | campaign={campaign_id} | error={str(e)}",
            exc_info=True
        )
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_character_reference_task(self, campaign_id: str) -> Dict[str, Any]:
    """Generate character reference image for consistency across all segments.

    On completion, triggers parallel generation of all scene images.
    """
    logger.info(f"Generating character reference | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return {"status": "failed", "error": "Campaign not found"}

            story_document = campaign.story_document
            characters = story_document.get("characters", [])

            # Build character reference prompt
            char_prompt = build_character_reference_prompt(characters)

            # Create prediction for character reference image
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

            base_url = settings.API_URL or "https://zapcut-api.fly.dev"
            webhook_url = f"{base_url.rstrip('/')}/webhooks/replicate/character-ref?campaign_id={campaign_id}"

            logger.info(
                f"Creating character reference prediction | campaign={campaign_id} | "
                f"prompt={char_prompt[:80]}..."
            )

            prediction = client.predictions.create(
                version=IMAGE_MODEL,
                input={
                    "prompt": char_prompt,
                    "width": 720,  # Portrait for character reference (3:4 aspect)
                    "height": 960,
                    "output_format": "png",
                    "output_quality": 95
                },
                webhook=webhook_url
            )

            # Store prediction ID
            story_document["character_ref_prediction_id"] = prediction.id
            campaign.story_document = story_document
            campaign.pipeline_stage = "generating_character_ref"
            db.commit()

            logger.info(
                f"Character reference prediction created | campaign={campaign_id} | "
                f"prediction_id={prediction.id}"
            )

            return {"status": "generating", "prediction_id": prediction.id}

    except Exception as e:
        logger.error(
            f"Character reference generation error | campaign={campaign_id} | error={str(e)}",
            exc_info=True
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_all_scene_images_task(self, campaign_id: str) -> Dict[str, Any]:
    """Generate all scene images in parallel.

    Called after character reference is ready.
    Creates predictions for all 5 segment scene images simultaneously.
    Uses app screenshots as reference images for accurate app screen rendering.
    """
    logger.info(f"Generating all scene images in parallel | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return {"status": "failed", "error": "Campaign not found"}

            story_document = campaign.story_document
            segments = story_document.get("segments", [])
            characters = story_document.get("characters", [])

            # Get character reference URL for consistency
            char_ref_url = story_document.get("character_reference_url")

            # Get app screenshots from campaign.images for reference
            app_screenshot_urls = []
            if campaign.images:
                app_screenshot_urls = [
                    img.get("url") for img in campaign.images
                    if img.get("url")
                ][:3]  # Limit to 3 reference images

            logger.info(
                f"Scene generation setup | campaign={campaign_id} | "
                f"char_ref={'yes' if char_ref_url else 'no'} | "
                f"app_screenshots={len(app_screenshot_urls)}"
            )

            campaign.pipeline_stage = "generating_scene_images"
            db.commit()

            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            base_url = settings.API_URL or "https://zapcut-api.fly.dev"

            predictions = []
            for segment in segments:
                seg_num = segment.get("number", 0)
                app_screen = segment.get("app_screen")

                # Build scene image prompt
                scene_prompt = build_scene_image_prompt(segment, characters, seg_num)

                webhook_url = f"{base_url.rstrip('/')}/webhooks/replicate/scene-image?campaign_id={campaign_id}&segment_num={seg_num}"

                # Build input for Nano Banana
                replicate_input = {
                    "prompt": scene_prompt,
                    "aspect_ratio": "16:9",
                    "output_format": "png"
                }

                # Add reference images for segments with app screens (segments 2-5)
                # Include character reference + app screenshots for visual consistency
                if seg_num >= 2 and app_screen and app_screenshot_urls:
                    reference_images = []
                    if char_ref_url:
                        reference_images.append(char_ref_url)
                    reference_images.extend(app_screenshot_urls)
                    replicate_input["image_input"] = reference_images[:4]  # Nano Banana limit
                    logger.info(
                        f"Segment {seg_num} using {len(replicate_input['image_input'])} reference images | "
                        f"campaign={campaign_id}"
                    )
                elif char_ref_url:
                    # For segment 1 (no phone), just use character reference
                    replicate_input["image_input"] = [char_ref_url]
                    logger.info(
                        f"Segment {seg_num} using character reference only | "
                        f"campaign={campaign_id}"
                    )

                logger.info(
                    f"Creating scene image prediction for segment {seg_num} | "
                    f"campaign={campaign_id}"
                )

                prediction = client.predictions.create(
                    version=IMAGE_MODEL,
                    input=replicate_input,
                    webhook=webhook_url
                )

                predictions.append({
                    "segment_num": seg_num,
                    "prediction_id": prediction.id
                })

                # Update video_urls with prediction ID
                video_urls = list(campaign.video_urls or [])
                for entry in video_urls:
                    if entry.get("scene_number") == seg_num:
                        entry["image_prediction_id"] = prediction.id
                        entry["status"] = "image_generating"
                        break
                campaign.video_urls = video_urls

            db.commit()

            logger.info(
                f"All scene image predictions created | campaign={campaign_id} | "
                f"count={len(predictions)}"
            )

            return {"status": "generating", "predictions": predictions}

    except Exception as e:
        logger.error(
            f"Scene images generation error | campaign={campaign_id} | error={str(e)}",
            exc_info=True
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_segment_video_parallel_task(
    self,
    campaign_id: str,
    segment_num: int,
    scene_image_url: str
) -> Dict[str, Any]:
    """Generate video for a single segment using its scene image.

    Called when a scene image completes. Uses character reference for consistency.

    Args:
        campaign_id: Campaign UUID string
        segment_num: Segment number (1-5)
        scene_image_url: URL of the scene image to animate

    Returns:
        Dict with status and prediction info
    """
    logger.info(
        f"Generating video for segment {segment_num} | campaign={campaign_id} | "
        f"scene_image={scene_image_url[:60]}..."
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
            video_prompt = build_video_prompt(segment, characters, segment_num)

            # Update status
            video_urls = list(campaign.video_urls or [])
            for entry in video_urls:
                if entry.get("scene_number") == segment_num:
                    entry["status"] = "video_generating"
                    entry["video_status"] = "generating"
                    break
            campaign.video_urls = video_urls
            db.commit()

            # Create Replicate prediction for Veo 3.1
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

            base_url = settings.API_URL or "https://zapcut-api.fly.dev"
            webhook_url = f"{base_url.rstrip('/')}/webhooks/replicate/parallel-video?campaign_id={campaign_id}&segment_num={segment_num}"

            # NOTE: Veo 3.1 does NOT allow both 'image' and 'reference_images' parameters.
            # Since we're using scene_image_url as the starting frame, we cannot also pass
            # reference_images. The scene image already establishes character appearance.
            replicate_input = {
                "prompt": video_prompt,
                "image": scene_image_url,  # Scene image as starting frame
                "duration": VEO_SEGMENT_DURATION,
                "aspect_ratio": "16:9",
                "resolution": "1080p",
                "generate_audio": True
            }

            logger.info(
                f"Creating Veo 3.1 prediction for segment {segment_num} | "
                f"campaign={campaign_id} | prompt={video_prompt[:80]}..."
            )

            prediction = client.predictions.create(
                version=VIDEO_MODEL,
                input=replicate_input,
                webhook=webhook_url
            )

            # Store prediction ID
            video_urls = list(campaign.video_urls or [])
            for entry in video_urls:
                if entry.get("scene_number") == segment_num:
                    entry["video_prediction_id"] = prediction.id
                    break
            campaign.video_urls = video_urls
            db.commit()

            logger.info(
                f"Video prediction created for segment {segment_num} | "
                f"campaign={campaign_id} | prediction_id={prediction.id}"
            )

            return {
                "status": "generating",
                "segment_num": segment_num,
                "prediction_id": prediction.id
            }

    except Exception as e:
        logger.error(
            f"Video generation error for segment {segment_num} | "
            f"campaign={campaign_id} | error={str(e)}",
            exc_info=True
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        # Mark segment as failed
        try:
            with db_session() as db:
                campaign_uuid = uuid.UUID(campaign_id)
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    video_urls = list(campaign.video_urls or [])
                    for entry in video_urls:
                        if entry.get("scene_number") == segment_num:
                            entry["status"] = "failed"
                            entry["error"] = str(e)
                            break
                    campaign.video_urls = video_urls
                    db.commit()
        except Exception:
            pass

        return {"status": "failed", "error": str(e)}


def check_all_videos_complete_and_assemble(campaign_id: str) -> None:
    """Check if all videos are complete and trigger assembly.

    Called after each video completes. Only triggers assembly when ALL
    segments have completed video generation.
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return

            video_urls = campaign.video_urls or []
            story_document = campaign.story_document or {}
            total_segments = len(story_document.get("segments", []))

            # Count completed videos
            completed = [
                v for v in video_urls
                if v.get("video_status") == "completed" and v.get("video_url")
            ]

            logger.info(
                f"Checking video completion | campaign={campaign_id} | "
                f"completed={len(completed)}/{total_segments}"
            )

            if len(completed) >= total_segments:
                logger.info(
                    f"All {total_segments} videos complete, checking audio | "
                    f"campaign={campaign_id}"
                )
                campaign.pipeline_stage = "videos_ready"
                db.commit()

                # Use coordinated assembly (waits for audio too)
                from app.tasks.video_generation import check_ready_and_assemble
                check_ready_and_assemble(campaign_id)
            else:
                # Check for failures
                failed = [v for v in video_urls if v.get("status") == "failed"]
                if failed:
                    logger.warning(
                        f"Some segments failed | campaign={campaign_id} | "
                        f"failed={len(failed)}"
                    )

    except Exception as e:
        logger.error(
            f"Error checking video completion | campaign={campaign_id} | "
            f"error={str(e)}",
            exc_info=True
        )
