"""Celery tasks for V2 voiceover generation using ElevenLabs TTS."""
import logging
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional
from elevenlabs.client import ElevenLabs
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 2
RETRY_DELAY_BASE = 30

# Default voice ID if not specified in story_document
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Warm female voice


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


def build_full_narration(story_document: Dict[str, Any]) -> str:
    """Concatenate all segment voiceovers into full 40-second script.

    Args:
        story_document: The story document with segments

    Returns:
        Full voiceover text for TTS
    """
    segments = story_document.get("segments", [])

    if not segments:
        # Fallback to full_narrative if no segments
        return story_document.get("full_narrative", "")

    # Concatenate voiceovers with natural pauses
    voiceovers = []
    for segment in sorted(segments, key=lambda s: s.get("number", 0)):
        # Try "voiceover" first (new format), fall back to "narration" (old format)
        voiceover = segment.get("voiceover", "").strip() or segment.get("narration", "").strip()
        if voiceover:
            voiceovers.append(voiceover)

    # If no voiceovers found in segments, fall back to full_narrative
    if not voiceovers:
        return story_document.get("full_narrative", "")

    return " ".join(voiceovers)


def update_voiceover_status(
    campaign_id: str,
    status: str,
    voiceover_url: Optional[str] = None,
    error: Optional[str] = None
) -> bool:
    """Update voiceover generation status in campaign."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return False

            campaign.voiceover_status = status

            if voiceover_url:
                campaign.voiceover_url = voiceover_url
            if error:
                campaign.audio_generation_error = error

            if status == "completed":
                logger.info(
                    f"Voiceover generation {status} | campaign={campaign_id} | "
                    f"url={voiceover_url}"
                )
            else:
                logger.info(f"Voiceover status updated | campaign={campaign_id} | status={status}")

            return True

    except Exception as e:
        logger.error(f"Failed to update voiceover status | campaign={campaign_id} | error={str(e)}")
        return False


def check_audio_ready_and_mix(campaign_id: str) -> None:
    """Check if both voiceover and music are ready, then trigger audio mixing.

    Called after voiceover or music generation completes.
    """
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                return

            voiceover_ready = (
                campaign.voiceover_status == "completed" and
                campaign.voiceover_url
            )
            music_ready = (
                campaign.audio_status == "completed" and
                campaign.audio_url
            )

            if voiceover_ready and music_ready:
                logger.info(f"Both voiceover and music ready, triggering audio mixing | campaign={campaign_id}")
                from app.tasks.audio_mixing import mix_final_audio_task
                mix_final_audio_task.delay(campaign_id)
            elif voiceover_ready:
                logger.info(f"Voiceover ready, waiting for music | campaign={campaign_id}")
            elif music_ready:
                logger.info(f"Music ready, waiting for voiceover | campaign={campaign_id}")

    except Exception as e:
        logger.error(f"Error checking audio ready state | campaign={campaign_id} | error={str(e)}")


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def generate_voiceover_task(self, campaign_id: str) -> Dict[str, Any]:
    """Generate voiceover narration using ElevenLabs TTS.

    Reads story_document from campaign and generates full 40-second narration.
    Uses consistent voice ID from story_document.narrator.elevenlabs_voice_id.

    On completion:
    - Updates campaign.voiceover_url
    - Checks if music is ready and triggers audio mixing

    Args:
        campaign_id: Campaign UUID string

    Returns:
        Dict with status and voiceover_url
    """
    logger.info(f"Starting voiceover generation | campaign={campaign_id}")

    try:
        update_voiceover_status(campaign_id, "generating")

        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return {"status": "failed", "error": "Campaign not found"}

            # Get story document
            story_document = campaign.story_document

            if not story_document:
                error_msg = "No story_document found - run story generation first"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_voiceover_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

            # Check API key
            if not settings.ELEVENLABS_API_KEY:
                error_msg = "ELEVENLABS_API_KEY not configured"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_voiceover_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

            # Get voice ID from story document
            narrator = story_document.get("narrator", {})
            voice_id = narrator.get("elevenlabs_voice_id", DEFAULT_VOICE_ID)
            voice_style = narrator.get("voice_style", "Warm, conversational")

            # Build full narration text
            narration_text = build_full_narration(story_document)

            # Debug logging for narration extraction
            segments = story_document.get("segments", [])
            logger.info(
                f"Voiceover debug | campaign={campaign_id} | "
                f"segments_count={len(segments)} | "
                f"has_full_narrative={bool(story_document.get('full_narrative'))} | "
                f"narration_text_length={len(narration_text) if narration_text else 0}"
            )
            if segments:
                for seg in segments[:2]:  # Log first 2 segments for debugging
                    logger.info(
                        f"Segment {seg.get('number')}: voiceover={bool(seg.get('voiceover'))} "
                        f"narration={bool(seg.get('narration'))} "
                        f"text_preview={str(seg.get('voiceover') or seg.get('narration') or '')[:50]}"
                    )

            if not narration_text:
                error_msg = f"No narration text in story_document. segments={len(segments)}, has_full_narrative={bool(story_document.get('full_narrative'))}"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                update_voiceover_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

            word_count = len(narration_text.split())
            logger.info(
                f"Generating voiceover | campaign={campaign_id} | "
                f"voice_id={voice_id} | voice_style={voice_style} | "
                f"words={word_count}"
            )

            # Initialize ElevenLabs client
            client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

            # Generate TTS audio
            # Use text_to_speech.convert() for simple TTS generation
            try:
                audio_generator = client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=narration_text,
                    model_id="eleven_multilingual_v2",  # High quality multilingual model
                    output_format="mp3_44100_128"  # High quality MP3
                )

                # Collect audio bytes from generator
                audio_bytes = b""
                for chunk in audio_generator:
                    audio_bytes += chunk

                if not audio_bytes:
                    raise ValueError("Empty audio response from ElevenLabs")

                logger.info(
                    f"Voiceover generated | campaign={campaign_id} | "
                    f"size={len(audio_bytes)} bytes"
                )

            except Exception as tts_error:
                error_msg = f"ElevenLabs TTS error: {str(tts_error)}"
                logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)

                if self.request.retries < self.max_retries:
                    raise self.retry(exc=tts_error)

                update_voiceover_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

            # Upload to S3 using existing function
            # Use different bucket/path for voiceover
            try:
                from app.services.storage import upload_bytes as storage_upload_bytes

                bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET  # Use video bucket for all campaign assets
                file_key = f"generated/{campaign_id}/audio/voiceover.mp3"

                voiceover_url = storage_upload_bytes(
                    bucket_name=bucket_name,
                    file_key=file_key,
                    data=audio_bytes,
                    content_type='audio/mpeg',
                    acl='public-read'
                )

                logger.info(
                    f"Voiceover uploaded | campaign={campaign_id} | url={voiceover_url}"
                )

            except Exception as upload_error:
                error_msg = f"Failed to upload voiceover: {str(upload_error)}"
                logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)

                if self.request.retries < self.max_retries:
                    raise self.retry(exc=upload_error)

                update_voiceover_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

            # Update campaign with voiceover URL
            campaign.voiceover_url = voiceover_url
            campaign.voiceover_status = "completed"
            db.commit()

            logger.info(f"Voiceover generation complete | campaign={campaign_id}")

        # Check if we can trigger audio mixing
        check_audio_ready_and_mix(campaign_id)

        return {
            "status": "completed",
            "campaign_id": campaign_id,
            "voiceover_url": voiceover_url,
            "word_count": word_count
        }

    except Exception as e:
        error_msg = f"Voiceover generation error: {str(e)}"
        logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)

        if self.request.retries < self.max_retries:
            retry_delay = RETRY_DELAY_BASE * (2 ** self.request.retries)
            logger.info(
                f"Retrying voiceover generation ({self.request.retries + 1}/{self.max_retries}) | "
                f"campaign={campaign_id} | delay={retry_delay}s"
            )
            raise self.retry(exc=e, countdown=retry_delay)

        update_voiceover_status(campaign_id, "failed", error=error_msg)
        return {"status": "failed", "error": error_msg}
