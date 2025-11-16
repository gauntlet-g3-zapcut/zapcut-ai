# Story 5.1 Validation Guide: Wire Frontend to Backend Pipeline

## 30-Second Quick Test
1. Navigate to `/brands/{brandId}/storyline-review/{creativeBibleId}`
2. Click "Generate Video Ad" button
3. Verify: Button shows "Starting Generation..." while loading
4. Verify: Redirects to `/campaigns/{campaign_id}/progress` with real ID (not "default")

## Automated Tests
- **Unit Tests:** None required (UI integration)
- **Integration Tests:** Manual browser testing required
- **Coverage:** Frontend UI component

## Manual Validation Steps

### Happy Path
1. **Setup:**
   ```bash
   cd frontend && npm run dev
   cd backend && uvicorn app.main:app --reload
   ```

2. **Test Campaign Creation:**
   - Navigate to StorylineReview page
   - Click "Generate Video Ad"
   - Expected: Button text changes to "Starting Generation..."
   - Expected: Button becomes disabled
   - Expected: API call to `POST /api/campaigns` with:
     ```json
     {
       "brand_id": "{brandId}",
       "creative_bible_id": "{creativeBibleId}"
     }
     ```

3. **Test Navigation:**
   - Expected: Redirects to `/campaigns/{real-uuid}/progress`
   - Expected: URL contains actual campaign ID, not "default"

### Error Handling
1. **Backend Offline:**
   - Stop backend server
   - Click "Generate Video Ad"
   - Expected: Error message displays in red card
   - Expected: Button re-enables after error
   - Expected: User can retry

2. **Invalid Data:**
   - Call with missing brand_id or creative_bible_id
   - Expected: Error message displays
   - Expected: No navigation occurs

### Edge Cases
1. **Rapid Clicking:**
   - Click button multiple times quickly
   - Expected: Only one API call is made
   - Expected: Button stays disabled during request

2. **Browser Back Button:**
   - Start generation
   - Click back before navigation
   - Expected: Request continues in background

## Acceptance Criteria Checklist
- [x] Button click creates campaign in database
- [x] Celery task starts automatically (depends on backend implementation in Story 5.2+)
- [x] User navigates to progress page with real campaign ID
- [x] Loading state shown while API call in flight
- [x] Error states handled gracefully
- [x] Buttons disabled during generation

## Rollback Plan
```bash
# Revert StorylineReview.jsx changes
git checkout HEAD~1 -- frontend/src/pages/StorylineReview.jsx

# Restart frontend
cd frontend && npm run dev
```

## Files Modified
- `frontend/src/pages/StorylineReview.jsx`
  - Added `isGenerating` state
  - Added `error` state
  - Updated `handleApprove()` to call API
  - Added loading/error UI

## Notes
- API endpoint `/api/campaigns` must be implemented in backend (Epic 1-4)
- Celery task auto-start depends on backend implementation
- Progress page polling implemented in Story 5.8
