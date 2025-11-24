"""Celery tasks for V2 audio mixing (voiceover + music)."""
import logging
import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional
import httpx
from app.celery_app import celery_app
from app.database import get_session_local
from app.models.campaign import Campaign
from app.config import settings
from app.services.storage import upload_bytes

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 2
RETRY_DELAY_BASE = 30

# Audio mix settings
VOICEOVER_VOLUME = 1.0  # 100% volume for voiceover
MUSIC_VOLUME = 0.3  # 30% volume for background music
FADE_OUT_DURATION = 2.0  # 2 second fade out at end


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


def get_audio_duration(file_path: str) -> Optional[float]:
    """Get audio duration using ffprobe.

    Args:
        file_path: Path to audio file

    Returns:
        Duration in seconds, or None if failed
    """
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


def mix_voiceover_and_music(
    voiceover_path: str,
    music_path: str,
    output_path: str,
    voiceover_volume: float = VOICEOVER_VOLUME,
    music_volume: float = MUSIC_VOLUME
) -> bool:
    """Mix voiceover and music using FFmpeg.

    The voiceover is the primary audio (100% volume).
    The music is mixed underneath at lower volume (30%) with fade out.

    Args:
        voiceover_path: Path to voiceover audio file
        music_path: Path to music audio file
        output_path: Path for output mixed audio
        voiceover_volume: Volume level for voiceover (default 1.0)
        music_volume: Volume level for music (default 0.3)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get voiceover duration to match output length
        voiceover_duration = get_audio_duration(voiceover_path)
        if not voiceover_duration:
            voiceover_duration = 40.0  # Default for 40-second ad

        # Build FFmpeg command
        # Mix voiceover at full volume with music at reduced volume
        # Trim/loop music to match voiceover duration
        # Apply fade out to music at the end

        fade_start = max(0, voiceover_duration - FADE_OUT_DURATION)

        cmd = [
            "ffmpeg", "-y",
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            # Voiceover: keep at specified volume
            f"[0:a]volume={voiceover_volume}[vo];"
            # Music: trim to voiceover length, reduce volume, fade out
            f"[1:a]atrim=0:{voiceover_duration},asetpts=PTS-STARTPTS,"
            f"volume={music_volume},"
            f"afade=t=out:st={fade_start}:d={FADE_OUT_DURATION}[music];"
            # Mix both tracks together
            f"[vo][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "libmp3lame",  # Output as MP3
            "-b:a", "192k",  # 192kbps bitrate
            "-ar", "44100",  # 44.1kHz sample rate
            output_path
        ]

        logger.info(
            f"Running FFmpeg audio mix | voiceover_duration={voiceover_duration}s | "
            f"music_volume={music_volume}"
        )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
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


def update_final_audio_status(
    campaign_id: str,
    status: str,
    final_audio_url: Optional[str] = None,
    error: Optional[str] = None
) -> bool:
    """Update final audio mix status in campaign."""
    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return False

            if final_audio_url:
                campaign.final_audio_url = final_audio_url

            if error:
                campaign.audio_generation_error = error

            if status == "completed":
                logger.info(
                    f"Final audio mix {status} | campaign={campaign_id} | "
                    f"url={final_audio_url}"
                )

            return True

    except Exception as e:
        logger.error(f"Failed to update final audio status | campaign={campaign_id} | error={str(e)}")
        return False


@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY_BASE)
def mix_final_audio_task(self, campaign_id: str) -> Dict[str, Any]:
    """Mix voiceover and music into final audio track.

    Downloads voiceover and music from S3, mixes them using FFmpeg,
    and uploads the result to S3.

    Prerequisites:
    - campaign.voiceover_url must be set (voiceover generation complete)
    - campaign.audio_url must be set (music generation complete)

    Args:
        campaign_id: Campaign UUID string

    Returns:
        Dict with status and final_audio_url
    """
    logger.info(f"Starting audio mixing | campaign={campaign_id}")

    try:
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if not campaign:
                logger.error(f"Campaign not found | campaign={campaign_id}")
                return {"status": "failed", "error": "Campaign not found"}

            # Check prerequisites
            voiceover_url = campaign.voiceover_url
            music_url = campaign.audio_url

            if not voiceover_url:
                error_msg = "Voiceover not ready for mixing"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                return {"status": "failed", "error": error_msg}

            if not music_url:
                # If no music, just use voiceover as final audio
                logger.info(f"No music track, using voiceover as final audio | campaign={campaign_id}")
                campaign.final_audio_url = voiceover_url
                db.commit()
                return {
                    "status": "completed",
                    "campaign_id": campaign_id,
                    "final_audio_url": voiceover_url,
                    "note": "No music track - voiceover only"
                }

            logger.info(
                f"Mixing audio | campaign={campaign_id} | "
                f"voiceover={voiceover_url[:60]}... | music={music_url[:60]}..."
            )

        # Download and mix in temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            voiceover_path = os.path.join(temp_dir, "voiceover.mp3")
            music_path = os.path.join(temp_dir, "music.mp3")
            output_path = os.path.join(temp_dir, "final_audio.mp3")

            # Download voiceover
            logger.info(f"Downloading voiceover | campaign={campaign_id}")
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(voiceover_url)
                    response.raise_for_status()
                    with open(voiceover_path, 'wb') as f:
                        f.write(response.content)
                logger.info(f"Voiceover downloaded | size={os.path.getsize(voiceover_path)} bytes")
            except Exception as e:
                error_msg = f"Failed to download voiceover: {str(e)}"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e)
                return {"status": "failed", "error": error_msg}

            # Download music
            logger.info(f"Downloading music | campaign={campaign_id}")
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(music_url)
                    response.raise_for_status()
                    with open(music_path, 'wb') as f:
                        f.write(response.content)
                logger.info(f"Music downloaded | size={os.path.getsize(music_path)} bytes")
            except Exception as e:
                error_msg = f"Failed to download music: {str(e)}"
                logger.error(f"{error_msg} | campaign={campaign_id}")
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e)
                return {"status": "failed", "error": error_msg}

            # Mix audio
            mix_success = mix_voiceover_and_music(
                voiceover_path,
                music_path,
                output_path
            )

            if not mix_success or not os.path.exists(output_path):
                error_msg = "FFmpeg audio mixing failed"
                logger.error(f"{error_msg} | campaign={campaign_id}")

                if self.request.retries < self.max_retries:
                    raise self.retry(exc=Exception(error_msg))

                update_final_audio_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

            # Upload mixed audio to S3
            logger.info(f"Uploading mixed audio | campaign={campaign_id}")

            with open(output_path, 'rb') as f:
                audio_bytes = f.read()

            bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
            file_key = f"generated/{campaign_id}/audio/final_mixed.mp3"

            try:
                final_audio_url = upload_bytes(
                    bucket_name=bucket_name,
                    file_key=file_key,
                    data=audio_bytes,
                    content_type='audio/mpeg',
                    acl='public-read'
                )

                logger.info(f"Mixed audio uploaded | campaign={campaign_id} | url={final_audio_url}")

            except Exception as upload_error:
                error_msg = f"Failed to upload mixed audio: {str(upload_error)}"
                logger.error(f"{error_msg} | campaign={campaign_id}")

                if self.request.retries < self.max_retries:
                    raise self.retry(exc=upload_error)

                update_final_audio_status(campaign_id, "failed", error=error_msg)
                return {"status": "failed", "error": error_msg}

        # Update campaign with final audio URL
        with db_session() as db:
            campaign_uuid = uuid.UUID(campaign_id)
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()

            if campaign:
                campaign.final_audio_url = final_audio_url
                db.commit()

        logger.info(f"Audio mixing complete | campaign={campaign_id}")

        # Check if videos are also ready, trigger assembly if so
        from app.tasks.video_generation import check_ready_and_assemble
        check_ready_and_assemble(campaign_id)

        return {
            "status": "completed",
            "campaign_id": campaign_id,
            "final_audio_url": final_audio_url
        }

    except Exception as e:
        error_msg = f"Audio mixing error: {str(e)}"
        logger.error(f"{error_msg} | campaign={campaign_id}", exc_info=True)

        if self.request.retries < self.max_retries:
            retry_delay = RETRY_DELAY_BASE * (2 ** self.request.retries)
            logger.info(
                f"Retrying audio mixing ({self.request.retries + 1}/{self.max_retries}) | "
                f"campaign={campaign_id} | delay={retry_delay}s"
            )
            raise self.retry(exc=e, countdown=retry_delay)

        update_final_audio_status(campaign_id, "failed", error=error_msg)
        return {"status": "failed", "error": error_msg}
