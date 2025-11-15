# Story S062: Replicate Model Abstraction Layer

## Epic
[E004: Multi-Agent Video Generation Pipeline](../Epics/E004-multi-agent-video-generation.md)

## Story
**As a** backend engineer  
**I want to** create a unified abstraction layer for all Replicate models  
**So that** we can easily switch between text, image, video, and audio models without changing agent code

## Priority
**P0 - MVP Critical**

## Size
**L** (3-5 days)

## Description
Implement a model abstraction layer that wraps Replicate's API and provides unified interfaces for:
- **Text Models**: Llama 3.1, Mistral, Claude (for agents)
- **Image Models**: FLUX 1.1 Pro, SDXL, Playground v2.5 (for reference images)
- **Video Models**: Minimax Video-01, Luma Dream Machine, Runway Gen-3 (for scenes)
- **Audio Models**: Suno, MusicGen, AudioCraft (for music)

## Acceptance Criteria
- [ ] ReplicateClient class created with authentication
- [ ] Text generation method with streaming support
- [ ] Image generation method with multiple model support
- [ ] Video generation method with polling and webhooks
- [ ] Audio generation method for music/effects
- [ ] Automatic retry logic with exponential backoff
- [ ] Cost tracking per model/generation
- [ ] Model fallback strategy (if primary fails, use backup)
- [ ] Rate limiting and queue management
- [ ] Comprehensive error handling

## Technical Details

### Replicate Client Architecture

```python
# backend/app/services/replicate_client.py

import replicate
from typing import Optional, Dict, Any, List, AsyncIterator
from enum import Enum
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ModelType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class ReplicateModel(Enum):
    # Text Models
    LLAMA_70B = "meta/llama-3.1-70b-instruct"
    LLAMA_405B = "meta/llama-3.1-405b-instruct"
    MISTRAL_LARGE = "mistralai/mistral-large-2407"
    LLAMA_GUARD = "meta/llama-guard-3-8b"
    
    # Image Models
    FLUX_PRO = "black-forest-labs/flux-1.1-pro"
    FLUX_DEV = "black-forest-labs/flux-dev"
    SDXL = "stability-ai/sdxl"
    PLAYGROUND_V25 = "playgroundai/playground-v2.5-1024px-aesthetic"
    
    # Video Models
    MINIMAX_VIDEO = "minimax/video-01"
    LUMA_DREAM = "luma/dream-machine"
    RUNWAY_GEN3 = "runway/gen-3-alpha-turbo"
    STABLE_VIDEO = "stability-ai/stable-video-diffusion"
    
    # Audio Models
    SUNO = "suno-ai/bark"
    MUSICGEN = "meta/musicgen"
    AUDIOCRAFT = "facebook/audiocraft"

class ReplicateClient:
    """
    Unified client for all Replicate models.
    Handles authentication, retries, cost tracking, and model fallbacks.
    """
    
    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)
        self.costs = {}  # Track costs per model
        
    # TEXT MODELS
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def generate_text(
        self,
        prompt: str,
        model: ReplicateModel = ReplicateModel.LLAMA_70B,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str | AsyncIterator[str]:
        """
        Generate text using Llama, Mistral, or other text models.
        
        Args:
            prompt: User prompt
            model: Which text model to use
            system_prompt: System instructions
            max_tokens: Max response length
            temperature: Creativity (0-1)
            stream: Stream response chunks
            
        Returns:
            Generated text (or async iterator if streaming)
        """
        
        input_params = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if system_prompt:
            input_params["system_prompt"] = system_prompt
        
        try:
            output = await self.client.async_run(
                model.value,
                input=input_params
            )
            
            if stream:
                async for chunk in output:
                    yield chunk
            else:
                result = "".join([chunk for chunk in output])
                self._track_cost(model, "text", len(prompt) + len(result))
                return result
                
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    # IMAGE MODELS
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def generate_image(
        self,
        prompt: str,
        model: ReplicateModel = ReplicateModel.FLUX_PRO,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> List[str]:
        """
        Generate images using FLUX, SDXL, or Playground.
        
        Args:
            prompt: Image description
            model: Which image model to use
            negative_prompt: What to avoid
            width: Image width
            height: Image height
            num_images: Number of variations
            guidance_scale: Prompt adherence (1-20)
            seed: Random seed for reproducibility
            
        Returns:
            List of image URLs
        """
        
        input_params = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_outputs": num_images,
            "guidance_scale": guidance_scale
        }
        
        if negative_prompt:
            input_params["negative_prompt"] = negative_prompt
        
        if seed:
            input_params["seed"] = seed
        
        try:
            output = await self.client.async_run(
                model.value,
                input=input_params
            )
            
            # Output is list of file URLs
            image_urls = [str(img) for img in output]
            self._track_cost(model, "image", num_images)
            
            return image_urls
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    # VIDEO MODELS
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def generate_video(
        self,
        prompt: str,
        model: ReplicateModel = ReplicateModel.MINIMAX_VIDEO,
        image_url: Optional[str] = None,  # For image-to-video
        duration: int = 6,
        fps: int = 30,
        resolution: str = "1920x1080",
        guidance_scale: float = 7.5,
        motion_strength: float = 0.8,
        seed: Optional[int] = None,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Generate video using Minimax, Luma, or Runway.
        
        Args:
            prompt: Video description
            model: Which video model to use
            image_url: Starting image for image-to-video
            duration: Video length in seconds
            fps: Frames per second
            resolution: "1920x1080", "1280x720", etc.
            guidance_scale: Prompt adherence
            motion_strength: Amount of movement (0-1)
            seed: Random seed
            webhook_url: Callback URL when complete
            
        Returns:
            Video URL
        """
        
        input_params = {
            "prompt": prompt,
            "duration": duration,
            "fps": fps,
            "guidance_scale": guidance_scale,
            "motion_strength": motion_strength
        }
        
        # Parse resolution
        width, height = map(int, resolution.split('x'))
        input_params["width"] = width
        input_params["height"] = height
        
        if image_url:
            input_params["image"] = image_url
        
        if seed:
            input_params["seed"] = seed
        
        try:
            # Video generation is async, use prediction API
            prediction = await self.client.predictions.async_create(
                version=await self._get_model_version(model),
                input=input_params,
                webhook=webhook_url
            )
            
            # Poll for completion
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(5)
                prediction = await self.client.predictions.async_get(prediction.id)
            
            if prediction.status == "succeeded":
                video_url = prediction.output
                self._track_cost(model, "video", duration)
                return video_url
            else:
                raise Exception(f"Video generation failed: {prediction.error}")
                
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    # AUDIO MODELS
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def generate_audio(
        self,
        prompt: str,
        model: ReplicateModel = ReplicateModel.MUSICGEN,
        duration: int = 30,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        continuation: bool = False,
        continuation_start: Optional[str] = None
    ) -> str:
        """
        Generate music/audio using Suno, MusicGen, or AudioCraft.
        
        Args:
            prompt: Audio description
            model: Which audio model to use
            duration: Audio length in seconds
            temperature: Randomness (0-1)
            top_k: Token sampling parameter
            top_p: Nucleus sampling parameter
            continuation: Continue from existing audio
            continuation_start: Audio URL to continue from
            
        Returns:
            Audio URL
        """
        
        input_params = {
            "prompt": prompt,
            "duration": duration,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p
        }
        
        if continuation and continuation_start:
            input_params["continuation"] = True
            input_params["continuation_start"] = continuation_start
        
        try:
            output = await self.client.async_run(
                model.value,
                input=input_params
            )
            
            audio_url = str(output)
            self._track_cost(model, "audio", duration)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise
    
    # SAFETY MODEL
    
    async def check_safety(
        self,
        content: str,
        context: str = "video_generation"
    ) -> Dict[str, Any]:
        """
        Check content safety using Llama Guard.
        
        Returns:
            {
                "safe": bool,
                "violations": List[str],
                "confidence": float
            }
        """
        
        prompt = f"""[INST] Task: Check if there is unsafe content in '{context}' according to our safety policy.

<BEGIN UNSAFE CONTENT CATEGORIES>
S1: Violence and Hate
S2: Sexual Content
S3: Criminal Planning
S4: Guns and Illegal Weapons
S5: Regulated or Controlled Substances
S6: Self-Harm
S7: Profanity
S13: Misinformation
<END UNSAFE CONTENT CATEGORIES>

<BEGIN CONVERSATION>
{content}
<END CONVERSATION>

Provide your safety assessment for the content above. [/INST]"""
        
        output = await self.generate_text(
            prompt=prompt,
            model=ReplicateModel.LLAMA_GUARD,
            max_tokens=500
        )
        
        # Parse Llama Guard output
        if "safe" in output.lower():
            return {
                "safe": True,
                "violations": [],
                "confidence": 0.95
            }
        else:
            # Extract violation categories
            violations = []
            for line in output.split('\n'):
                if line.startswith('S'):
                    violations.append(line.split(':')[0])
            
            return {
                "safe": False,
                "violations": violations,
                "confidence": 0.90
            }
    
    # UTILITY METHODS
    
    def _track_cost(self, model: ReplicateModel, type: str, units: int):
        """Track API costs per model"""
        if model.value not in self.costs:
            self.costs[model.value] = 0
        
        # Approximate costs (update with actual Replicate pricing)
        cost_per_unit = {
            "text": 0.00001,  # per token
            "image": 0.04,    # per image
            "video": 0.25,    # per second
            "audio": 0.05     # per second
        }
        
        cost = units * cost_per_unit.get(type, 0)
        self.costs[model.value] += cost
    
    async def _get_model_version(self, model: ReplicateModel) -> str:
        """Get latest version ID for a model"""
        # Cache version IDs to avoid repeated API calls
        # In production, fetch from Replicate API
        return model.value
    
    def get_total_costs(self) -> Dict[str, float]:
        """Get cost breakdown by model"""
        return self.costs
```

### Model Fallback Strategy

```python
# backend/app/services/model_fallback.py

class ModelFallbackStrategy:
    """
    Automatically fallback to alternative models if primary fails.
    """
    
    FALLBACK_CHAINS = {
        # Text Models
        ReplicateModel.LLAMA_405B: [
            ReplicateModel.LLAMA_70B,
            ReplicateModel.MISTRAL_LARGE
        ],
        
        # Image Models
        ReplicateModel.FLUX_PRO: [
            ReplicateModel.FLUX_DEV,
            ReplicateModel.SDXL,
            ReplicateModel.PLAYGROUND_V25
        ],
        
        # Video Models
        ReplicateModel.MINIMAX_VIDEO: [
            ReplicateModel.LUMA_DREAM,
            ReplicateModel.RUNWAY_GEN3,
            ReplicateModel.STABLE_VIDEO
        ],
        
        # Audio Models
        ReplicateModel.SUNO: [
            ReplicateModel.MUSICGEN,
            ReplicateModel.AUDIOCRAFT
        ]
    }
    
    async def generate_with_fallback(
        self,
        client: ReplicateClient,
        method_name: str,
        primary_model: ReplicateModel,
        **kwargs
    ):
        """
        Attempt generation with primary model, fallback on failure.
        """
        
        models_to_try = [primary_model] + self.FALLBACK_CHAINS.get(primary_model, [])
        
        for model in models_to_try:
            try:
                logger.info(f"Attempting generation with {model.value}")
                
                method = getattr(client, method_name)
                result = await method(model=model, **kwargs)
                
                logger.info(f"Successfully generated with {model.value}")
                return result
                
            except Exception as e:
                logger.warning(f"Failed with {model.value}: {e}")
                
                if model == models_to_try[-1]:
                    # Last model in chain failed
                    raise Exception(f"All models failed: {e}")
                else:
                    # Try next model
                    continue
```

## Testing Plan

### Unit Tests

```python
# tests/unit/test_replicate_client.py

import pytest
from app.services.replicate_client import ReplicateClient, ReplicateModel

@pytest.fixture
def replicate_client():
    return ReplicateClient(api_token="test-token")

async def test_generate_text(replicate_client):
    """Test text generation with Llama"""
    result = await replicate_client.generate_text(
        prompt="Write a short product description",
        model=ReplicateModel.LLAMA_70B,
        max_tokens=100
    )
    
    assert isinstance(result, str)
    assert len(result) > 0

async def test_generate_image(replicate_client):
    """Test image generation with FLUX"""
    result = await replicate_client.generate_image(
        prompt="A modern coffee bottle on a kitchen counter",
        model=ReplicateModel.FLUX_PRO,
        num_images=1
    )
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].startswith("https://")

async def test_generate_video(replicate_client):
    """Test video generation with Minimax"""
    result = await replicate_client.generate_video(
        prompt="Close-up of coffee being poured",
        model=ReplicateModel.MINIMAX_VIDEO,
        duration=6
    )
    
    assert isinstance(result, str)
    assert result.startswith("https://")

async def test_safety_check(replicate_client):
    """Test content safety with Llama Guard"""
    safe_content = "A beautiful sunrise over mountains"
    result = await replicate_client.check_safety(safe_content)
    
    assert result["safe"] is True
    assert len(result["violations"]) == 0
    
    unsafe_content = "Violence and weapons"
    result = await replicate_client.check_safety(unsafe_content)
    
    assert result["safe"] is False
    assert len(result["violations"]) > 0

async def test_model_fallback(replicate_client):
    """Test fallback to alternative models"""
    strategy = ModelFallbackStrategy()
    
    # Mock primary model failure
    with pytest.raises(Exception):
        result = await strategy.generate_with_fallback(
            client=replicate_client,
            method_name="generate_image",
            primary_model=ReplicateModel.FLUX_PRO,
            prompt="Test image"
        )
```

## Configuration

```python
# backend/app/config.py

class Settings:
    # Replicate API
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN")
    
    # Default Models
    DEFAULT_TEXT_MODEL: str = "llama-70b"
    DEFAULT_IMAGE_MODEL: str = "flux-pro"
    DEFAULT_VIDEO_MODEL: str = "minimax-video"
    DEFAULT_AUDIO_MODEL: str = "musicgen"
    
    # Model Selection Strategy
    USE_FALLBACK: bool = True
    ENABLE_COST_OPTIMIZATION: bool = True  # Use cheaper models when quality allows
```

## Cost Optimization

```python
# backend/app/services/cost_optimizer.py

class CostOptimizer:
    """
    Select most cost-effective model for the task.
    """
    
    MODEL_COSTS = {
        # Text (per 1M tokens)
        ReplicateModel.LLAMA_405B: 5.00,
        ReplicateModel.LLAMA_70B: 0.65,
        ReplicateModel.MISTRAL_LARGE: 2.00,
        
        # Image (per image)
        ReplicateModel.FLUX_PRO: 0.04,
        ReplicateModel.FLUX_DEV: 0.025,
        ReplicateModel.SDXL: 0.015,
        
        # Video (per second)
        ReplicateModel.MINIMAX_VIDEO: 0.30,
        ReplicateModel.LUMA_DREAM: 0.25,
        ReplicateModel.RUNWAY_GEN3: 0.40,
        
        # Audio (per second)
        ReplicateModel.MUSICGEN: 0.05,
        ReplicateModel.SUNO: 0.08
    }
    
    def select_optimal_model(
        self,
        model_type: ModelType,
        quality_requirement: str = "standard"  # "economy", "standard", "premium"
    ) -> ReplicateModel:
        """
        Select best model for quality/cost balance.
        """
        
        if model_type == ModelType.TEXT:
            if quality_requirement == "economy":
                return ReplicateModel.LLAMA_70B
            elif quality_requirement == "premium":
                return ReplicateModel.LLAMA_405B
            else:
                return ReplicateModel.MISTRAL_LARGE
        
        # Similar logic for image, video, audio...
```

## Dependencies
- replicate Python SDK
- tenacity (retry logic)
- asyncio
- FastAPI

## Definition of Done
- [ ] ReplicateClient implemented with all methods
- [ ] Model fallback strategy working
- [ ] Safety checking with Llama Guard
- [ ] Cost tracking functional
- [ ] Unit tests passing (>85% coverage)
- [ ] Integration tests with real API
- [ ] Documentation complete
- [ ] Code reviewed and merged

---
**Created**: 2025-11-15  
**Assigned To**: Backend AI Team  
**Status**: Ready
