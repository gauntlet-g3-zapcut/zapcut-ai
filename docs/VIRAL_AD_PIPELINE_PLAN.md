# Viral Mobile App Ad Pipeline - V2 (Refined)

> **Last Updated:** November 2025
> **Status:** Ready for Implementation

## Goal
Create 40-second video ads for mobile apps with:
1. **Consistent story** - coherent narrative start to finish
2. **Consistent audio** - reliable narrator/voiceover throughout
3. **Consistent characters** - same person recognizable across all segments
4. **Clear marketing** - the app and its benefit are obvious
5. **Real app screenshots** - actual UI appears in the video

---

## Video Specs
- **Duration**: 40 seconds (5 segments × 8 seconds)
- **Resolution**: 1080p (1920×1080)
- **Aspect Ratio**: 16:9

---

## Pipeline Overview (V2)

```
┌─────────────────────────────────────────────────────────────┐
│  INPUTS                                                     │
│  • Creative Bible (app info, features, audience)            │
│  • Brand images (logo, product photos)                      │
│  • Campaign images (app screenshots - ACTUAL UI)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: Story Writing (GPT-4o Vision)                     │
│  - Analyzes app screenshots to understand UI                │
│  - Writes FULL narrative first (not segmented)              │
│  - Creates character descriptions, narrator style           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: Story Segmentation (GPT-4o)                       │
│  - Breaks narrative into 5 segments                         │
│  - Adds action, end_state, app_screen per segment           │
│  - Output: story_document JSON                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
         ┌──────────────────┴──────────────────┐
         ↓                                     ↓
┌─────────────────┐                 ┌─────────────────────────┐
│ STAGE 3A:       │                 │ STAGE 3B:               │
│ Voiceover (TTS) │                 │ Scene Images            │
│ ElevenLabs      │                 │ (Nano Banana)           │
│                 │                 │                         │
│ Full 40-sec     │                 │ Uses app screenshots    │
│ narration       │                 │ as reference images     │
└────────┬────────┘                 └────────────┬────────────┘
         ↓                                       ↓
┌─────────────────┐                 ┌─────────────────────────┐
│ Mix with music  │                 │ Upscale (Real-ESRGAN)   │
│ (existing)      │                 └────────────┬────────────┘
└────────┬────────┘                              ↓
         ↓                          ┌─────────────────────────┐
┌─────────────────┐                 │ STAGE 4: Sequential     │
│ final_audio_url │                 │ Video (Veo 3.1)         │
└────────┬────────┘                 │                         │
         │                          │ Seg1 → frame → Seg2 →   │
         │                          │ frame → Seg3 → frame →  │
         │                          │ Seg4 → frame → Seg5     │
         │                          │                         │
         │                          │ Uses:                   │
         │                          │ • image: scene/frame    │
         │                          │ • reference_images:     │
         │                          │   [app_screenshot,      │
         │                          │    character_ref]       │
         │                          └────────────┬────────────┘
         │                                       ↓
         └──────────────────┬────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STAGE 5: Assembly (FFmpeg)                                 │
│  - Concatenate 5 video segments                             │
│  - Add mixed audio (voiceover + music)                      │
│  - Add CTA overlay on segment 5                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
                     final_video_url
```

---

## Key Design Decisions (from brainstorming session)

### 1. Story-First Approach
**Decision:** Write the full story first, THEN segment it.
**Rationale:** Produces more natural narrative flow vs forcing GPT to think in segments upfront.

### 2. Voiceover Tool
**Decision:** ElevenLabs TTS (not Veo native audio)
**Rationale:** Veo generates different voices per API call. ElevenLabs uses consistent voice_id across all segments.

### 3. App Screenshots Integration
**Decision:** Hybrid approach using both Nano Banana and Veo reference images.
**Rationale:**
- GPT-4o Vision analyzes screenshots for accurate descriptions
- Nano Banana uses screenshots as subject reference
- Veo uses screenshots + character ref in `reference_images` parameter

### 4. Music
**Decision:** Keep existing ElevenLabs Music API (already implemented)
**Rationale:** Works well, matches scene energy. Mixed with voiceover in final audio.

---

## Phase 1: Input (from existing Creative Bible)

We already collect this via chat:
- App name & description
- Key features & core benefit
- Target audience
- Brand images/style
- **App screenshots** (campaign.images) ← Critical for V2

**No changes needed** - use existing creative bible data.

---

## Phase 2: Story Generation (Two-Step Process)

### Step 1: Story Writing (GPT-4o Vision)
Analyzes app screenshots and writes full narrative.

**Input:**
- Creative bible data
- App screenshots (sent to GPT-4o Vision)

**Output:**
```json
{
  "title": "Story concept name",
  "logline": "One sentence summary",
  "full_narrative": "We've all been there. The alarm screams... [full 40-sec script]",

  "characters": [
    {
      "id": "main",
      "name": "Sarah",
      "description": "Woman, early 30s, dark curly hair, warm brown skin, cream blazer over white tee, silver stud earrings"
    }
  ],

  "narrator": {
    "voice_style": "Warm, conversational female voice",
    "tone": "Empathetic, slightly playful",
    "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB"
  },

  "app_screens": [
    {
      "id": "dashboard",
      "url": "https://storage.../dashboard.png",
      "description": "Main dashboard with focus timer and daily stats"
    },
    {
      "id": "timer_active",
      "url": "https://storage.../timer.png",
      "description": "Active focus session with countdown"
    }
  ]
}
```

### Step 2: Story Segmentation (GPT-4o)
Breaks the narrative into 5 segments with visual details.

**Input:** Story from Step 1

**Output:** Adds `segments` array to story_document:

### Story Document Structure

```json
{
  "title": "Story concept name",
  "logline": "One sentence summary",

  "characters": [
    {
      "id": "main",
      "name": "Sarah",
      "description": "Woman, early 30s, dark curly hair, warm brown skin, cream blazer over white tee, silver stud earrings"
    }
  ],

  "narrator": {
    "voice_style": "Warm, conversational female voice",
    "tone": "Empathetic, slightly playful"
  },

  "segments": [
    {
      "number": 1,
      "narration": "We've all been there. The alarm screams, you hit snooze for the sixth time...",
      "action": "Sarah slams alarm, checks phone showing 47 emails, zombie-walks to kitchen, spills coffee",
      "end_state": "Sarah in kitchen, coffee stain on blazer, looking at phone notification",
      "app_moment": null
    },
    {
      "number": 2,
      "narration": "But what if today could be different?",
      "action": "Sarah taps notification, opens app, sees clean dashboard, taps 'Start Focus'",
      "end_state": "Sarah looking at phone with hopeful expression, app timer starting",
      "app_moment": "App opens, dashboard visible, START FOCUS button tapped"
    },
    {
      "number": 3,
      "narration": "FocusFlow doesn't just block distractions. It changes how you move through your day.",
      "action": "Montage: Sarah working focused, getting coffee with a smile, checking app showing progress",
      "end_state": "Sarah walking confidently down sunny street",
      "app_moment": "Quick shot of timer and progress stats"
    },
    {
      "number": 4,
      "narration": "And before you know it...",
      "action": "Sarah meets friend Maya in park, shows her the app excitedly, both laugh",
      "end_state": "Sarah and Maya looking at phone together, smiling",
      "app_moment": "Achievement screen: '2 Hour Focus Complete!'"
    },
    {
      "number": 5,
      "narration": "You're not just getting things done. You're getting your life back. FocusFlow. Start your free trial today.",
      "action": "Sunset, Sarah on balcony peaceful, app logo appears",
      "end_state": "App logo and 'Download Free' CTA",
      "app_moment": "Logo + CTA overlay"
    }
  ]
}
```

### Key Rules for Story Generation

1. **Character description is EXACT** - copy verbatim into every video prompt
2. **Narration is the audio backbone** - carries the story even if video varies
3. **Each segment has clear end_state** - this seeds the next segment
4. **App moments are specific** - what screen, what's visible
5. **Segment 5 has CTA** - always end with clear call to action

---

## Phase 3: Audio Generation (Before Video)

Generate audio FIRST. This ensures:
- Consistent narrator voice across all segments
- Audio timing drives video timing
- No sync issues

### Audio Components

1. **Voiceover** (ElevenLabs)
   - Generate full 40-second narration as one audio file
   - Use consistent voice ID throughout
   - Split into 5 segments by timestamp

2. **Music Bed** (ElevenLabs or Suno)
   - Single continuous track
   - Builds from minimal → full → resolving
   - Mixed at 30-40% under voiceover

3. **Final Audio Track**
   - Voiceover + Music mixed together
   - This becomes the audio for final video

**Note**: We do NOT rely on Veo's native audio. Voiceover provides consistency.

---

## Phase 4: Sequential Video Generation

### Prompt Templates

**These templates are used for EVERY video generation. No exceptions.**

#### Image Generation Prompt (Segment 1 only)
```
CHARACTERS:
{characters_block}

SCENE: {segment_1_action}

SETTING: {location_description}

STYLE: Photorealistic, cinematic lighting, 16:9 aspect ratio.
```

#### Video Prompt - Segment 1
```
CHARACTERS:
{characters_block}

ACTION: {segment_action}

END STATE: {end_state}

CAMERA: Cinematic, handheld, follows character naturally.
DURATION: 8 seconds.
```

#### Video Prompt - Segments 2-5 (Continuation)
```
CONTINUING EXACTLY FROM THE PROVIDED IMAGE.

CHARACTERS:
{characters_block}

ACTION: {segment_action}

END STATE: {end_state}

CAMERA: Cinematic, handheld, follows character naturally.
DURATION: 8 seconds.
```

#### Characters Block Format
```
- {name}: {description}
```

Example:
```
- Sarah: Woman, early 30s, dark curly hair, warm brown skin, cream blazer over white tee, silver stud earrings
- Maya: Woman, late 20s, straight black hair, East Asian, green sundress, minimalist jewelry
```

**The characters block is built ONCE from story_document.characters and used in EVERY prompt.**

---

### Segment 1: Generate from Image

1. **Generate starting image** (Flux/Nano Banana)
   - Use Image Generation Prompt template
   - Output: 1280×720 image

2. **Upscale image** (Real-ESRGAN)
   - 2x upscale to 2560×1440

3. **Generate video** (Veo 3.1)
   - Use Video Prompt - Segment 1 template
   - Image: upscaled_image_url
   - Duration: 8 seconds
   - Audio: disabled (we use our own)

4. **Extract last frame**
   ```bash
   ffmpeg -sseof -0.1 -i segment_1.mp4 -frames:v 1 -q:v 2 last_frame.png
   ```

### Segments 2-5: Generate from Previous Frame

For each segment N (2, 3, 4, 5):

1. **Use previous segment's last frame as seed image**
   - No new image generation needed
   - Ensures visual continuity

2. **Generate video** (Veo 3.1)
   - Use Video Prompt - Segments 2-5 template
   - Image: segment_(N-1)_last_frame_url
   - Duration: 8 seconds
   - Audio: disabled

3. **Extract last frame** (except segment 5)

### Flow
```
Image Gen → Segment 1 → extract frame →
            Segment 2 → extract frame →
            Segment 3 → extract frame →
            Segment 4 → extract frame →
            Segment 5 (final)
```

**This is sequential, not parallel.** Each segment depends on the previous.

---

## Phase 5: Assembly

### Step 1: Concatenate Videos
```bash
ffmpeg -f concat -safe 0 -i segments.txt \
  -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.1 \
  -crf 23 video_only.mp4
```

### Step 2: Add Audio Track
```bash
ffmpeg -i video_only.mp4 -i final_audio.mp3 \
  -c:v copy -c:a aac -b:a 192k \
  -map 0:v -map 1:a \
  -shortest final_ad.mp4
```

### Step 3: Add CTA Overlay (Segment 5)
- App logo
- "Download Free" or custom CTA
- App store badges (optional)

---

## What Makes This Consistent

| Element | How We Ensure Consistency |
|---------|--------------------------|
| **Story** | Single story document, generated once, drives everything |
| **Characters** | Exact description copied into EVERY video prompt |
| **Audio/Narration** | Generated once as continuous track, not per-segment |
| **Visual Flow** | Frame seeding - each segment starts from previous end frame |
| **Marketing Message** | Narration carries the message, video supports it |

---

## Database Changes

Add to Campaign model:
```python
story_document = Column(JSON)  # The story JSON above
voiceover_url = Column(String)  # Full narration audio
music_url = Column(String)      # Music bed
final_audio_url = Column(String)  # Mixed VO + music
current_segment = Column(Integer, default=0)  # Track sequential progress
```

---

## Implementation Files

### New:
- `backend/app/tasks/story_generation.py` - Generate story document
- `backend/app/tasks/voiceover_generation.py` - ElevenLabs narration
- `backend/app/services/frame_extraction.py` - FFmpeg last frame

### Modified:
- `backend/app/api/campaigns.py` - New pipeline trigger
- `backend/app/tasks/video_generation.py` - Sequential generation with frame seeding
- `backend/app/api/webhooks.py` - Handle sequential callbacks

---

## Timeline

- Story generation: ~10 seconds
- Audio generation: ~30 seconds
- Segment 1 (with image): ~3 minutes
- Segments 2-5: ~2 minutes each = ~8 minutes
- Assembly: ~30 seconds

**Total: ~12-15 minutes**

---

## What We're NOT Doing

1. ~~Multiple review personas~~ - One generation pass with good prompting
2. ~~Revision loops~~ - Get it right first time or flag for human
3. ~~Complex JSON structures~~ - Minimal fields that actually get used
4. ~~Veo native audio~~ - Unreliable, use our own voiceover
5. ~~Parallel generation~~ - Sequential is slower but consistent

---

## Resolved Questions

1. **App screen integration**: ✅ RESOLVED
   - Use hybrid approach: Nano Banana composites screenshots into scene images
   - Veo uses `reference_images` parameter with app screenshots for consistency
   - GPT-4o Vision analyzes screenshots for accurate descriptions

2. **Character drift**: If Veo drifts despite frame seeding, what's the fallback?
   - Use `reference_images` with character reference to maintain consistency
   - Narration carries the story even if visuals drift slightly

3. **Failure handling**: If segment 3 fails, do we restart from segment 2?
   - Retry same segment 2x with same seed frame. If still fails, flag for human.

---

## Implementation Plan

### Phase 1: Database & Model Changes

**File:** `backend/app/models/campaign.py`

Add new fields:
```python
story_document = Column(JSON, nullable=True)      # Full story with characters, narrator, segments
voiceover_url = Column(String, nullable=True)     # ElevenLabs TTS audio
voiceover_status = Column(String, nullable=True)  # pending/generating/completed/failed
final_audio_url = Column(String, nullable=True)   # Mixed voiceover + music
current_segment = Column(Integer, default=0)      # Track sequential progress
pipeline_version = Column(String, default="v2")   # "v1" (parallel) or "v2" (sequential)
```

**File:** `backend/migrations/versions/xxx_add_story_document_fields.py`
- Create Alembic migration for new fields

---

### Phase 2: Story Generation

**File:** `backend/app/tasks/story_generation.py` (NEW)

```python
@celery_app.task
def generate_story_task(campaign_id: str):
    """
    Two-step story generation:

    Step 1: Story Writing (GPT-4o Vision)
    - Analyze app screenshots
    - Write full 40-second narrative
    - Define characters and narrator

    Step 2: Segmentation (GPT-4o)
    - Break into 5 segments
    - Add action, end_state, app_screen for each

    Output: story_document saved to campaign
    Triggers: voiceover_generation + image_generation (parallel)
    """
```

---

### Phase 3: Voiceover Generation

**File:** `backend/app/tasks/voiceover_generation.py` (NEW)

```python
@celery_app.task
def generate_voiceover_task(campaign_id: str):
    """
    1. Concatenate all segment narrations from story_document
    2. Select ElevenLabs voice based on narrator.voice_style
    3. Generate full 40-second audio (single API call)
    4. Upload to S3
    5. Update campaign.voiceover_url
    """
```

**File:** `backend/app/tasks/audio_mixing.py` (NEW)

```python
@celery_app.task
def mix_final_audio_task(campaign_id: str):
    """
    1. Download voiceover + music (from existing audio_generation)
    2. Mix with FFmpeg (voiceover at 100%, music at 30%)
    3. Upload to S3
    4. Update campaign.final_audio_url
    """
```

---

### Phase 4: Image Generation Updates

**File:** `backend/app/tasks/image_generation.py` (MODIFY)

Update to use reference images:
```python
def generate_single_image_task(campaign_id, scene_num, image_prompt):
    # Get app screenshots from story_document.app_screens
    # Get character reference from first generated image (for scenes 2-5)

    input = {
        "prompt": scene_prompt,
        "reference_images": [
            app_screenshot_url,      # App UI as subject reference
            character_reference_url  # For character consistency
        ],
        "width": 1280,
        "height": 720
    }
```

---

### Phase 5: Sequential Video Generation

**File:** `backend/app/services/frame_extraction.py` (NEW)

```python
def extract_last_frame(video_url: str) -> str:
    """
    1. Download video from S3
    2. Extract last frame with FFmpeg:
       ffmpeg -sseof -0.1 -i video.mp4 -frames:v 1 -q:v 2 last_frame.png
    3. Upload frame to S3
    4. Return frame URL
    """
```

**File:** `backend/app/tasks/sequential_video.py` (NEW)

```python
@celery_app.task
def generate_segment_video_task(campaign_id: str, segment_num: int):
    """
    Sequential video generation (called one segment at a time):

    If segment 1:
        - Use Nano Banana scene image as starting frame
    Else:
        - Use previous segment's last frame (frame seeding)

    1. Call Veo 3.1 with:
       - image: starting_frame_url
       - reference_images: [app_screenshot, character_ref] (up to 3)
       - prompt: segment.action + segment.end_state
       - duration: 8
       - generate_audio: false

    2. On webhook completion:
       - Extract last frame
       - Update campaign.current_segment
       - Trigger next segment (if not last)
       - If last segment, trigger assembly
    """
```

---

### Phase 6: Webhook Updates

**File:** `backend/app/api/webhooks.py` (MODIFY)

Add sequential video handling:
```python
@router.post("/replicate/sequential-video")
async def sequential_video_webhook(...):
    """
    Handle Veo 3.1 completion for sequential pipeline:
    1. Download and store video
    2. Extract last frame (if not segment 5)
    3. Trigger next segment OR assembly
    """
```

---

### Phase 7: Assembly Updates

**File:** `backend/app/tasks/video_generation.py` (MODIFY)

Update `assemble_videos_basic_task`:
```python
def assemble_videos_basic_task(campaign_id: str):
    # Use final_audio_url (mixed voiceover + music) instead of just audio_url
    # Ensure segments are in order (1-5)
    # Add CTA overlay on segment 5 (optional - Phase 2)
```

---

### Phase 8: API Orchestration

**File:** `backend/app/api/campaigns.py` (MODIFY)

Update `approve_campaign` to trigger V2 pipeline:
```python
@router.post("/{campaign_id}/approve")
async def approve_campaign(...):
    if campaign.pipeline_version == "v2":
        # V2: Story-first sequential pipeline
        generate_story_task.delay(campaign_id)
        # Story task triggers everything else
    else:
        # V1: Legacy parallel pipeline (existing code)
        generate_enhanced_prompts_task.delay(campaign_id)
```

**File:** `backend/app/celery_app.py` (MODIFY)

Add new task modules:
```python
include=[
    'app.tasks.story_generation',      # NEW
    'app.tasks.voiceover_generation',  # NEW
    'app.tasks.audio_mixing',          # NEW
    'app.tasks.sequential_video',      # NEW
    'app.tasks.video_generation',
    'app.tasks.audio_generation',
    'app.tasks.prompt_generation',
    'app.tasks.image_generation',
]
```

---

## File Summary

| Action | File | Description |
|--------|------|-------------|
| MODIFY | `backend/app/models/campaign.py` | Add story_document, voiceover fields |
| CREATE | `backend/migrations/versions/xxx_add_story_fields.py` | Database migration |
| CREATE | `backend/app/tasks/story_generation.py` | Two-step story generation |
| CREATE | `backend/app/tasks/voiceover_generation.py` | ElevenLabs TTS |
| CREATE | `backend/app/tasks/audio_mixing.py` | FFmpeg voiceover + music mix |
| CREATE | `backend/app/services/frame_extraction.py` | FFmpeg last frame extraction |
| CREATE | `backend/app/tasks/sequential_video.py` | Sequential Veo generation |
| MODIFY | `backend/app/tasks/image_generation.py` | Add reference_images support |
| MODIFY | `backend/app/tasks/video_generation.py` | Update assembly for V2 |
| MODIFY | `backend/app/api/webhooks.py` | Add sequential video webhook |
| MODIFY | `backend/app/api/campaigns.py` | V2 pipeline trigger |
| MODIFY | `backend/app/celery_app.py` | Register new tasks |

---

## Implementation Order

1. Database changes (model + migration)
2. Story generation task
3. Voiceover generation task
4. Image generation updates (reference images)
5. Frame extraction service
6. Sequential video pipeline
7. Webhook updates
8. Audio mixing task
9. Assembly updates
10. API orchestration

**Estimated effort:** 2-3 days

---

## Testing Checklist

- [ ] Story generation produces valid story_document JSON
- [ ] GPT-4o Vision correctly analyzes app screenshots
- [ ] Voiceover generates consistent 40-second audio
- [ ] Nano Banana uses app screenshots as reference
- [ ] Frame extraction produces usable PNG
- [ ] Sequential video respects frame seeding
- [ ] Veo reference_images maintains character/UI consistency
- [ ] Audio mixing produces balanced voiceover + music
- [ ] Assembly concatenates in correct order
- [ ] Final video is 40 seconds with synced audio
