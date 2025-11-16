# Epic 5: Video Generation Pipeline (Updated Implementation)

**Status:** In Progress
**Priority:** P0 (MVP)
**Estimated Effort:** 6-7 hours
**Dependencies:** Epic 1-4 (Completed by previous team)

---

## Epic Overview

### Value Proposition
Users get complete, AI-generated video ads from their approved scripts using orchestrated scene generation (Sora), voiceover (TTS), music (Suno), and video composition (FFmpeg). Building on existing infrastructure from Epics 1-4.

### What We're Building On (Already Exists)
- ✅ Celery task queue infrastructure
- ✅ Campaign and Brand database models
- ✅ Replicate API integration (Sora, Suno, image generation)
- ✅ Supabase Storage for asset uploads
- ✅ Basic FFmpeg video composition
- ✅ Frontend: StorylineReview page with "Generate Video" button
- ✅ Frontend: VideoProgress polling page
- ✅ Frontend: VideoPlayer component
- ✅ API endpoints structure (`/api/campaigns/`)

### What We're Adding (Epic 5 Completion)
- 🔨 Wire "Generate Video" button to backend API
- 🔨 Voiceover generation (TTS) per scene
- 🔨 Product image overlays with timestamps
- 🔨 Enhanced FFmpeg: crossfade transitions + audio mixing
- 🔨 Granular job tracking (`generation_jobs` table)
- 🔨 Sequential scene generation for continuity
- 🔨 Real-time progress stages (0-100%)

### Success Criteria
- [x] Campaign creation via "Generate Video" button triggers pipeline
- [ ] Sequential video generation per scene with scene continuity
- [ ] Voiceover generated for each scene with narration text
- [ ] Background music generated for full ad (Suno)
- [ ] All assets composited into final MP4 video
- [ ] Real-time progress tracking with granular stages
- [ ] Video generation completes in 6-8 minutes
- [ ] Generated video includes product images as overlays
- [ ] 1-second crossfade transitions between scenes
- [ ] Audio mixing: voiceover (100%), music (30%)
- [ ] User can preview and download final video
- [ ] Job tracking in database for debugging/monitoring

### Demo Scenario
1. User reviews storyline on StorylineReview page
2. User clicks "Generate Video Ad" button
3. API creates campaign and starts Celery task
4. Progress page shows granular updates:
   - "Generating reference images..." (10%)
   - "Creating storyboard..." (20%)
   - "Generating scene 1/5..." (28%)
   - "Generating scene 2/5..." (36%)
   - ... through all 5 scenes
   - "Generating voiceovers..." (65%)
   - "Composing soundtrack..." (75%)
   - "Composing final video..." (90%)
5. After 6-8 minutes, "Your ad is ready!" (100%)
6. User redirected to VideoPlayer
7. User watches video with crossfades, voiceover, music, product overlays
8. User can download or proceed to editor (Epic 6)

---

## User Stories

### Story 5.1: Wire Frontend to Backend Pipeline
**What:** Connect "Generate Video" button to actually trigger video generation
**Status:** Not Started (Priority 1)

**Tasks:**
- Update `StorylineReview.jsx` `handleApprove()` to call `api.createCampaign()`
- Pass `brand_id` and `creative_bible_id` to API
- Navigate to `/campaigns/{campaign_id}/progress` with real ID
- Handle error states (API down, validation errors)

**Files to Modify:**
- `frontend/src/pages/StorylineReview.jsx:70-73`

**Acceptance Criteria:**
- Button click creates campaign in database
- Celery task starts automatically
- User navigates to progress page with real campaign ID
- Loading state shown while API call in flight

---

### Story 5.2: Enhanced Job Queue & Tracking System
**What:** Add `generation_jobs` table for granular job tracking
**Status:** Not Started (Priority 1)

**Tasks:**
- Create database migration for `generation_jobs` table
- Create `GenerationJob` SQLAlchemy model
- Add `generation_stage` and `generation_progress` to `campaigns` table
- Update pipeline to create job records for each step

**Database Schema:**
```sql
CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,  -- 'scene_video', 'voiceover', 'music', 'composite'
    scene_number INTEGER,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    replicate_job_id VARCHAR(255),
    input_params JSONB,
    output_url TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_generation_jobs_campaign ON generation_jobs(campaign_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);

-- Add to campaigns table
ALTER TABLE campaigns
ADD COLUMN voiceover_urls JSONB,
ADD COLUMN generation_stage VARCHAR(50) DEFAULT 'not_started',
ADD COLUMN generation_progress INTEGER DEFAULT 0;
```

**Files to Create:**
- `backend/app/models/generation_job.py` (NEW)
- `backend/migrations/add_generation_jobs.sql` (NEW)

**Files to Modify:**
- `backend/app/models/campaign.py` (add new columns)
- `backend/app/tasks/video_generation.py` (create job records)

**Acceptance Criteria:**
- `generation_jobs` table created successfully
- Job records created for each scene, voiceover, music, composite step
- Jobs track start/end times and status
- Failed jobs capture error messages
- Campaign progress updates 0-100%

---

### Story 5.3: Sequential Scene Video Generation with Continuity
**What:** Change parallel scene generation to sequential, passing previous scene for visual continuity
**Status:** Not Started (Priority 2)

**Current Behavior:**
- Uses `generate_videos_parallel()` - all 5 scenes start simultaneously

**New Behavior:**
- Generate scenes sequentially (1 → 2 → 3 → 4 → 5)
- Pass previous scene URL to next scene as continuity reference
- Create `generation_job` record per scene
- Update progress after each scene (20% → 28% → 36% → 44% → 52% → 60%)

**Tasks:**
- Replace parallel generation loop with sequential
- Modify `generate_video_with_sora()` to accept `prev_scene_url` parameter
- Build scene prompts with continuity context
- Create job tracking per scene

**Files to Modify:**
- `backend/app/tasks/video_generation.py:112-136`
- `backend/app/services/replicate_service.py:50-91` (add prev_scene param)

**Acceptance Criteria:**
- Scenes generate one at a time (not parallel)
- Scene 2-5 prompts reference previous scene for continuity
- Progress updates after each scene completes
- Total scene generation: ~10-15 minutes for 5 scenes

---

### Story 5.4: Voiceover Generation (TTS)
**What:** Generate voiceover audio for each scene using Replicate TTS
**Status:** Not Started (Priority 2)

**Tasks:**
- Add `generate_voiceover()` to `replicate_service.py`
- Add `generate_voiceovers_parallel()` for batch processing
- Extract voiceover text from `campaign.storyline.scenes[].voiceover_text`
- Generate TTS audio for each scene with narration
- Upload voiceover files to Supabase Storage
- Store URLs in `campaign.voiceover_urls` JSONB field

**Model:**
- Using `suno-ai/bark` on Replicate for TTS

**Files to Modify:**
- `backend/app/services/replicate_service.py` (add TTS functions)
- `backend/app/tasks/video_generation.py` (add voiceover step)

**Acceptance Criteria:**
- Voiceover generated for each scene with narration text
- Audio files uploaded to Supabase Storage
- URLs stored in `campaign.voiceover_urls`
- Generation stage shows "Generating voiceovers..." (65%)
- Empty/missing voiceover text handled gracefully

---

### Story 5.5: Product Image Overlays
**What:** Overlay brand product images on video at specified timestamps
**Status:** Not Started (Priority 2)

**Tasks:**
- Create `add_product_overlays()` FFmpeg function
- Fetch product images from `brand.product_image_1_url` and `brand.product_image_2_url`
- Download product images during composition
- Overlay product 1 at 5-8 seconds (bottom-right, 200px wide)
- Overlay product 2 at 15-18 seconds (bottom-right, 200px wide)
- Scale images maintaining aspect ratio

**FFmpeg Filter:**
```bash
[1:v]scale=200:-1[ovr1];
[0:v][ovr1]overlay=W-w-20:H-h-20:enable='between(t,5,8)'[v1];
[2:v]scale=200:-1[ovr2];
[v1][ovr2]overlay=W-w-20:H-h-20:enable='between(t,15,18)'[v2]
```

**Files to Modify:**
- `backend/app/tasks/video_generation.py` (add overlay function)

**Acceptance Criteria:**
- Product image 1 appears at 5s for 3 seconds
- Product image 2 appears at 15s for 3 seconds
- Images scaled to 200px width, positioned bottom-right
- Images maintain aspect ratio
- Missing product images handled gracefully

---

### Story 5.6: Enhanced FFmpeg Video Composition
**What:** Upgrade basic video concat to professional composition with crossfades and audio mixing
**Status:** Not Started (Priority 2)

**Current Behavior:**
- Simple concat of 5 scenes
- Basic music overlay

**New Behavior:**
- 1-second crossfade transitions between scenes
- Audio mixing: voiceover (100%) + music (30%)
- Product image overlays
- Professional output (H.264, 1080p, 30fps)

**Tasks:**
- Replace `compose_video()` with `compose_video_enhanced()`
- Create `create_crossfade_video()` - xfade filter for N scenes
- Create `concatenate_audio()` - join voiceover files
- Create `mix_audio_tracks()` - mix voiceover + music (100% + 30%)
- Create `add_product_overlays()` - overlay product images
- Create `combine_video_audio()` - merge video + mixed audio

**FFmpeg Commands:**
```bash
# Crossfade transitions
ffmpeg -i scene1.mp4 -i scene2.mp4 -i scene3.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=1:offset=5[v01];
                   [v01][2:v]xfade=transition=fade:duration=1:offset=10[vout]" \
  -map "[vout]" output.mp4

# Audio mixing
ffmpeg -i voiceover.mp3 -i music.mp3 \
  -filter_complex "[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2[aout]" \
  -map "[aout]" mixed.mp3
```

**Files to Modify:**
- `backend/app/tasks/video_generation.py:223-294` (replace entire function)

**Acceptance Criteria:**
- Scenes transition with 1-second crossfade (not hard cut)
- Voiceover audible at 100% volume
- Music audible underneath at 30% volume
- Product images overlay correctly
- Final video: H.264, 1080p, 30fps, smooth playback
- Composition completes in ~60 seconds

---

### Story 5.7: Background Music Generation
**What:** Generate 30-second background track with Suno
**Status:** ✅ Already Implemented

**No changes needed** - existing code already:
- Calls `generate_music_with_suno(campaign.suno_prompt)`
- Uploads to Supabase Storage
- Stores in `campaign.music_url`

**Files:**
- `backend/app/services/replicate_service.py:93-127`
- `backend/app/tasks/video_generation.py:139-149`

---

### Story 5.8: Granular Progress Tracking UI
**What:** Show detailed progress stages instead of generic "Generating..."
**Status:** Not Started (Priority 3)

**Current Behavior:**
- Generic "Generating..." message
- No progress percentage

**New Behavior:**
- Detailed stage names
- Progress bar 0-100%
- Estimated time remaining per stage

**Tasks:**
- Update `GET /api/campaigns/{id}/status` to return `stage` and `progress`
- Update `VideoProgress.jsx` to show granular stages
- Add progress bar component
- Map stage names to user-friendly text

**Progress Stages:**
```javascript
reference_images: 10%  "Generating reference images..."
storyboard: 20%        "Creating storyboard..."
scene_videos: 60%      "Generating scene X/5..."
voiceovers: 65%        "Generating voiceovers..."
music: 75%             "Composing soundtrack..."
compositing: 90%       "Composing final video..."
complete: 100%         "Your ad is ready!"
```

**Files to Modify:**
- `backend/app/api/campaigns.py:117-121` (add stage/progress to response)
- `frontend/src/pages/VideoProgress.jsx:59-92` (granular stages)

**Acceptance Criteria:**
- Progress bar updates smoothly 0 → 100%
- Stage text updates as pipeline progresses
- Poll every 5 seconds
- Auto-redirect to video player at 100%

---

### Story 5.9: Video Preview & Download
**What:** User can watch and download final video
**Status:** ✅ Already Implemented

**No changes needed** - existing code already has:
- VideoPlayer component with playback controls
- Navigation from VideoProgress → VideoPlayer
- Video URL from campaign

**Files:**
- `frontend/src/pages/VideoPlayer.jsx`
- `frontend/src/pages/VideoProgress.jsx:24-28` (auto-navigation)

**Enhancement (Optional):**
- Add explicit "Download Video" button
- Add "Open in Editor" button (Epic 6)

---

## Database Schema Summary

### New Table: `generation_jobs`
Tracks individual job execution for debugging and monitoring.

### Modified Table: `campaigns`
Added fields:
- `voiceover_urls` (JSONB) - URLs for scene voiceovers
- `generation_stage` (VARCHAR) - Current pipeline stage
- `generation_progress` (INTEGER) - Progress percentage 0-100

---

## API Endpoints

### Existing (No Changes)
```
POST /api/campaigns/                        # Create campaign, start generation
GET /api/campaigns/{campaign_id}            # Get campaign details
```

### Modified
```
GET /api/campaigns/{campaign_id}/status     # Add: stage, progress fields
Response:
{
  "campaign_id": "uuid",
  "status": "generating",
  "stage": "scene_videos",           // NEW
  "progress": 45,                    // NEW (0-100)
  "final_video_url": null
}
```

---

## Frontend Routes

### Existing (No Changes)
```
/brands/:brandId/storyline-review           # Review script, click "Generate"
/campaigns/:campaignId/progress             # Progress tracking
/campaigns/:campaignId/video                # Video player
```

---

## Backend Pipeline Flow

```python
def generate_campaign_video(campaign_id):
    # STEP 1: Reference images (10%) - EXISTING
    if not creative_bible.reference_image_urls:
        campaign.generation_stage = "reference_images"
        campaign.generation_progress = 5
        generate_reference_images(...)
        campaign.generation_progress = 10

    # STEP 2: Storyline (20%) - EXISTING
    if not campaign.storyline:
        campaign.generation_stage = "storyboard"
        campaign.generation_progress = 15
        generate_storyline_and_prompts(...)
        campaign.generation_progress = 20

    # STEP 3: Scene videos SEQUENTIAL (20-60%) - MODIFIED
    campaign.generation_stage = "scene_videos"
    prev_scene_url = None
    for i in range(1, 6):
        create_generation_job("scene_video", i)
        video_url = generate_video_with_sora(scene_prompt, prev_scene_url)
        prev_scene_url = video_url
        campaign.generation_progress = 20 + (i * 8)
        complete_generation_job(job_id, video_url)

    # STEP 4: Voiceovers PARALLEL (60-70%) - NEW
    campaign.generation_stage = "voiceovers"
    campaign.generation_progress = 60
    voiceover_urls = generate_voiceovers_parallel(scenes_with_text)
    campaign.voiceover_urls = voiceover_urls
    campaign.generation_progress = 70

    # STEP 5: Music (70-80%) - EXISTING
    campaign.generation_stage = "music"
    music_url = generate_music_with_suno(suno_prompt)
    campaign.music_url = music_url
    campaign.generation_progress = 80

    # STEP 6: Compose (80-100%) - ENHANCED
    campaign.generation_stage = "compositing"
    final_video = compose_video_enhanced(
        scene_videos=video_urls,
        voiceovers=voiceover_urls,
        music=music_url,
        product_images=[brand.product_image_1_url, brand.product_image_2_url]
    )
    # Includes: crossfades, audio mixing, product overlays

    campaign.final_video_url = upload_to_supabase(final_video)
    campaign.status = "completed"
    campaign.generation_stage = "complete"
    campaign.generation_progress = 100
```

---

## File Changes Summary

### New Files (3)
1. `backend/app/models/generation_job.py` - Job tracking model
2. `backend/migrations/add_generation_jobs.sql` - Database migration
3. Helper functions in existing files (no new files needed)

### Modified Files (6)
1. `backend/app/tasks/video_generation.py`
   - Add job tracking
   - Change parallel → sequential scenes
   - Add voiceover step
   - Replace `compose_video()` with enhanced version

2. `backend/app/services/replicate_service.py`
   - Add `generate_voiceover()`
   - Add `generate_voiceovers_parallel()`
   - Modify `generate_video_with_sora()` to accept prev_scene

3. `backend/app/models/campaign.py`
   - Add `voiceover_urls` column
   - Add `generation_stage` column
   - Add `generation_progress` column

4. `backend/app/api/campaigns.py`
   - Modify `/status` endpoint to return `stage` and `progress`

5. `frontend/src/pages/StorylineReview.jsx`
   - Wire `handleApprove()` to `api.createCampaign()`
   - Add loading state
   - Navigate with real campaign ID

6. `frontend/src/pages/VideoProgress.jsx`
   - Add granular stage display
   - Add progress bar
   - Map stage names to user-friendly text

---

## Testing Strategy

### Component Tests
- Job creation and tracking in database
- Voiceover generation (with mock Replicate)
- Product overlay FFmpeg command
- Crossfade FFmpeg command
- Audio mixing FFmpeg command
- Progress calculation logic

### Integration Tests
- End-to-end pipeline with test campaign
- Sequential scene generation order
- Voiceover → music → composition flow
- Progress polling updates correctly
- Error handling and retry

### Manual Testing Checklist
- [ ] Click "Generate Video" creates campaign
- [ ] Progress page shows 0-100% correctly
- [ ] Each stage name displays correctly
- [ ] Scenes generate sequentially (not parallel)
- [ ] Voiceovers audible in final video
- [ ] Music plays underneath at 30%
- [ ] Product images appear at 5s and 15s
- [ ] Crossfade transitions visible between scenes
- [ ] Final video downloads successfully
- [ ] Video quality: 1080p, 30fps, smooth playback

---

## Definition of Done

- [ ] All 9 user stories completed
- [ ] Database migration applied successfully
- [ ] "Generate Video" button triggers backend
- [ ] Video generation pipeline runs end-to-end
- [ ] Sequential scene generation with continuity working
- [ ] Voiceovers generated and mixed into final video
- [ ] Music generated and mixed at 30% volume
- [ ] Product images overlay at correct timestamps
- [ ] Crossfade transitions between scenes
- [ ] Progress tracking shows 0-100% with stages
- [ ] Generated video meets quality standards (1080p, smooth)
- [ ] Generation time < 8 minutes for 30-second video
- [ ] Error handling tested (API failures, timeouts)
- [ ] Code reviewed and tested in local environment
- [ ] Demo scenario executable

---

## Dependencies

### External Services (Already Configured)
- ✅ Replicate API key (Sora, TTS, Suno models)
- ✅ Supabase Storage for assets
- ✅ Redis for Celery queue
- ✅ FFmpeg installed on backend
- ✅ PostgreSQL database

### Internal (Epics 1-4)
- ✅ Epic 1: Infrastructure deployed
- ✅ Epic 2: Authentication & brands
- ✅ Epic 3: AI chat & creative bible
- ✅ Epic 4: Script generation & review

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sora API rate limits during sequential generation | High | Add retry logic, exponential backoff |
| Voiceover TTS quality/accent issues | Medium | Test with multiple TTS models, allow regeneration |
| FFmpeg crossfade complexity/failures | Medium | Extensive local testing, fallback to concat |
| Generation time exceeds 8 minutes | Medium | Optimize prompts, monitor performance |
| High Supabase storage costs | Low | Lifecycle policies, cleanup old campaigns |

---

## Estimated Timeline

| Story | Effort | Priority |
|-------|--------|----------|
| 5.1: Wire frontend to backend | 45 mins | P1 |
| 5.2: Job tracking system | 1 hour | P1 |
| 5.3: Sequential scene generation | 1 hour | P2 |
| 5.4: Voiceover generation | 1 hour | P2 |
| 5.5: Product overlays | 45 mins | P2 |
| 5.6: Enhanced FFmpeg composition | 2 hours | P2 |
| 5.8: Granular progress UI | 30 mins | P3 |
| Testing & debugging | 1.5 hours | P3 |
| **Total** | **~7 hours** | |

---

## References

- **Original Epic 5 Spec:** `docs/epics/Epic-5-Video-Generation-Pipeline.md`
- **Existing Pipeline:** `backend/app/tasks/video_generation.py`
- **Replicate Services:** `backend/app/services/replicate_service.py`
- **Campaign Model:** `backend/app/models/campaign.py`
- **Frontend Entry Point:** `frontend/src/pages/StorylineReview.jsx`
