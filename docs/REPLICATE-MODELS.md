# Zapcut AI: Replicate Models Guide

## Overview
Zapcut uses Replicate's comprehensive model suite for all AI generation tasks. This document outlines which models are used where, fallback strategies, and cost optimization.

**Last Updated**: 2025-11-15

---

## Model Categories

### 🔤 Text Models
Used for: Orchestration, story planning, prompt synthesis, safety validation

| Model | Use Case | Cost | Priority |
|-------|----------|------|----------|
| **Llama 3.1 70B** | Primary text generation, agents | $0.65/1M tokens | Primary |
| **Llama 3.1 405B** | Complex reasoning, premium quality | $5.00/1M tokens | Fallback (premium) |
| **Mistral Large** | Alternative text generation | $2.00/1M tokens | Fallback |
| **Llama Guard 3 8B** | Content safety moderation | $0.20/1M tokens | Safety only |

**Replicate Paths**:
- `meta/llama-3.1-70b-instruct`
- `meta/llama-3.1-405b-instruct`
- `mistralai/mistral-large-2407`
- `meta/llama-guard-3-8b`

---

### 🎨 Image Models
Used for: Reference images, brand style anchoring, Creative Bible visualization

| Model | Use Case | Cost | Priority |
|-------|----------|------|----------|
| **FLUX 1.1 Pro** | Primary image generation | $0.04/image | Primary |
| **FLUX Dev** | Fast iterations, drafts | $0.025/image | Fallback |
| **Stable Diffusion XL** | Budget-friendly alternative | $0.015/image | Fallback |
| **Playground v2.5** | Artistic style variations | $0.03/image | Optional |

**Replicate Paths**:
- `black-forest-labs/flux-1.1-pro`
- `black-forest-labs/flux-dev`
- `stability-ai/sdxl`
- `playgroundai/playground-v2.5-1024px-aesthetic`

**Typical Usage**:
```python
# Generate 4 reference images for Creative Bible
reference_images = await replicate_client.generate_image(
    prompt="Product shot of Luna Coffee bottle, modern minimalist style",
    model=ReplicateModel.FLUX_PRO,
    num_images=4,
    width=1024,
    height=1024
)
```

---

### 🎬 Video Models
Used for: Scene generation (5 scenes per 30s ad)

| Model | Use Case | Cost | Priority |
|-------|----------|------|----------|
| **Minimax Video-01** | Primary video generation | $0.30/second | Primary |
| **Luma Dream Machine** | Fast, high-quality videos | $0.25/second | Fallback |
| **Runway Gen-3 Alpha** | Premium quality, slower | $0.40/second | Fallback (premium) |
| **Stable Video Diffusion** | Budget option, shorter clips | $0.15/second | Fallback (economy) |

**Replicate Paths**:
- `minimax/video-01`
- `luma/dream-machine`
- `runway/gen-3-alpha-turbo`
- `stability-ai/stable-video-diffusion`

**Typical Usage**:
```python
# Generate 6-second scene
scene_video = await replicate_client.generate_video(
    prompt="Close-up of Luna Coffee bottle on kitchen counter, morning sunlight",
    model=ReplicateModel.MINIMAX_VIDEO,
    duration=6,
    fps=30,
    resolution="1920x1080",
    image_url=reference_images[0]  # Use reference for consistency
)
```

**Video Generation Features**:
- Image-to-video (use reference images as starting frames)
- Text-to-video (generate from scratch)
- Duration: 2-10 seconds per scene
- Resolution: 720p to 1080p
- FPS: 24 or 30

---

### 🎵 Audio Models
Used for: Background music, sound effects

| Model | Use Case | Cost | Priority |
|-------|----------|------|----------|
| **MusicGen** | Primary music generation | $0.05/second | Primary |
| **Suno Bark** | Voice synthesis, effects | $0.08/second | Optional |
| **AudioCraft** | Multi-track audio | $0.06/second | Fallback |

**Replicate Paths**:
- `meta/musicgen`
- `suno-ai/bark`
- `facebook/audiocraft`

**Typical Usage**:
```python
# Generate 30-second background music
music = await replicate_client.generate_audio(
    prompt="Calm, acoustic guitar background music, warm and inviting, 90 BPM",
    model=ReplicateModel.MUSICGEN,
    duration=30
)
```

---

## Agent-to-Model Mapping

### 1. Master Orchestrator Agent
**Models**: Llama 3.1 70B  
**Purpose**: Guide user through workflow, validate stage transitions  
**Cost**: ~$0.002 per conversation

```python
orchestrator = MasterOrchestrator()
response = await orchestrator.process_message(
    user_message="Luna Coffee",
    model=ReplicateModel.LLAMA_70B
)
```

---

### 2. Story Structuring Agent
**Models**: Llama 3.1 70B or Mistral Large  
**Purpose**: Create 5-scene storyboard  
**Cost**: ~$0.001 per storyboard

```python
storyboard = await story_agent.generate_storyboard(
    user_brief="Modern coffee ad, morning routine",
    model=ReplicateModel.LLAMA_70B
)
```

---

### 3. Style & Brand Consistency Agent
**Models**: 
- Text: Llama 3.1 70B (Creative Bible generation)
- Image: FLUX 1.1 Pro (Reference images)

**Purpose**: Generate Creative Bible + 4 reference images  
**Cost**: ~$0.17 ($0.001 text + $0.16 images)

```python
# Step 1: Generate Creative Bible
creative_bible = await style_agent.generate_creative_bible(
    user_brief="Clean, modern, warm morning light",
    product_images=["url1", "url2"],
    text_model=ReplicateModel.LLAMA_70B
)

# Step 2: Generate reference images
reference_images = await style_agent.generate_reference_images(
    creative_bible=creative_bible,
    image_model=ReplicateModel.FLUX_PRO,
    num_images=4
)
```

---

### 4. Safety Validation Agent
**Models**: Llama Guard 3 8B  
**Purpose**: Check all prompts for unsafe content  
**Cost**: ~$0.0002 per validation

```python
safety_check = await safety_agent.validate(
    content=all_scene_descriptions,
    model=ReplicateModel.LLAMA_GUARD
)

if not safety_check["safe"]:
    raise ContentViolation(safety_check["violations"])
```

---

### 5. Prompt Synthesis Agent
**Models**: Llama 3.1 70B  
**Purpose**: Optimize prompts for video/image generation  
**Cost**: ~$0.001 per batch (5 scenes)

```python
optimized_prompts = await prompt_agent.synthesize_prompts(
    scenes=storyboard["scenes"],
    creative_bible=creative_bible,
    model=ReplicateModel.LLAMA_70B
)
```

---

### 6. Continuity Back-Propagation Agent
**Models**: Llama 3.1 70B  
**Purpose**: Ensure visual consistency across scenes  
**Cost**: ~$0.0005 per scene pair

```python
for i in range(1, len(scenes)):
    updated_prompt = await continuity_agent.enhance_prompt(
        current_scene=scenes[i],
        previous_scene=scenes[i-1],
        model=ReplicateModel.LLAMA_70B
    )
```

---

## Cost Breakdown: 30-Second Ad

### Per-Video Cost Analysis

| Component | Model | Units | Unit Cost | Total |
|-----------|-------|-------|-----------|-------|
| **Orchestrator** | Llama 70B | 5K tokens | $0.00065/1K | $0.003 |
| **Story Agent** | Llama 70B | 2K tokens | $0.00065/1K | $0.001 |
| **Creative Bible** | Llama 70B | 3K tokens | $0.00065/1K | $0.002 |
| **Reference Images** | FLUX Pro | 4 images | $0.04 | $0.16 |
| **Safety Checks** | Llama Guard | 5K tokens | $0.0002/1K | $0.001 |
| **Prompt Synthesis** | Llama 70B | 3K tokens | $0.00065/1K | $0.002 |
| **Scene Generation** | Minimax | 30 seconds | $0.30/sec | $9.00 |
| **Music Generation** | MusicGen | 30 seconds | $0.05/sec | $1.50 |
| **TOTAL** | | | | **$10.67** |

### Cost Optimization Strategies

**1. Reuse Creative Bible** (40% savings on images)
- First ad: $10.67
- Subsequent ads: $10.51 (skip reference images)
- Savings: $0.16 per ad

**2. Use Fallback Models** (25-40% savings)
```python
# Premium: Minimax Video ($0.30/sec) = $9.00 for 30s
# Standard: Luma Dream ($0.25/sec) = $7.50 for 30s  
# Economy: Stable Video ($0.15/sec) = $4.50 for 30s
```

**3. Batch Generation**
- Generate 5 ads in parallel
- Amortize Creative Bible cost
- Cost per ad: $10.51 → $10.48

**4. Quality Tiers**
```python
COST_TIERS = {
    "economy": {
        "text": ReplicateModel.LLAMA_70B,
        "image": ReplicateModel.SDXL,
        "video": ReplicateModel.STABLE_VIDEO,
        "audio": ReplicateModel.MUSICGEN,
        "cost": "$6.50"
    },
    "standard": {
        "text": ReplicateModel.LLAMA_70B,
        "image": ReplicateModel.FLUX_PRO,
        "video": ReplicateModel.LUMA_DREAM,
        "audio": ReplicateModel.MUSICGEN,
        "cost": "$9.17"
    },
    "premium": {
        "text": ReplicateModel.LLAMA_405B,
        "image": ReplicateModel.FLUX_PRO,
        "video": ReplicateModel.MINIMAX_VIDEO,
        "audio": ReplicateModel.AUDIOCRAFT,
        "cost": "$13.80"
    }
}
```

---

## Model Fallback Strategy

### Fallback Chains

When primary model fails or is unavailable, automatically fallback:

```python
FALLBACK_CHAINS = {
    # Text Models
    ReplicateModel.LLAMA_405B: [
        ReplicateModel.LLAMA_70B,      # Fallback 1
        ReplicateModel.MISTRAL_LARGE   # Fallback 2
    ],
    
    # Image Models
    ReplicateModel.FLUX_PRO: [
        ReplicateModel.FLUX_DEV,       # Fallback 1
        ReplicateModel.SDXL,           # Fallback 2
        ReplicateModel.PLAYGROUND_V25  # Fallback 3
    ],
    
    # Video Models
    ReplicateModel.MINIMAX_VIDEO: [
        ReplicateModel.LUMA_DREAM,     # Fallback 1
        ReplicateModel.RUNWAY_GEN3,    # Fallback 2
        ReplicateModel.STABLE_VIDEO    # Fallback 3
    ],
    
    # Audio Models
    ReplicateModel.SUNO: [
        ReplicateModel.MUSICGEN,       # Fallback 1
        ReplicateModel.AUDIOCRAFT      # Fallback 2
    ]
}
```

### Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def generate_with_fallback(model, **kwargs):
    """
    Try primary model, fallback on failure.
    Exponential backoff: 4s, 16s, 60s
    """
    pass
```

---

## Performance Benchmarks

### Generation Times (30-second ad)

| Stage | Model | Time |
|-------|-------|------|
| Creative Bible | Llama 70B | 5-10s |
| Reference Images | FLUX Pro | 30-45s |
| Storyboard | Llama 70B | 10-15s |
| Safety Validation | Llama Guard | 3-5s |
| Scene 1-5 (parallel) | Minimax | 120-180s |
| Music (parallel) | MusicGen | 60-90s |
| **TOTAL** | | **~4-5 minutes** |

### Quality Benchmarks

| Model | Resolution | Consistency | Speed | Cost Efficiency |
|-------|-----------|-------------|-------|-----------------|
| **Minimax Video-01** | 1080p | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Luma Dream** | 1080p | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Runway Gen-3** | 1080p | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Stable Video** | 720p | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Configuration

### Environment Variables

```bash
# Replicate API
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx

# Default Models
DEFAULT_TEXT_MODEL=llama-70b
DEFAULT_IMAGE_MODEL=flux-pro
DEFAULT_VIDEO_MODEL=minimax-video
DEFAULT_AUDIO_MODEL=musicgen

# Quality Tier
QUALITY_TIER=standard  # economy, standard, premium

# Fallback Strategy
ENABLE_MODEL_FALLBACK=true
MAX_RETRY_ATTEMPTS=3
```

### Model Selection

```python
# backend/app/config.py

class ReplicateConfig:
    # Text Models
    TEXT_MODELS = {
        "economy": "llama-70b",
        "standard": "llama-70b", 
        "premium": "llama-405b"
    }
    
    # Image Models
    IMAGE_MODELS = {
        "economy": "sdxl",
        "standard": "flux-pro",
        "premium": "flux-pro"
    }
    
    # Video Models
    VIDEO_MODELS = {
        "economy": "stable-video",
        "standard": "luma-dream",
        "premium": "minimax-video"
    }
    
    # Audio Models
    AUDIO_MODELS = {
        "economy": "musicgen",
        "standard": "musicgen",
        "premium": "audiocraft"
    }
```

---

## Monitoring & Analytics

### Track Model Usage

```python
# Log every model call
logger.info({
    "event": "model_call",
    "model": model.value,
    "type": model_type,
    "duration_ms": duration,
    "cost": cost,
    "success": success,
    "fallback_used": fallback_used
})
```

### Cost Dashboard Metrics

- Total API spend per day/month
- Cost per video breakdown
- Model usage distribution
- Fallback rate by model
- Average generation time by model

---

## Best Practices

### 1. Use Appropriate Models
```python
# ✅ Good: Use Llama 70B for most text tasks
text = await generate_text(model=ReplicateModel.LLAMA_70B)

# ❌ Bad: Overusing expensive models unnecessarily
text = await generate_text(model=ReplicateModel.LLAMA_405B)
```

### 2. Implement Caching
```python
# Cache Creative Bibles and reference images
if project.creative_bible_id:
    # Reuse existing, save $0.17
    creative_bible = CreativeBible.get(project.creative_bible_id)
else:
    # Generate new
    creative_bible = await generate_creative_bible()
```

### 3. Parallel Processing
```python
# Generate all 5 scenes + music in parallel
tasks = [
    generate_video(scene_1),
    generate_video(scene_2),
    generate_video(scene_3),
    generate_video(scene_4),
    generate_video(scene_5),
    generate_audio(music_prompt)
]
results = await asyncio.gather(*tasks)
```

### 4. Monitor Costs
```python
# Track costs per generation
cost_tracker = ReplicateCostTracker()
total_cost = cost_tracker.get_total_costs()

if total_cost > BUDGET_LIMIT:
    alert_team(f"Budget exceeded: ${total_cost}")
```

---

## Troubleshooting

### Common Issues

**1. Model Unavailable**
```python
# Use fallback chain
try:
    result = await generate_video(model=ReplicateModel.MINIMAX_VIDEO)
except ModelUnavailableError:
    result = await generate_video(model=ReplicateModel.LUMA_DREAM)
```

**2. Generation Timeout**
```python
# Increase timeout for video models
result = await asyncio.wait_for(
    generate_video(),
    timeout=300  # 5 minutes
)
```

**3. Rate Limiting**
```python
# Implement exponential backoff
@retry(wait=wait_exponential(min=4, max=60))
async def generate():
    # API call
    pass
```

---

## Related Documentation

- [E004: Multi-Agent Video Generation](./Epics/E004-multi-agent-video-generation.md)
- [S062: Replicate Model Abstraction Layer](./Stories/S062-replicate-model-abstraction.md)
- [Architecture: AI Services](./Architecture.md#ai-services)

---

**Questions?** Contact: engineering@zapcut.video  
**Replicate Docs**: https://replicate.com/docs  
**API Reference**: https://replicate.com/docs/reference/http

---

**Last Updated**: 2025-11-15  
**Maintained By**: Backend AI Team
