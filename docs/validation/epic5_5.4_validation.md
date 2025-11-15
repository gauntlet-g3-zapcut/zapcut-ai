# Story 5.4 Validation Guide: Voiceover Generation (TTS)

## 30-Second Quick Test
1. Trigger campaign with scenes containing voiceover_text
2. Monitor generation_jobs: `SELECT * FROM generation_jobs WHERE job_type = 'voiceover';`
3. Check campaign.voiceover_urls is populated: `SELECT voiceover_urls FROM campaigns WHERE id = '...';`
4. Verify audio files uploaded to Supabase Storage

## Automated Tests
```python
# Test voiceover generation
from app.services.replicate_service import generate_voiceover, generate_voiceovers_parallel

# Test single voiceover
result = generate_voiceover("Welcome to our product showcase", 1)
assert result["scene_number"] == 1
assert result["url"] is not None
assert result["text"] == "Welcome to our product showcase"

# Test parallel generation
scenes = [
    {"scene_number": 1, "voiceover_text": "Scene 1 narration"},
    {"scene_number": 2, "voiceover_text": "Scene 2 narration"},
    {"scene_number": 3, "voiceover_text": ""}  # Empty text
]

results = generate_voiceovers_parallel(scenes)
assert len(results) == 3
assert results[0]["url"] is not None
assert results[1]["url"] is not None
assert results[2]["url"] is None  # Skipped due to empty text
```

## Manual Validation Steps

### Test Voiceover Generation
1. **Create Test Campaign:**
   ```json
   {
     "brand_id": "...",
     "creative_bible_id": "...",
     "storyline": {
       "scenes": [
         {
           "scene_number": 1,
           "voiceover_text": "Introducing our revolutionary new product",
           "description": "Product showcase"
         },
         {
           "scene_number": 2,
           "voiceover_text": "Experience unmatched quality and performance",
           "description": "Feature highlights"
         }
       ]
     }
   }
   ```

2. **Monitor Generation:**
   ```sql
   -- Watch voiceover jobs
   SELECT scene_number, status, input_params->>'text' as text, output_url
   FROM generation_jobs
   WHERE job_type = 'voiceover' AND campaign_id = '...'
   ORDER BY scene_number;

   -- Check campaign voiceover_urls
   SELECT voiceover_urls FROM campaigns WHERE id = '...';
   ```

3. **Verify Audio Files:**
   - Check Supabase Storage bucket "videos"
   - Files named: `campaigns/{campaign_id}/voiceover_1.mp3`, etc.
   - Verify files are playable

4. **Check Progress:**
   ```sql
   SELECT generation_stage, generation_progress
   FROM campaigns
   WHERE id = '...';

   -- Should show:
   -- generation_stage: 'voiceovers' (during generation) → 'music' (after)
   -- generation_progress: 60% → 70%
   ```

### Test Edge Cases

#### Empty Voiceover Text
```json
{
  "scene_number": 3,
  "voiceover_text": ""
}
```
- Expected: Job created with status "completed"
- Expected: voiceover_urls[2] = None
- Expected: No Replicate API call made

#### Missing voiceover_text Field
```json
{
  "scene_number": 4,
  "description": "Fallback to description"
}
```
- Expected: Uses scene.description as voiceover text
- Expected: Generates voiceover from description

#### Special Characters in Text
```json
{
  "voiceover_text": "Welcome! Try our product—it's amazing. 50% off today!"
}
```
- Expected: Handles punctuation correctly
- Expected: TTS pronounces properly

#### Very Long Text
```json
{
  "voiceover_text": "..." // 500+ words
}
```
- Expected: Bark TTS may truncate or fail
- Expected: Error captured in generation_job.error_message

### Test TTS Quality
1. **Download Generated Audio:**
   ```bash
   wget {voiceover_url} -O test_voiceover.mp3
   ```

2. **Play and Verify:**
   ```bash
   ffplay test_voiceover.mp3
   ```

3. **Check Audio Properties:**
   ```bash
   ffprobe test_voiceover.mp3
   # Expected: MP3 format, ~5-15 seconds duration
   ```

### Test Parallel Execution
1. **Time Multiple Voiceovers:**
   - 5 voiceovers in parallel should complete in ~same time as 1
   - Not sequential (would be 5x longer)

2. **Verify All Jobs Created:**
   ```sql
   SELECT COUNT(*) FROM generation_jobs
   WHERE job_type = 'voiceover' AND campaign_id = '...';
   -- Should equal number of scenes with text
   ```

## Performance Metrics
- Single voiceover: ~10-30 seconds (Replicate processing)
- 5 voiceovers in parallel: ~10-30 seconds total
- Upload to Supabase: <1 second per file

## Acceptance Criteria Checklist
- [x] Voiceover generated for each scene with narration text
- [x] Audio files uploaded to Supabase Storage
- [x] URLs stored in `campaign.voiceover_urls`
- [x] Generation stage shows "Generating voiceovers..." (65%)
- [x] Empty/missing voiceover text handled gracefully
- [x] GenerationJob records created for tracking
- [x] Failed voiceovers captured with error messages
- [x] Progress updates from 60% → 70%

## Rollback Plan
```bash
# Revert code changes
git checkout HEAD~1 -- backend/app/services/replicate_service.py
git checkout HEAD~1 -- backend/app/tasks/video_generation.py

# Remove voiceover_urls from campaigns (optional - doesn't break anything)
# ALTER TABLE campaigns DROP COLUMN IF EXISTS voiceover_urls;

# Restart Celery
celery -A app.celery_app worker --restart
```

## Files Modified
- `backend/app/services/replicate_service.py`
  - Added `generate_voiceover(text, scene_number)`
  - Added `generate_voiceovers_parallel(scenes_with_text)`
- `backend/app/tasks/video_generation.py`
  - Added voiceover generation step (Step 4)
  - Extract voiceover_text from storyline.scenes
  - Create GenerationJob records for voiceovers
  - Upload voiceovers to Supabase
  - Store URLs in campaign.voiceover_urls

## API Models Used
- **Bark TTS (suno-ai/bark):**
  - High-quality text-to-speech
  - Supports natural prosody
  - Output: Audio file (MP3/WAV)

## Integration Notes
- Voiceovers will be mixed with video in Story 5.6 (FFmpeg composition)
- Audio mixing: Voiceover 100%, Music 30%
- Fallback: If voiceover_text missing, uses scene.description
- Storage: Supabase "videos" bucket (alongside video files)

## Known Limitations
- Bark TTS may have text length limits (~200 words recommended)
- Accent/voice cannot be customized in current implementation
- No retry logic for failed TTS generation
- Parallel execution limited by Replicate API rate limits
