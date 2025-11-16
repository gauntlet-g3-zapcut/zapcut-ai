import replicate
from app.config import settings
import time
from functools import wraps

client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)


def retry_with_backoff(max_retries=3, initial_delay=2, backoff_factor=2, log_callback=None):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts (default 3)
        initial_delay: Initial delay between retries in seconds (default 2)
        backoff_factor: Multiplier for delay after each retry (default 2)
        log_callback: Optional callback function for logging retry attempts
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Don't retry on certain errors
                    error_str = str(e).lower()
                    if "invalid" in error_str or "unauthorized" in error_str or "not found" in error_str:
                        # These are likely configuration errors, don't retry
                        raise

                    if attempt < max_retries:
                        if log_callback:
                            log_callback(f"   ⚠️ Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}")
                            log_callback(f"   🔄 Retrying in {delay} seconds...")
                        else:
                            print(f"   ⚠️ Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}")
                            print(f"   🔄 Retrying in {delay} seconds...")

                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        if log_callback:
                            log_callback(f"   ❌ All {max_retries + 1} attempts failed")
                        else:
                            print(f"   ❌ All {max_retries + 1} attempts failed")
                        raise last_exception

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


def generate_reference_images(prompts):
    """
    Generate reference images using Replicate
    Using Flux Pro or SDXL (best available model)
    """
    print(f"\n🔧 REPLICATE SERVICE - generate_reference_images()")
    print(f"   📥 Generating {len(prompts)} reference images")

    results = []

    # Flux Pro 1.1 is one of the best models on Replicate
    # Using official model (no version pinning needed for official models)
    model = "black-forest-labs/flux-1.1-pro"
    print(f"   🎨 Using model: {model}")

    for i, prompt_data in enumerate(prompts, start=1):
        print(f"\n   ─── Image {i}/{len(prompts)}: {prompt_data['type']} ───")
        print(f"   📝 Prompt: {prompt_data['prompt'][:100]}...")

        try:
            import time
            api_start = time.time()

            print(f"   📡 Calling Replicate API...")
            output = client.run(
                model,
                input={
                    "prompt": prompt_data["prompt"],
                    "aspect_ratio": "1:1",
                    "output_format": "png",
                    "output_quality": 100,
                    "safety_tolerance": 2,
                }
            )

            api_elapsed = time.time() - api_start
            print(f"   ✅ API responded in {api_elapsed:.2f} seconds")

            # Get the image URL from output
            image_url = output if isinstance(output, str) else output[0]
            print(f"   ✅ Image URL: {image_url[:80]}...")

            results.append({
                "type": prompt_data["type"],
                "url": image_url,
                "prompt": prompt_data["prompt"]
            })
        except Exception as e:
            print(f"   ❌ ERROR generating {prompt_data['type']} image:")
            print(f"      - Exception: {type(e).__name__}")
            print(f"      - Message: {str(e)}")

            import traceback
            traceback.print_exc()

            results.append({
                "type": prompt_data["type"],
                "url": "",
                "error": str(e),
                "error_type": type(e).__name__
            })

    successful_count = len([r for r in results if r.get('url')])
    print(f"\n   ✅ Reference image generation complete: {successful_count}/{len(results)} successful")
    return results


def generate_video_with_sora(scene_prompt, scene_number, prev_scene_url=None):
    """
    Generate video using OpenAI Sora 2 on Replicate

    Args:
        scene_prompt: Dict with prompt and scene info
        scene_number: Scene number (1-5)
        prev_scene_url: URL of previous scene for visual continuity (optional)

    Note: Using OpenAI Sora 2 - flagship video generation with synced audio
    """
    print(f"\n🔧 REPLICATE SERVICE - generate_video_with_sora()")
    print(f"   📥 Input Parameters:")
    print(f"      - Scene Number: {scene_number}")
    print(f"      - Scene Prompt Keys: {list(scene_prompt.keys())}")
    print(f"      - Prev Scene URL: {prev_scene_url[:60] if prev_scene_url else 'None'}...")

    try:
        # Use OpenAI Sora 2 - official model on Replicate
        # Generates video with synchronized audio
        model = "openai/sora-2"

        # Enhance prompt with continuity context if previous scene exists
        prompt = scene_prompt["prompt"]
        if prev_scene_url and scene_number > 1:
            prompt = f"Continuing from previous scene: {prompt}"

        input_params = {
            "prompt": prompt,
            "seconds": 4,  # Sora 2 supports 4, 8, or 12 seconds
            "aspect_ratio": "landscape",  # landscape (1280x720) or portrait (720x1280)
        }

        print(f"   📡 Calling Replicate API:")
        print(f"      - Model: {model}")
        print(f"      - Prompt: {prompt[:100]}...")
        print(f"      - Duration: {input_params['seconds']} seconds")
        print(f"      - Aspect Ratio: {input_params['aspect_ratio']}")
        print(f"   ⏳ Waiting for Replicate response...")

        import time
        api_start = time.time()
        output = client.run(model, input=input_params)
        api_elapsed = time.time() - api_start

        print(f"   ✅ Replicate API responded in {api_elapsed:.2f} seconds")
        print(f"   📦 Response Type: {type(output)}")
        print(f"   📦 Response Value: {output if isinstance(output, str) else str(output)[:200]}...")

        # Get video URL
        video_url = output if isinstance(output, str) else output[0]

        print(f"   ✅ Video URL extracted: {video_url[:80]}...")

        return {
            "scene_number": scene_number,
            "url": video_url,
            "prompt": prompt,
            "prev_scene": prev_scene_url
        }
    except Exception as e:
        print(f"   ❌ REPLICATE API ERROR:")
        print(f"      - Exception Type: {type(e).__name__}")
        print(f"      - Exception Message: {str(e)}")
        print(f"      - Scene Number: {scene_number}")

        # Try to get more detailed error information
        import traceback
        print(f"      - Stack Trace:")
        traceback.print_exc()

        # Check if it's a Replicate-specific error
        if hasattr(e, '__dict__'):
            print(f"      - Error Attributes: {e.__dict__}")

        return {
            "scene_number": scene_number,
            "url": "",
            "error": str(e),
            "error_type": type(e).__name__
        }


def generate_voiceover(text, scene_number):
    """
    Generate voiceover audio using TTS (Text-to-Speech)

    Args:
        text: Voiceover text/narration for the scene
        scene_number: Scene number for tracking

    Returns:
        Dict with url, text, and scene_number
    """
    try:
        # Using Bark TTS model for high-quality voiceover
        # Pinned to specific version for production stability
        model = "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787"

        output = client.run(
            model,
            input={
                "prompt": text,
                "text_temp": 0.7,
                "waveform_temp": 0.7,
            }
        )

        # Get audio URL
        audio_url = output.get("audio_out") if isinstance(output, dict) else output
        if isinstance(audio_url, list):
            audio_url = audio_url[0]

        return {
            "scene_number": scene_number,
            "url": audio_url,
            "text": text
        }
    except Exception as e:
        print(f"Error generating voiceover for scene {scene_number}: {e}")
        return {
            "scene_number": scene_number,
            "url": "",
            "text": text,
            "error": str(e)
        }


def generate_voiceovers_parallel(scenes_with_text):
    """
    Generate voiceovers for multiple scenes in parallel

    Args:
        scenes_with_text: List of dicts with scene_number and voiceover_text

    Returns:
        List of results with scene_number, url, and text
    """
    results = []

    for scene_data in scenes_with_text:
        scene_num = scene_data.get("scene_number")
        text = scene_data.get("voiceover_text", "")

        # Skip if no voiceover text
        if not text or text.strip() == "":
            print(f"Skipping voiceover for scene {scene_num} - no text")
            results.append({
                "scene_number": scene_num,
                "url": None,
                "text": ""
            })
            continue

        result = generate_voiceover(text, scene_num)
        results.append(result)

    return results


def generate_music_with_suno(suno_prompt):
    """
    Generate music using Suno on Replicate
    """
    try:
        # Using Meta's MusicGen for background music generation
        # Pinned to specific version for production stability
        model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"

        output = client.run(
            model,
            input={
                "prompt": suno_prompt,
                "duration": 30,  # 30 seconds
                "model_version": "stereo-large",
                "output_format": "mp3",
            }
        )

        # Get audio URL
        audio_url = output if isinstance(output, str) else output[0]

        return {
            "url": audio_url,
            "prompt": suno_prompt
        }
    except Exception as e:
        print(f"Error generating music: {e}")
        return {
            "url": "",
            "error": str(e)
        }


def wait_for_prediction(prediction_id, timeout=3600, log_callback=None):
    """
    Wait for a Replicate prediction to complete

    Args:
        prediction_id: Replicate prediction ID
        timeout: Maximum wait time in seconds (default 3600 = 60 minutes)
        log_callback: Optional callback function for logging updates to UI

    Returns:
        Prediction output on success

    Raises:
        Exception on failure or timeout
    """
    start_time = time.time()
    last_log_time = start_time
    log_interval = 30  # Log every 30 seconds

    while time.time() - start_time < timeout:
        try:
            prediction = client.predictions.get(prediction_id)

            if prediction.status == "succeeded":
                elapsed = time.time() - start_time
                if log_callback:
                    log_callback(f"   ✅ Prediction completed in {elapsed:.1f} seconds")
                return prediction.output
            elif prediction.status == "failed":
                error_msg = f"Prediction failed: {prediction.error}"
                if log_callback:
                    log_callback(f"   ❌ {error_msg}")
                raise Exception(error_msg)

            # Log progress periodically
            current_time = time.time()
            if log_callback and (current_time - last_log_time) >= log_interval:
                elapsed = current_time - start_time
                if log_callback:
                    log_callback(f"   ⏳ Still waiting... ({elapsed:.0f}s elapsed, status: {prediction.status})")
                last_log_time = current_time

        except Exception as e:
            # If it's a network error, retry after a short delay
            if "network" in str(e).lower() or "connection" in str(e).lower():
                if log_callback:
                    log_callback(f"   ⚠️ Network error, retrying...")
                time.sleep(5)
                continue
            else:
                # Re-raise other exceptions
                raise

        time.sleep(2)

    elapsed = time.time() - start_time
    error_msg = f"Prediction timed out after {elapsed:.0f} seconds (limit: {timeout}s)"
    if log_callback:
        log_callback(f"   ❌ {error_msg}")
    raise Exception(error_msg)


def generate_videos_sequential(sora_prompts):
    """
    Generate videos sequentially with continuity
    Each scene uses the previous scene's output for visual consistency

    Args:
        sora_prompts: List of prompt dicts with scene_number and prompt

    Returns:
        List of results with scene_number, url, and prompt
    """
    results = []
    prev_scene_url = None

    # Generate scenes one at a time
    for prompt_data in sora_prompts:
        scene_number = prompt_data["scene_number"]
        print(f"Generating scene {scene_number} sequentially...")

        result = generate_video_with_sora(
            prompt_data,
            scene_number,
            prev_scene_url=prev_scene_url
        )

        results.append(result)

        # Use this scene as reference for next scene
        if result.get("url"):
            prev_scene_url = result["url"]

    return results


def generate_videos_parallel(sora_prompts, log_callback=None):
    """
    Generate multiple videos in parallel using OpenAI Sora 2 with retry logic

    Args:
        sora_prompts: List of prompt dicts with scene_number and prompt
        log_callback: Optional callback function for logging updates to UI

    Returns:
        List of results with scene_number, url, and prompt
    """
    def log(msg):
        """Helper to log to both console and callback"""
        print(msg)
        if log_callback:
            log_callback(msg)

    log(f"\n🔧 REPLICATE SERVICE - generate_videos_parallel()")
    log(f"   📥 Generating {len(sora_prompts)} videos in parallel")

    predictions = []
    model = "openai/sora-2"

    # Get the latest version of the model with retry
    @retry_with_backoff(max_retries=3, log_callback=log_callback)
    def get_model_version():
        model_obj = client.models.get(model)
        return model_obj.latest_version.id

    try:
        version = get_model_version()
        log(f"   📦 Using Sora 2 version: {version[:16]}...")
    except Exception as e:
        log(f"   ❌ Failed to get Sora 2 version after retries: {e}")
        return []

    # Start all predictions in parallel with retry logic
    def start_prediction_with_retry(prompt_data):
        """Start a prediction with retry logic"""
        scene_number = prompt_data["scene_number"]
        prompt = prompt_data["prompt"]

        @retry_with_backoff(max_retries=3, log_callback=log_callback)
        def create_prediction():
            return client.predictions.create(
                version=version,
                input={
                    "prompt": prompt,
                    "seconds": 4,  # Sora 2 supports 4, 8, or 12 seconds
                    "aspect_ratio": "landscape",  # landscape (1280x720) or portrait (720x1280)
                }
            )

        log(f"\n   🚀 Starting scene {scene_number} (async)...")
        log(f"   📝 Prompt: {prompt[:100]}...")

        try:
            prediction = create_prediction()
            log(f"   ✓ Scene {scene_number} prediction started: {prediction.id}")
            return {
                "prediction_id": prediction.id,
                "scene_number": scene_number,
                "prompt": prompt
            }
        except Exception as e:
            log(f"   ❌ Error starting scene {scene_number} after retries: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Start all predictions
    for prompt_data in sora_prompts:
        pred_info = start_prediction_with_retry(prompt_data)
        if pred_info:
            predictions.append(pred_info)

    if not predictions:
        log(f"   ❌ Failed to start any predictions")
        return []

    log(f"\n   ⏳ All {len(predictions)} predictions started, waiting for completion...")
    log(f"   ⏱️  Timeout: 60 minutes per scene")

    # Wait for all predictions to complete
    results = []
    for pred_info in predictions:
        scene_number = pred_info["scene_number"]
        prediction_id = pred_info["prediction_id"]

        log(f"\n   ⏳ Waiting for scene {scene_number} (prediction {prediction_id})...")

        try:
            # Wait with extended timeout and progress logging
            output = wait_for_prediction(prediction_id, timeout=3600, log_callback=log_callback)
            video_url = output if isinstance(output, str) else output[0]

            log(f"   ✅ Scene {scene_number} complete: {video_url[:80]}...")

            results.append({
                "scene_number": scene_number,
                "url": video_url,
                "prompt": pred_info["prompt"],
                "prediction_id": prediction_id
            })
        except Exception as e:
            log(f"   ❌ Error waiting for scene {scene_number}: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                "scene_number": scene_number,
                "url": "",
                "error": str(e),
                "error_type": type(e).__name__,
                "prediction_id": prediction_id
            })

    successful = len([r for r in results if r.get('url')])
    log(f"\n   ✅ Parallel video generation complete: {successful}/{len(results)} successful")
    return results


# Model identifiers with pinned versions for production stability
# Version format: owner/model:version_hash
# Official models (flux-1.1-pro) don't require version hashing
MODELS = {
    # Image Generation Models
    "flux_pro": "black-forest-labs/flux-1.1-pro",  # Official model - no version pinning needed
    "flux_dev": "black-forest-labs/flux-dev",  # Open weights image generation
    "sdxl": "stability-ai/sdxl",  # Stable Diffusion XL

    # Video Generation Models (PRIMARY)
    "sora_2": "openai/sora-2",  # OpenAI Sora 2 - flagship video generation with synced audio
    "cogvideox_5b": "cuuupid/cogvideox-5b:5b14e2c2c648efecc8d36c6353576552f8a124e690587212f8e8bb17ecda3d8c",  # Legacy fallback

    # Audio Generation Models
    "bark_tts": "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787",  # TTS
    "musicgen": "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38",  # Music

    # Unused/Legacy
    "stable_video": "stability-ai/stable-video-diffusion",  # Image-to-Video (not currently used)
}

