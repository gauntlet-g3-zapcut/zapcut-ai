"""Celery tasks for music soundtrack generation using ElevenLabs Music Soundtrack API."""
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


def split_prompt_into_lines(prompt: str, max_length: int = 200) -> List[str]:
    """Split a prompt into multiple lines, each under max_length characters.
    
    Tries to split at sentence boundaries first, then falls back to word boundaries.
    Ensures all lines are strictly under max_length.
    """
    if len(prompt) <= max_length:
        return [prompt]
    
    lines = []
    remaining = prompt.strip()
    
    while len(remaining) > max_length:
        # Try to find a sentence boundary (period followed by space) within the limit
        best_split = -1
        search_start = max(0, max_length - 50)  # Look in the last 50 chars before limit
        search_end = min(max_length, len(remaining))
        
        for i in range(search_end - 1, search_start - 1, -1):  # Search backwards
            if remaining[i] == '.':
                # Check if it's followed by a space (sentence boundary)
                if i + 1 < len(remaining) and remaining[i + 1] == ' ':
                    best_split = i + 1
                    break
        
        # If no sentence boundary found, try word boundary
        if best_split == -1:
            for i in range(search_end - 1, search_start - 1, -1):  # Search backwards
                if remaining[i] == ' ':
                    best_split = i
                    break
        
        # If still no good split point, force split at max_length (but try to avoid mid-word)
        if best_split == -1:
            # Try to find any space near the limit
            for i in range(max_length - 1, max(0, max_length - 20), -1):
                if i < len(remaining) and remaining[i] == ' ':
                    best_split = i
                    break
            
            # Last resort: split at max_length
            if best_split == -1:
                best_split = max_length
        
        # Extract the line and remaining text
        line = remaining[:best_split].strip()
        remaining = remaining[best_split:].strip()
        
        # Safety: if line is still too long (shouldn't happen), truncate
        if len(line) > max_length:
            line = line[:max_length]
        
        if line:  # Only add non-empty lines
            lines.append(line)
    
    # Add remaining text if any
    if remaining:
        # Final safety check
        if len(remaining) > max_length:
            remaining = remaining[:max_length]
        lines.append(remaining)
    
    return lines if lines else [prompt[:max_length]]  # Fallback if something went wrong


def build_composition_plan_from_storyline(storyline: Dict[str, Any]) -> Dict[str, Any]:
    """Build ElevenLabs composition plan from storyline scenes.
    
    Creates a structured composition plan with sections matching each scene,
    including durations, energy transitions, and musical style descriptions.
    This plan is used with client.music.compose_detailed() to generate music.
    
    Validates durations (1-300 seconds) and energy values (0.0-1.0) per ElevenLabs API requirements.
    
    Returns:
        Dictionary representing the composition plan structure matching ElevenLabs API schema
    """
    scenes = storyline.get("scenes", [])
    if not scenes:
        return {
            "positive_global_styles": [],
            "negative_global_styles": [],
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
        
        # Validate and clamp duration (ElevenLabs requires 1-300 seconds per section)
        duration = max(1.0, min(300.0, float(duration)))
        
        # Validate and clamp energy values (0.0-1.0)
        energy_start = max(0.0, min(1.0, float(energy_start)))
        energy_end = max(0.0, min(1.0, float(energy_end)))
        
        duration_ms = int(duration * 1000)
        
        # Get mood descriptors for this scene's energy levels
        start_moods = map_energy_to_moods(energy_start)
        end_moods = map_energy_to_moods(energy_end)
        
        # Combine moods for local styles - these vary per scene while genre stays consistent
        if energy_start != energy_end:
            local_moods = [start_moods[0], end_moods[0]]
        else:
            local_moods = start_moods[:2] if len(start_moods) >= 2 else start_moods
        
        # Build music description lines for this section
        # These describe the musical style/mood for the section, not spoken narration
        music_description_parts = []
        
        # Add scene context
        if description:
            # Extract musical context from description if present
            music_description_parts.append(f"Music for {description.lower()}")
        
        # Add energy/mood description for music
        if energy_start < energy_end:
            music_description_parts.append(f"Building from {start_moods[0]} to {end_moods[0]} energy")
        elif energy_end < energy_start:
            music_description_parts.append(f"Transitioning from {start_moods[0]} to {end_moods[0]} energy")
        else:
            music_description_parts.append(f"Maintaining {start_moods[0]} energy")
        
        # Add genre/style note
        music_description_parts.append(f"{base_genre} style")
        
        # Create music description line (keep it concise, under 200 chars)
        music_description = ". ".join(music_description_parts) if music_description_parts else f"{base_genre} music for scene {scene_num}"
        
        # Split if needed (though music descriptions should be shorter)
        if len(music_description) > 200:
            music_description = music_description[:200]
        
        # Create section structure matching ElevenLabs API schema
        # IMPORTANT: Use snake_case field names as required by the API
        section = {
            "section_name": f"Scene {scene_num}: {title}",
            "positive_local_styles": local_moods,  # Moods for this section
            "negative_local_styles": [],  # No negative styles needed
            "duration_ms": duration_ms,
            "lines": [music_description]  # Music style description for this section
        }
        
        sections.append(section)
    
    return {
        "positive_global_styles": positive_global_styles,
        "negative_global_styles": negative_global_styles,
        "sections": sections
    }


def extract_audio_from_response(music_response: Any) -> bytes:
    """Extract audio bytes from ElevenLabs compose_detailed response.
    
    The compose_detailed() method returns a MultipartResponse object.
    Use .audio attribute to get the raw bytes - this is the correct method.
    
    Available attributes: ['audio', 'filename', 'json']
    
    DO NOT try to iterate over the response - that causes "not iterable" error.
    
    Args:
        music_response: The response from client.music.compose_detailed()
        
    Returns:
        bytes: The audio file bytes
        
    Raises:
        ValueError: If response is empty or cannot be read
    """
    if not music_response:
        raise ValueError("Empty response from ElevenLabs API")
    
    # Log response details for debugging
    response_type = type(music_response).__name__
    response_module = type(music_response).__module__
    available_attrs = [attr for attr in dir(music_response) if not attr.startswith('_')]
    
    logger.info(
        f"Extracting audio from response | "
        f"type={response_type} | "
        f"module={response_module} | "
        f"has_audio={hasattr(music_response, 'audio')} | "
        f"has_content={hasattr(music_response, 'content')} | "
        f"has_read={hasattr(music_response, 'read')} | "
        f"available_attrs={available_attrs[:10]}"  # First 10 attributes
    )
    
    # Log additional httpx Response properties if available
    if hasattr(music_response, 'status_code'):
        logger.info(f"Response status_code={music_response.status_code}")
    if hasattr(music_response, 'headers'):
        content_type = music_response.headers.get('content-type', 'unknown')
        content_length = music_response.headers.get('content-length', 'unknown')
        logger.info(f"Response headers | content-type={content_type} | content-length={content_length}")
    
    try:
        # MultipartResponse has an .audio attribute - this is the correct way to extract audio
        # Available attributes: ['audio', 'filename', 'json']
        if hasattr(music_response, 'audio'):
            # MultipartResponse object - use .audio attribute
            logger.info("Using .audio attribute to extract audio bytes")
            audio_bytes = music_response.audio
            logger.info(f"Extracted {len(audio_bytes)} bytes using .audio attribute")
        elif hasattr(music_response, 'content'):
            # httpx Response object - use .content property (fallback)
            logger.info("Using .content property to extract audio bytes")
            audio_bytes = music_response.content
            logger.info(f"Extracted {len(audio_bytes)} bytes using .content property")
        elif hasattr(music_response, 'read'):
            # BinaryIO object - use .read() method (fallback for other response types)
            logger.info("Using .read() method to extract audio bytes")
            audio_bytes = music_response.read()
            logger.info(f"Extracted {len(audio_bytes)} bytes using .read() method")
        else:
            # Unknown response type
            logger.error(
                f"Response type {response_type} has no .audio, .content, or .read() method. "
                f"Available attributes: {available_attrs}"
            )
            raise ValueError(
                f"Response type {response_type} has no .audio, .content, or .read() method. "
                f"Available attributes: {available_attrs}"
            )
        
        # Validate we got actual audio data
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Empty audio data received from ElevenLabs API")
        
        logger.info(
            f"Audio extracted successfully | "
            f"size={len(audio_bytes)} bytes | "
            f"response_type={response_type}"
        )
        return audio_bytes
        
    except Exception as e:
        logger.error(
            f"Failed to extract audio | "
            f"error={str(e)} | "
            f"response_type={response_type} | "
            f"has_audio={hasattr(music_response, 'audio')} | "
            f"has_content={hasattr(music_response, 'content')} | "
            f"has_read={hasattr(music_response, 'read')}",
            exc_info=True
        )
        raise


def validate_composition_plan(composition_plan: Dict[str, Any]) -> None:
    """Validate composition plan structure before sending to ElevenLabs API.
    
    Ensures all required fields are present and have correct types/values.
    
    Args:
        composition_plan: The composition plan dictionary
        
    Raises:
        ValueError: If validation fails
    """
    # Check required top-level fields
    required_fields = ["positive_global_styles", "negative_global_styles", "sections"]
    for field in required_fields:
        if field not in composition_plan:
            raise ValueError(f"Missing required field in composition plan: {field}")
    
    # Validate sections
    sections = composition_plan.get("sections", [])
    if not sections:
        raise ValueError("Composition plan must have at least one section")
    
    # Validate each section
    required_section_fields = ["section_name", "positive_local_styles", "negative_local_styles", "duration_ms", "lines"]
    for i, section in enumerate(sections):
        for field in required_section_fields:
            if field not in section:
                raise ValueError(f"Section {i} missing required field: {field}")
        
        # Validate duration_ms (1-300 seconds = 1000-300000 ms)
        duration_ms = section.get("duration_ms", 0)
        if not isinstance(duration_ms, int) or duration_ms < 1000 or duration_ms > 300000:
            raise ValueError(
                f"Section {i} has invalid duration_ms: {duration_ms}. "
                "Must be between 1000 and 300000 milliseconds (1-300 seconds)."
            )
        
        # Validate lines is a list
        lines = section.get("lines", [])
        if not isinstance(lines, list) or len(lines) == 0:
            raise ValueError(f"Section {i} must have at least one line in 'lines' array")


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
    
    Builds a structured composition plan from the campaign storyline with sections
    matching each scene, including durations, energy transitions, and musical styles.
    Uses client.music.compose_detailed() or client.music.compose() with the
    composition_plan to generate actual music soundtracks.
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
                error_msg = "Failed to build composition plan: no sections"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_audio_status_safe(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}
            
            # Validate composition plan structure before sending to API
            try:
                validate_composition_plan(composition_plan)
            except ValueError as validation_error:
                error_msg = f"Invalid composition plan: {str(validation_error)}"
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
            # We use compose_detailed() with a composition_plan for structured music generation
            try:
                # Initialize ElevenLabs client
                client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
                
                # Check if music API is available in the SDK
                if not hasattr(client, 'music'):
                    raise AttributeError(
                        "ElevenLabs SDK version does not support music API. "
                        "Please update elevenlabs package to latest version."
                    )
                
                # Use compose_detailed() with composition_plan for structured music generation
                # compose_detailed() has been stable since SDK 2.13.0 and returns BinaryIO directly
                logger.info(f"Composing music soundtrack with composition plan | campaign={campaign_id}")
                
                # Use compose_detailed() directly - it's the standard method for composition plans
                if not hasattr(client.music, 'compose_detailed'):
                    raise AttributeError(
                        "ElevenLabs SDK version does not support compose_detailed() method. "
                        "Please update elevenlabs package to version 2.13.0 or later."
                    )
                
                music_response = client.music.compose_detailed(
                    composition_plan=composition_plan
                )
                
                # Log response details immediately after API call
                response_type = type(music_response).__name__
                response_module = type(music_response).__module__
                logger.info(
                    f"Music response received from API | campaign={campaign_id} | "
                    f"type={response_type} | "
                    f"module={response_module} | "
                    f"has_audio={hasattr(music_response, 'audio')} | "
                    f"has_content={hasattr(music_response, 'content')} | "
                    f"has_read={hasattr(music_response, 'read')}"
                )
                
                # Log response status and headers if available (httpx Response)
                if hasattr(music_response, 'status_code'):
                    logger.info(f"Response status_code={music_response.status_code}")
                if hasattr(music_response, 'headers'):
                    headers_summary = {
                        'content-type': music_response.headers.get('content-type', 'N/A'),
                        'content-length': music_response.headers.get('content-length', 'N/A'),
                    }
                    logger.info(f"Response headers: {headers_summary}")
                
                # Extract audio bytes from response
                # compose_detailed() returns a MultipartResponse (httpx Response object)
                audio_bytes = extract_audio_from_response(music_response)
                
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

