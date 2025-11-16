# ✅ Verify Celery Worker is Working

You just changed the start command! Let's verify it's working.

---

## Step 1: Check Deployment Status

**Railway Dashboard → Celery Worker Service → Deployments**

Wait for the latest deployment to show:
- ✅ **Status: Active** (green checkmark)
- ⏱️ Takes ~2-3 minutes to build and deploy

---

## Step 2: Check Worker Logs

**Railway Dashboard → Celery Worker Service → Deployments → Latest → Logs**

### ✅ Success - You should see:

```
 -------------- celery@railway v5.3.4 (dawn-chorus)
--- ***** -----
-- ******* ---- Linux-...
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         adcraft:0x...
- ** ---------- .> transport:   redis://redis-adcraft.railway.internal:6379
- ** ---------- .> results:     redis://redis-adcraft.railway.internal:6379
- *** --- * --- .> concurrency: 2 (prefork)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** -----

[tasks]
  . app.tasks.video_generation.generate_campaign_video_test_mode

[2025-11-16 15:30:00,000: INFO/MainProcess] Connected to redis://redis-adcraft.railway.internal:6379
[2025-11-16 15:30:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-11-16 15:30:01,000: INFO/MainProcess] mingle: all alone
[2025-11-16 15:30:01,000: INFO/MainProcess] celery@railway ready.
```

**Key things to look for:**
- ✅ `celery@railway ready.`
- ✅ `[tasks]` section shows your task
- ✅ `Connected to redis://...`
- ✅ No error messages

### ❌ If you see errors:

**Error 1: "Cannot connect to redis"**
```
[ERROR] Cannot connect to redis://...
```
**Fix:** Check REDIS_URL environment variable

**Error 2: "ModuleNotFoundError"**
```
ModuleNotFoundError: No module named 'app'
```
**Fix:** Set Root Directory to `/backend`

**Error 3: Worker exits immediately**
```
Worker terminated with exit code 1
```
**Fix:** Check environment variables (SUPABASE_URL, etc.)

---

## Step 3: Test with Your Existing Queued Task

Remember this task from earlier?
```
✅ Epic 5 TEST MODE task queued successfully!
   Celery Task ID: 7da2e3cd-8690-4780-9dc8-f6a070a85d6a
```

Once the worker starts, it should **immediately pick up and process** this queued task!

**In worker logs, you should see:**
```
[2025-11-16 15:30:05,000: INFO/MainProcess] Task app.tasks.video_generation.generate_campaign_video_test_mode[7da2e3cd-8690-4780-9dc8-f6a070a85d6a] received
[2025-11-16 15:30:05,100: INFO/ForkPoolWorker-1] 🎬 Starting Epic 5 video generation (TEST MODE)
[2025-11-16 15:30:05,200: INFO/ForkPoolWorker-1] Campaign ID: 78ff00af-d143-41c0-b62b-fb96f3e2d292
...
[2025-11-16 15:30:35,000: INFO/ForkPoolWorker-1] Task app.tasks.video_generation.generate_campaign_video_test_mode[7da2e3cd-8690-4780-9dc8-f6a070a85d6a] succeeded in 30.5s
```

---

## Step 4: Check Campaign Status Updates

**In your frontend (browser console or UI):**

The campaign should now change from:
```
❌ status: "pending", stage: "not_started", progress: 0
```

To:
```
✅ status: "processing", stage: "storyline_generation", progress: 10
✅ status: "processing", stage: "video_generation", progress: 50
✅ status: "completed", progress: 100
```

**Refresh your browser or wait for the polling to update!**

---

## Step 5: Verify in Database

The campaign record in your Supabase database should update:
- `status` → "processing" then "completed"
- `generation_stage` → "storyline_generation" → "video_generation" → "complete"
- `generation_progress` → 0 → 25 → 50 → 75 → 100
- `final_video_url` → (URL when complete)

---

## Quick Verification Commands

### Check if worker is processing tasks:
```bash
# Watch worker logs in real-time
railway logs --tail -s celery-worker
```

### Check campaign status:
```bash
curl https://backend-adcraft-production.up.railway.app/api/campaigns/78ff00af-d143-41c0-b62b-fb96f3e2d292/status \
  -H "Authorization: Bearer mock-token-for-development"
```

**Expected response:**
```json
{
  "campaign_id": "78ff00af-d143-41c0-b62b-fb96f3e2d292",
  "status": "processing",  // or "completed"
  "stage": "video_generation",
  "progress": 50
}
```

---

## Timeline

**If everything is working correctly:**

1. **T+0s:** Celery worker starts, logs show "ready"
2. **T+5s:** Worker picks up queued task
3. **T+10s:** Campaign status updates to "processing"
4. **T+30s:** Task completes (TEST MODE is fast)
5. **T+35s:** Campaign status updates to "completed"

**Total time: ~30-60 seconds for TEST MODE**

(Production mode with actual video generation would take 5-10 minutes)

---

## What to Share if It's Not Working

If the worker still isn't processing tasks, please share:

1. **Worker deployment status** (Active/Building/Failed?)
2. **Worker logs** (copy the full output)
3. **Any error messages** you see

Then I can diagnose the exact issue!

---

## Success Indicators

**You'll know it's working when you see:**

✅ Worker logs show "celery@railway ready."
✅ Worker logs show "Task received" and "Task succeeded"
✅ Campaign status changes from "pending" to "processing"
✅ Frontend polling shows progress updates
✅ Campaign eventually completes with status="completed"

**That means your video generation pipeline is FULLY WORKING!** 🎉

---

## Next Steps After Verification

Once confirmed working:

1. ✅ Test creating a new campaign (should auto-queue and process)
2. ✅ Monitor worker logs for any errors during processing
3. ✅ Check that all environment variables are set correctly
4. ✅ Test the full "Continue to Storyline" flow end-to-end

**Let me know what you see in the logs!** 🔍
