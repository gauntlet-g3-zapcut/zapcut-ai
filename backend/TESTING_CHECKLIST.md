# Testing Checklist for Video Generation Workflow Fixes

## Pre-Testing Setup

1. **Backend is deployed and running**
   - API: `zapcut-api` on Fly.io
   - Worker: `zapcut-worker` on Fly.io
   - Both apps have correct secrets (especially REDIS_URL with `rediss://`)

2. **Frontend is running**
   - Local dev server or production build
   - Connected to deployed API

## Test Scenarios

### Test 1: Sora Prompts Generated with Storyline

**Steps:**
1. Log in to the application
2. Create or select a brand
3. Go through campaign answers flow
4. Review storyline

**Expected Results:**
- Storyline is generated successfully
- Check API response: Should include `sora_prompts` array
- Each prompt should have `scene_number` and `prompt` fields
- Prompts should be stored in creative_bible in database

**Verification:**
```bash
# Check creative_bible in database
# Should see sora_prompts array with prompts for each scene
```

### Test 2: Campaign Creation with Stored Prompts

**Steps:**
1. After storyline is generated, click "Approve" to create campaign
2. Campaign should be created immediately

**Expected Results:**
- Campaign is created successfully
- Campaign should have `sora_prompts` populated (not empty array)
- Check database: `campaigns.sora_prompts` should contain prompts

**Verification:**
```bash
# Check campaign in database
# campaigns.sora_prompts should match creative_bible.sora_prompts
```

### Test 3: Video Generation Uses Stored Prompts

**Steps:**
1. Campaign is created and video generation starts
2. Check worker logs

**Expected Results:**
- Worker should use stored prompts from campaign
- No "No stored prompt provided" warnings in logs
- Each scene uses the correct prompt from campaign.sora_prompts

**Verification:**
```bash
fly logs -a zapcut-worker | grep -i "prompt\|scene"
# Should see prompts being used, not generated
```

### Test 4: Scene URLs Stored Incrementally

**Steps:**
1. Monitor campaign status while videos generate
2. Check database after each scene completes

**Expected Results:**
- Scene URLs appear in database as each scene completes
- `campaigns.video_urls` array updates incrementally
- Each scene entry has `video_url` when completed

**Verification:**
```bash
# Poll campaign status endpoint
curl -H "Authorization: Bearer <token>" \
  https://zapcut-api.fly.dev/api/campaigns/<campaign_id>/status

# Check video_urls array - should grow as scenes complete
```

### Test 5: VideoProgress Screen Updates

**Steps:**
1. Navigate to `/campaigns/<campaign_id>/progress`
2. Watch the screen update
3. Refresh the page

**Expected Results:**
- Screen updates every 3 seconds showing progress
- Scene statuses change: pending → generating → completed
- Video URLs appear for completed scenes
- "View Video" links work for completed scenes
- User remains logged in after refresh

**Verification:**
- Open browser console (should have minimal logging)
- Check network tab - status requests every 3 seconds
- Scene statuses should update in real-time
- Video URLs should appear as scenes complete

### Test 6: Authentication Persistence

**Steps:**
1. Log in to the application
2. Refresh the page (F5 or Cmd+R)
3. Navigate to different pages
4. Close and reopen browser tab

**Expected Results:**
- User remains logged in after refresh
- No redirect to login page
- Session persists across page navigations
- Session persists after closing/reopening tab (if cookies/localStorage enabled)

**Verification:**
- Check browser localStorage: Should have `supabase.auth.token`
- Check network requests: Should include Authorization header
- No 401 errors after refresh

### Test 7: Campaign Status Endpoint Returns All Data

**Steps:**
1. Create a campaign and wait for some scenes to complete
2. Call status endpoint

**Expected Results:**
- Response includes `sora_prompts` array
- Response includes `progress.scenes` with:
  - `video_url` for completed scenes
  - `sora_prompt` for each scene
  - `status` for each scene
- All scene data is present and correct

**Verification:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://zapcut-api.fly.dev/api/campaigns/<campaign_id>/status | jq

# Should see:
# - sora_prompts: [...]
# - progress.scenes: [{scene_number, title, status, video_url, sora_prompt}, ...]
```

## Quick Test Commands

### Check API Health
```bash
curl https://zapcut-api.fly.dev/health
```

### Check Worker Status
```bash
fly status -a zapcut-worker
fly logs -a zapcut-worker --recent
```

### Check API Logs
```bash
fly logs -a zapcut-api --recent
```

### Test Campaign Status (replace with actual campaign_id and token)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://zapcut-api.fly.dev/api/campaigns/CAMPAIGN_ID/status
```

## Common Issues to Watch For

1. **Sora prompts not in storyline response**
   - Check chat.py - sora_prompts should be generated and returned

2. **Campaign has empty sora_prompts**
   - Check campaigns.py - should extract from creative_bible

3. **Worker generating prompts instead of using stored**
   - Check video_generation.py - should use stored prompts

4. **Scene URLs not updating**
   - Check update_scene_status() - should commit to database immediately

5. **VideoProgress not updating**
   - Check browser console for errors
   - Verify polling is working (network tab)
   - Check API response format matches expected

6. **User logged out on refresh**
   - Check AuthContext - session should be restored
   - Check localStorage for supabase.auth.token
   - Verify supabase.ts configuration

