import logging
from celery import Task
from app.database import SessionLocal
from app.models.campaign import Campaign
from app.models.creative_bible import CreativeBible
from app.models.brand import Brand
from app.services.openai_service import (
    generate_storyline_and_prompts,
    generate_sora_prompts,
    generate_reference_image_prompts
)
from app.services.replicate_service import (
    generate_reference_images,
    generate_videos_parallel,
    generate_music_with_suno
)
from app.services.storage import upload_bytes_to_storage
import uuid
import subprocess
import os
import tempfile
import httpx

logger = logging.getLogger(__name__)


class VideoGenerationTask(Task):
    """Base task with database session"""
    def __call__(self, *args, **kwargs):
        self.db = SessionLocal()
        try:
            return super().__call__(*args, **kwargs)
        finally:
            self.db.close()


# Lazy import and conditional decorator for celery_app
def _get_task_decorator():
    """Get the task decorator if celery_app is available"""
    from app.celery_app import celery_app
    if celery_app is not None:
        return celery_app.task(base=VideoGenerationTask, bind=True)
    else:
        # Return a no-op decorator if celery is not available
        def noop_decorator(func):
            return func
        return noop_decorator


@_get_task_decorator()
def generate_campaign_video(self, campaign_id: str):
    """
    Main task to generate complete video ad
    
    Steps:
    1. Generate reference images (if needed)
    2. Generate storyline and prompts
    3. Generate video scenes with Sora (Replicate)
    4. Generate music with Suno (Replicate)
    5. Compose final video with FFmpeg
    6. Upload to Supabase Storage
    """
    try:
        logger.info(f"Starting video generation for campaign: {campaign_id}")
        
        # Get campaign
        campaign = self.db.query(Campaign).filter(Campaign.id == uuid.UUID(campaign_id)).first()
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            raise Exception("Campaign not found")
        
        # Update status
        campaign.status = "generating"
        self.db.commit()
        logger.info(f"Campaign {campaign_id} status updated to 'generating'")
        
        # Get brand and creative bible
        brand = campaign.brand
        creative_bible = campaign.creative_bible
        
        # Step 1: Generate reference images if not already done
        if not creative_bible.reference_image_urls.get("hero"):
            logger.info(f"Step 1: Generating reference images for campaign {campaign_id}")
            self.update_state(state="PROGRESS", meta={"stage": "Generating reference images..."})
            
            brand_info = {
                "title": brand.title,
                "description": brand.description
            }
            
            image_prompts = generate_reference_image_prompts(
                creative_bible.creative_bible,
                brand_info
            )
            logger.debug(f"Generated {len(image_prompts)} image prompts")
            
            reference_images = generate_reference_images(image_prompts)
            logger.info(f"Generated {len(reference_images)} reference images")
            
            # Update creative bible with image URLs
            creative_bible.reference_image_urls.update({
                img["type"]: img["url"] for img in reference_images
            })
            self.db.commit()
            logger.info("Reference images saved to creative bible")
        
        # Step 2: Generate storyline and prompts (if not already done)
        if not campaign.storyline:
            logger.info(f"Step 2: Creating storyboard for campaign {campaign_id}")
            self.update_state(state="PROGRESS", meta={"stage": "Creating storyboard..."})
            
            brand_info = {
                "title": brand.title,
                "description": brand.description
            }
            
            storyline_data = generate_storyline_and_prompts(
                creative_bible.creative_bible,
                brand_info
            )
            logger.info("Storyline generated successfully")
            
            # Generate Sora prompts
            sora_prompts = generate_sora_prompts(
                storyline_data["storyline"],
                creative_bible.creative_bible,
                creative_bible.reference_image_urls,
                brand_info
            )
            logger.info(f"Generated {len(sora_prompts)} Sora prompts")
            
            # Update campaign
            campaign.storyline = storyline_data["storyline"]
            campaign.sora_prompts = sora_prompts
            campaign.suno_prompt = storyline_data["suno_prompt"]
            self.db.commit()
            logger.info("Storyline and prompts saved to campaign")
        
        # Step 3: Generate videos with Sora (Replicate) - PARALLEL
        logger.info(f"Step 3: Generating video scenes for campaign {campaign_id}")
        self.update_state(state="PROGRESS", meta={"stage": "Generating video scenes..."})
        
        video_results = generate_videos_parallel(campaign.sora_prompts)
        logger.info(f"Generated {len(video_results)} video scenes")
        
        # Download videos and upload to storage
        video_urls = {}
        for result in video_results:
            scene_num = result["scene_number"]
            logger.info(f"Processing scene {scene_num}/5...")
            self.update_state(
                state="PROGRESS",
                meta={"stage": f"Processing scene {scene_num}/5..."}
            )
            
            if result.get("url"):
                # Download video
                logger.debug(f"Downloading scene {scene_num} from {result['url']}")
                video_data = download_file(result["url"])
                
                # Upload to storage
                key = f"campaigns/{campaign_id}/scene_{scene_num}.mp4"
                video_url = upload_to_storage_bytes(video_data, key, "video/mp4")
                video_urls[f"scene_{scene_num}"] = video_url
                logger.info(f"Scene {scene_num} uploaded to storage: {video_url}")
        
        campaign.video_urls = video_urls
        self.db.commit()
        logger.info("All video scenes saved to campaign")
        
        # Step 4: Generate music with Suno (Replicate)
        logger.info(f"Step 4: Generating soundtrack for campaign {campaign_id}")
        self.update_state(state="PROGRESS", meta={"stage": "Generating soundtrack..."})
        
        music_result = generate_music_with_suno(campaign.suno_prompt)
        logger.info("Music generated successfully")
        
        if music_result.get("url"):
            # Download and upload to storage
            logger.debug(f"Downloading music from {music_result['url']}")
            music_data = download_file(music_result["url"])
            key = f"campaigns/{campaign_id}/music.mp3"
            music_url = upload_to_storage_bytes(music_data, key, "audio/mpeg")
            campaign.music_url = music_url
            self.db.commit()
            logger.info(f"Music uploaded to storage: {music_url}")
        
        # Step 5: Compose final video with FFmpeg
        logger.info(f"Step 5: Composing final video for campaign {campaign_id}")
        self.update_state(state="PROGRESS", meta={"stage": "Composing final video..."})
        
        final_video_path = compose_video(
            video_urls,
            music_result.get("url") or campaign.music_url,
            brand.title
        )
        logger.info(f"Final video composed: {final_video_path}")
        
        # Upload final video to storage
        with open(final_video_path, "rb") as f:
            video_data = f.read()
        
        key = f"campaigns/{campaign_id}/final.mp4"
        final_url = upload_to_storage_bytes(video_data, key, "video/mp4")
        logger.info(f"Final video uploaded to storage: {final_url}")
        
        campaign.final_video_url = final_url
        campaign.status = "completed"
        self.db.commit()
        
        # Cleanup temp files
        os.remove(final_video_path)
        logger.info(f"Video generation completed successfully for campaign {campaign_id}")
        
        return {
            "campaign_id": campaign_id,
            "final_video_url": final_url,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error generating campaign video for {campaign_id}: {e}", exc_info=True)
        if 'campaign' in locals():
            campaign.status = "failed"
            self.db.commit()
        raise


def download_file(url):
    """Download file from URL"""
    response = httpx.get(url)
    response.raise_for_status()
    return response.content


def upload_to_storage_bytes(data, key, content_type):
    """Upload bytes to Supabase Storage"""
    import asyncio
    
    # Determine bucket based on content type
    if content_type.startswith("video/"):
        bucket = "videos"
    elif content_type.startswith("audio/"):
        bucket = "videos"  # Store audio with videos for campaigns
    else:
        bucket = "uploads"
    
    # Run async function in sync context (Celery tasks are sync)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        upload_bytes_to_storage(
            data=data,
            bucket=bucket,
            path=key,
            content_type=content_type
        )
    )


def compose_video(video_urls, music_url, brand_title):
    """
    Compose final video using FFmpeg
    - Stitch 5 scenes with 0.5s crossfade
    - Mix audio underneath
    - Add text overlays
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download all video files
        scene_files = []
        for i in range(1, 6):
            scene_url = video_urls.get(f"scene_{i}")
            if scene_url:
                video_data = download_file(scene_url)
                scene_path = os.path.join(temp_dir, f"scene_{i}.mp4")
                with open(scene_path, "wb") as f:
                    f.write(video_data)
                scene_files.append(scene_path)
        
        # Download music
        if music_url:
            music_data = download_file(music_url)
            music_path = os.path.join(temp_dir, "music.mp3")
            with open(music_path, "wb") as f:
                f.write(music_data)
        else:
            music_path = None
        
        # Create concat file for FFmpeg
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for scene_file in scene_files:
                f.write(f"file '{scene_file}'\n")
        
        # Output file
        output_path = os.path.join(temp_dir, "output.mp4")
        
        # FFmpeg command to concatenate videos
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        
        # If music exists, mix it
        if music_path:
            output_with_music = os.path.join(temp_dir, "output_with_music.mp4")
            cmd = [
                "ffmpeg",
                "-i", output_path,
                "-i", music_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_with_music
            ]
            subprocess.run(cmd, check=True)
            final_path = output_with_music
        else:
            final_path = output_path
        
        # Copy to permanent location
        import shutil
        permanent_path = f"/tmp/{uuid.uuid4()}.mp4"
        shutil.copy(final_path, permanent_path)
        
        return permanent_path
