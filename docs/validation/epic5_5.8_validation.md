# Story 5.8 Validation Guide: Granular Progress Tracking UI

## 30-Second Quick Test
1. Create campaign via frontend
2. Navigate to progress page
3. Verify:
   - Progress bar fills from 0% → 100%
   - Stage text updates with each step
   - Stage icons update (pending → loading → complete)
   - Auto-redirects to video player at 100%

## Automated Tests
```javascript
// Test API response
const response = await api.getCampaignStatus(campaignId);

expect(response).toHaveProperty('status');
expect(response).toHaveProperty('stage');
expect(response).toHaveProperty('progress');
expect(response.progress).toBeGreaterThanOrEqual(0);
expect(response.progress).toBeLessThanOrEqual(100);
```

## Manual Validation Steps

### Test Progress API Endpoint
1. **Start Campaign:**
   ```bash
   curl -X POST http://localhost:8000/api/campaigns \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer {token}" \
     -d '{
       "brand_id": "...",
       "creative_bible_id": "..."
     }'
   ```

2. **Poll Status:**
   ```bash
   curl http://localhost:8000/api/campaigns/{campaign_id}/status \
     -H "Authorization: Bearer {token}"
   ```

3. **Verify Response:**
   ```json
   {
     "campaign_id": "uuid",
     "status": "generating",
     "stage": "scene_videos",
     "progress": 40,
     "final_video_url": null
   }
   ```

### Test Frontend Progress Display
1. **Navigate to Progress Page:**
   - Click "Generate Video Ad" from StorylineReview
   - Should navigate to `/campaigns/{campaign_id}/progress`

2. **Verify UI Updates:**
   - Progress bar starts at 0%
   - Stage text: "Initializing..." → "Generating reference images..." → etc.
   - Icons change: empty circle → spinner → checkmark

3. **Watch Progress Stages:**
   - 0%: "Initializing..."
   - 10%: "Generating reference images..."
   - 20%: "Creating storyboard..."
   - 20-60%: "Generating video scenes..."
   - 60-70%: "Generating voiceovers..."
   - 70-80%: "Composing soundtrack..."
   - 80-100%: "Composing final video..."
   - 100%: "Your Ad is Ready!"

4. **Verify Auto-Redirect:**
   - At 100%, wait 2 seconds
   - Should auto-navigate to `/campaigns/{campaign_id}/video`

### Test Progress Bar
1. **Inspect Progress Bar:**
   - Blue bar fills from left to right
   - Width matches progress percentage
   - Smooth transition (no jumps)

2. **Verify Percentage Display:**
   - Text shows "X%" below bar
   - Updates every 5 seconds with API poll

### Test Stage Icons
1. **Pending Stage:**
   - Empty circle icon
   - Gray text

2. **Active Stage:**
   - Spinning loader icon
   - Normal text color

3. **Completed Stage:**
   - Green checkmark icon
   - Normal text color

### Test Polling Behavior
1. **Poll Interval:**
   - API called every 5 seconds
   - Console logs each poll (check network tab)

2. **Cleanup on Unmount:**
   - Navigate away from page
   - Verify polling stops (no continued API calls)

3. **Error Handling:**
   - Stop backend API
   - Verify fallback behavior (simulated progress)

### Test Edge Cases

#### Campaign Already Completed
```javascript
// Navigate to progress page for completed campaign
// Expected: Shows 100% immediately
// Expected: Redirects to video player after 2s
```

#### Campaign Failed
```javascript
// Campaign status = "failed"
// Expected: Shows error icon and message
// Expected: No auto-redirect
```

#### Invalid Campaign ID
```bash
curl http://localhost:8000/api/campaigns/invalid-uuid/status
# Expected: 404 error
# Frontend should handle gracefully
```

#### Network Error During Poll
- Disconnect network
- Verify: Fallback to simulated progress
- Verify: Error logged to console

## Acceptance Criteria Checklist
- [x] Progress bar updates smoothly 0 → 100%
- [x] Stage text updates as pipeline progresses
- [x] Poll every 5 seconds
- [x] Auto-redirect to video player at 100%
- [x] Backend returns `stage` and `progress` fields
- [x] Frontend maps stages to user-friendly text
- [x] Icons update based on stage status
- [x] Percentage displayed below progress bar

## Rollback Plan
```bash
# Revert frontend changes
git checkout HEAD~1 -- frontend/src/pages/VideoProgress.jsx

# Revert backend changes
git checkout HEAD~1 -- backend/app/api/campaigns.py

# Restart services
npm run dev  # Frontend
uvicorn app.main:app --reload  # Backend
```

## Files Modified
- `backend/app/api/campaigns.py`
  - Updated `/status` endpoint to return `stage` and `progress`
- `frontend/src/pages/VideoProgress.jsx`
  - Added `stage` and `progress` state
  - Added progress bar UI
  - Updated `getStageInfo()` to map granular stages
  - Updated ProgressStage components with dynamic status
  - Poll and display stage/progress from API

## Stage Mapping
```javascript
const stageMap = {
  not_started: "Initializing...",
  reference_images: "Generating reference images...",
  storyboard: "Creating storyboard...",
  scene_videos: "Generating video scenes...",
  voiceovers: "Generating voiceovers...",
  music: "Composing soundtrack...",
  compositing: "Composing final video...",
  complete: "Complete!"
}
```

## Progress Milestones
- 0%: Not started
- 10%: Reference images done
- 20%: Storyboard done
- 28%, 36%, 44%, 52%, 60%: Scenes 1-5
- 70%: Voiceovers done
- 80%: Music done
- 100%: Final video ready

## UI/UX Notes
- Progress bar uses Tailwind `transition-all duration-500` for smooth animation
- Polling interval of 5 seconds balances responsiveness vs server load
- 2-second delay before redirect allows user to see "Complete!" message
- Fallback simulation ensures demo works even if backend is down

## Accessibility
- Progress bar has visual width indicator
- Text percentage for screen readers
- Stage text describes current action
- Icons provide visual status cues

## Performance
- Polling every 5 seconds (reasonable for 6-8 min generation)
- Cleanup on unmount prevents memory leaks
- Frontend-only state updates (no unnecessary re-renders)

## Known Limitations
- No pause/cancel functionality
- No estimated time remaining
- Progress doesn't account for Replicate API delays
- Hard-coded scene count (assumes 5 scenes)

## Future Enhancements
- WebSocket for real-time updates (no polling)
- Estimated time remaining per stage
- Pause/resume generation
- Detailed logs per stage
- Retry failed stages
- Cancel generation button
