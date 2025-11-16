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


@celery_app.task(bind=True)
def generate_campaign_video_test_mode(self, campaign_id: str):
    """
    🧪 TEST MODE: Generate video without database
    Runs full Epic 5 pipeline with test data
    """
    print(f"🧪 TEST MODE: Starting Epic 5 for campaign {campaign_id}")

    try:
        # Test data (no database)
        brand_info = {
            "title": "ZapCut Test Brand",
            "description": "A revolutionary video editing platform powered by AI"
        }

        creative_bible_data = {
            "vibe": "Modern & Professional",
            "style": "Clean, minimalist with dynamic motion",
            "colors": ["#3b82f6", "#1e40af", "#60a5fa"],
            "energy_level": "High"
        }

        # Step 1: Generate reference images
        self.update_state(state="PROGRESS", meta={"stage": "Generating reference images...", "progress": 10})
        print("📸 Step 1: Generating reference images...")

        image_prompts = generate_reference_image_prompts(creative_bible_data, brand_info)
        reference_images = generate_reference_images(image_prompts)
        reference_image_urls = {img["type"]: img["url"] for img in reference_images}

        # Step 2: Generate storyline and prompts
        self.update_state(state="PROGRESS", meta={"stage": "Creating storyboard...", "progress": 20})
        print("📝 Step 2: Generating storyline...")

        storyline_data = generate_storyline_and_prompts(creative_bible_data, brand_info)
        sora_prompts = generate_sora_prompts(
            storyline_data["storyline"],
            creative_bible_data,
            reference_image_urls,
            brand_info
        )

        # Step 3: Generate video scenes
        print("🎬 Step 3: Generating video scenes...")
        video_urls = {}
        prev_scene_url = None

        for i, prompt_data in enumerate(sora_prompts, start=1):
            scene_num = prompt_data.get("scene_number", i)
            progress = 20 + (scene_num * 10)  # 30%, 40%, 50%...

            self.update_state(
                state="PROGRESS",
                meta={"stage": f"Generating scene {scene_num}/5...", "progress": progress}
            )
            print(f"   Scene {scene_num}/5...")

            from app.services.replicate_service import generate_video_with_sora
            result = generate_video_with_sora(prompt_data, scene_num, prev_scene_url=prev_scene_url)

            if result.get("url"):
                video_data = download_file(result["url"])
                key = f"test-campaigns/{campaign_id}/scene_{scene_num}.mp4"
                s3_url = upload_to_s3_bytes(video_data, key, "video/mp4")
                video_urls[f"scene_{scene_num}"] = s3_url
                prev_scene_url = s3_url
                print(f"   ✅ Scene {scene_num} generated")

        # Step 4: Generate voiceovers
        self.update_state(state="PROGRESS", meta={"stage": "Generating voiceovers...", "progress": 70})
        print("🎙️ Step 4: Generating voiceovers...")

        scenes_with_text = []
        if storyline_data.get("storyline", {}).get("scenes"):
            for scene in storyline_data["storyline"]["scenes"]:
                scenes_with_text.append({
                    "scene_number": scene.get("scene_number", len(scenes_with_text) + 1),
                    "voiceover_text": scene.get("voiceover_text", scene.get("description", ""))
                })

        voiceover_results = generate_voiceovers_parallel(scenes_with_text)
        voiceover_urls = []

        for result in voiceover_results:
            if result.get("url"):
                scene_num = result["scene_number"]
                audio_data = download_file(result["url"])
                key = f"test-campaigns/{campaign_id}/voiceover_{scene_num}.mp3"
                voiceover_url = upload_to_s3_bytes(audio_data, key, "audio/mpeg")
                voiceover_urls.append(voiceover_url)
            else:
                voiceover_urls.append(None)

        # Step 5: Generate music
        self.update_state(state="PROGRESS", meta={"stage": "Generating soundtrack...", "progress": 80})
        print("🎵 Step 5: Generating music...")

        music_result = generate_music_with_suno(storyline_data.get("suno_prompt", "Upbeat modern electronic music"))
        music_url = None

        if music_result.get("url"):
            music_data = download_file(music_result["url"])
            key = f"test-campaigns/{campaign_id}/music.mp3"
            music_url = upload_to_s3_bytes(music_data, key, "audio/mpeg")

        # Step 6: Compose final video
        self.update_state(state="PROGRESS", meta={"stage": "Composing final video...", "progress": 90})
        print("🎞️ Step 6: Composing final video...")

        final_video_path = compose_video(
            video_urls,
            music_url,
            brand_info["title"],
            product_images=None,
            voiceover_urls=voiceover_urls if voiceover_urls else None
        )

        # Upload final video
        with open(final_video_path, "rb") as f:
            video_data = f.read()

        key = f"test-campaigns/{campaign_id}/final.mp4"
        final_url = upload_to_s3_bytes(video_data, key, "video/mp4")

        os.remove(final_video_path)

        self.update_state(state="SUCCESS", meta={"stage": "Complete!", "progress": 100})
        print(f"✅ TEST MODE: Epic 5 complete! Final video: {final_url}")

        return {
            "campaign_id": campaign_id,
            "final_video_url": final_url,
            "status": "completed",
            "test_mode": True
        }

    except Exception as e:
        print(f"❌ TEST MODE ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


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

        # Get product images from brand
        product_images = []
        if hasattr(brand, 'product_image_1_url') and brand.product_image_1_url:
            product_images.append(brand.product_image_1_url)
        if hasattr(brand, 'product_image_2_url') and brand.product_image_2_url:
            product_images.append(brand.product_image_2_url)

        final_video_path = compose_video(
            video_urls,
            music_result.get("url") or campaign.music_url,
            brand.title,
            product_images=product_images if product_images else None,
            voiceover_urls=campaign.voiceover_urls if campaign.voiceover_urls else None
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


def add_product_overlays(input_video, output_video, product_images, temp_dir):
    """
    Add product image overlays at specified timestamps using FFmpeg

    Args:
        input_video: Path to input video file
        output_video: Path to output video file
        product_images: List of product image URLs [product_1_url, product_2_url]
        temp_dir: Temporary directory for downloaded images
    """
    if not product_images or len(product_images) == 0:
        # No product images, just copy input to output
        import shutil
        shutil.copy(input_video, output_video)
        return

    # Download product images
    product_image_files = []
    for i, image_url in enumerate(product_images[:2], start=1):  # Max 2 products
        if image_url:
            try:
                image_data = download_file(image_url)
                image_path = os.path.join(temp_dir, f"product_{i}.png")
                with open(image_path, "wb") as f:
                    f.write(image_data)
                product_image_files.append(image_path)
            except Exception as e:
                print(f"Error downloading product image {i}: {e}")
                product_image_files.append(None)
        else:
            product_image_files.append(None)

    # Build FFmpeg filter for overlays
    filter_parts = []
    current_label = "0:v"

    # Product 1 overlay: 5-8 seconds, bottom-right
    if len(product_image_files) > 0 and product_image_files[0]:
        filter_parts.append(f"[1:v]scale=200:-1[ovr1]")
        filter_parts.append(f"[{current_label}][ovr1]overlay=W-w-20:H-h-20:enable='between(t,5,8)'[v1]")
        current_label = "v1"

    # Product 2 overlay: 15-18 seconds, bottom-right
    if len(product_image_files) > 1 and product_image_files[1]:
        filter_parts.append(f"[2:v]scale=200:-1[ovr2]")
        filter_parts.append(f"[{current_label}][ovr2]overlay=W-w-20:H-h-20:enable='between(t,15,18)'[v2]")
        current_label = "v2"

    if not filter_parts:
        # No overlays to add
        import shutil
        shutil.copy(input_video, output_video)
        return

    # Build FFmpeg command
    cmd = ["ffmpeg", "-i", input_video]

    # Add product image inputs
    for img_file in product_image_files:
        if img_file:
            cmd.extend(["-i", img_file])

    # Add filter complex
    filter_complex = ";".join(filter_parts)
    cmd.extend(["-filter_complex", filter_complex])

    # Map output
    cmd.extend(["-map", f"[{current_label}]", "-map", "0:a?"])

    # Output settings
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        output_video
    ])

    print(f"FFmpeg overlay command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def create_crossfade_video(scene_files, output_path, crossfade_duration=1.0):
    """
    Create video with crossfade transitions between scenes

    Args:
        scene_files: List of scene video file paths
        output_path: Output video path
        crossfade_duration: Duration of crossfade in seconds (default 1.0)
    """
    if len(scene_files) == 0:
        raise ValueError("No scene files provided")

    if len(scene_files) == 1:
        # Single scene, just copy
        import shutil
        shutil.copy(scene_files[0], output_path)
        return

    # Build xfade filter complex for N scenes
    # Assumes each scene is ~6 seconds (adjust offsets accordingly)
    scene_duration = 6  # seconds per scene (approximate)

    # Start with all inputs
    cmd = ["ffmpeg"]
    for scene_file in scene_files:
        cmd.extend(["-i", scene_file])

    # Build filter complex for crossfades
    filter_parts = []
    current_label = "[0:v]"
    offset = scene_duration - crossfade_duration

    for i in range(1, len(scene_files)):
        prev_label = current_label
        input_label = f"[{i}:v]"
        output_label = f"[v{i}]"

        # xfade transition
        filter_parts.append(
            f"{prev_label}{input_label}xfade=transition=fade:duration={crossfade_duration}:offset={offset}{output_label}"
        )

        current_label = output_label
        offset += scene_duration - crossfade_duration

    filter_complex = ";".join(filter_parts)

    cmd.extend(["-filter_complex", filter_complex])
    cmd.extend(["-map", current_label])

    # Output settings
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        output_path
    ])

    print(f"Crossfade command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def concatenate_audio(audio_files, output_path):
    """
    Concatenate multiple audio files

    Args:
        audio_files: List of audio file paths
        output_path: Output audio path
    """
    if len(audio_files) == 0:
        return None

    # Filter out None values
    valid_files = [f for f in audio_files if f]

    if len(valid_files) == 0:
        return None

    if len(valid_files) == 1:
        import shutil
        shutil.copy(valid_files[0], output_path)
        return output_path

    # Create concat file
    concat_file = output_path.replace(".mp3", "_concat.txt")
    with open(concat_file, "w") as f:
        for audio_file in valid_files:
            f.write(f"file '{audio_file}'\n")

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path
    ]

    subprocess.run(cmd, check=True)
    return output_path


def mix_audio_tracks(voiceover_path, music_path, output_path, voiceover_volume=1.0, music_volume=0.3):
    """
    Mix voiceover and music tracks with specified volumes

    Args:
        voiceover_path: Path to voiceover audio file
        music_path: Path to music audio file
        output_path: Output mixed audio path
        voiceover_volume: Volume for voiceover (default 1.0 = 100%)
        music_volume: Volume for music (default 0.3 = 30%)
    """
    if not voiceover_path and not music_path:
        return None

    if not voiceover_path:
        # Only music, adjust volume
        cmd = [
            "ffmpeg",
            "-i", music_path,
            "-af", f"volume={music_volume}",
            output_path
        ]
    elif not music_path:
        # Only voiceover
        import shutil
        shutil.copy(voiceover_path, output_path)
        return output_path
    else:
        # Mix both
        cmd = [
            "ffmpeg",
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            f"[0:a]volume={voiceover_volume}[a1];[1:a]volume={music_volume}[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
            "-map", "[aout]",
            output_path
        ]

    subprocess.run(cmd, check=True)
    return output_path


def combine_video_audio(video_path, audio_path, output_path):
    """
    Combine video with audio track

    Args:
        video_path: Path to video file (may have existing audio)
        audio_path: Path to audio file to replace/add
        output_path: Output video path
    """
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, check=True)


def compose_video(video_urls, music_url, brand_title, product_images=None, voiceover_urls=None):
    """
    Compose final video using FFmpeg with professional transitions and audio mixing
    - Stitch scenes with 1-second crossfade transitions
    - Mix voiceover (100%) + music (30%)
    - Add product image overlays
    - Professional output (H.264, 1080p, 30fps)

    Args:
        video_urls: Dict of scene URLs {scene_1: url, scene_2: url, ...}
        music_url: URL of background music
        brand_title: Brand name for text overlay
        product_images: List of product image URLs [product_1_url, product_2_url]
        voiceover_urls: List of voiceover audio URLs per scene
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

        # Step 1: Create video with crossfade transitions
        video_with_crossfades = os.path.join(temp_dir, "crossfaded.mp4")
        create_crossfade_video(scene_files, video_with_crossfades, crossfade_duration=1.0)

        # Step 2: Download and concatenate voiceovers
        voiceover_files = []
        if voiceover_urls:
            for i, vo_url in enumerate(voiceover_urls, start=1):
                if vo_url:
                    try:
                        vo_data = download_file(vo_url)
                        vo_path = os.path.join(temp_dir, f"voiceover_{i}.mp3")
                        with open(vo_path, "wb") as f:
                            f.write(vo_data)
                        voiceover_files.append(vo_path)
                    except Exception as e:
                        print(f"Error downloading voiceover {i}: {e}")

        voiceover_concat_path = None
        if voiceover_files:
            voiceover_concat_path = os.path.join(temp_dir, "voiceover_full.mp3")
            concatenate_audio(voiceover_files, voiceover_concat_path)

        # Step 3: Download music
        music_path = None
        if music_url:
            try:
                music_data = download_file(music_url)
                music_path = os.path.join(temp_dir, "music.mp3")
                with open(music_path, "wb") as f:
                    f.write(music_data)
            except Exception as e:
                print(f"Error downloading music: {e}")

        # Step 4: Mix audio tracks (voiceover 100%, music 30%)
        mixed_audio_path = None
        if voiceover_concat_path or music_path:
            mixed_audio_path = os.path.join(temp_dir, "mixed_audio.mp3")
            mix_audio_tracks(
                voiceover_concat_path,
                music_path,
                mixed_audio_path,
                voiceover_volume=1.0,
                music_volume=0.3
            )

        # Step 5: Combine video with mixed audio
        if mixed_audio_path:
            video_with_audio = os.path.join(temp_dir, "video_with_audio.mp4")
            combine_video_audio(video_with_crossfades, mixed_audio_path, video_with_audio)
        else:
            video_with_audio = video_with_crossfades

        # Step 6: Add product image overlays
        if product_images:
            output_with_overlays = os.path.join(temp_dir, "output_with_overlays.mp4")
            add_product_overlays(video_with_audio, output_with_overlays, product_images, temp_dir)
            final_path = output_with_overlays
        else:
            final_path = video_with_audio

        # Copy to permanent location
        import shutil
        permanent_path = f"/tmp/{uuid.uuid4()}.mp4"
        shutil.copy(final_path, permanent_path)

        return permanent_path

