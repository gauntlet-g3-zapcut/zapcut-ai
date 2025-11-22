# Video Improvements Plan

## Overview

This document outlines the enhanced video generation pipeline for ZapCut, implementing an image-first workflow with quality upscaling, image-to-video generation, and cinematic post-processing.

**Branch:** `videoImprovements`
**Created:** 2025-11-22

---

## Goals

1. **Ultra high quality** - Image-first approach for better consistency
2. **Cinematic polish** - Color grading, speed ramping, brand-matched colors
3. **User control** - "Surprise Me" vs "I'll Direct" modes
4. **Flexibility** - Switch from auto to manual mid-flow
5. **Viral & Funny** - Comedy-driven content that gets shared

---

## Technology Stack

| Step | Service | Model | Cost |
|------|---------|-------|------|
| Image Generation | Replicate | **Nano Banana** (`google/nano-banana`) | ~$0.039/image |
| Upscaling | Replicate | **Real-ESRGAN** (`nightmareai/real-esrgan`) | ~$0.01/image |
| Video Generation | Replicate | **Veo 3.1** (`google/veo-3.1`) image-to-video | ~$0.50/video |
| Post-Processing | Local | **FFmpeg** + LUTs | Free |
| Audio | ElevenLabs | Music Composition API | Existing |

---

## User Experience Modes

### ✨ "Surprise Me" (Default)

- One-click generation
- Auto-approves all steps
- ~5 minutes total
- User sees final result only
- Can switch to "I'll Direct" at any time

### 🎬 "I'll Direct"

- Review each checkpoint
- Approve/regenerate per scene
- ~15-20 minutes total
- Full creative control

### Switch Mid-Flow

Users start in "Surprise Me" mode but can click **"Take Control"** at any point to:
- Pause generation
- Review what's been created so far
- Regenerate specific scenes
- Edit prompts
- Resume or continue manually

---

## Pipeline Phases

```
PHASE 1: STORYLINE (Existing)
├── User edits scenes in StorylineReview
├── Clicks "Generate Video Ad"
└── Campaign status → "pending"

PHASE 2: PROMPT ENHANCEMENT (New)
├── GPT-4o generates per scene:
│   ├── image_prompt (detailed static description)
│   └── motion_prompt (camera/action description)
├── Store in campaign.image_prompts
└── Pipeline stage → "prompts_ready"

PHASE 3: IMAGE GENERATION (New)
├── Replicate: google/nano-banana
├── Input: image_prompt + product images as reference
├── Output: 1280x720 PNG (16:9 for Veo)
├── Webhook → Download → Upload to S3
└── Pipeline stage → "images_ready"

PHASE 4: UPSCALING (New)
├── Replicate: nightmareai/real-esrgan
├── Input: base image, scale=2
├── Output: 2560x1440 PNG
├── Webhook → Download → Upload to S3
└── Auto-triggers video generation

PHASE 5: VIDEO GENERATION (Modified)
├── Replicate: google/veo-3.1 (IMAGE-TO-VIDEO mode)
├── Input: {
│     "prompt": motion_prompt,
│     "image": upscaled_image_url,  ← New
│     "duration": 6,
│     "aspect_ratio": "16:9",
│     "resolution": "1080p",
│     "generate_audio": false
│   }
├── Webhook → Download → Upload to S3
└── Pipeline stage → "videos_ready"

PHASE 6: POST-PROCESSING (New)
├── FFmpeg: Apply cinematic LUT
├── FFmpeg: Shift colors toward brand palette
├── FFmpeg: Apply speed ramp based on energy curve
└── Upload processed videos to S3

PHASE 7: FINAL ASSEMBLY (New)
├── FFmpeg: Concatenate all processed videos
├── FFmpeg: Add transitions between scenes
├── FFmpeg: Mix with soundtrack
├── Upload final video to S3
└── Campaign status → "completed"
```

---

## API Endpoints

### Existing (No Changes)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/campaigns/` | Create campaign |
| GET | `/api/campaigns/{id}` | Get campaign details |
| GET | `/api/campaigns/{id}/status` | Get generation status |
| POST | `/api/campaigns/{id}/approve` | Approve draft, start generation |
| DELETE | `/api/campaigns/{id}` | Delete campaign |
| POST | `/webhooks/replicate` | Video generation webhook |

### New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/campaigns/{id}/take-control` | Switch to Director mode, pause generation |
| POST | `/api/campaigns/{id}/resume-auto` | Switch back to Surprise Me mode |
| POST | `/api/campaigns/{id}/approve-prompts` | Approve prompts, start image gen |
| POST | `/api/campaigns/{id}/approve-images` | Approve images, start upscale+video |
| POST | `/api/campaigns/{id}/approve-videos` | Approve videos, start post-processing |
| POST | `/api/campaigns/{id}/scenes/{num}/regenerate-image` | Regenerate single image |
| POST | `/api/campaigns/{id}/scenes/{num}/regenerate-video` | Regenerate single video |
| PUT | `/api/campaigns/{id}/scenes/{num}/prompts` | Edit image/motion prompts |
| POST | `/webhooks/replicate/image` | Image generation webhook |
| POST | `/webhooks/replicate/upscale` | Upscaling webhook |

### Modified Endpoints

| Method | Endpoint | Changes |
|--------|----------|---------|
| GET | `/api/campaigns/{id}/status` | Add image/upscale/processing status per scene |
| POST | `/api/campaigns/{id}/approve` | Now triggers prompt enhancement first |

---

## Database Model Changes

### Campaign Model - New Fields

```python
class Campaign(Base):
    # Existing fields...

    # NEW: Director mode
    director_mode = Column(String, nullable=True, default="surprise_me")
    # Values: "surprise_me" | "ill_direct"

    # NEW: Enhanced prompts per scene
    image_prompts = Column(JSON, nullable=True)
    # Structure: [
    #   {
    #     "scene_number": 1,
    #     "image_prompt": "Cinematic wide shot...",
    #     "motion_prompt": "Slow push-in camera..."
    #   }
    # ]

    # NEW: Pipeline stage tracking
    pipeline_stage = Column(String, nullable=True, default="pending")
    # Values: pending, prompts_generating, prompts_ready,
    #         images_generating, images_ready,
    #         upscaling, videos_generating, videos_ready,
    #         post_processing, assembling, completed, failed

    # NEW: Post-processing config
    color_grade_preset = Column(String, nullable=True, default="cinematic")
    brand_colors = Column(JSON, nullable=True)
```

### Enhanced video_urls Structure (Per Scene)

```python
{
    "scene_number": 1,

    # Prompts
    "image_prompt": "...",
    "motion_prompt": "...",
    "prompts_approved": False,

    # Image generation
    "base_image_url": "...",
    "image_status": "pending",  # pending/generating/completed/failed
    "image_prediction_id": "...",
    "image_approved": False,

    # Upscaling
    "upscaled_image_url": "...",
    "upscale_status": "pending",
    "upscale_prediction_id": "...",

    # Video generation
    "video_url": "...",
    "video_status": "pending",
    "video_prediction_id": "...",
    "video_approved": False,

    # Post-processing
    "processed_video_url": "...",
    "processing_status": "pending",

    # Metadata
    "duration": 6.0,
    "error": null,
    "retry_count": 0
}
```

---

## New Celery Tasks

| Task | File | Purpose |
|------|------|---------|
| `generate_enhanced_prompts_task` | `tasks/prompt_generation.py` | GPT-4o prompt enhancement |
| `generate_single_image_task` | `tasks/image_generation.py` | Nano Banana image gen |
| `upscale_single_image_task` | `tasks/image_generation.py` | Real-ESRGAN upscaling |
| `post_process_video_task` | `tasks/post_processing.py` | FFmpeg color/speed |
| `assemble_final_video_task` | `tasks/post_processing.py` | FFmpeg concat + audio |

### Modified Task

| Task | Changes |
|------|---------|
| `generate_single_scene_task` | Add `image` parameter for image-to-video mode |

---

## Frontend Changes

### Modified: StorylineReview.tsx

After generation starts, show review UI:
- Scene thumbnails with status indicators
- Image preview when ready
- Video preview when ready
- Approve/Regenerate buttons per scene

### Modified: VideoProgress.jsx

- "Take Control" button to switch modes
- Director Mode review UI
- Multi-phase progress indicators
- Live thumbnails as scenes complete

### Modified: api.ts

```typescript
// New methods
takeControl: (campaignId: string) => apiRequest(`/api/campaigns/${campaignId}/take-control`, { method: "POST" }),
resumeAuto: (campaignId: string) => apiRequest(`/api/campaigns/${campaignId}/resume-auto`, { method: "POST" }),
approvePrompts: (campaignId: string) => apiRequest(`/api/campaigns/${campaignId}/approve-prompts`, { method: "POST" }),
approveImages: (campaignId: string) => apiRequest(`/api/campaigns/${campaignId}/approve-images`, { method: "POST" }),
approveVideos: (campaignId: string) => apiRequest(`/api/campaigns/${campaignId}/approve-videos`, { method: "POST" }),
regenerateImage: (campaignId: string, sceneNum: number) => apiRequest(`/api/campaigns/${campaignId}/scenes/${sceneNum}/regenerate-image`, { method: "POST" }),
regenerateVideo: (campaignId: string, sceneNum: number) => apiRequest(`/api/campaigns/${campaignId}/scenes/${sceneNum}/regenerate-video`, { method: "POST" }),
updateScenePrompts: (campaignId: string, sceneNum: number, prompts: { image_prompt: string, motion_prompt: string }) => apiRequest(`/api/campaigns/${campaignId}/scenes/${sceneNum}/prompts`, { method: "PUT", body: JSON.stringify(prompts) }),
```

---

## Review UI Design

### Progress Page with "Take Control"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Generating your video...                                                   │
│                                                                             │
│  ████████████████░░░░░░  75%                                               │
│                                                                             │
│  ✓ Prompts generated                                                        │
│  ✓ Images created                                                           │
│  ● Creating videos... (4/5)                                                 │
│  ○ Adding cinematic polish                                                  │
│                                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │  [img]  │ │  [img]  │ │  [img]  │ │  [img]  │ │  [img]  │ ← Live       │
│  │   ✓     │ │   ✓     │ │   ✓     │ │   ◠     │ │   ◠     │   preview   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────── │
│  Not what you expected?                                                     │
│                                                                             │
│  [🎬 Take Control]                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Director Mode Review

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  🎬 You're now directing                                                    │
│                                                                             │
│  Generation paused. Review what we have so far:                             │
│                                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │  [img]  │ │  [img]  │ │  [img]  │ │  [vid]  │ │ pending │              │
│  │         │ │         │ │         │ │         │ │         │              │
│  │ [Keep]  │ │ [Keep]  │ │ [Redo]  │ │ [Keep]  │ │ [Edit]  │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│   Scene 1     Scene 2     Scene 3     Scene 4     Scene 5                  │
│   Image ✓     Image ✓     Image ✓     Video ✓     Pending                  │
│                                                                             │
│  Click any scene to:                                                        │
│  • View full size                                                           │
│  • Edit the prompt                                                          │
│  • Regenerate image or video                                                │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  [← Back to Auto]              [Continue with changes →]                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Edge Cases & Failure Handling

| Scenario | Handling |
|----------|----------|
| Nano Banana fails | Retry 3x, then mark image failed, allow manual regenerate |
| Upscaling fails | Retry 3x, fallback to using base image for video gen |
| Veo rejects image | Retry with adjusted prompt, or fallback to text-to-video |
| FFmpeg crashes | Retry, skip post-processing if persistent failure |
| User regenerates during processing | Cancel in-flight prediction, start new one |
| User deletes campaign during generation | Webhook returns 200 OK, logs "campaign not found" |
| Partial scene failures | Allow proceeding with completed scenes |
| S3 upload fails | Retry 3x with exponential backoff |
| Brand has no product images | Use text-only prompt for Nano Banana |
| User clicks "Take Control" | Pause generation, show current state |
| User clicks "Back to Auto" | Resume from current state |

---

## Implementation Checklist

### Phase 1: Database & Models
- [ ] Add `director_mode` field to Campaign model
- [ ] Add `image_prompts` JSON field to Campaign model
- [ ] Add `pipeline_stage` string field to Campaign model
- [ ] Add `color_grade_preset` string field to Campaign model
- [ ] Add `brand_colors` JSON field to Campaign model
- [ ] Create Alembic migration
- [ ] Run migration

### Phase 2: Backend Tasks
- [ ] Create `backend/app/tasks/prompt_generation.py`
  - [ ] `generate_enhanced_prompts_task(campaign_id)`
- [ ] Create `backend/app/tasks/image_generation.py`
  - [ ] `start_image_generation_task(campaign_id)`
  - [ ] `generate_single_image_task(campaign_id, scene_num)`
  - [ ] `upscale_single_image_task(campaign_id, scene_num)`
- [ ] Create `backend/app/tasks/post_processing.py`
  - [ ] `post_process_videos_task(campaign_id)`
  - [ ] `assemble_final_video_task(campaign_id)`
- [ ] Modify `backend/app/tasks/video_generation.py`
  - [ ] Update `generate_single_scene_task` to accept `image` parameter
  - [ ] Build image-to-video Replicate input

### Phase 3: Webhooks
- [ ] Create `/webhooks/replicate/image` endpoint
- [ ] Create `/webhooks/replicate/upscale` endpoint
- [ ] Update webhook URL builders for new endpoints

### Phase 4: API Endpoints
- [ ] Create `POST /api/campaigns/{id}/take-control`
- [ ] Create `POST /api/campaigns/{id}/resume-auto`
- [ ] Modify `POST /api/campaigns/{id}/approve` to trigger prompt generation
- [ ] Add `POST /api/campaigns/{id}/approve-prompts`
- [ ] Add `POST /api/campaigns/{id}/approve-images`
- [ ] Add `POST /api/campaigns/{id}/approve-videos`
- [ ] Add `POST /api/campaigns/{id}/scenes/{num}/regenerate-image`
- [ ] Add `POST /api/campaigns/{id}/scenes/{num}/regenerate-video`
- [ ] Add `PUT /api/campaigns/{id}/scenes/{num}/prompts`
- [ ] Modify `GET /api/campaigns/{id}/status` for new fields

### Phase 5: Frontend API Service
- [ ] Add `takeControl()` method
- [ ] Add `resumeAuto()` method
- [ ] Add `approvePrompts()` method
- [ ] Add `approveImages()` method
- [ ] Add `approveVideos()` method
- [ ] Add `regenerateImage()` method
- [ ] Add `regenerateVideo()` method
- [ ] Add `updateScenePrompts()` method

### Phase 6: Frontend UI
- [ ] Update VideoProgress.jsx
  - [ ] Add "Take Control" button
  - [ ] Add Director Mode review UI
  - [ ] Show live thumbnails during generation
  - [ ] Multi-phase progress indicators
- [ ] Add scene detail modal
  - [ ] Full-size image/video preview
  - [ ] Edit prompts
  - [ ] Regenerate buttons

### Phase 7: Infrastructure
- [ ] Ensure FFmpeg is installed (Docker)
- [ ] Bundle default cinematic LUT file
- [ ] Test end-to-end flow

---

## Post-Processing Details

### Cinematic Color Grading
- Apply base cinematic LUT (orange/teal film look)
- Shift colors 20% toward dominant brand color
- Preserve skin tones

### Speed Ramping (Energy-Based)
- Energy < 0.3 → 0.7x slow motion
- Energy 0.3-0.7 → 1.0x normal speed
- Energy > 0.7 → 1.3x speed up
- Smooth transitions between speed changes

### Scene Transitions
- Cross-dissolve between scenes (0.5s)
- Optional: Match cut on movement

---

## Rollback Plan

If issues arise:
1. `git checkout main` - Switch back to stable main branch
2. `git branch -D videoImprovements` - Delete feature branch entirely
3. Database: Revert Alembic migration if applied

The `main` branch remains untouched until explicit merge.

---

## Viral Comedy System

### The Science of Viral Content

| Factor | Why It Works | Implementation |
|--------|--------------|----------------|
| **Pattern interrupt** | Brain notices unexpected things | Hook templates for scene 1 |
| **Emotional spike** | Strong emotion = share impulse | Comedy escalation engine |
| **Identity signaling** | "This is SO me" → share | Hyper-specific scenarios |
| **Social currency** | Sharing makes you look funny | Quotable lines |
| **Incompleteness** | Brain wants closure | Callbacks from scene 5 to scene 1 |

### The Viral Ad Formula

```
HOOK (0-2 sec)     → Pattern interrupt, "wait what?"
ESCALATE (2-20 sec) → Each beat raises stakes/absurdity
PAYOFF (20-26 sec)  → The laugh, the twist, the "ohhhh"
CTA (26-30 sec)     → Download, but make it funny too
```

---

## Comedy Director Personas

Users select a "Comedy Director" that shapes the entire ad's humor style:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Who should direct your ad?                                                 │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  🦉 DUOLINGO    │  │  🎭 THE OFFICE  │  │  🌀 ADULT SWIM  │            │
│  │                 │  │                 │  │                 │            │
│  │  Chaotic brand  │  │  Awkward cringe │  │  Absurdist      │            │
│  │  energy, weird  │  │  comedy, dry    │  │  fever dream,   │            │
│  │  but lovable    │  │  humor, pauses  │  │  unhinged       │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  📱 TIKTOK      │  │  🎬 MARVEL      │  │  😐 DEADPAN     │            │
│  │                 │  │                 │  │                 │            │
│  │  Trend-aware,   │  │  Epic setup,    │  │  Dry delivery,  │            │
│  │  quick cuts,    │  │  undercut with  │  │  contrast       │            │
│  │  meme format    │  │  humor          │  │  visuals        │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Director Persona Definitions

```python
COMEDY_DIRECTORS = {
    "duolingo": {
        "name": "Duolingo Energy",
        "description": "Chaotic brand that's somehow endearing",
        "prompt_injection": """
            Write like the Duolingo owl's unhinged marketing team:
            - Brand has WAY too much personality
            - Slightly threatening undertones played for laughs
            - Self-aware about being annoying
            - Chaos that somehow makes you love them
            - Example energy: "You missed your Spanish lesson. We know where you live. 🙂"
        """,
        "visual_style": "Bright colors, mascot energy, text overlays with attitude"
    },

    "the_office": {
        "name": "The Office",
        "description": "Cringe comedy, awkward pauses, documentary style",
        "prompt_injection": """
            Write like a mockumentary:
            - Uncomfortable silences that say everything
            - Characters who lack self-awareness
            - Cut to reaction shots (Jim face to camera)
            - Mundane situations treated with dramatic weight
            - The humor is in the discomfort
        """,
        "visual_style": "Documentary framing, natural lighting, zoom-ins on reactions"
    },

    "adult_swim": {
        "name": "Adult Swim",
        "description": "Absurdist, surreal, fever dream energy",
        "prompt_injection": """
            Write like a 2am Adult Swim bump:
            - Logic is optional
            - Non-sequiturs are welcome
            - Surreal imagery that somehow makes sense
            - Deadpan delivery of insane statements
            - The viewer should think "what am I watching" but keep watching
        """,
        "visual_style": "Surreal imagery, unexpected juxtapositions, liminal spaces"
    },

    "tiktok": {
        "name": "TikTok Native",
        "description": "Trend-aware, quick cuts, meme-literate",
        "prompt_injection": """
            Write for the TikTok generation:
            - Use current meme formats (POV, Nobody:, etc.)
            - Quick cuts, no wasted frames
            - Text overlays are part of the joke
            - Sound/music sync is crucial
            - Would make sense in a "sounds" trend
            - Caption should be quotable
        """,
        "visual_style": "Vertical-friendly, text overlays, trend-aware aesthetics"
    },

    "marvel": {
        "name": "Marvel Undercut",
        "description": "Epic buildup deflated with humor",
        "prompt_injection": """
            Write like a Marvel movie trailer that becomes a comedy:
            - Start with DRAMATIC epic energy
            - Slow-mo, orchestral music vibes
            - Then completely undercut it with mundane reality
            - "All that drama... for a to-do app"
            - The joke is the contrast between setup and payoff
        """,
        "visual_style": "Cinematic, dramatic lighting, then mundane reality"
    },

    "deadpan": {
        "name": "Deadpan",
        "description": "Dry delivery, contrast is the comedy",
        "prompt_injection": """
            Write with bone-dry delivery:
            - Say absurd things with complete seriousness
            - No winking at the camera
            - The visuals are chaotic but delivery is calm
            - Contrast between what's said and what's shown
            - Example: "Everything is fine" [building collapsing behind them]
        """,
        "visual_style": "Chaos in background, calm subject in foreground"
    }
}
```

---

## Hook Templates (Scene 1)

The first 2 seconds MUST stop the scroll:

| Hook Type | Example | Best For |
|-----------|---------|----------|
| **False premise** | "This is a nature documentary about the rare Organized Human" | Productivity apps |
| **Chaos opening** | Start with explosion/screaming, then "Let me explain" | Any app |
| **Relatable attack** | "POV: You said you'd do it tomorrow. It's been 3 years." | Habit/task apps |
| **Confident lie** | "I have never once forgotten anything" [everything on fire] | Memory/reminder apps |
| **Meme format** | "Nobody: ... Me at 3am:" | Any app |
| **Direct address** | "You. Yes you. You have 47 unread emails." | Productivity |

---

## Escalation Engine

Each scene must be MORE ridiculous than the last:

```
Scene 1: Normal situation (relatable)
         ↓ escalate
Scene 2: Mild exaggeration ("that's me!")
         ↓ escalate
Scene 3: Getting absurd ("okay this is funny")
         ↓ escalate
Scene 4: Completely unhinged ("LMAO I need to share this")
         ↓ resolve
Scene 5: Sudden resolution + callback to scene 1
```

### Escalation Prompts for GPT

```
"Each scene must be MORE ridiculous than the last.
Scene 3 should make the viewer think 'okay this is silly'
Scene 4 should make them think 'this is unhinged and I love it'
The escalation should feel like a snowball rolling downhill."
```

---

## Specificity Generator

Generic = forgettable. Specific = viral.

| Generic (Bad) | Specific (Good) |
|---------------|-----------------|
| "Busy professional" | "You, at 11:47pm, wondering if you replied to that email from Tuesday" |
| "Saves time" | "Reclaim the 3 hours you spend panicking about whether you locked the door" |
| "Easy to use" | "If you can doom-scroll, you can use this" |
| "Stay organized" | "Finally remember your dentist appointment (the one you've rescheduled 4 times)" |

---

## Viral Mechanics

### 1. The Callback/Loop

End connects to beginning → rewatchable → more views

```
Scene 1: "I'll just check one email"
Scene 5: "I'll just check one email" [1000 yard stare]
```

### 2. The Quotable Line

Every ad needs ONE line people will repeat:

```
"I've made a terrible mistake" (Arrested Development energy)
"This is fine" (meme reference)
"We don't talk about [thing]" (trend reference)
```

### 3. The Screenshot Moment

Scene 3 or 4 should work as a meme still image:

```
Person surrounded by floating tasks, dead inside
Before/after split that's absurdly dramatic
Text overlay that's funny out of context
```

### 4. The Sound Bite

Audio moment that's satisfying/funny:

```
*ding* of task completion (ASMR satisfying)
Record scratch at the twist
Dramatic music that stops abruptly
```

---

## Enhanced Storyline Generation Prompt

```python
VIRAL_STORYLINE_PROMPT = """
You are a viral content strategist creating a 30-second mobile app ad.

APP: {app_name}
CATEGORY: {app_category}
PAIN POINT: {pain_point}
COMEDY DIRECTOR: {comedy_director}

{comedy_director_prompt_injection}

VIRAL REQUIREMENTS:
1. HOOK (Scene 1): Must stop the scroll in 2 seconds
   - Pattern interrupt or "wait what?" moment
   - No slow buildup - grab attention immediately

2. ESCALATION (Scenes 2-4): Each scene more ridiculous than last
   - Scene 2: Mild exaggeration (relatable)
   - Scene 3: Getting absurd (that's funny)
   - Scene 4: Completely unhinged (I need to share this)

3. PAYOFF (Scene 5): The laugh + CTA
   - Callback to scene 1 if possible
   - CTA should be funny, not generic

4. QUOTABLE LINE: Include one line people will repeat

5. SCREENSHOT MOMENT: Scene 3 or 4 should work as a meme still

6. SPECIFICITY: No generic situations
   - BAD: "Busy professional"
   - GOOD: "You at 2am wondering if you replied to that email"

VIRALITY CHECKLIST (verify before output):
- [ ] Does scene 1 stop the scroll?
- [ ] Is there an actual laugh moment (not just a smile)?
- [ ] Would someone tag a friend?
- [ ] Is there a quotable line?
- [ ] Does it subvert expectations?
- [ ] Would it work without sound?

OUTPUT FORMAT:
For each scene:
- title: Short punchy title
- description: What happens (funny)
- visual_notes: Specific imagery for AI generation
- text_overlay: Any on-screen text (part of the joke)
- audio_cue: Sound effect or music note
- energy: 0.0-1.0 for pacing
- quotable_line: If this scene has the quotable moment

Also provide:
- hook_type: What kind of hook is scene 1
- callback_setup: How scene 5 connects to scene 1
- screenshot_scene: Which scene works as a still meme
- tiktok_sound_suggestion: What trending sound would fit
"""
```

---

## Visual Comedy Prompts for Nano Banana

```python
def enhance_image_prompt_for_comedy(base_prompt: str, comedy_director: str) -> str:

    comedy_visual_additions = {
        "duolingo": "Exaggerated expressions, bright saturated colors, slight menacing energy",
        "the_office": "Documentary-style framing, character looking at camera, mundane office setting",
        "adult_swim": "Surreal elements, unexpected objects in frame, liminal space aesthetic",
        "tiktok": "Vertical-friendly composition, space for text overlay, trendy aesthetic",
        "marvel": "Dramatic cinematic lighting, epic composition, lens flare",
        "deadpan": "Chaos in background, calm subject in foreground, contrast"
    }

    return f"{base_prompt}. {comedy_visual_additions.get(comedy_director, '')}. Photorealistic, high detail, comedic timing captured in still frame."
```

---

## Motion Prompts for Comedy

```python
COMEDY_MOTION_PATTERNS = {
    "zoom_to_face": "Slow zoom into character's face, deadpan expression",
    "chaos_calm": "Background exploding/chaotic while subject remains perfectly still",
    "whip_pan": "Fast pan to reveal unexpected element",
    "slow_mo_mundane": "Dramatic slow motion of completely ordinary action",
    "record_scratch": "Freeze frame moment for text overlay",
    "jim_look": "Character slowly turns to look at camera"
}
```

---

## Example Viral Storyline

**App:** TaskBuster (task management)
**Comedy Director:** Adult Swim
**Pain Point:** Forgetting important tasks

| Scene | Title | Description | Visual | Text Overlay | Audio |
|-------|-------|-------------|--------|--------------|-------|
| 1 | "Day 1" | Person at clean desk, optimistic | Bright, organized desk, person smiling | "Day 1 of being organized" | Upbeat music |
| 2 | "Day 3" | Same desk, slight mess. Person twitching. One plant dying. | Desk messier, person's smile forced | "Day 3" | Music slightly off-key |
| 3 | "Day ???" | Person in forest, feral, desk is there somehow, on fire | Surreal forest scene, burning desk, person has leaves in hair | "I don't know what day it is" | Distorted music |
| 4 | "The Prophecy" | Phone descends from clouds. App notification glows. Person weeps. | Heavenly light, phone floating down, person on knees | "The ancient texts spoke of this" | Choir singing |
| 5 | "Day 1" | Back at desk. Clean. Person suspicious. Doesn't trust it. | Same as scene 1 but person looks traumatized | "I'm afraid to jinx it. But... TaskBuster." | Silence, then *ding* |

**Quotable line:** "I don't know what day it is"
**Screenshot moment:** Scene 3 (forest/burning desk)
**Callback:** "Day 1" → "Day 1" (but different energy)

---

## Database Model Additions for Comedy

### Creative Bible - New Fields

```python
creative_bible = {
    # Existing fields...
    "brand_style": "modern",
    "vibe": "energetic",
    "colors": ["#FF5733"],

    # NEW: Comedy settings
    "comedy_director": "adult_swim",  # duolingo | the_office | adult_swim | tiktok | marvel | deadpan
    "humor_level": "high",            # subtle | medium | high | unhinged

    # NEW: Mobile app specific
    "app_category": "productivity",   # productivity | finance | social | game | health | utility
    "main_pain_point": "forgetting tasks",
    "magic_moment": "one-tap task completion"
}
```

### Enhanced Scene Structure

```python
{
    "scene_number": 1,
    "title": "Day 1",
    "description": "...",
    "visual_notes": "...",

    # NEW: Comedy fields
    "text_overlay": "Day 1 of being organized",
    "audio_cue": "upbeat_music",
    "quotable_line": null,  # or the line if this scene has it
    "is_screenshot_moment": false,

    # Existing
    "energy_start": 0.3,
    "energy_end": 0.5,
    "duration": 6.0
}
```

### Campaign Model - New Fields

```python
class Campaign(Base):
    # Existing fields...

    # NEW: Comedy metadata
    comedy_director = Column(String, nullable=True)
    hook_type = Column(String, nullable=True)
    quotable_line = Column(String, nullable=True)
    screenshot_scene = Column(Integer, nullable=True)
    callback_setup = Column(String, nullable=True)
```

---

## App Screenshot Integration

### The Problem

Current AI video generation will:
- Generate generic/blurry phone screens
- Make up fake UI that doesn't match the real app
- Lose text legibility
- Create inconsistent app visuals across scenes

### The Solution: Screenshot-First Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER UPLOADS                                                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ Screen1 │ │ Screen2 │ │ Screen3 │ │ Screen4 │ │ Screen5 │              │
│  │ Onboard │ │ Main UI │ │ Feature │ │ Success │ │ Result  │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│       ↓           ↓           ↓           ↓           ↓                    │
│  Scene 1      Scene 2     Scene 3     Scene 4     Scene 5                  │
│                                                                             │
│  Each scene uses the REAL screenshot, composited into the video            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Hybrid Approach (Recommended)

1. **Hero shots** (scenes showing the app): Composite real screenshots in post-processing
2. **Reaction shots** (person reacting): Phone in background/hand with embedded mockup
3. **Context shots** (environment): No phone needed

---

### Screenshot Upload & Mapping

```python
# User uploads screenshots with scene mapping
screenshots = [
    {
        "id": "uuid",
        "scene_number": 1,
        "screenshot_url": "https://.../onboarding.png",
        "screen_action": "static",  # static | scroll_down | scroll_up | tap | swipe_left | swipe_right
        "highlight_area": null,  # Optional: {x, y, width, height} to zoom/highlight
        "caption": "Sign up in 10 seconds",  # Optional text overlay on screen
        "mockup_url": "https://.../mockup1.png"  # Generated phone mockup
    },
    {
        "id": "uuid",
        "scene_number": 3,
        "screenshot_url": "https://.../main_dashboard.png",
        "screen_action": "scroll_down",
        "highlight_area": {"x": 100, "y": 200, "width": 200, "height": 100},
        "caption": null,
        "mockup_url": "https://.../mockup3.png"
    }
]
```

### Scene Types

| Scene Type | Screenshot Usage | Generation Approach |
|------------|------------------|---------------------|
| **App Demo** | Full screen, clear | Composite in post |
| **Hand Holding Phone** | Visible but smaller | Embed in Nano Banana reference |
| **Reaction Shot** | Phone in background/pocket | Minimal/none |
| **Problem Scene** | No phone (showing the pain) | None |
| **Solution Reveal** | Phone appears dramatically | Composite with animation |

### Phone Mockup Generator

```python
def create_phone_mockup(
    screenshot_url: str,
    phone_model: str = "iphone_15",  # iphone_15 | pixel_8 | samsung_s24 | generic
    orientation: str = "portrait",   # portrait | landscape
    angle: str = "front",            # front | slight_left | slight_right | hand_held
    shadow: bool = True
) -> str:
    """
    Embeds screenshot into a phone frame mockup.
    Returns URL to the composite image.
    """
    pass
```

### Screen Animations

```python
SCREEN_ANIMATIONS = {
    "static": "No movement, screenshot displayed as-is",
    "scroll_down": "Content scrolls up (finger swipe down gesture)",
    "scroll_up": "Content scrolls down (finger swipe up gesture)",
    "tap": "Ripple effect at tap point, brief highlight",
    "swipe_left": "Screen slides left, next screen slides in",
    "swipe_right": "Screen slides right, previous screen slides in",
    "zoom_in": "Zoom into highlight_area",
    "pulse_highlight": "Gentle pulse animation on highlight_area"
}
```

### FFmpeg Screen Replacement Pipeline

```python
def composite_screenshot_into_video(
    video_path: str,
    screenshot_path: str,
    screen_mask_path: str,  # Where to place the screenshot
    animation: str,
    output_path: str
) -> str:
    """
    1. Detect phone screen area in video (green screen or AI detection)
    2. Track screen position across frames
    3. Perspective-transform screenshot to match screen angle
    4. Composite screenshot onto video
    5. Apply screen animation
    6. Add screen glow/lighting to match scene
    """
    pass
```

---

### Updated Pipeline with Screenshots

```
PHASE 0: SCREENSHOT UPLOAD (New)
├── User uploads 3-5 app screenshots
├── User maps screenshots to scenes
├── User selects screen actions per scene
├── System generates phone mockups
└── Store in campaign.screenshots

PHASE 2: PROMPT ENHANCEMENT (Modified)
├── GPT-4o generates prompts WITH screenshot context
├── Prompts specify: "phone showing [screenshot description]"
├── Prompts indicate phone position: "hand holding phone", "phone on desk", etc.
└── Store screenshot_scene_type per scene

PHASE 3: IMAGE GENERATION (Modified)
├── For app demo scenes: Generate with phone mockup as reference
├── Nano Banana input includes phone mockup image
└── Output: Scene with phone, screen may be placeholder

PHASE 5: VIDEO GENERATION (Modified)
├── For scenes with screenshots: Use green/solid screen placeholder
├── Veo generates natural phone movement
└── Screen content added in post-processing

PHASE 6: POST-PROCESSING (Modified)
├── FFmpeg: Screen detection and tracking
├── FFmpeg: Screenshot composite with perspective correction
├── FFmpeg: Screen animation (scroll, tap, etc.)
├── FFmpeg: Apply screen glow/lighting to match scene
└── Continue with color grading, speed ramps
```

---

### Screenshot Quality Requirements

```python
SCREENSHOT_REQUIREMENTS = {
    "min_width": 1080,      # Minimum pixel width
    "min_height": 1920,     # Minimum pixel height (for portrait)
    "aspect_ratios": ["9:16", "9:19.5", "9:20"],  # Common phone ratios
    "formats": ["png", "jpg", "webp"],
    "max_file_size_mb": 10,
    "recommendations": [
        "Use actual device screenshots, not mockups",
        "Capture at highest resolution available",
        "Remove status bar if possible (we'll add generic one)",
        "Ensure text is readable at 50% size",
        "Avoid sensitive user data in screenshots"
    ]
}
```

---

### UI: Screenshot Upload & Scene Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Upload Your App Screenshots                                                │
│                                                                             │
│  These will appear in your video. Upload 3-5 key screens.                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │     [+] Drop screenshots here or click to upload                    │   │
│  │                                                                     │   │
│  │     PNG, JPG • Min 1080x1920 • Max 10MB each                       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Uploaded Screenshots:                                                      │
│                                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                          │
│  │ ░░░░░░░ │ │ ░░░░░░░ │ │ ░░░░░░░ │ │   [+]   │                          │
│  │ Screen1 │ │ Screen2 │ │ Screen3 │ │  Add    │                          │
│  │ ✓ Scene1│ │ ✓ Scene3│ │ ✓ Scene5│ │  more   │                          │
│  │ [Edit]  │ │ [Edit]  │ │ [Edit]  │ │         │                          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Screenshot Detail Modal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Configure Screenshot                                           [× Close]   │
│                                                                             │
│  ┌───────────────────┐  Which scene should show this screen?               │
│  │                   │                                                      │
│  │    [Screenshot    │  [Scene 1 ▼] Hook - The Problem                     │
│  │     Preview]      │                                                      │
│  │                   │  What happens on screen?                             │
│  │                   │                                                      │
│  └───────────────────┘  ( ) Static - just display                          │
│                         (•) Scroll down - show more content                 │
│                         ( ) Tap - highlight a button/feature                │
│                         ( ) Swipe - transition to next screen               │
│                                                                             │
│                         Highlight area? (optional)                          │
│                         [ ] Draw box to zoom/highlight                      │
│                                                                             │
│                         [Cancel]                    [Save]                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Database Additions for Screenshots

#### Campaign Model

```python
class Campaign(Base):
    # Existing fields...

    # NEW: Screenshot data
    screenshots = Column(JSON, nullable=True)
    # Structure: [
    #   {
    #     "id": "uuid",
    #     "url": "https://.../screenshot1.png",
    #     "scene_number": 1,
    #     "screen_action": "scroll_down",
    #     "highlight_area": {"x": 100, "y": 200, "width": 200, "height": 100},
    #     "caption": "Sign up in seconds",
    #     "mockup_url": "https://.../mockup1.png"
    #   }
    # ]

    phone_model = Column(String, nullable=True, default="iphone_15")
```

#### Scene Structure Addition

```python
{
    "scene_number": 1,
    # Existing fields...

    # NEW: Screenshot integration
    "screenshot_id": "uuid-of-screenshot",  # Reference to campaign.screenshots
    "scene_type": "app_demo",  # app_demo | hand_holding | reaction | problem | solution_reveal
    "phone_position": "center_frame",  # center_frame | hand_right | hand_left | desk | floating
    "screen_visible": True
}
```

---

### Screenshot API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/campaigns/{id}/screenshots` | Upload screenshots |
| PUT | `/api/campaigns/{id}/screenshots/{screenshot_id}` | Update screenshot config |
| DELETE | `/api/campaigns/{id}/screenshots/{screenshot_id}` | Remove screenshot |
| POST | `/api/campaigns/{id}/screenshots/{screenshot_id}/generate-mockup` | Generate phone mockup |

---

## Implementation Checklist - Comedy System

### Phase 8: Comedy System
- [ ] Add comedy_director field to CreativeBible model
- [ ] Add humor_level field to CreativeBible model
- [ ] Add app_category field to CreativeBible model
- [ ] Add main_pain_point field to CreativeBible model
- [ ] Add comedy fields to Campaign model
- [ ] Create comedy director selection UI in onboarding
- [ ] Implement COMEDY_DIRECTORS prompt injections
- [ ] Add hook template selection logic
- [ ] Implement escalation engine in storyline generation
- [ ] Add specificity generator for generic → specific conversion
- [ ] Add viral checklist validation to storyline output
- [ ] Enhance image prompts with comedy visual styles
- [ ] Add motion pattern selection for video generation
- [ ] Implement text_overlay field for scenes
- [ ] Add audio_cue field for post-processing sync

### Phase 9: Screenshot Integration
- [ ] Add screenshots JSON field to Campaign model
- [ ] Add phone_model field to Campaign model
- [ ] Create screenshot upload API endpoint
- [ ] Implement screenshot validation (size, format, dimensions)
- [ ] Create phone mockup generator service
- [ ] Add screenshot-to-scene mapping UI
- [ ] Add screen action selector UI (static, scroll, tap, swipe)
- [ ] Modify prompt generation to include screenshot context
- [ ] Modify image generation to use phone mockups as reference
- [ ] Implement FFmpeg screen tracking and replacement
- [ ] Implement screen animations (scroll, tap, swipe, zoom)
- [ ] Add screen glow/lighting matching in post-processing
- [ ] Add highlight area selection UI
- [ ] Implement perspective correction for angled phones

---

## Future Enhancements (Out of Scope)

- [ ] Kling/Hailuo integration for even better image-to-video
- [ ] Magnific AI for superior upscaling
- [ ] Beat-synced speed ramping
- [ ] Custom LUT upload
- [ ] A/B testing different video versions
- [ ] AI-powered auto-retouch (replace Photoshop step)
