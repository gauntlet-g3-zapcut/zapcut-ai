# Backend API vs Celery Worker - Important Difference!

## The Confusion

You're looking at the **Backend API** service, which runs:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

This is **NOT** the Celery worker! This handles HTTP requests.

---

## You Need TWO Separate Services

### Service 1: Backend API ✅ (You Have This)

**What it does:** Handles HTTP requests from frontend
**Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
**Port:** Has a public URL (https://backend-adcraft-production.up.railway.app)

**Responsibilities:**
- Handle `/api/brands/` requests
- Handle `/api/campaigns/` requests
- **Queue** Celery tasks (but doesn't process them!)
- Serve API endpoints

### Service 2: Celery Worker ❌ (You DON'T Have This - Need to Create)

**What it does:** Processes background tasks (video generation)
**Start command:** `celery -A app.celery_app worker --loglevel=info --concurrency=2`
**Port:** No public URL (runs in background)

**Responsibilities:**
- Pick up tasks from Redis queue
- **Process** video generation tasks
- Update campaign status in database
- Call Replicate API for video generation

---

## Current Architecture (Missing Worker!)

```
┌─────────────────────────────────────────────────────────┐
│ Service 1: Backend API ✅                               │
│ Command: uvicorn app.main:app ...                      │
│ - Receives HTTP requests                               │
│ - Queues tasks to Redis                                │
│ - Returns responses                                    │
└──────────────────┬──────────────────────────────────────┘
                   │ (queues task)
                   ↓
         ┌─────────────────┐
         │ Redis Queue     │
         │ - Tasks waiting │
         └─────────────────┘
                   │ (should be picked up by...)
                   ↓
         ┌─────────────────┐
         │ ❌ NO WORKER!   │  ← THIS IS THE PROBLEM
         └─────────────────┘

Tasks are queued but never processed!
```

---

## Required Architecture (With Worker)

```
┌─────────────────────────────────────────────────────────┐
│ Service 1: Backend API ✅                               │
│ Command: uvicorn app.main:app ...                      │
└──────────────────┬──────────────────────────────────────┘
                   │ (queues task)
                   ↓
         ┌─────────────────┐
         │ Redis Queue     │
         └─────────┬───────┘
                   │ (picks up task)
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Service 2: Celery Worker ✅ NEW!                        │
│ Command: celery -A app.celery_app worker ...           │
│ - Picks up tasks from Redis                            │
│ - Processes video generation                           │
│ - Updates campaign status                              │
└─────────────────────────────────────────────────────────┘

Tasks are queued AND processed!
```

---

## How to Check What Services You Have

### Option 1: Railway CLI
```bash
# From project root
railway status
```

**If you see only:**
- `Service: backend`

**Then you're missing the Celery worker!**

### Option 2: Railway Dashboard
1. Go to: https://railway.app/project/dc2d037a-6243-4a5f-a3ec-06fd85a299b9
2. Look at services list

**You should see:**
- ✅ `backend` (or similar name)
- ✅ `Redis-AdCraft`
- ❌ `celery-worker` (MISSING - need to create this!)

---

## How to Create Celery Worker Service

### Step 1: Create New Service in Railway

1. **Railway Dashboard** → Your Project → **+ New Service**
2. Select **"GitHub Repo"**
3. Choose your repository
4. Configure:
   - **Name:** `celery-worker`
   - **Root Directory:** `/backend`

### Step 2: Set Custom Start Command

In the new service settings:
- Go to **Settings → Deploy**
- Under **"Custom Start Command"**, enter:
  ```bash
  celery -A app.celery_app worker --loglevel=info --concurrency=2
  ```

**OR** create `backend/railway.celery.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "celery -A app.celery_app worker --loglevel=info --concurrency=2",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 3: Set Environment Variables

Copy ALL environment variables from Backend service:

```bash
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
SUPABASE_SERVICE_ROLE_KEY=(copy from backend)
OPENAI_API_KEY=(copy from backend)
REPLICATE_API_TOKEN=(copy from backend)
REDIS_URL=redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379
```

**Important:** Worker needs the SAME environment variables as backend!

### Step 4: Deploy

Click **"Deploy"** and wait for it to start.

---

## How to Verify Celery Worker is Running

### Check Worker Logs

In Railway Dashboard → Celery Worker Service → Logs

**You should see:**
```
 -------------- celery@railway v5.3.4
---- **** -----
--- * ***  * -- Linux-...
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         adcraft:0x...
- ** ---------- .> transport:   redis://redis-adcraft.railway.internal:6379
- ** ---------- .> results:     redis://redis-adcraft.railway.internal:6379
- *** --- * --- .> concurrency: 2 (prefork)

[tasks]
  . app.tasks.video_generation.generate_campaign_video_test_mode

[2025-11-16 ...] celery@railway ready.
```

**Key indicators:**
- ✅ Shows `[tasks]` with your task names
- ✅ Shows `celery@railway ready.`
- ✅ Shows connection to Redis

### Test Task Processing

1. Create a new campaign in your frontend
2. Watch Celery worker logs
3. You should see:
   ```
   [2025-11-16 ...] Task app.tasks.video_generation.generate_campaign_video_test_mode[task-id] received
   [2025-11-16 ...] Task app.tasks.video_generation.generate_campaign_video_test_mode[task-id] succeeded in 45.2s
   ```

---

## Common Mistakes

### ❌ Mistake 1: Changing Backend Start Command

**DON'T change the backend service start command to run Celery!**

The backend must run:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

Create a **separate service** for Celery.

### ❌ Mistake 2: Same Service, Different Commands

You can't have one service run both uvicorn AND celery. They are separate processes.

### ❌ Mistake 3: Missing Environment Variables

Celery worker needs ALL the same environment variables as backend (database, API keys, etc.)

---

## Quick Reference

| Aspect | Backend API | Celery Worker |
|--------|-------------|---------------|
| **Purpose** | Handle HTTP requests | Process background tasks |
| **Start Command** | `uvicorn app.main:app ...` | `celery -A app.celery_app worker ...` |
| **Public URL** | ✅ Yes (https://backend-...) | ❌ No (background service) |
| **Port** | ✅ Needs PORT env var | ❌ No port needed |
| **When it runs** | Always (serves API) | Always (waits for tasks) |
| **What it does** | Receives requests, queues tasks | Picks up tasks, processes them |

---

## Summary

**What you have:**
- ✅ Backend API service (uvicorn)
- ✅ Redis service
- ❌ Celery Worker service (MISSING!)

**What you need to do:**
1. Create a NEW service in Railway called `celery-worker`
2. Set start command: `celery -A app.celery_app worker --loglevel=info --concurrency=2`
3. Copy ALL environment variables from backend
4. Deploy

**After creating the worker:**
- Your queued tasks will start processing
- Campaign status will update
- Video generation will begin!

---

## TL;DR

The screenshot shows your **Backend API** (uvicorn), NOT a Celery worker.

You need to create a **separate Railway service** for the Celery worker with the command:
```bash
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**Two services, same codebase, different start commands!** 🚀
