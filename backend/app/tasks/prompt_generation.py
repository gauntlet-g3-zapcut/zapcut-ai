"""Celery tasks for GPT-4o prompt enhancement (image_prompt + motion_prompt)."""
import logging
import uuid
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# System prompt for generating image and motion prompts
PROMPT_ENHANCEMENT_SYSTEM = """You are an expert visual director for video advertisements.
Your task is to transform scene descriptions into two types of prompts:

1. IMAGE_PROMPT: A detailed static image description for AI image generation.
   - Describe the exact visual composition, lighting, colors, subjects, and mood
   - Be specific about camera angle, framing, and depth of field
   - Include style references (cinematic, photorealistic, etc.)
   - Output size: 1280x720 (16:9 landscape)

2. MOTION_PROMPT: A camera/action description for video generation from the image.
   - Describe camera movement (slow push-in, pan left, dolly shot, etc.)
   - Describe any subject movement or action
   - Keep it concise - the image provides the visual, this adds motion
   - Duration: 6 seconds of video

Output JSON format:
{
  "image_prompt": "...",
  "motion_prompt": "..."
}"""


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


def generate_prompts_for_scene(
    scene_data: Dict[str, Any],
    brand_context: str,
    product_images: List[str]
) -> Dict[str, str]:
    """Generate image_prompt and motion_prompt for a single scene using GPT-4o.

    Args:
        scene_data: Scene dictionary with title, description, visual_notes, energy
        brand_context: Brand name and style context
        product_images: URLs of product/brand images for reference

    Returns:
        Dict with image_prompt and motion_prompt
    """
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured")
        raise ValueError("OPENAI_API_KEY not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    scene_num = scene_data.get("scene_number", 1)
    scene_title = scene_data.get("title", f"Scene {scene_num}")
    scene_description = scene_data.get("description", "")
    visual_notes = scene_data.get("visual_notes", "")
    energy = scene_data.get("energy", 0.5)

    # Build user prompt
    user_prompt = f"""Brand: {brand_context}

Scene {scene_num}: {scene_title}
Description: {scene_description}
Visual Notes: {visual_notes}
Energy Level: {energy} (0=calm, 1=intense)
"""

    if product_images:
        user_prompt += f"\nProduct/Brand Images Available: {len(product_images)} reference images"
        user_prompt += "\nIncorporate brand visual elements where appropriate."

    user_prompt += """

Generate the image_prompt and motion_prompt for this scene.
Remember:
- image_prompt: detailed static visual description for 1280x720 image generation
- motion_prompt: camera movement and action for 6-second video from that image

Output as JSON only, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PROMPT_ENHANCEMENT_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1000
        )

        import json
        result = json.loads(response.choices[0].message.content)

        image_prompt = result.get("image_prompt", "")
        motion_prompt = result.get("motion_prompt", "")

        if not image_prompt:
            # Fallback to building from scene data
            image_prompt = f"Cinematic wide shot: {scene_title}. {scene_description}. {visual_notes}. Photorealistic, high detail, 16:9 aspect ratio."

        if not motion_prompt:
            # Fallback to default motion
            if energy > 0.7:
                motion_prompt = "Dynamic camera movement with quick cuts and energy."
            elif energy < 0.3:
                motion_prompt = "Slow, smooth camera push-in with gentle movement."
            else:
                motion_prompt = "Medium-paced camera pan following the action."

        logger.info(f"Scene {scene_num}: generated prompts | image_prompt={len(image_prompt)} chars | motion_prompt={len(motion_prompt)} chars")

        return {
            "image_prompt": image_prompt,
            "motion_prompt": motion_prompt
        }

    except Exception as e:
        logger.error(f"Failed to generate prompts for scene {scene_num}: {e}", exc_info=True)
        # Return fallback prompts
        return {
            "image_prompt": f"Cinematic wide shot: {scene_title}. {scene_description}. {visual_notes}. Photorealistic, high detail.",
            "motion_prompt": "Smooth camera movement revealing the scene with natural motion."
        }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_enhanced_prompts_task(self, campaign_id: str) -> Dict[str, Any]:
    """Generate enhanced image_prompt and motion_prompt for all scenes using GPT-4o.

    This task:
    1. Reads storyline scenes from campaign
    2. Generates image_prompt and motion_prompt for each scene
    3. Stores in campaign.image_prompts
    4. Updates pipeline_stage to "prompts_ready"
    5. Triggers image generation task (in surprise_me mode) or waits for approval

    Args:
        campaign_id: Campaign UUID string

    Returns:
        Dict with status and generated prompts
    """
    logger.info(f"Starting prompt generation | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return {"status": "failed", "error": "Campaign not found"}

            # Update pipeline stage
            campaign.pipeline_stage = "prompts_generating"
            db.commit()

            # Get storyline scenes
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])

            if not scenes:
                logger.warning(f"No scenes in storyline | campaign={campaign_id}")
                campaign.pipeline_stage = "failed"
                campaign.status = "failed"
                db.commit()
                return {"status": "failed", "error": "No scenes in storyline"}

            # Get brand context
            brand = campaign.brand
            brand_context = f"{brand.title}" if brand else "Unknown Brand"

            # Get product images from brand
            product_images = []
            if brand and brand.images:
                product_images = [img.get("url") for img in brand.images if img.get("url")]

            # Generate prompts for each scene
            image_prompts = []
            for scene in scenes:
                scene_num = scene.get("scene_number", len(image_prompts) + 1)

                prompts = generate_prompts_for_scene(scene, brand_context, product_images)

                image_prompts.append({
                    "scene_number": scene_num,
                    "image_prompt": prompts["image_prompt"],
                    "motion_prompt": prompts["motion_prompt"]
                })

            # Store prompts in campaign
            campaign.image_prompts = image_prompts
            campaign.pipeline_stage = "prompts_ready"
            db.commit()

            logger.info(f"Prompt generation complete | campaign={campaign_id} | scenes={len(image_prompts)}")

            # Initialize video_urls with enhanced structure for each scene
            video_urls = []
            for prompt_data in image_prompts:
                scene_num = prompt_data["scene_number"]
                video_urls.append({
                    "scene_number": scene_num,
                    "image_prompt": prompt_data["image_prompt"],
                    "motion_prompt": prompt_data["motion_prompt"],
                    "prompts_approved": False,
                    "base_image_url": None,
                    "image_status": "pending",
                    "image_prediction_id": None,
                    "image_approved": False,
                    "upscaled_image_url": None,
                    "upscale_status": "pending",
                    "upscale_prediction_id": None,
                    "video_url": None,
                    "video_status": "pending",
                    "video_prediction_id": None,
                    "video_approved": False,
                    "processed_video_url": None,
                    "processing_status": "pending",
                    "status": "pending",  # Overall scene status
                    "duration": 6.0,
                    "error": None,
                    "retry_count": 0
                })

            campaign.video_urls = video_urls
            db.commit()

            # In "surprise_me" mode, auto-trigger image generation
            if campaign.director_mode == "surprise_me":
                logger.info(f"Surprise Me mode: triggering image generation | campaign={campaign_id}")
                from app.tasks.image_generation import start_image_generation_task
                start_image_generation_task.delay(campaign_id)
            else:
                logger.info(f"Director mode: waiting for prompt approval | campaign={campaign_id}")

            return {
                "status": "success",
                "campaign_id": campaign_id,
                "prompts_count": len(image_prompts),
                "pipeline_stage": "prompts_ready"
            }

    except Exception as e:
        logger.error(f"Prompt generation failed | campaign={campaign_id} | error={str(e)}", exc_info=True)

        # Update campaign status
        try:
            with db_session() as db:
                campaign_uuid = uuid.UUID(campaign_id)
                campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
                if campaign:
                    campaign.pipeline_stage = "failed"
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update campaign status | campaign={campaign_id} | error={str(db_error)}")

        # Retry if possible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "failed", "error": str(e)}
