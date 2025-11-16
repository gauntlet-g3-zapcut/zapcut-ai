# 🚨 Issue Found: Celery Worker Not Running

## The Problem

Your video generation tasks ARE being queued successfully:
```
✅ Epic 5 TEST MODE task queued successfully!
   Celery Task ID: 7da2e3cd-8690-4780-9dc8-f6a070a85d6a
```

But **no Celery worker is running** to process them! The tasks are sitting in Redis, waiting forever.

---

## Quick Fix: Start Celery Worker in Railway

### Option 1: Manual Railway Dashboard Setup (Recommended)

1. **Go to Railway Dashboard:**
   - https://railway.app/project/dc2d037a-6243-4a5f-a3ec-06fd85a299b9

2. **Create New Service:**
   - Click "+ New Service"
   - Select "GitHub Repo"
   - Choose your repository
   - Set **Root Directory**: `/backend`
   - Name it: `celery-worker`

3. **Configure Custom Start Command:**
   - Go to: Service Settings → Deploy
   - Under "Custom Start Command", enter:
     ```
     celery -A app.celery_app worker --loglevel=info --concurrency=2
     ```

4. **Set Environment Variables:**
   Copy these from your backend service (Railway Dashboard → Backend → Variables):
   ```
   SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
   SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
   SUPABASE_SERVICE_ROLE_KEY=(your service role key)
   OPENAI_API_KEY=(your OpenAI key)
   REPLICATE_API_TOKEN=(your Replicate token)
   REDIS_URL=redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379
   ```

   **Important:** Use the same REDIS_URL as backend!

5. **Deploy:**
   - Click "Deploy"
   - Wait for deployment to complete

### Option 2: Quick Test Locally

While waiting for Railway setup, test locally:

```bash
cd /Users/reena/gauntletai/zapcut-ai/backend

# Activate virtual environment
source venv/bin/activate

# Start Celery worker
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**Expected output:**
```
 -------------- celery@your-machine v5.3.4
---- **** -----
--- * ***  * -- Darwin-24.6.0-arm64
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         adcraft:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 2 (prefork)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . app.tasks.video_generation.generate_campaign_video
  . app.tasks.video_generation.generate_campaign_video_test_mode

[2025-11-16 ...] [MainProcess] INFO - celery@your-machine ready.
```

Then your local worker will start processing the queued tasks!

---

## Verify It's Working

### 1. Check Railway Celery Worker Logs

```bash
# In Railway dashboard, go to:
# Celery Worker Service → Deployments → Latest → Logs
```

**Look for:**
```
[tasks]
  . app.tasks.video_generation.generate_campaign_video_test_mode

celery@railway ready.

Received task: app.tasks.video_generation.generate_campaign_video_test_mode[task-id]
Task app.tasks.video_generation.generate_campaign_video_test_mode[task-id] succeeded
```

### 2. Check Campaign Status Updates

Once worker is running, the campaign status should change from:
```
❌ status: "pending", stage: "not_started", progress: 0
```

To:
```
✅ status: "processing", stage: "storyline_generation", progress: 10
```

### 3. Watch Frontend Console

You should see:
```
📊 Status update: {status: "processing", stage: "storyline_generation", ...}
📊 Status update: {status: "processing", stage: "video_generation", ...}
📊 Status update: {status: "completed", progress: 100, ...}
```

---

## Why This Happened

Your deployment has:
- ✅ **Backend API** - Running (handles HTTP requests)
- ✅ **Redis** - Running (message queue)
- ❌ **Celery Worker** - **NOT RUNNING** (processes background tasks)

The backend can queue tasks, but without a worker, they never get processed.

---

## Architecture Overview

```
Frontend
   ↓ (HTTP)
Backend API
   ↓ (queues task)
Redis (message queue)
   ↓ (worker picks up task)
Celery Worker  ← MISSING!
   ↓ (processes task)
Updates Campaign in Database
```

---

## Environment Variables for Celery Worker

The Celery worker needs the **same environment variables** as the backend:

| Variable | Value | Why Needed |
|----------|-------|------------|
| `SUPABASE_URL` | `https://rksxuhhegcxqmkjopudx.supabase.co` | Database connection |
| `SUPABASE_DB_PASSWORD` | `RyanMeow76!!!...` | Database auth |
| `SUPABASE_SERVICE_ROLE_KEY` | (your key) | Supabase admin access |
| `OPENAI_API_KEY` | (your key) | Generate storylines |
| `REPLICATE_API_TOKEN` | (your token) | Generate videos |
| `REDIS_URL` | `redis://default:...@redis-adcraft.railway.internal:6379` | Task queue |

**Get these from:** Railway Dashboard → Backend Service → Variables → Copy values

---

## Quick Command Reference

### Start Celery Worker Locally
```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### Check Tasks in Redis
```bash
# From backend directory
python -c "from app.celery_app import celery_app; from celery.result import AsyncResult; print(AsyncResult('7da2e3cd-8690-4780-9dc8-f6a070a85d6a', app=celery_app).state)"
```

### Manually Trigger Task (for testing)
```bash
# Create a campaign via API, it will auto-queue
curl -X POST https://backend-adcraft-production.up.railway.app/api/campaigns/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token-for-development" \
  -d '{"brand_id": "YOUR_BRAND_ID", "creative_bible_id": "YOUR_BIBLE_ID"}'
```

---

## Summary

**Root Cause:** Celery worker service not running in Railway

**Solution:** Create Celery worker service with custom start command:
```
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**ETA:** 5 minutes to set up, then tasks will start processing immediately!

---

## Next Steps

1. ✅ Create Celery worker service in Railway (see Option 1 above)
2. ✅ Copy environment variables from backend service
3. ✅ Deploy worker
4. ✅ Watch worker logs for task processing
5. ✅ Test "Continue to Storyline" flow again
6. ✅ See campaign progress update in real-time!

**Once the worker is running, your video generation will start working!** 🚀
