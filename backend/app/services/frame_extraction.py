"""Frame extraction service for V2 sequential video pipeline."""
import logging
import os
import subprocess
import tempfile
import uuid
from typing import Optional
import httpx
from app.config import settings
from app.services.storage import upload_bytes

logger = logging.getLogger(__name__)


def extract_last_frame(video_url: str, campaign_id: str, segment_num: int) -> Optional[str]:
    """Extract the last frame from a video and upload to S3.

    Uses FFmpeg to extract the final frame from a video file.
    This frame is used to seed the next segment in the sequential pipeline.

    Args:
        video_url: URL of the video to extract frame from
        campaign_id: Campaign UUID for S3 path
        segment_num: Segment number for naming

    Returns:
        S3 URL of the extracted frame, or None if extraction failed
    """
    logger.info(
        f"Extracting last frame | campaign={campaign_id} | "
        f"segment={segment_num} | video_url={video_url[:60]}..."
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video
            video_path = os.path.join(temp_dir, f"segment_{segment_num}.mp4")
            frame_path = os.path.join(temp_dir, f"segment_{segment_num}_last_frame.png")

            logger.info(f"Downloading video for frame extraction | campaign={campaign_id}")

            with httpx.Client(timeout=120.0) as client:
                response = client.get(video_url)
                response.raise_for_status()
                with open(video_path, 'wb') as f:
                    f.write(response.content)

            video_size = os.path.getsize(video_path)
            logger.info(f"Video downloaded | campaign={campaign_id} | size={video_size} bytes")

            # Extract last frame using FFmpeg
            # -sseof -0.1 seeks to 0.1 seconds before end
            # -frames:v 1 extracts only 1 frame
            # -q:v 2 high quality JPEG output
            cmd = [
                "ffmpeg", "-y",
                "-sseof", "-0.1",  # Seek to 0.1s before end of file
                "-i", video_path,
                "-frames:v", "1",  # Extract 1 frame
                "-q:v", "2",  # High quality
                frame_path
            ]

            logger.info(f"Running FFmpeg frame extraction | campaign={campaign_id} | segment={segment_num}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            if result.returncode != 0:
                logger.error(
                    f"FFmpeg frame extraction failed | campaign={campaign_id} | "
                    f"segment={segment_num} | stderr={result.stderr[:500]}"
                )
                return None

            if not os.path.exists(frame_path):
                logger.error(
                    f"Frame file not created | campaign={campaign_id} | segment={segment_num}"
                )
                return None

            frame_size = os.path.getsize(frame_path)
            logger.info(
                f"Frame extracted | campaign={campaign_id} | "
                f"segment={segment_num} | size={frame_size} bytes"
            )

            # Upload frame to S3
            with open(frame_path, 'rb') as f:
                frame_bytes = f.read()

            bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
            file_key = f"generated/{campaign_id}/frames/segment_{segment_num}_last_frame.png"

            frame_url = upload_bytes(
                bucket_name=bucket_name,
                file_key=file_key,
                data=frame_bytes,
                content_type='image/png',
                acl='public-read'
            )

            logger.info(
                f"Frame uploaded | campaign={campaign_id} | "
                f"segment={segment_num} | url={frame_url}"
            )

            return frame_url

    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg frame extraction timed out | campaign={campaign_id} | segment={segment_num}")
        return None
    except httpx.HTTPError as e:
        logger.error(
            f"Failed to download video for frame extraction | campaign={campaign_id} | "
            f"segment={segment_num} | error={str(e)}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Frame extraction error | campaign={campaign_id} | "
            f"segment={segment_num} | error={str(e)}",
            exc_info=True
        )
        return None


def extract_frame_at_time(
    video_url: str,
    campaign_id: str,
    segment_num: int,
    time_seconds: float
) -> Optional[str]:
    """Extract a frame at a specific timestamp from a video.

    Args:
        video_url: URL of the video
        campaign_id: Campaign UUID for S3 path
        segment_num: Segment number for naming
        time_seconds: Time in seconds to extract frame at

    Returns:
        S3 URL of the extracted frame, or None if extraction failed
    """
    logger.info(
        f"Extracting frame at {time_seconds}s | campaign={campaign_id} | "
        f"segment={segment_num}"
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, f"segment_{segment_num}.mp4")
            frame_path = os.path.join(temp_dir, f"segment_{segment_num}_frame_{time_seconds}s.png")

            # Download video
            with httpx.Client(timeout=120.0) as client:
                response = client.get(video_url)
                response.raise_for_status()
                with open(video_path, 'wb') as f:
                    f.write(response.content)

            # Extract frame at specific time
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(time_seconds),  # Seek to timestamp
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                frame_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0 or not os.path.exists(frame_path):
                logger.error(
                    f"FFmpeg extraction at {time_seconds}s failed | "
                    f"campaign={campaign_id} | segment={segment_num}"
                )
                return None

            # Upload frame
            with open(frame_path, 'rb') as f:
                frame_bytes = f.read()

            bucket_name = settings.SUPABASE_S3_VIDEO_BUCKET
            file_key = f"generated/{campaign_id}/frames/segment_{segment_num}_frame_{time_seconds}s.png"

            frame_url = upload_bytes(
                bucket_name=bucket_name,
                file_key=file_key,
                data=frame_bytes,
                content_type='image/png',
                acl='public-read'
            )

            logger.info(f"Frame at {time_seconds}s uploaded | campaign={campaign_id} | url={frame_url}")
            return frame_url

    except Exception as e:
        logger.error(
            f"Frame extraction at {time_seconds}s error | campaign={campaign_id} | "
            f"segment={segment_num} | error={str(e)}",
            exc_info=True
        )
        return None
