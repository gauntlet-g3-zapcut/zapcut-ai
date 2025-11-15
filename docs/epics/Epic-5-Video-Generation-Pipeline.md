# Epic 5: Video Generation Pipeline

**Status:** Not Started
**Priority:** P0 (MVP)
**Estimated Effort:** 4-5 weeks
**Dependencies:** Epic 1-4

---

## Epic Overview

### Value Proposition
Users get complete, AI-generated video ads from their approved scripts using orchestrated scene generation (Sora), voiceover (TTS), music (Suno), and video composition (FFmpeg).

### Success Criteria
- [ ] Sequential video generation per scene with scene continuity
- [ ] Voiceover generated for each scene
- [ ] Background music generated for full ad
- [ ] All assets composited into final MP4 video
- [ ] Real-time progress tracking (5-second polling)
- [ ] Video generation completes in 6-8 minutes
- [ ] Generated video includes product images as overlays
- [ ] User can preview and download final video

### Demo Scenario
1. User approves script (Epic 4)
2. Generation status page shows progress
3. Progress updates: Scene 1 → Scene 2 → Scene 3 → Audio → Music → Compositing
4. Each step shows estimated time remaining
5. After 6-8 minutes, "Your ad is ready!" with video player
6. User plays video, sees professional result
7. Click "Open in Editor" → Epic 6

---

## User Stories

### Story 5.1: Job Queue System
- RQ (Redis Queue) for sequential job orchestration
- Job creation on script approval
- Worker process picks up jobs
- **Backend:** RQ worker, job status tracking
- **Database:** `generation_jobs` table

### Story 5.2: Scene Video Generation (Sora)
- For each scene, call Replicate Sora API
- Sequential generation with previous scene reference for continuity
- Download generated videos to S3
- **Backend:** Replicate API integration, scene-to-scene prompting
- **Tasks:** ~2-3 minutes per scene

### Story 5.3: Voiceover Generation (TTS)
- Generate voiceover for all scenes using Replicate TTS (Bark/Coqui)
- One audio file per scene with narration
- **Backend:** TTS API integration
- **Tasks:** ~10 seconds per scene

### Story 5.4: Background Music (Suno)
- Generate 30-60 second background track
- Prompt based on brand tone and ad mood
- **Backend:** Suno API integration (standalone API)
- **Tasks:** ~30-60 seconds

### Story 5.5: Product Image Overlays
- Extract product images from brand
- Define overlay timestamps and positions (from script or AI)
- Prepare overlays for FFmpeg composition
- **Backend:** Overlay configuration generation

### Story 5.6: Video Composition (FFmpeg)
- Stitch scenes with 1-second crossfade transitions
- Overlay product images at specified times
- Mix audio: voiceover (100%), music (30%), SFX (50%)
- Export as MP4 (H.264, 1080p, 30fps)
- **Backend:** FFmpeg subprocess orchestration
- **Tasks:** ~60 seconds for composition

### Story 5.7: Progress Tracking UI
- Frontend polls `/generation-status` every 5 seconds
- Display progress bar (0-100%)
- Show current step and ETA
- Progress stages with checkmarks
- **Frontend:** GenerationStatusPage, ProgressBar, ProgressSteps

### Story 5.8: Video Preview & Download
- Success screen with video player
- "Download Video" button (save to local)
- "Open in Editor" button (Epic 6)
- **Frontend:** GenerationCompleteScreen, VideoPlayer

---

## Database Schema

```sql
CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'scene_video', 'voiceover', 'music', 'composite'
    scene_number INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    replicate_job_id VARCHAR(255),
    input_params JSONB,
    output_url TEXT, -- S3 URL
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_generation_jobs_project ON generation_jobs(ad_project_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);

-- Add to ad_projects
ALTER TABLE ad_projects
ADD COLUMN final_video_url TEXT,
ADD COLUMN generation_status VARCHAR(50) DEFAULT 'not_started';
```

---

## API Endpoints

```
POST /api/projects/:projectId/generate-video  -- Start generation
GET /api/projects/:projectId/generation-status  -- Poll status
GET /api/videos/:videoId  -- Get video URL
```

---

## Frontend Routes

```
/brands/:brandId/projects/:projectId/generate → GenerationStatusPage
/brands/:brandId/projects/:projectId/complete → GenerationCompleteScreen
```

---

## Backend Architecture

### Sequential Pipeline
```python
def generate_video(ad_project_id):
    """
    Orchestrates full video generation pipeline.
    Sequential execution ensures scene continuity.
    """
    project = get_project(ad_project_id)
    script = get_script(ad_project_id)

    # Step 1: Generate scene videos (sequential)
    scene_urls = []
    for i, scene in enumerate(script.scenes):
        job = create_job(ad_project_id, 'scene_video', i+1)
        update_status('processing')

        # Scene 1: base prompt
        # Scene 2+: include previous scene for continuity
        prompt = build_scene_prompt(scene, prev_scene=scene_urls[-1] if scene_urls else None)

        video_url = generate_scene_video(prompt, scene.duration)
        scene_urls.append(video_url)

        complete_job(job.id, video_url)

    # Step 2: Generate voiceover (parallel per scene or sequential)
    voiceover_urls = []
    for i, scene in enumerate(script.scenes):
        if scene.voiceoverText:
            audio_url = generate_voiceover(scene.voiceoverText)
            voiceover_urls.append(audio_url)

    # Step 3: Generate music
    music_url = generate_music(script.storyline, duration=sum(scene.duration for scene in script.scenes))

    # Step 4: Composite final video
    final_video = compose_video(
        scene_videos=scene_urls,
        voiceovers=voiceover_urls,
        music=music_url,
        product_images=get_brand_product_images(project.brand_id),
        transitions='crossfade',
        duration=1  # 1-second crossfade
    )

    # Step 5: Upload to S3
    s3_url = upload_to_s3(final_video, f"videos/{ad_project_id}.mp4")

    # Step 6: Update project
    update_project(ad_project_id, {
        'final_video_url': s3_url,
        'generation_status': 'completed',
        'status': 'completed'
    })

    return s3_url
```

### FFmpeg Composition
```python
def compose_video(scene_videos, voiceovers, music, product_images, transitions, duration):
    """
    FFmpeg pipeline for final video composition.
    """
    temp_dir = f"/tmp/zapcut_{uuid4()}"

    # Step 1: Stitch scenes with crossfade
    stitched_video = stitch_scenes_with_crossfade(scene_videos, duration)

    # Step 2: Overlay product images
    video_with_overlays = overlay_product_images(stitched_video, product_images)

    # Step 3: Mix audio
    final_video = mix_audio(
        video=video_with_overlays,
        voiceover=voiceovers,
        music=music,
        levels={'voiceover': 1.0, 'music': 0.3}
    )

    return final_video
```

---

## Testing Strategy

### Component Tests
- RQ job creation and execution
- Replicate API integration (mocked)
- FFmpeg composition (with sample assets)
- Progress calculation logic

### Integration Tests
- End-to-end pipeline with test script
- Polling mechanism
- Error recovery and retry

---

## Definition of Done

- [ ] All user stories completed
- [ ] Video generation pipeline functional
- [ ] Sequential scene generation with continuity
- [ ] Audio generation and mixing working
- [ ] FFmpeg composition reliable
- [ ] Progress tracking accurate
- [ ] Generated videos include brand product images
- [ ] Video quality meets standards (1080p, smooth playback)
- [ ] Generation time < 8 minutes for 30-second video
- [ ] Error handling and retry logic tested
- [ ] Code deployed and tested in staging
- [ ] Demo scenario executable

---

## Dependencies

**External:**
- Replicate API key (Sora, TTS models)
- Suno API key
- Redis for job queue
- FFmpeg installed on workers
- S3 bucket for generated assets

**Internal:**
- Epic 4 (need approved script)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sora API reliability/rate limits | High | Implement retry logic, queue management |
| Generation time exceeds 8 minutes | Medium | Optimize prompts, parallel where possible |
| FFmpeg composition failures | Medium | Extensive testing, fallback options |
| High S3 storage costs | Medium | Lifecycle policies, cleanup old files |

---

## References

- **PRD:** Section 3.5 (Video Generation Pipeline)
- **Technical Architecture:** Sections 10-15 (Job Orchestration, FFmpeg Pipeline)
- **UI Spec:** Screens 9-10 (Generation Status, Complete)
