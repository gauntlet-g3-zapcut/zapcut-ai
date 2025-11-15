import replicate
from app.config import settings
import time

client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)


def generate_reference_images(prompts):
    """
    Generate reference images using Replicate
    Using Flux Pro or SDXL (best available model)
    """
    results = []
    
    # Flux Pro 1.1 is one of the best models on Replicate
    model = "black-forest-labs/flux-1.1-pro"
    
    for prompt_data in prompts:
        try:
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
            
            # Get the image URL from output
            image_url = output if isinstance(output, str) else output[0]
            
            results.append({
                "type": prompt_data["type"],
                "url": image_url,
                "prompt": prompt_data["prompt"]
            })
        except Exception as e:
            print(f"Error generating {prompt_data['type']} image: {e}")
            results.append({
                "type": prompt_data["type"],
                "url": "",
                "error": str(e)
            })
    
    return results


def generate_video_with_sora(scene_prompt, scene_number, prev_scene_url=None):
    """
    Generate video using Sora 2 on Replicate with optional continuity

    Args:
        scene_prompt: Dict with prompt and scene info
        scene_number: Scene number (1-5)
        prev_scene_url: URL of previous scene for visual continuity (optional)

    Note: At the time of writing, Sora might not be publicly available on Replicate.
    This is a placeholder for when it becomes available.
    For now, we'll use an alternative video generation model.
    """
    try:
        # Check if Sora is available, otherwise use alternative
        # Example: using a placeholder video generation model
        # Replace with actual Sora model when available

        # For demonstration, using Stable Video Diffusion
        model = "stability-ai/stable-video-diffusion"

        # Enhance prompt with continuity context if previous scene exists
        prompt = scene_prompt["prompt"]
        if prev_scene_url and scene_number > 1:
            prompt = f"Continuing from previous scene: {prompt}"

        input_params = {
            "prompt": prompt,
            "frames_per_second": 30,
            "num_frames": 180,  # 6 seconds at 30fps
            "motion_bucket_id": 127,
        }

        # If prev_scene_url is provided, use it for continuity (when model supports it)
        # Note: SVD doesn't support init_image in the same way, but Sora will
        if prev_scene_url:
            input_params["context_url"] = prev_scene_url  # Placeholder for Sora continuity

        output = client.run(model, input=input_params)

        # Get video URL
        video_url = output if isinstance(output, str) else output[0]

        return {
            "scene_number": scene_number,
            "url": video_url,
            "prompt": prompt,
            "prev_scene": prev_scene_url
        }
    except Exception as e:
        print(f"Error generating video for scene {scene_number}: {e}")
        return {
            "scene_number": scene_number,
            "url": "",
            "error": str(e)
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
        model = "suno-ai/bark"

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
        # Suno v3.5 model on Replicate
        model = "suno-ai/bark"  # or the actual Suno model when available

        # For now, using a music generation model available on Replicate
        # Replace with actual Suno model identifier
        model = "meta/musicgen"

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


def wait_for_prediction(prediction_id, timeout=600):
    """
    Wait for a Replicate prediction to complete
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        prediction = client.predictions.get(prediction_id)
        
        if prediction.status == "succeeded":
            return prediction.output
        elif prediction.status == "failed":
            raise Exception(f"Prediction failed: {prediction.error}")
        
        time.sleep(2)
    
    raise Exception("Prediction timed out")


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


def generate_videos_parallel(sora_prompts):
    """
    Generate multiple videos in parallel using Replicate
    """
    predictions = []

    # Start all predictions
    for prompt_data in sora_prompts:
        try:
            prediction = client.predictions.create(
                version="stability-ai/stable-video-diffusion",
                input={
                    "prompt": prompt_data["prompt"],
                    "frames_per_second": 30,
                    "num_frames": 180,
                }
            )
            predictions.append({
                "prediction_id": prediction.id,
                "scene_number": prompt_data["scene_number"]
            })
        except Exception as e:
            print(f"Error starting video generation for scene {prompt_data['scene_number']}: {e}")

    # Wait for all predictions to complete
    results = []
    for pred_info in predictions:
        try:
            output = wait_for_prediction(pred_info["prediction_id"])
            video_url = output if isinstance(output, str) else output[0]

            results.append({
                "scene_number": pred_info["scene_number"],
                "url": video_url
            })
        except Exception as e:
            print(f"Error waiting for scene {pred_info['scene_number']}: {e}")
            results.append({
                "scene_number": pred_info["scene_number"],
                "url": "",
                "error": str(e)
            })

    return results


# Model identifiers (update these with actual model versions when available)
MODELS = {
    "flux_pro": "black-forest-labs/flux-1.1-pro",
    "flux_dev": "black-forest-labs/flux-dev",
    "sdxl": "stability-ai/sdxl",
    "sora": "openai/sora",  # Placeholder - update when available
    "suno": "suno-ai/bark",  # Placeholder - update when available
    "musicgen": "meta/musicgen",
    "stable_video": "stability-ai/stable-video-diffusion",
}

