# Technical Architecture Decisions - AI Video Generation Pipeline
**Date:** 2025-11-15
**Status:** Validated through Interactive Brainstorming
**Related:** PRD-AI-Video-Generation-Pipeline.md, 2025-11-15-ai-video-pipeline-design.md

---

## Document Purpose

This document captures ALL technical architecture decisions made during the collaborative brainstorming session for Zapcut's AI video generation pipeline. Each decision includes the options considered, rationale, and chosen approach.

---

## Table of Contents

1. [Audio Architecture](#1-audio-architecture)
2. [LoRA Fine-Tuning Strategy](#2-lora-fine-tuning-strategy)
3. [Pricing Model](#3-pricing-model)
4. [Video Length Limits](#4-video-length-limits)
5. [Multi-Language Support](#5-multi-language-support)
6. [Backend Tech Stack](#6-backend-tech-stack)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Video Asset Loading](#8-video-asset-loading)
9. [Database Architecture](#9-database-architecture)
10. [Job Orchestration Strategy](#10-job-orchestration-strategy)
11. [Job Queue System](#11-job-queue-system)
12. [Frontend-Backend Communication](#12-frontend-backend-communication)
13. [Product Image Integration](#13-product-image-integration)
14. [Scene Transitions](#14-scene-transitions)
15. [FFmpeg Composition Pipeline](#15-ffmpeg-composition-pipeline)

---

## 1. Audio Architecture

### Question
What audio capabilities should be included in MVP ads?

### Options Considered
- A) Voiceovers only
- B) Background music only
- C) Both voiceover + music
- **D) Full audio suite (voiceover + music + SFX)** ✅ SELECTED

### Decision
**Full Audio Suite via Mixed Services**

### Implementation
**Services:**
- **Voiceover**: Replicate TTS models (Bark or Coqui XTTS)
  - Use case: Scene-by-scene narration
  - Accents: American, British, Australian
  - Cost: ~$0.05-0.10 per 30s ad

- **Music**: Suno AI (standalone API at suno.ai)
  - Use case: Custom 30-60 second background tracks
  - Quality: Premium musical structure
  - Cost: $10-30/month subscription
  - Note: NOT available on Replicate; requires separate integration

- **Sound Effects**: Replicate audio models or Freesound API
  - Use case: Product sounds, transitions, ambient audio
  - Cost: ~$0.01-0.05 per ad

**Total Audio Cost:** ~$0.20-0.30 per ad

### Rationale
Professional ads require complete audio production. Music quality is critical for emotional impact, justifying the separate Suno integration despite adding another service dependency.

---

## 2. LoRA Fine-Tuning Strategy

### Question
When should the system train brand-specific LoRA models?

### Options Considered
- A) Immediately on brand creation
- **B) After first video generation with preview** ✅ SELECTED
- C) On-demand/manual trigger
- D) Not for MVP

### Decision
**Progressive Training with User Preview**

### Implementation Timeline

**First Video (Day 1):**
- Use base Sora with brand-aware prompts
- Include brand colors, product descriptions
- Fast generation: 3-5 minutes
- User gets immediate value

**Background Training (Automatic):**
- Triggers after first video completes
- Training data:
  - 2+ original product images
  - Generated video frames from first ad (~10-15 high-quality images total)
- Duration: 30-45 minutes
- Runs as backend job in Redis queue
- Persists if user closes app
- Model saved to S3 when complete

**Before Second Video (User Choice):**
- Notification: "Your custom brand style is ready!"
- Preview UI: Side-by-side comparison
  - Standard Sora style vs. Custom LoRA style
- User decision: "Use custom style for future ads?" (Yes/No)
- If approved: All future videos use LoRA model

### Backend Schema
```typescript
Brand.loraModel = {
  status: 'none' | 'training' | 'ready' | 'failed',
  trainingJobId: string,
  modelUrl: string, // S3 location
  trainedAt: Date,
  userApproved: boolean,
  previewImageUrl: string // Sample frame for comparison
}
```

### Rationale
- First video needs speed for user validation
- After first video, user is invested and willing to wait
- Training from generated content produces better results than 2 images alone
- User preview builds trust and demonstrates value
- Best time for training is after seeing what works visually

---

## 3. Pricing Model

### Question
What pricing model fits target users (small business owners, marketers)?

### Options Considered
- A) Credit-based system
- B) Freemium with limits
- C) Subscription tiers
- **D) Hybrid: Free trial + credits/subscriptions** ✅ SELECTED

### Decision
**Hybrid Free Trial + Flexible Monetization**

### Specific Implementation

**Free Tier:**
- **Video 1**: Up to 15 seconds (free)
- **Video 2**: Up to 30 seconds (free)
- **After 2 videos**: Must purchase

**Features Included:**
- Full AI chat + script generation
- Complete audio suite (voiceover, music, SFX)
- 1080p export
- No watermark
- LoRA custom style (after first video)

**Pay-Per-Video (Credits):**
- $5 per 30s video
- $8 per 60s video
- Credit packs:
  - $40 = 10 videos (30s) → $4/video
  - $70 = 10 videos (60s) → $7/video
- Credits never expire

**Subscription Tiers:**

| Tier | Price | Videos/Month | Max Length | Resolution | Special Features |
|------|-------|--------------|------------|------------|------------------|
| Starter | $29/mo | 10 | 30s | 1080p | - |
| Pro | $79/mo | 30 | 60s | 1080p | Priority processing |
| Agency | $199/mo | 100 | 60s | 4K | Priority + API access |

### Rationale
- 15s video lets users try short-form (Instagram Stories, TikTok)
- 30s video lets users try medium-form (Facebook Feed)
- Experience full value before payment commitment
- Two paths (credits vs subscription) accommodate different user types
- Clear upgrade incentive after 2 free videos

---

## 4. Video Length Limits

### Question
What video length limits make sense across tiers?

### Options Considered
- A) Conservative (15s free, 30s paid)
- **B) Platform-aligned (30s free, 60s paid)** ✅ SELECTED
- C) Flexible (variable pricing by length)
- D) Aggressive (30s free, 90s paid)

### Decision
**Platform-Aligned Duration Strategy**

### Implementation

**Free Tier:**
- Video 1: 15 seconds → Instagram Stories, TikTok, Reels
- Video 2: 30 seconds → Instagram Feed, Facebook, extended TikTok

**Credits/Starter ($29/mo):**
- Up to 30 seconds per video
- Platforms: Instagram, TikTok, Facebook Feed, LinkedIn, Twitter/X

**Pro ($79/mo) & Agency ($199/mo):**
- Up to 60 seconds per video
- Platforms: All above + YouTube pre-roll, in-stream ads

### Chat Integration
During AI conversation (Question 3/5):
- AI asks: "How long should your ad be?"
- Provides platform recommendations
- Validates against user's tier
- Inline upgrade prompt if exceeds tier

### Rationale
- Limits match real platform requirements (not arbitrary)
- Natural upgrade incentive (want YouTube? Need Pro)
- Clear value proposition at each tier
- Industry-standard durations

---

## 5. Multi-Language Support

### Question
What language support makes sense for MVP?

### Options Considered
- **A) English only** ✅ SELECTED
- B) English + Spanish
- C) Top 5 languages
- D) Auto-detect with basic support

### Decision
**English-Only MVP with i18n Foundation**

### Implementation

**MVP Scope:**
- UI/UX: All English
- GPT-4 conversations: English
- Voiceover: English voices (American, British, Australian accents)
- Script generation: English-optimized prompts
- Target: US, UK, Canada, Australia (~500M users)

**Technical Foundation:**
- Install react-i18next from day 1
- All UI strings in translation files (no hardcoded strings)
- Database schema includes `preferredLocale` field
- Example: `{t('button.createBrand')}` instead of `"Create Brand"`

**Post-MVP Roadmap:**
- Phase 1 (v2.0): Spanish (~3-6 months post-launch)
- Phase 2 (v2.5): French, German, Italian (~6-9 months)
- Phase 3 (v3.0): Mandarin, Hindi, Japanese (~12+ months)

### Rationale
- Focus on product-market fit first
- English market large enough for validation
- Avoid multi-language testing complexity in MVP
- Technical foundation enables fast expansion
- 2-3 months faster to market

---

## 6. Backend Tech Stack

### Question
Node.js or Python for backend services?

### Options Considered
- A) Node.js + Express
- **B) Python + FastAPI** ✅ SELECTED
- C) Hybrid (Node API + Python workers)

### Decision
**Python/FastAPI**

### Stack Details
- **Framework**: FastAPI (async, type-safe, modern)
- **ORM**: SQLAlchemy
- **Job Queue**: RQ (Redis Queue)
- **Type Safety**: Pydantic models
- **Database**: PostgreSQL

### Rationale
1. Replicate API is Python-first (better SDK, docs, examples)
2. FFmpeg video processing significantly easier in Python
3. Future-proof for ML features (LoRA training, custom models)
4. FastAPI provides TypeScript-like type safety with Pydantic
5. RQ for job queues battle-tested for video processing
6. Video/AI processing is core to product (not just an API layer)

---

## 7. Deployment Architecture

### Question
Where should services run - cloud, local, or hybrid?

### Options Considered
- A) Cloud-hosted backend only
- B) Bundled local backend in Electron
- **C) Hybrid (cloud backend + local editor)** ✅ SELECTED

### Decision
**Hybrid Cloud + Local Architecture**

### Implementation

**Cloud Backend (Python/FastAPI):**
- Authentication & user management
- Brand storage & management
- AI chat (GPT-4)
- Script generation
- Video generation orchestration (Replicate/Suno)
- LoRA training jobs
- S3 asset management
- **Requires**: Internet connection

**Local Electron App:**
- Existing Zapcut video editor (works offline)
- Timeline editing, effects, transitions
- Local video playback & rendering
- Export to local files
- **Can work**: Offline (after videos downloaded)

### Rationale
- Video editor stays local (offline-capable, fast scrubbing)
- AI features require cloud APIs anyway (Replicate, Suno, OpenAI)
- Best of both worlds: powerful cloud processing + responsive local editing
- Clean separation of concerns
- Simpler than bundling Python with Electron

---

## 8. Video Asset Loading

### Question
How should generated videos get into the local editor?

### Options Considered
- **A) Download-first approach** ✅ SELECTED
- B) Stream from S3
- C) Hybrid caching

### Decision
**Download-First Approach**

### Implementation Flow
```typescript
// After video generation completes
1. Backend returns: { videoUrl: 's3://...', status: 'completed' }
2. Electron downloads to:
   ~/Library/Application Support/Zapcut/generated-videos/{projectId}.mp4
3. Call existing: addAssetsFromPaths([localPath])
4. Video loads into editor as normal asset
```

### Rationale
- Editor designed for local files (timeline scrubbing needs instant frames)
- Timeline scrubbing with S3 streams would be laggy
- Applying effects requires local frame access
- Can't have buffering during creative work
- User expectation: downloaded = they own it, can work offline
- Simpler MVP implementation
- Consistent with existing `addAssetsFromPaths` architecture

---

## 9. Database Architecture

### Question
How should cloud and local data be structured?

### Options Considered
- A) Separate databases, linked by ID
- B) Cloud-first with sync
- **C) Hybrid: Cloud for generation, local for editing** ✅ SELECTED

### Decision
**Hybrid Cloud + Local Storage**

### Implementation

**Cloud PostgreSQL:**
- Users, brands, ad projects
- Generation metadata, jobs
- LoRA models
- Chat history, scripts

**Local Zustand Persist:**
- Full Zapcut editor state
- Assets, clips, timeline
- Canvas nodes, playback state

**Link:**
- `AdProject.zapcutProjectId` references local project ID
- Generated videos download → become local assets

### Specific Schema Design
**Database Approach**: Hybrid normalized + JSONB

```sql
-- Core tables with JSONB for flexible data
users (table)
brands (table with brand_guidelines as JSONB)
ad_projects (table with ad_details as JSONB)
chat_messages (table - needs ordering/querying)
scripts (table with scenes as JSONB array)
generation_jobs (table - status tracking)
lora_models (table)
```

### Complete PostgreSQL Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    credits INTEGER DEFAULT 0,
    free_videos_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    product_images TEXT[], -- S3 URLs
    brand_guidelines JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE lora_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE UNIQUE,
    status VARCHAR(50) NOT NULL,
    model_url TEXT,
    preview_image_url TEXT,
    training_job_id VARCHAR(255),
    user_approved BOOLEAN DEFAULT false,
    error_message TEXT,
    trained_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ad_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'chat',
    ad_details JSONB,
    zapcut_project_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE UNIQUE,
    storyline TEXT NOT NULL,
    scenes JSONB NOT NULL,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    replicate_job_id VARCHAR(255),
    input_params JSONB,
    output_url TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_brands_user ON brands(user_id);
CREATE INDEX idx_ad_projects_user ON ad_projects(user_id);
CREATE INDEX idx_ad_projects_brand ON ad_projects(brand_id);
CREATE INDEX idx_chat_messages_project ON chat_messages(ad_project_id);
CREATE INDEX idx_generation_jobs_project ON generation_jobs(ad_project_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
```

### Rationale
- Clean separation matches hybrid deployment
- Editor stays fast and local
- Generation state persists in cloud
- Simple for MVP (no complex sync)
- Projects device-specific initially (acceptable for MVP)
- Hybrid schema: queryable fields as columns, flexible data as JSONB

---

## 10. Job Orchestration Strategy

### Question
How should video generation jobs be orchestrated - sequential or parallel?

### Options Considered
- **A) Sequential pipeline** ✅ SELECTED
- B) Parallel generation
- C) Smart hybrid

### Decision
**Sequential Pipeline for Quality**

### Implementation Flow
```
Scene 1 video (with prompt) →
Scene 2 video (with Scene 1 reference) →
Scene 3 video (with Scene 1+2 reference) →
Voiceover (all scenes) →
Music (full ad) →
SFX (optional) →
Composite (stitch everything)
```

**Total Time:** 6-8 minutes

### Rationale - Continuity Over Speed

**Why Sequential Wins:**

**Visual Continuity:**
- Each scene references previous scenes
- Better lighting/color consistency
- Characters/products look the same across scenes
- Smoother transitions
- More coherent narrative flow

**Quality Trade-off:**
- Parallel: 3-4 minutes but potential visual discontinuity
- Sequential: 6-8 minutes but professional quality
- **Decision**: Quality matters more for professional ads
- LoRA helps brand consistency but doesn't solve scene-to-scene continuity

**User Expectation:**
- Users willing to wait 6-8 minutes for professional result
- Discontinuous scenes would feel amateur
- Better to deliver quality than speed for MVP

---

## 11. Job Queue System

### Question
Which Python job queue for sequential orchestration?

### Options Considered
- A) Celery + Redis
- **B) RQ (Redis Queue)** ✅ SELECTED
- C) No queue (direct Replicate polling)

### Decision
**RQ (Redis Queue)**

### Implementation

**RQ Workflow:**
```python
from rq import Queue
from redis import Redis

redis_conn = Redis()
q = Queue(connection=redis_conn)

def generate_ad_video(ad_project_id):
    # Sequential orchestration
    # 1. Scene 1
    scene1_job = q.enqueue(generate_scene_video, scene_1_data)
    wait_for_job(scene1_job)

    # 2. Scene 2 (with Scene 1 reference)
    scene2_job = q.enqueue(generate_scene_video, scene_2_data, prev_scene=scene1_url)
    wait_for_job(scene2_job)

    # 3. Scene 3 (with Scene 1+2 reference)
    scene3_job = q.enqueue(generate_scene_video, scene_3_data, prev_scenes=[scene1_url, scene2_url])
    wait_for_job(scene3_job)

    # 4. Audio generation (sequential)
    vo_job = q.enqueue(generate_voiceover, script)
    wait_for_job(vo_job)

    music_job = q.enqueue(generate_music, prompt)
    wait_for_job(music_job)

    # 5. Composite
    composite_job = q.enqueue(composite_video, all_assets)
    wait_for_job(composite_job)
```

### Why RQ vs Celery

**RQ Advantages:**
- Simpler than Celery (less configuration)
- Just needs Redis (no RabbitMQ)
- Python-native, easier to debug
- Perfect for sequential workflows
- Good job status tracking
- Sufficient for MVP needs

**Celery Advantages (not needed for MVP):**
- More features (scheduled tasks, complex routing)
- Better for large-scale distributed systems
- Overkill for initial launch

### Infrastructure
- Redis: Job queue + caching
- RQ Worker: Process jobs (can scale horizontally)
- Job monitoring: RQ Dashboard (web UI)

### Rationale
- Simpler setup than Celery
- Perfect for sequential orchestration
- Easy to track job status (critical for progress updates)
- Can scale workers horizontally if needed
- Redis needed anyway for caching

---

## 12. Frontend-Backend Communication

### Question
How should Electron track long-running video generation progress?

### Options Considered
- **A) HTTP Polling** ✅ SELECTED
- B) WebSocket (real-time)
- C) Server-Sent Events (SSE)

### Decision
**HTTP Polling Every 5 Seconds**

### Implementation

**Frontend (Electron):**
```typescript
// After starting video generation
const pollGenerationStatus = async (projectId: string) => {
  const intervalId = setInterval(async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/projects/${projectId}/generation-status`
      );
      const data = await response.json();

      // Update UI
      setGenerationProgress(data.progress);
      setCurrentStep(data.currentStep);

      // Check completion
      if (data.status === 'completed') {
        clearInterval(intervalId);
        downloadAndLoadVideo(data.videoUrl);
      } else if (data.status === 'failed') {
        clearInterval(intervalId);
        showError(data.errorMessage);
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, 5000); // Poll every 5 seconds

  return intervalId;
};
```

**Backend API:**
```python
@app.get("/api/projects/{project_id}/generation-status")
async def get_generation_status(project_id: str):
    project = await db.get_ad_project(project_id)
    jobs = await db.get_generation_jobs(project_id)

    # Calculate progress
    total_jobs = len(jobs)
    completed_jobs = len([j for j in jobs if j.status == 'completed'])
    progress = int((completed_jobs / total_jobs) * 100)

    # Current step
    current_job = next((j for j in jobs if j.status == 'processing'), None)
    current_step = f"Generating {current_job.job_type}" if current_job else "Finalizing"

    return {
        "status": project.status,
        "progress": progress,
        "currentStep": current_step,
        "videoUrl": project.final_video_url if project.status == 'completed' else None,
        "errorMessage": project.error_message if project.status == 'failed' else None
    }
```

### Rationale
- **Simple**: Easy to implement and debug
- **Reliable**: Works with any network configuration
- **Acceptable latency**: 5-second updates fine for 6-8 minute jobs
- **Resilient**: Auto-reconnects if network drops
- **MVP appropriate**: Can upgrade to WebSocket post-launch if needed
- **No firewall issues**: Standard HTTP, no special ports

**Future Enhancement:** Switch to WebSocket for real-time updates in v2.0

---

## 13. Product Image Integration

### Question
How should product images be incorporated into generated videos?

### Options Considered
- A) Sora embeds them (image conditioning)
- B) FFmpeg overlays only
- **C) Hybrid approach (Sora + overlays)** ✅ SELECTED

### Decision
**Hybrid: Sora Integration + FFmpeg Overlays**

### Implementation

**Phase 1: Sora Generation (Products IN Scenes)**
```python
# When generating each scene with Sora
prompt = f"""
Scene {scene_number}: {scene.description}

Product context:
- Product images provided show: {product_description}
- Integrate these products naturally into the scene
- Visual style: {brand_guidelines.tone}
- Colors: {brand_guidelines.colors}

{scene.visualPrompt}
"""

# If Sora supports image conditioning
sora_params = {
    "prompt": prompt,
    "reference_images": product_image_urls,  # Product images as visual references
    "duration": scene.duration
}
```

**Phase 2: FFmpeg Overlays (Clean Product Shots)**
```python
# Add product overlay at key moments
# Defined in script: overlay_config = { imageIndex, timestamp, duration, position }

overlay_configs = [
    {
        "imageIndex": 0,  # Which product image
        "timestamp": 8.0,  # 8 seconds into video
        "duration": 2.0,   # Show for 2 seconds
        "position": "bottom-right",
        "size": 400  # 400px width
    },
    {
        "imageIndex": 1,
        "timestamp": 20.0,
        "duration": 2.5,
        "position": "center",
        "size": 600
    }
]

# FFmpeg overlay command (applied during composition)
```

**Example Ad Structure:**
```
0-5s:   Scene 1 (Sora generated, product in context)
5-7s:   Scene 1 continues
7-9s:   [OVERLAY] Clean product shot (pixel-perfect)
9-15s:  Scene 2 (Sora generated, product in use)
15-17s: [OVERLAY] Second product shot
17-30s: Scene 3 (Sora generated, final CTA with product)
```

### Rationale
- **Natural integration**: Sora embeds products into scenes (feels organic)
- **Perfect showcase**: FFmpeg overlays show products pixel-perfect
- **Best of both worlds**: Contextual usage + clean hero shots
- **Professional quality**: Matches high-end ad production
- **Flexibility**: Script can define when/where overlays appear

---

## 14. Scene Transitions

### Question
How should scenes be stitched together?

### Options Considered
- A) Hard cuts
- **B) Crossfade transitions** ✅ SELECTED
- C) User-defined in editor

### Decision
**1-Second Crossfade Transitions**

### Implementation

```bash
# FFmpeg command for crossfade between scenes
ffmpeg -i scene_1.mp4 -i scene_2.mp4 -i scene_3.mp4 \
  -filter_complex "
    [0][1]xfade=transition=fade:duration=1:offset=4[v1];
    [v1][2]xfade=transition=fade:duration=1:offset=13[v_out]
  " \
  -map "[v_out]" scenes_stitched.mp4
```

**Parameters:**
- Transition type: `fade` (crossfade/dissolve)
- Duration: 1 second
- Offset: Calculated based on scene durations

**Example Timeline:**
```
Scene 1: 0-5s (5 seconds)
  [CROSSFADE 1s]  (overlaps 4-5s of Scene 1 with 0-1s of Scene 2)
Scene 2: 5-15s (10 seconds)
  [CROSSFADE 1s]  (overlaps 14-15s of Scene 2 with 0-1s of Scene 3)
Scene 3: 15-30s (15 seconds)
```

### Rationale
- **Professional polish**: Smooth, cinematic transitions
- **Masks continuity issues**: Even with sequential generation, slight color shifts happen
- **Industry standard**: Most video ads use crossfades
- **Not too slow**: 1 second is quick enough for social media pacing
- **Better than cuts**: Hard cuts can feel jarring for brand videos
- **Customizable later**: Users can adjust in Zapcut editor if they want

**Alternative considered:** User-defined in editor (Option C)
- Rejected because: Users want polished output from generation
- Can still customize in editor if desired

---

## 15. FFmpeg Composition Pipeline

### Question
What's the complete video composition workflow?

### Decision
**Multi-Stage FFmpeg Pipeline**

### Complete Implementation

```python
def compose_final_video(ad_project_id: str):
    """
    Complete FFmpeg composition pipeline for final ad video.
    Runs after all generation jobs complete.
    """

    # Step 1: Download all assets from S3 to temp folder
    temp_dir = f"/tmp/zapcut_compose_{ad_project_id}"
    os.makedirs(temp_dir, exist_ok=True)

    assets = {
        'scenes': download_scenes(ad_project_id, temp_dir),  # [scene_1.mp4, scene_2.mp4, scene_3.mp4]
        'voiceover': download_audio(ad_project_id, 'voiceover', temp_dir),  # voiceover.mp3
        'music': download_audio(ad_project_id, 'music', temp_dir),  # music.mp3
        'sfx': download_audio(ad_project_id, 'sfx', temp_dir),  # sfx.mp3 (optional)
        'product_images': download_product_images(ad_project_id, temp_dir)  # [product_1.png, product_2.png]
    }

    # Step 2: Stitch scenes with 1-second crossfade transitions
    scenes_input = " ".join([f"-i {scene}" for scene in assets['scenes']])
    num_scenes = len(assets['scenes'])

    # Build crossfade filter chain
    filter_chain = build_crossfade_filter(assets['scenes'])

    subprocess.run([
        "ffmpeg",
        *scenes_input.split(),
        "-filter_complex", filter_chain,
        "-map", "[v_out]",
        f"{temp_dir}/scenes_stitched.mp4"
    ])

    # Step 3: Overlay product images at specified timestamps
    # Product overlay config from script
    overlay_configs = get_product_overlay_configs(ad_project_id)

    video_with_overlays = overlay_product_images(
        video_path=f"{temp_dir}/scenes_stitched.mp4",
        product_images=assets['product_images'],
        overlay_configs=overlay_configs,
        output_path=f"{temp_dir}/video_with_products.mp4"
    )

    # Step 4: Mix audio layers
    audio_inputs = []
    audio_filters = []

    # Voiceover (100% volume, primary)
    audio_inputs.append(f"-i {assets['voiceover']}")
    audio_filters.append("[1:a]volume=1.0[vo]")

    # Music (30% volume, background)
    audio_inputs.append(f"-i {assets['music']}")
    audio_filters.append("[2:a]volume=0.3[music]")

    # SFX (50% volume, if exists)
    mix_inputs = "[vo][music]"
    if assets['sfx']:
        audio_inputs.append(f"-i {assets['sfx']}")
        audio_filters.append("[3:a]volume=0.5[sfx]")
        mix_inputs = "[vo][music][sfx]"
        num_audio_inputs = 3
    else:
        num_audio_inputs = 2

    # Combine all audio
    audio_filter = ";".join(audio_filters) + f";{mix_inputs}amix=inputs={num_audio_inputs}:duration=first[a_out]"

    final_output = f"{temp_dir}/final_ad.mp4"

    subprocess.run([
        "ffmpeg",
        "-i", video_with_overlays,
        *" ".join(audio_inputs).split(),
        "-filter_complex", audio_filter,
        "-map", "0:v",
        "-map", "[a_out]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",  # Quality (lower = better, 23 = good quality)
        "-c:a", "aac",
        "-b:a", "192k",
        final_output
    ])

    # Step 5: Upload final video to S3
    s3_url = upload_to_s3(final_output, f"generated_videos/{ad_project_id}/final_ad.mp4")

    # Step 6: Update database
    await db.update_ad_project(ad_project_id, {
        'status': 'completed',
        'final_video_url': s3_url,
        'completed_at': datetime.now()
    })

    # Step 7: Cleanup temp files
    shutil.rmtree(temp_dir)

    return s3_url


def build_crossfade_filter(scene_paths: list) -> str:
    """
    Build FFmpeg filter for crossfade transitions.
    Example for 3 scenes:
    [0][1]xfade=transition=fade:duration=1:offset=4[v1];
    [v1][2]xfade=transition=fade:duration=1:offset=13[v_out]
    """
    if len(scene_paths) == 1:
        return "[0]copy[v_out]"

    # Get scene durations
    durations = [get_video_duration(path) for path in scene_paths]

    filters = []
    offset = durations[0] - 1  # Start fade 1s before end of first scene

    for i in range(len(scene_paths) - 1):
        if i == 0:
            input_left = "0"
            input_right = "1"
        else:
            input_left = f"v{i}"
            input_right = str(i + 1)

        output = f"v{i+1}" if i < len(scene_paths) - 2 else "v_out"

        filters.append(
            f"[{input_left}][{input_right}]xfade=transition=fade:duration=1:offset={offset}[{output}]"
        )

        if i < len(scene_paths) - 2:
            offset += durations[i+1] - 1

    return ";".join(filters)


def overlay_product_images(video_path, product_images, overlay_configs, output_path):
    """
    Overlay product images at specified timestamps.

    overlay_configs = [
        {
            "imageIndex": 0,
            "timestamp": 8.0,
            "duration": 2.0,
            "position": "bottom-right",  # or "center", "top-left", etc.
            "size": 400  # width in pixels
        }
    ]
    """
    overlay_filters = []

    # Build position calculations
    position_map = {
        "bottom-right": "W-w-40:H-h-40",
        "bottom-left": "40:H-h-40",
        "top-right": "W-w-40:40",
        "top-left": "40:40",
        "center": "(W-w)/2:(H-h)/2"
    }

    current_input = "0:v"

    for idx, config in enumerate(overlay_configs):
        image_path = product_images[config['imageIndex']]
        size = config['size']
        position = position_map.get(config['position'], position_map['bottom-right'])
        start_time = config['timestamp']
        end_time = start_time + config['duration']

        # Scale image
        scale_filter = f"[{idx+1}]scale={size}:-1[img{idx}]"
        overlay_filters.append(scale_filter)

        # Overlay with time constraint
        output_label = f"v{idx}" if idx < len(overlay_configs) - 1 else "v_out"
        overlay_filter = f"[{current_input}][img{idx}]overlay={position}:enable='between(t,{start_time},{end_time})'[{output_label}]"
        overlay_filters.append(overlay_filter)

        current_input = output_label

    filter_complex = ";".join(overlay_filters)

    # Build ffmpeg command
    image_inputs = [f"-i {img}" for img in [product_images[c['imageIndex']] for c in overlay_configs]]

    subprocess.run([
        "ffmpeg",
        "-i", video_path,
        *" ".join(image_inputs).split(),
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
        "-c:v", "libx264",
        "-preset", "medium",
        output_path
    ])

    return output_path
```

### Audio Mixing Levels

**Voiceover**: 100% (primary, always clear)
**Music**: 30% (background, doesn't overpower voice)
**SFX**: 50% (noticeable but not dominant)

### Product Overlay Defaults

**Position**: Bottom-right corner (default)
**Size**: 400px width (maintains aspect ratio)
**Padding**: 40px from edges
**Duration**: 2 seconds per image (default)
**Animation**: Fade in/out (optional, can add later)

### Video Export Settings

**Codec**: H.264 (libx264) - universal compatibility
**Preset**: Medium (balanced speed/quality)
**CRF**: 23 (good quality, reasonable file size)
**Audio Codec**: AAC
**Audio Bitrate**: 192k (high quality)
**Resolution**: Maintained from source (1080p for Pro, 4K for Agency)

### Rationale
- Complete pipeline handles all composition needs
- Sequential steps ensure each phase completes before next
- Audio mixing levels optimized for professional ads
- Product overlays add brand value without overwhelming
- Crossfades provide polish
- Export settings balance quality and file size
- Modular design allows easy debugging and updates

---

## Summary: Complete Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL (with JSONB)
- **ORM**: SQLAlchemy
- **Job Queue**: RQ (Redis Queue)
- **Cache**: Redis
- **Storage**: AWS S3
- **Video Processing**: FFmpeg (via subprocess)

### External APIs
- **LLM**: OpenAI GPT-4 (chat, script generation)
- **Video**: Sora via Replicate API
- **Voiceover**: Replicate TTS (Bark/Coqui)
- **Music**: Suno AI (standalone API)
- **SFX**: Replicate audio or Freesound
- **LoRA Training**: Replicate (fine-tuning jobs)

### Frontend
- **Desktop**: Electron + React + TypeScript
- **Video Editor**: Existing Zapcut (local)
- **State**: Zustand with persist
- **Styling**: TailwindCSS + Glassmorphism
- **Icons**: Lucide React

### Infrastructure
- **Hosting**: AWS (EC2/ECS for backend)
- **Database**: AWS RDS PostgreSQL
- **Queue**: Redis (ElastiCache or self-hosted)
- **Storage**: AWS S3
- **CDN**: CloudFront (optional for static assets)

### Deployment
- **Backend**: Cloud-hosted FastAPI
- **Frontend**: Electron app (local)
- **Communication**: HTTPS REST API + HTTP polling
- **Video Loading**: Download-first from S3

---

## Next Steps

1. Set up development environment
   - Python/FastAPI backend scaffold
   - PostgreSQL database
   - Redis for RQ
   - S3 buckets (dev/staging/prod)

2. Implement authentication
   - User signup/login
   - JWT tokens
   - Session management

3. Build brand management
   - Brand CRUD APIs
   - Image upload to S3
   - Database integration

4. Develop chat interface
   - GPT-4 integration
   - 5-question flow
   - Conversation storage

5. Create script generation
   - Script generation prompts
   - Scene breakdown
   - Review UI

6. Build generation pipeline
   - RQ job orchestration
   - Sequential scene generation
   - Audio generation (voiceover, music, SFX)
   - FFmpeg composition

7. Implement LoRA training
   - Background job after first video
   - Preview generation
   - User approval flow

8. Integrate with Zapcut editor
   - Download generated videos
   - Load into editor
   - Link projects

9. Deploy to production
   - AWS infrastructure
   - CI/CD pipeline
   - Monitoring and logging

---

**Document Status:** Complete
**All Technical Decisions:** Validated
**Ready for:** Implementation Planning
