# Railway Config File Issues & Fixes

## Your Current Config - Issues Found

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "celery -A app.celery_app worker --loglevel=info --concurrency=2",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",  ❌ WRONG for Celery
    "healthcheckTimeout": 100       ❌ Not needed
  }
}
```

---

## Problems

### Problem 1: Healthcheck for Celery Worker ❌

**Issue:** `"healthcheckPath": "/health"`

**Why it's wrong:**
- Celery workers don't serve HTTP endpoints!
- Celery is a background task processor, not a web server
- Only the backend API (uvicorn) has a `/health` endpoint

**What happens:**
- Railway will try to call `http://celery-worker/health`
- This will fail because Celery doesn't listen on HTTP
- Deployment might be marked as failed

**Fix:** Remove the healthcheck entirely for Celery worker

### Problem 2: Will This Affect Backend? ⚠️

**Answer:** It depends on WHERE this file is located!

#### Scenario A: File at `/backend/railway.json`
```
zapcut-ai/
├── backend/
│   ├── railway.json  ← HERE
│   ├── app/
│   └── ...
```

**Impact:**
- ✅ Affects ONLY services with Root Directory = `/backend`
- ❌ Problem: If backend also has Root Directory = `/backend`, this config will override backend's uvicorn command!

#### Scenario B: File at `/backend/railway.celery.json`
```
zapcut-ai/
├── backend/
│   ├── railway.celery.json  ← HERE (custom name)
│   ├── app/
│   └── ...
```

**Impact:**
- ✅ Only affects services that explicitly reference this file
- ✅ Backend won't be affected (uses default railway.json or no config)

---

## Solutions

### Solution 1: Use Service-Specific Config Files (Recommended)

**Create TWO separate config files:**

#### File 1: `backend/railway.backend.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

#### File 2: `backend/railway.celery.json`
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

**Then in Railway Dashboard:**

**Backend Service:**
- Settings → Config-as-code → Railway Config File
- Enter: `/backend/railway.backend.json`

**Celery Worker Service:**
- Settings → Config-as-code → Railway Config File
- Enter: `/backend/railway.celery.json`

---

### Solution 2: Remove Config File, Use Dashboard Only (Simpler)

**Remove the railway.json file entirely** and configure each service in Railway Dashboard:

#### Backend Service Settings:
- Root Directory: `/backend`
- Custom Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
- Healthcheck Path: `/health`

#### Celery Worker Service Settings:
- Root Directory: `/backend`
- Custom Start Command: `celery -A app.celery_app worker --loglevel=info --concurrency=2`
- Healthcheck Path: (leave empty)

**Benefits:**
- ✅ Simpler to manage
- ✅ No confusion about which file applies to which service
- ✅ Clear separation in Railway UI

---

### Solution 3: Use Watch Paths to Differentiate

If you want to keep a single config file, use watch paths:

#### `backend/railway.json` (for Celery worker ONLY)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "watchPaths": [
      "/backend/app/tasks/**",
      "/backend/app/celery_app.py"
    ]
  },
  "deploy": {
    "startCommand": "celery -A app.celery_app worker --loglevel=info --concurrency=2",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Then in Backend service:**
- Don't set a config file path (uses default behavior)
- Set Custom Start Command manually in dashboard

---

## Recommended Approach

**I recommend Solution 2 (Dashboard Only) because:**

1. ✅ Simple and clear
2. ✅ No file conflicts
3. ✅ Easy to update per service
4. ✅ No risk of one config affecting both services

---

## Step-by-Step Fix

### 1. Remove Healthcheck from Celery Config

If keeping the config file, edit it to:

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

**Removed:**
- ❌ `"healthcheckPath": "/health"`
- ❌ `"healthcheckTimeout": 100`

### 2. Verify Backend Service Won't Use This Config

**Option A:** Backend uses different config file path
**Option B:** Backend doesn't use config file (manual dashboard settings)

### 3. Check Current Setup

**Backend Service:**
- Railway Dashboard → Backend → Settings → Config-as-code
- Check "Railway Config File" field
- If it says `/backend/railway.json`, it WILL use your Celery config!

**Fix:** Either:
- Leave blank (use dashboard settings)
- Point to a different file (`/backend/railway.backend.json`)

---

## Verification

### After Deploying:

**Backend should show:**
```
Starting with: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Celery Worker should show:**
```
Starting with: celery -A app.celery_app worker --loglevel=info --concurrency=2
celery@railway v5.3.4
[tasks]
  . app.tasks.video_generation.generate_campaign_video_test_mode
celery@railway ready.
```

**If backend shows Celery output instead:**
- ❌ Config is being applied to wrong service!
- Fix: Remove config file path from backend service settings

---

## Quick Answer to Your Questions

### "Is this correct?"
**Partially.** Remove the healthcheck lines:
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

### "Will this also change backend?"
**It depends on the file location and config file path settings.**

**To be safe:**
1. Don't use config files for Celery worker
2. Set Custom Start Command directly in Railway Dashboard
3. This way backend and worker stay completely separate

---

## TL;DR

**Current issues:**
1. ❌ Healthcheck doesn't work for Celery (not HTTP server)
2. ⚠️ Might affect backend if both use same config file

**Quick fix:**
1. Remove `healthcheckPath` and `healthcheckTimeout` from config
2. OR just use Railway Dashboard settings instead of config file
3. Verify backend service doesn't reference this config file

**Recommended:**
Don't use config file for Celery worker. Just set "Custom Start Command" in Railway Dashboard.
