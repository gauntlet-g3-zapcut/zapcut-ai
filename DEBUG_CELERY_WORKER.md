# Debug Celery Worker - Why Tasks Aren't Processing

## You Have Two Services ✅

So the issue isn't missing services - let's debug why the Celery worker isn't processing tasks.

---

## Step 1: Check Celery Worker Logs

In Railway Dashboard → Celery Worker Service → Logs

**What to look for:**

### ✅ Good Signs (Worker is Running)
```
 -------------- celery@railway v5.3.4
[tasks]
  . app.tasks.video_generation.generate_campaign_video_test_mode
celery@railway ready.
```

### ❌ Bad Signs (Worker Has Issues)

**Sign 1: Connection Error**
```
[ERROR] Cannot connect to redis://...
[ERROR] Connection refused
```
**Fix:** Check REDIS_URL environment variable

**Sign 2: Import Error**
```
[ERROR] Unable to load celery application.
ModuleNotFoundError: No module named 'app.tasks.video_generation'
```
**Fix:** Check start command and working directory

**Sign 3: No Tasks Registered**
```
[tasks]
  (empty)
```
**Fix:** Tasks not being discovered

**Sign 4: Worker Crashes**
```
[ERROR] Worker exited prematurely
```
**Fix:** Check environment variables and dependencies

---

## Step 2: Verify Worker Start Command

**Celery Worker service should have:**

```bash
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**NOT:**
```bash
uvicorn app.main:app ...  ← This is the backend API!
```

### Check in Railway:
1. Go to Celery Worker Service
2. Settings → Deploy → Custom Start Command
3. Verify it says `celery -A app.celery_app worker ...`

---

## Step 3: Check Environment Variables

**Celery worker needs ALL of these:**

```bash
# Required for database access
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
SUPABASE_SERVICE_ROLE_KEY=(your key)

# Required for task processing
OPENAI_API_KEY=(your key)
REPLICATE_API_TOKEN=(your token)

# Required for Redis connection
REDIS_URL=redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379
```

### Verify in Railway:
1. Celery Worker Service → Variables
2. Check each variable exists
3. Compare with Backend service variables (should be identical)

---

## Step 4: Test Task Manually

### Check if task is in Redis queue:

```bash
# From your local backend directory
cd backend
source venv/bin/activate

python -c "
from app.celery_app import celery_app
from celery.result import AsyncResult

# Use the task ID from your logs
task_id = '7da2e3cd-8690-4780-9dc8-f6a070a85d6a'
result = AsyncResult(task_id, app=celery_app)
print(f'Task State: {result.state}')
print(f'Task Info: {result.info}')
"
```

**Expected states:**
- `PENDING` - Task is queued, waiting for worker
- `STARTED` - Worker picked it up
- `SUCCESS` - Task completed
- `FAILURE` - Task failed

If it stays `PENDING` forever, the worker isn't picking it up.

---

## Step 5: Check Redis Connection

### From Backend Logs:
```bash
railway logs --tail 20
```

Look for:
```
✅ Epic 5 TEST MODE task queued successfully!
   Celery Task ID: 7da2e3cd-8690-4780-9dc8-f6a070a85d6a
```

This confirms Redis connection from backend is OK.

### From Celery Worker Logs:
Look for:
```
.> transport:   redis://redis-adcraft.railway.internal:6379
```

This confirms worker can connect to Redis.

---

## Common Issues & Fixes

### Issue 1: Worker Connects but Doesn't Process Tasks

**Symptom:**
```
celery@railway ready.
```
(but no task processing)

**Possible causes:**
1. **Different REDIS_URL** - Backend and worker using different Redis instances
2. **Queue name mismatch** - Task sent to different queue than worker is listening to
3. **Task not imported** - Worker doesn't know about the task

**Fix:**
```bash
# Verify REDIS_URL is EXACTLY the same in both services
# Backend REDIS_URL: redis://default:...@redis-adcraft.railway.internal:6379
# Worker REDIS_URL:  redis://default:...@redis-adcraft.railway.internal:6379
```

### Issue 2: Worker Can't Import Tasks

**Symptom:**
```
[ERROR] Unable to load celery application.
```

**Fix:**
1. Check Root Directory is set to `/backend`
2. Check start command is `celery -A app.celery_app worker ...`
3. Verify requirements.txt includes `celery==5.3.4`

### Issue 3: Worker Crashes on Startup

**Symptom:**
Worker starts then immediately exits

**Fix:**
Check for missing environment variables:
```bash
# These are REQUIRED
SUPABASE_URL
SUPABASE_DB_PASSWORD
REDIS_URL
```

---

## Debug Checklist

Run through this checklist:

- [ ] Celery worker service exists in Railway
- [ ] Worker start command is `celery -A app.celery_app worker --loglevel=info --concurrency=2`
- [ ] Worker logs show `celery@railway ready.`
- [ ] Worker logs show tasks registered under `[tasks]`
- [ ] Worker has ALL environment variables from backend
- [ ] REDIS_URL is identical in backend and worker
- [ ] Task is being queued (check backend logs)
- [ ] Worker is picking up task (check worker logs)

---

## Next Steps Based on Logs

### If worker logs show errors:
Share the error logs and we'll debug the specific issue.

### If worker logs show "ready" but no task processing:
Check REDIS_URL matches between services.

### If worker logs are empty/not running:
Worker service might be stopped or crashed. Check deployment status.

### If worker is processing but tasks fail:
Check for errors in worker logs - might be missing API keys or database connection issues.

---

## Quick Test Command

**Run this in backend service terminal (Railway):**

```bash
# Check Redis connection
python -c "
import redis
from app.config import settings
r = redis.from_url(settings.REDIS_URL)
print('Redis ping:', r.ping())
print('Queued tasks:', r.llen('celery'))
"
```

**Expected output:**
```
Redis ping: True
Queued tasks: 1  (or more)
```

If queued tasks > 0 but worker isn't processing them, there's a connection issue between worker and Redis.

---

## Summary

Since you have two services, the issue is likely:

1. **Worker not actually running** - Check deployment status
2. **Worker can't connect to Redis** - Check REDIS_URL
3. **Worker missing environment variables** - Check Variables tab
4. **Worker has wrong start command** - Should be `celery -A app.celery_app worker ...`

**Please share your Celery worker service logs so I can see exactly what's happening!**
