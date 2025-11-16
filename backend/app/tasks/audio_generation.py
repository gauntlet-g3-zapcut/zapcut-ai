"""Celery tasks for music soundtrack generation using ElevenLabs Music Composition API."""
import json
import logging
import uuid
import time
import io
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
from elevenlabs.client import ElevenLabs
import boto3
from botocore.exceptions import ClientError
from celery import Task
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY_BASE = 60  # Base delay in seconds for exponential backoff


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


def determine_base_genre_and_mood(scenes: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """Determine a consistent base genre and overall mood for the soundtrack.
    
    Analyzes all scenes to determine a consistent musical style that works across
    all scenes, ensuring the soundtrack doesn't jump between incompatible genres.
    
    Returns:
        tuple: (base_genre, base_moods) - A consistent genre and list of moods
    """
    # Calculate average energy across all scenes
    avg_energy = sum(
        (scene.get("energy_start", 0.5) + scene.get("energy_end", 0.5)) / 2
        for scene in scenes
    ) / len(scenes) if scenes else 0.5
    
    # Determine base genre based on average energy and scene count
    # For advertisements, we typically want modern, versatile genres
    if avg_energy < 0.4:
        base_genre = "ambient"
        base_moods = ["calm", "subtle", "atmospheric"]
    elif avg_energy < 0.6:
        base_genre = "cinematic"
        base_moods = ["moderate", "building", "emotional"]
    elif avg_energy < 0.8:
        base_genre = "modern pop"
        base_moods = ["energetic", "dynamic", "uplifting"]
    else:
        base_genre = "electronic"
        base_moods = ["intense", "powerful", "driving"]
    
    return base_genre, base_moods


def map_energy_to_moods(energy: float) -> List[str]:
    """Map energy level to appropriate mood descriptors.
    
    Args:
        energy: Energy level between 0.0 and 1.0
        
    Returns:
        List of mood strings appropriate for the energy level
    """
    if energy < 0.3:
        return ["calm", "peaceful", "gentle"]
    elif energy < 0.5:
        return ["moderate", "steady", "balanced"]
    elif energy < 0.7:
        return ["energetic", "dynamic", "uplifting"]
    else:
        return ["intense", "powerful", "driving"]


def build_composition_plan_from_storyline(storyline: Dict[str, Any]) -> Dict[str, Any]:
    """Build ElevenLabs composition plan from storyline scenes.
    
    Creates a structured composition plan with sections matching each scene,
    ensuring consistent genre/style while allowing mood and energy variations.
    
    Returns:
        Dictionary representing the composition plan structure matching ElevenLabs API schema
    """
    scenes = storyline.get("scenes", [])
    if not scenes:
        return {
            "positiveGlobalStyles": [],
            "negativeGlobalStyles": [],
            "sections": []
        }
    
    # Determine consistent base genre and moods for the entire soundtrack
    base_genre, base_moods = determine_base_genre_and_mood(scenes)
    
    # Set global styles based on the consistent genre
    # This ensures the entire soundtrack maintains a consistent musical style
    positive_global_styles = [base_genre]
    negative_global_styles = []  # No negative styles - we want genre consistency
    
    # Build sections for each scene
    sections = []
    
    for scene in scenes:
        scene_num = scene.get("scene_number", 0)
        title = scene.get("title", f"Scene {scene_num}")
        description = scene.get("description", "")
        duration = scene.get("duration", 6.0)
        energy_start = scene.get("energy_start", 0.5)
        energy_end = scene.get("energy_end", 0.5)
        visual_notes = scene.get("visual_notes", "")
        
        duration_ms = int(duration * 1000)
        
        # Get mood descriptors for this scene's energy levels
        start_moods = map_energy_to_moods(energy_start)
        end_moods = map_energy_to_moods(energy_end)
        
        # Combine moods for local styles - these vary per scene while genre stays consistent
        if energy_start != energy_end:
            local_moods = [start_moods[0], end_moods[0]]
        else:
            local_moods = start_moods[:2] if len(start_moods) >= 2 else start_moods
        
        # Build prompt lines for this section
        # Keep it focused on the scene's mood and energy while maintaining genre consistency
        prompt_parts = []
        if description:
            prompt_parts.append(description)
        if visual_notes:
            prompt_parts.append(visual_notes)
        
        # Add energy/mood description
        if energy_start < energy_end:
            prompt_parts.append(f"Building from {start_moods[0]} to {end_moods[0]} energy")
        elif energy_end < energy_start:
            prompt_parts.append(f"Transitioning from {start_moods[0]} to {end_moods[0]} energy")
        else:
            prompt_parts.append(f"Maintaining {start_moods[0]} energy")
        
        section_prompt = ". ".join(prompt_parts) if prompt_parts else f"Scene {scene_num}: {title}"
        
        # Create section structure matching ElevenLabs API schema
        # IMPORTANT: Use camelCase field names as required by the API
        # Based on the documentation: sectionName, positiveLocalStyles, negativeLocalStyles,
        # durationMs, lines (array of strings)
        section = {
            "sectionName": f"Scene {scene_num}: {title}",
            "positiveLocalStyles": local_moods,  # Moods for this section
            "negativeLocalStyles": [],  # No negative styles needed
            "durationMs": duration_ms,
            "lines": [section_prompt]  # Prompt as array of lines (required by API)
        }
        
        sections.append(section)
    
    return {
        "positiveGlobalStyles": positive_global_styles,
        "negativeGlobalStyles": negative_global_styles,
        "sections": sections
    }


def upload_audio_to_supabase_s3(audio_bytes: bytes, campaign_id: str) -> str:
    """Upload audio file to Supabase S3 storage.
    
    Args:
        audio_bytes: The audio file bytes to upload
        campaign_id: Campaign ID for file naming
        
    Returns:
        Public URL of the uploaded audio file
        
    Raises:
        Exception: If upload fails
    """
    if not all([
        settings.SUPABASE_S3_ENDPOINT,
        settings.SUPABASE_S3_ACCESS_KEY,
        settings.SUPABASE_S3_SECRET_KEY
    ]):
        raise ValueError("Supabase S3 credentials not configured")
    
    try:
        # Initialize S3 client for Supabase
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.SUPABASE_S3_ENDPOINT,
            aws_access_key_id=settings.SUPABASE_S3_ACCESS_KEY,
            aws_secret_access_key=settings.SUPABASE_S3_SECRET_KEY,
            region_name='us-east-1'  # Default region, adjust if needed
        )
        
        # Bucket name for audio files
        bucket_name = 'soundtracks'
        file_key = f"{campaign_id}.mp3"
        
        # Upload audio bytes
        audio_file = io.BytesIO(audio_bytes)
        s3_client.upload_fileobj(
            audio_file,
            Bucket=bucket_name,
            Key=file_key,
            ExtraArgs={
                'ContentType': 'audio/mpeg',
                'ACL': 'public-read'  # Make file publicly accessible
            }
        )
        
        # Construct public URL
        # Supabase Storage public URLs: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{key}
        # Extract base URL from endpoint
        endpoint = settings.SUPABASE_S3_ENDPOINT.rstrip('/')
        
        # If endpoint contains /storage/v1, extract the base URL
        if '/storage/v1' in endpoint:
            base_url = endpoint.split('/storage/v1')[0]
        else:
            # If endpoint is just the base URL, use it directly
            base_url = endpoint
        
        # Construct public URL
        audio_url = f"{base_url}/storage/v1/object/public/{bucket_name}/{file_key}"
        
        logger.info(f"Audio uploaded to Supabase S3 | campaign={campaign_id} | bucket={bucket_name} | url={audio_url}")
        return audio_url
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        logger.error(
            f"S3 upload error | campaign={campaign_id} | code={error_code} | error={error_msg}",
            exc_info=True
        )
        raise Exception(f"Failed to upload audio to S3: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error uploading audio | campaign={campaign_id} | error={str(e)}", exc_info=True)
        raise


def update_audio_status_safe(
    campaign_id: str,
    status: str,
    audio_url: Optional[str] = None,
    error: Optional[str] = None,
    retry_count: Optional[int] = None
) -> bool:
    """Safely update audio generation status."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                return False
            
            campaign.audio_status = status
            if audio_url:
                campaign.audio_url = audio_url
            if error:
                campaign.audio_generation_error = error
            elif error is None:
                campaign.audio_generation_error = None
            
            # Log important status changes
            if status in ["completed", "failed"]:
                if status == "completed" and audio_url:
                    logger.info(
                        f"Audio generation {status} | campaign={campaign_id} | "
                        f"audio_url={audio_url}"
                    )
                else:
                    logger.info(f"Audio generation {status} | campaign={campaign_id}")
            
            return True
    except Exception as e:
        logger.error(f"Failed to update audio status | campaign={campaign_id} | error={str(e)}")
        return False


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_audio_task(self, campaign_id: str) -> Dict[str, Any]:
    """Generate music soundtrack using ElevenLabs Music Composition API.
    
    Builds a descriptive prompt from the campaign storyline and uses ElevenLabs'
    composition plan API to generate a music soundtrack that matches scene
    transitions, moods, and energy levels.
    """
    logger.info(f"Starting audio generation | campaign={campaign_id}")
    
    try:
        # Update status to generating
        update_audio_status_safe(campaign_id, "generating")
        
        # Get campaign data
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            
            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                update_audio_status_safe(campaign_id, "failed", error="Campaign not found")
                return {"status": "failed", "error": "Campaign not found"}
            
            storyline = campaign.storyline or {}
            scenes = storyline.get("scenes", [])
            
            if not scenes:
                error_msg = "No scenes found in storyline"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_audio_status_safe(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}
            
            # Check API key
            if not settings.ELEVENLABS_API_KEY:
                error_msg = "ELEVENLABS_API_KEY not configured"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_audio_status_safe(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}
            
            # Build composition plan from storyline
            composition_plan = build_composition_plan_from_storyline(storyline)
            
            if not composition_plan.get("sections"):
                error_msg = "Failed to build composition plan"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_audio_status_safe(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}
            
            # Calculate total duration
            total_duration = sum(scene.get("duration", 6.0) for scene in scenes)
            
            logger.info(
                f"Generating music soundtrack | campaign={campaign_id} | "
                f"sections={len(composition_plan['sections'])} | duration={total_duration}s"
            )
            
            # Generate music soundtrack using ElevenLabs Music Composition API
            # We build a structured composition plan with sections matching each scene,
            # ensuring consistent genre while allowing mood/energy variations.
            try:
                # Initialize ElevenLabs client
                client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
                
                # Generate the music soundtrack using the composition plan
                logger.info(f"Composing music soundtrack | campaign={campaign_id}")
                
                # Check if music API is available in the SDK
                if not hasattr(client, 'music'):
                    raise AttributeError(
                        "ElevenLabs SDK version does not support music API. "
                        "Please update elevenlabs package to latest version."
                    )
                
                composition = client.music.compose(
                    composition_plan=composition_plan
                )
                
                # Read audio bytes from the response iterator
                audio_bytes = b""
                for chunk in composition:
                    if hasattr(chunk, 'read'):
                        audio_bytes += chunk.read()
                    elif isinstance(chunk, bytes):
                        audio_bytes += chunk
                    else:
                        # If chunk is a file-like object, read it
                        audio_bytes += bytes(chunk)
                
                logger.info(
                    f"Music soundtrack generated successfully | campaign={campaign_id} | "
                    f"audio_size={len(audio_bytes)} bytes | duration={total_duration}s"
                )
                
                # Upload audio to Supabase S3 storage
                try:
                    audio_url = upload_audio_to_supabase_s3(audio_bytes, campaign_id)
                    logger.info(f"Audio uploaded to storage | campaign={campaign_id} | url={audio_url}")
                except Exception as upload_error:
                    error_msg = f"Failed to upload audio: {str(upload_error)}"
                    logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)
                    # If upload fails, we still mark as failed (don't store placeholder)
                    update_audio_status_safe(campaign_id, "failed", error=error_msg)
                    raise upload_error
                
                update_audio_status_safe(campaign_id, "completed", audio_url=audio_url)
                
                return {
                    "status": "completed",
                    "audio_url": audio_url,
                    "duration": total_duration
                }
                
            except Exception as api_error:
                # Extract detailed error information if it's an SDK exception
                error_msg = f"ElevenLabs API error: {str(api_error)}"
                
                # Try to extract detailed error information from SDK exceptions
                if hasattr(api_error, 'body'):
                    try:
                        error_body = api_error.body
                        if isinstance(error_body, dict):
                            error_detail = error_body.get('detail', {})
                            error_status = error_detail.get('status', 'unknown')
                            error_data = error_detail.get('data', {})
                            
                            error_msg = (
                                f"ElevenLabs API error: {error_status} | "
                                f"details={json.dumps(error_data, indent=2)}"
                            )
                            
                            logger.error(
                                f"Audio generation API error | campaign={campaign_id} | "
                                f"error_status={error_status} | error_data={json.dumps(error_data, indent=2)}",
                                exc_info=True
                            )
                            
                            # Handle specific error types
                            if error_status == 'bad_composition_plan':
                                suggested_plan = error_data.get('composition_plan_suggestion')
                                if suggested_plan:
                                    logger.error(
                                        f"ElevenLabs suggested composition plan | campaign={campaign_id} | "
                                        f"suggestion={json.dumps(suggested_plan, indent=2)}"
                                    )
                    except (AttributeError, KeyError, TypeError):
                        # If we can't parse the error, use the default message
                        logger.error(
                            f"Audio generation API error | campaign={campaign_id} | error={error_msg}",
                            exc_info=True
                        )
                else:
                    logger.error(
                        f"Audio generation API error | campaign={campaign_id} | error={error_msg}",
                        exc_info=True
                    )
                
                # Retry if we haven't exceeded max retries
                if self.request.retries < self.max_retries:
                    retry_delay = RETRY_DELAY_BASE * (2 ** self.request.retries)
                    logger.info(
                        f"Retrying audio generation ({self.request.retries + 1}/{self.max_retries}) | "
                        f"campaign={campaign_id} | delay={retry_delay}s"
                    )
                    raise self.retry(exc=api_error, countdown=retry_delay)
                
                # Max retries exceeded
                update_audio_status_safe(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}
    
    except Exception as e:
        error_msg = f"Audio generation error: {str(e)}"
        logger.error(
            f"Audio generation failed | campaign={campaign_id} | error={error_msg}",
            exc_info=True
        )
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            retry_delay = RETRY_DELAY_BASE * (2 ** self.request.retries)
            logger.info(
                f"Retrying audio generation ({self.request.retries + 1}/{self.max_retries}) | "
                f"campaign={campaign_id} | delay={retry_delay}s"
            )
            raise self.retry(exc=e, countdown=retry_delay)
        
        # Max retries exceeded
        update_audio_status_safe(campaign_id, "failed", error=error_msg)
        return {"status": "failed", "error": error_msg}

