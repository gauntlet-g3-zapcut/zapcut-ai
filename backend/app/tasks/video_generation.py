from celery import Task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.campaign import Campaign
from app.models.generation_job import GenerationJob
from app.models.creative_bible import CreativeBible
from app.models.brand import Brand
from app.services.openai_service import (
    generate_storyline_and_prompts,
    generate_sora_prompts,
    generate_reference_image_prompts
)
from app.services.replicate_service import (
    generate_reference_images,
    generate_videos_sequential,
    generate_voiceovers_parallel,
    generate_music_with_suno
)
from app.services.storage import upload_bytes_to_storage
import uuid
import subprocess
import os
import tempfile
import httpx
from datetime import datetime


class VideoGenerationTask(Task):
    """Base task with database session"""
    def __call__(self, *args, **kwargs):
        self.db = SessionLocal()
        try:
            return super().__call__(*args, **kwargs)
        finally:
            self.db.close()


@celery_app.task(base=VideoGenerationTask, bind=True)
def generate_campaign_video(self, campaign_id: str):
    """
    Main task to generate complete video ad
    
    Steps:
    1. Generate reference images (if needed)
    2. Generate storyline and prompts
    3. Generate video scenes with Sora (Replicate)
    4. Generate music with Suno (Replicate)
    5. Compose final video with FFmpeg
    6. Upload to S3
    """
    try:
        # Get campaign
        campaign = self.db.query(Campaign).filter(Campaign.id == uuid.UUID(campaign_id)).first()
        if not campaign:
            raise Exception("Campaign not found")
        
        # Update status
        campaign.status = "generating"
        self.db.commit()
        
        # Get brand and creative bible
        brand = campaign.brand
        creative_bible = campaign.creative_bible
        
        # Step 1: Generate reference images if not already done
        if not creative_bible.reference_image_urls.get("hero"):
            self.update_state(state="PROGRESS", meta={"stage": "Generating reference images..."})
            
            brand_info = {
                "title": brand.title,
                "description": brand.description
            }
            
            image_prompts = generate_reference_image_prompts(
                creative_bible.creative_bible,
                brand_info
            )
            
            reference_images = generate_reference_images(image_prompts)
            
            # Update creative bible with image URLs
            creative_bible.reference_image_urls.update({
                img["type"]: img["url"] for img in reference_images
            })
            self.db.commit()
        
        # Step 2: Generate storyline and prompts (if not already done)
        if not campaign.storyline:
            self.update_state(state="PROGRESS", meta={"stage": "Creating storyboard..."})
            
            brand_info = {
                "title": brand.title,
                "description": brand.description
            }
            
            storyline_data = generate_storyline_and_prompts(
                creative_bible.creative_bible,
                brand_info
            )
            
            # Generate Sora prompts
            sora_prompts = generate_sora_prompts(
                storyline_data["storyline"],
                creative_bible.creative_bible,
                creative_bible.reference_image_urls,
                brand_info
            )
            
            # Update campaign
            campaign.storyline = storyline_data["storyline"]
            campaign.sora_prompts = sora_prompts
            campaign.suno_prompt = storyline_data["suno_prompt"]
            self.db.commit()
        
        # Step 3: Generate videos SEQUENTIALLY with continuity tracking
        campaign.generation_stage = "scene_videos"
        campaign.generation_progress = 20
        self.db.commit()

        self.update_state(state="PROGRESS", meta={"stage": "Generating video scenes sequentially..."})

        video_urls = {}
        prev_scene_url = None

        for i, prompt_data in enumerate(campaign.sora_prompts, start=1):
            scene_num = prompt_data.get("scene_number", i)

            # Create generation job record
            job = GenerationJob(
                campaign_id=campaign.id,
                job_type="scene_video",
                scene_number=scene_num,
                status="processing",
                input_params=prompt_data,
                started_at=datetime.utcnow()
            )
            self.db.add(job)
            self.db.commit()

            # Update progress
            progress = 20 + (scene_num * 8)  # 20% -> 28% -> 36% -> 44% -> 52% -> 60%
            campaign.generation_progress = progress
            self.db.commit()

            self.update_state(
                state="PROGRESS",
                meta={"stage": f"Generating scene {scene_num}/5..."}
            )

            # Generate video with continuity
            from app.services.replicate_service import generate_video_with_sora
            result = generate_video_with_sora(
                prompt_data,
                scene_num,
                prev_scene_url=prev_scene_url
            )

            if result.get("url"):
                # Download video
                video_data = download_file(result["url"])

                # Upload to S3
                key = f"campaigns/{campaign_id}/scene_{scene_num}.mp4"
                s3_url = upload_to_s3_bytes(video_data, key, "video/mp4")
                video_urls[f"scene_{scene_num}"] = s3_url

                # Update job as completed
                job.status = "completed"
                job.output_url = s3_url
                job.completed_at = datetime.utcnow()

                # Use this scene for next scene's continuity
                prev_scene_url = s3_url
            else:
                # Job failed
                job.status = "failed"
                job.error_message = result.get("error", "Unknown error")
                job.completed_at = datetime.utcnow()

            self.db.commit()

        campaign.video_urls = video_urls
        self.db.commit()

        # Step 4: Generate voiceovers (TTS) - PARALLEL
        campaign.generation_stage = "voiceovers"
        campaign.generation_progress = 60
        self.db.commit()

        self.update_state(state="PROGRESS", meta={"stage": "Generating voiceovers..."})

        # Extract scenes with voiceover text from storyline
        scenes_with_text = []
        if campaign.storyline and campaign.storyline.get("scenes"):
            for scene in campaign.storyline["scenes"]:
                scenes_with_text.append({
                    "scene_number": scene.get("scene_number", len(scenes_with_text) + 1),
                    "voiceover_text": scene.get("voiceover_text", scene.get("description", ""))
                })

        # Generate voiceovers
        voiceover_results = generate_voiceovers_parallel(scenes_with_text)

        # Download and upload voiceovers
        voiceover_urls = []
        for result in voiceover_results:
            scene_num = result["scene_number"]

            # Create generation job record
            job = GenerationJob(
                campaign_id=campaign.id,
                job_type="voiceover",
                scene_number=scene_num,
                status="processing",
                input_params={"text": result.get("text", "")},
                started_at=datetime.utcnow()
            )
            self.db.add(job)
            self.db.commit()

            if result.get("url"):
                # Download voiceover
                audio_data = download_file(result["url"])

                # Upload to S3
                key = f"campaigns/{campaign_id}/voiceover_{scene_num}.mp3"
                voiceover_url = upload_to_s3_bytes(audio_data, key, "audio/mpeg")
                voiceover_urls.append(voiceover_url)

                # Update job as completed
                job.status = "completed"
                job.output_url = voiceover_url
                job.completed_at = datetime.utcnow()
            else:
                # No voiceover or failed
                voiceover_urls.append(None)
                job.status = "completed" if not result.get("error") else "failed"
                job.error_message = result.get("error", "No voiceover text")
                job.completed_at = datetime.utcnow()

            self.db.commit()

        campaign.voiceover_urls = voiceover_urls
        campaign.generation_progress = 70
        self.db.commit()

        # Step 5: Generate music with Suno (Replicate)
        campaign.generation_stage = "music"
        campaign.generation_progress = 70
        self.db.commit()

        self.update_state(state="PROGRESS", meta={"stage": "Generating soundtrack..."})
        
        music_result = generate_music_with_suno(campaign.suno_prompt)
        
        if music_result.get("url"):
            # Download and upload to S3
            music_data = download_file(music_result["url"])
            key = f"campaigns/{campaign_id}/music.mp3"
            music_url = upload_to_s3_bytes(music_data, key, "audio/mpeg")
            campaign.music_url = music_url
            campaign.generation_progress = 80
            self.db.commit()

        # Step 6: Compose final video with FFmpeg
        campaign.generation_stage = "compositing"
        campaign.generation_progress = 80
        self.db.commit()

        self.update_state(state="PROGRESS", meta={"stage": "Composing final video..."})
        
        final_video_path = compose_video(
            video_urls,
            music_result.get("url") or campaign.music_url,
            brand.title
        )
        
        # Upload final video to S3
        with open(final_video_path, "rb") as f:
            video_data = f.read()
        
        key = f"campaigns/{campaign_id}/final.mp4"
        final_url = upload_to_s3_bytes(video_data, key, "video/mp4")
        
        campaign.final_video_url = final_url
        campaign.status = "completed"
        campaign.generation_stage = "complete"
        campaign.generation_progress = 100
        self.db.commit()
        
        # Cleanup temp files
        os.remove(final_video_path)
        
        return {
            "campaign_id": campaign_id,
            "final_video_url": final_url,
            "status": "completed"
        }
        
    except Exception as e:
        print(f"Error generating campaign video: {e}")
        campaign.status = "failed"
        self.db.commit()
        raise


def download_file(url):
    """Download file from URL"""
    response = httpx.get(url)
    response.raise_for_status()
    return response.content


def upload_to_s3_bytes(data, key, content_type):
    """Upload bytes to Supabase Storage (replaces S3)"""
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

