# Story 5.3 Validation Guide: Sequential Scene Video Generation with Continuity

## 30-Second Quick Test
1. Trigger campaign creation via API or frontend
2. Monitor generation_jobs table: `SELECT * FROM generation_jobs ORDER BY created_at;`
3. Verify scenes generate one at a time (not all at once)
4. Check campaign progress updates: 20% → 28% → 36% → 44% → 52% → 60%

## Automated Tests
```python
# Test sequential generation
from app.services.replicate_service import generate_videos_sequential

test_prompts = [
    {"scene_number": 1, "prompt": "Scene 1"},
    {"scene_number": 2, "prompt": "Scene 2"},
    {"scene_number": 3, "prompt": "Scene 3"}
]

results = generate_videos_sequential(test_prompts)

# Verify results
assert len(results) == 3
assert results[0]["scene_number"] == 1
assert results[1]["prev_scene"] is not None  # Scene 2 has reference to scene 1
assert results[2]["prev_scene"] is not None  # Scene 3 has reference to scene 2
```

## Manual Validation Steps

### Test Sequential Generation
1. **Start Campaign Generation:**
   ```bash
   # Via API
   curl -X POST http://localhost:8000/api/campaigns \
     -H "Content-Type: application/json" \
     -d '{
       "brand_id": "...",
       "creative_bible_id": "..."
     }'
   ```

2. **Monitor Database:**
   ```sql
   -- Watch jobs being created
   SELECT id, job_type, scene_number, status, started_at, completed_at
   FROM generation_jobs
   WHERE campaign_id = '...'
   ORDER BY scene_number;

   -- Check campaign progress
   SELECT id, generation_stage, generation_progress, status
   FROM campaigns
   WHERE id = '...';
   ```

3. **Verify Sequential Execution:**
   - Jobs created one at a time (not all at once)
   - started_at timestamps show sequential order
   - Scene 1 starts first, then scene 2, etc.

4. **Check Progress Updates:**
   ```sql
   -- Progress should update after each scene
   -- 20% (start) → 28% (scene 1) → 36% (scene 2) → 44% (scene 3) → 52% (scene 4) → 60% (scene 5)
   ```

### Test Continuity Feature
1. **Inspect Job Input Params:**
   ```sql
   SELECT scene_number, input_params->>'prev_scene' as prev_scene
   FROM generation_jobs
   WHERE job_type = 'scene_video'
   ORDER BY scene_number;
   ```

2. **Verify:**
   - Scene 1: prev_scene is NULL (no previous scene)
   - Scene 2-5: prev_scene contains URL of previous scene

### Test Error Handling
1. **Simulate Replicate Failure:**
   ```python
   # Temporarily break Replicate API
   # Verify job marked as failed
   # Error message captured in generation_jobs.error_message
   ```

2. **Check Database:**
   ```sql
   SELECT scene_number, status, error_message
   FROM generation_jobs
   WHERE status = 'failed';
   ```

### Test Performance
1. **Time Each Scene:**
   ```sql
   SELECT
     scene_number,
     EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
   FROM generation_jobs
   WHERE job_type = 'scene_video' AND status = 'completed'
   ORDER BY scene_number;
   ```

2. **Expected:**
   - Each scene: 2-3 minutes (Replicate processing time)
   - Total for 5 scenes: 10-15 minutes

## Edge Cases

### Empty Prompts
- Test with missing scene_number in prompt_data
- Should default to index+1

### API Rate Limits
- Replicate may rate limit sequential requests
- Verify retry logic or exponential backoff

### Missing Previous Scene
- If scene 1 fails, scene 2 should still attempt
- prev_scene_url will be None

### Database Connection Loss
- Job status should allow recovery
- Pending/processing jobs can be retried

## Acceptance Criteria Checklist
- [x] Scenes generate one at a time (not parallel)
- [x] Scene 2-5 prompts reference previous scene for continuity
- [x] Progress updates after each scene completes
- [x] Total scene generation: ~10-15 minutes for 5 scenes
- [x] GenerationJob records created for each scene
- [x] Job tracking includes start/end times
- [x] Failed scenes captured with error messages
- [x] Campaign progress: 20% → 60% across 5 scenes

## Rollback Plan
```bash
# Revert to parallel generation
git checkout HEAD~1 -- backend/app/tasks/video_generation.py
git checkout HEAD~1 -- backend/app/services/replicate_service.py

# Restart Celery workers
celery -A app.celery_app worker --loglevel=info
```

## Files Modified
- `backend/app/services/replicate_service.py`
  - Modified `generate_video_with_sora()` to accept `prev_scene_url`
  - Added `generate_videos_sequential()` function
- `backend/app/tasks/video_generation.py`
  - Replaced `generate_videos_parallel()` with sequential loop
  - Added GenerationJob creation per scene
  - Added progress updates (20% → 60%)
  - Added continuity via prev_scene_url

## Performance Notes
- Sequential generation is ~5x slower than parallel (10-15 min vs 2-3 min)
- Trade-off: Better visual continuity vs longer generation time
- Consider hybrid approach: Generate scenes 1-2 sequentially, then parallel for rest

## Dependencies
- Story 5.2 must be complete (GenerationJob model exists)
- Database migration must be applied
- Replicate API must support video generation models
