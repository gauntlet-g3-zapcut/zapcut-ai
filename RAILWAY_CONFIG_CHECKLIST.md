# Railway Configuration Checklist for Adcraft

## Quick Check Commands

Run this to see your current backend configuration:
```bash
cd backend
railway variables -k
railway status
railway logs --limit 50
```

---

## Required Services in Railway Project

Your Railway project should have **4 services**:

- [ ] **Redis** (Database service)
- [ ] **Backend API** (GitHub repo: `/backend` directory)
- [ ] **Celery Worker** (GitHub repo: `/backend` directory)
- [ ] **Frontend** (GitHub repo: `/frontend` directory)

---

## Backend API Service Configuration

### Service Settings

**Root Directory**: `/backend`

**Start Command** (should use railway.json):
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

### Environment Variables

**Required Variables:**

| Variable | Example | Notes |
|----------|---------|-------|
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGc...` | Service role key (admin access) |
| `SUPABASE_DB_PASSWORD` | `your-db-password` | Database password |
| `OPENAI_API_KEY` | `sk-...` | OpenAI API key |
| `REPLICATE_API_TOKEN` | `r8_...` | Replicate API token |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | **Reference to Redis service** |
| `CORS_ORIGINS` | `https://frontend.railway.app,http://localhost:5173` | Allowed frontend URLs |
| `PORT` | `8000` | (Optional, Railway sets this) |

**Optional Variables:**

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql://postgres:...` | If you want to set directly instead of auto-construct |

### Common Mistakes

❌ **WRONG**: `REDIS_URL=redis://default:...`
✅ **CORRECT**: `REDIS_URL=${{Redis.REDIS_URL}}`

❌ **WRONG**: `REDIS_URL=${{redis.REDIS_URL}}` (if your service is named "Redis")
✅ **CORRECT**: `REDIS_URL=${{Redis.REDIS_URL}}` (match exact service name)

### Health Check

After deployment, test:
```bash
curl https://your-backend.railway.app/health
# Should return: {"status":"healthy"}
```

---

## Celery Worker Service Configuration

### Service Settings

**Root Directory**: `/backend` (same as API)

**Custom Start Command** (CRITICAL):
```
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**Where to set this:**
1. Railway Dashboard → Celery Worker Service
2. Settings → Deploy
3. Custom Start Command → Enter the command above

### Environment Variables

**Required Variables (SAME as Backend API):**

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Same as Backend API |
| `SUPABASE_SERVICE_ROLE_KEY` | Same as Backend API |
| `SUPABASE_DB_PASSWORD` | Same as Backend API |
| `OPENAI_API_KEY` | Same as Backend API |
| `REPLICATE_API_TOKEN` | Same as Backend API |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` (same reference) |

**Variables NOT needed for Worker:**
- ❌ `CORS_ORIGINS` (worker doesn't serve HTTP)
- ❌ `PORT` (worker doesn't listen on a port)

### Common Mistakes

❌ **Using wrong start command**:
- `uvicorn app.main:app` (this is for API, not worker!)

✅ **Correct start command**:
- `celery -A app.celery_app worker --loglevel=info --concurrency=2`

❌ **Missing REDIS_URL**:
- Worker can't connect to Redis, tasks won't be processed

✅ **Has REDIS_URL with service reference**:
- `${{Redis.REDIS_URL}}`

### Expected Logs

Worker logs should show:
```
celery@railway-worker ready.
[INFO/MainProcess] Connected to redis://...
[tasks]
  . app.tasks.video_generation.generate_video_task
```

---

## Redis Service Configuration

### Service Settings

**Type**: Database → Redis

**No configuration needed** - Railway auto-provisions this.

### Check Redis is Active

1. Go to Railway Dashboard
2. Find "Redis" service
3. Status should be: **Active** (green)
4. Should show: **Connected** with number of clients

### Redis Service Name

**IMPORTANT**: The service name must match what you use in `REDIS_URL`

- If service is named **"Redis"** → Use `${{Redis.REDIS_URL}}`
- If service is named **"redis"** → Use `${{redis.REDIS_URL}}`
- If service is named **"redis-production"** → Use `${{redis-production.REDIS_URL}}`

**To check service name:**
1. Railway Dashboard
2. Look at the service name in the sidebar
3. Use EXACT name (case-sensitive) in your variable references

---

## Frontend Service Configuration

### Service Settings

**Root Directory**: `/frontend`

**Start Command** (should use railway.json):
```
npx serve -s dist -l $PORT
```

### Environment Variables

| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `https://backend-api.railway.app` | Your backend Railway URL |
| `VITE_SUPABASE_URL` | `https://xxxxx.supabase.co` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGc...` | Supabase anon/public key |

### Common Mistakes

❌ **Backend URL without https://**:
- `VITE_API_URL=backend-api.railway.app`

✅ **Backend URL with https://**:
- `VITE_API_URL=https://backend-api.railway.app`

❌ **Using localhost**:
- `VITE_API_URL=http://localhost:8000`

✅ **Using Railway domain**:
- `VITE_API_URL=https://backend-api.railway.app`

---

## How to Verify Configuration

### 1. Check Backend API

```bash
cd backend
railway variables -k
```

**Should show:**
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_DB_PASSWORD
- OPENAI_API_KEY
- REPLICATE_API_TOKEN
- REDIS_URL (with ${{...}} reference)
- CORS_ORIGINS
- PORT (optional)

**Check logs:**
```bash
railway logs --limit 50
```

**Should see:**
- `Application startup complete`
- `🌐 CORS allowed origins: ['https://...']`
- No Redis connection errors
- No database connection errors

### 2. Check Celery Worker

**Via Railway Dashboard:**
1. Go to Celery Worker service
2. Check "Variables" tab - should match backend (except CORS_ORIGINS, PORT)
3. Check "Settings" → "Deploy" → Custom Start Command
4. Should be: `celery -A app.celery_app worker --loglevel=info --concurrency=2`

**Check logs in dashboard:**

**Should see:**
```
celery@... ready.
Connected to redis://...
[tasks]
  . app.tasks.video_generation.generate_video_task
```

**Should NOT see:**
- "Error connecting to redis"
- "Cannot connect to database"
- "Module not found"

### 3. Check Redis

**Railway Dashboard:**
- Redis service status: **Active**
- Metrics should show: **Connected clients > 0**

### 4. Check Frontend

```bash
cd frontend
railway variables -k
```

**Should show:**
- VITE_API_URL (with https://)
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY

**Test in browser:**
- Visit your frontend URL
- Open browser console (F12)
- Should see NO CORS errors
- Should be able to login

---

## Debugging Common Issues

### Issue: Backend can't connect to Redis

**Symptoms:**
- Backend logs: "Error connecting to redis"
- Worker logs: "Error: Cannot connect to broker"

**Solution:**
1. Check Redis service name in Railway dashboard
2. Update backend and worker `REDIS_URL`:
   ```
   REDIS_URL=${{<actual-redis-service-name>.REDIS_URL}}
   ```
3. Redeploy both services

### Issue: Worker not processing tasks

**Symptoms:**
- Tasks appear in backend logs as "enqueued"
- Worker logs don't show task execution
- Worker logs show "celery@... ready" but no tasks

**Solution:**
1. Verify worker has SAME `REDIS_URL` as backend
2. Check worker logs for connection errors
3. Verify worker start command is correct:
   ```
   celery -A app.celery_app worker --loglevel=info --concurrency=2
   ```

### Issue: Database connection errors

**Symptoms:**
- "could not connect to server"
- "password authentication failed"
- "database does not exist"

**Solution:**
1. Check `SUPABASE_URL` format: `https://xxxxx.supabase.co`
2. Check `SUPABASE_DB_PASSWORD` is correct
3. If using `DATABASE_URL`, verify format:
   ```
   postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
   ```

### Issue: Frontend shows CORS errors

**Symptoms:**
- Browser console: "blocked by CORS policy"
- API requests fail from frontend

**Solution:**
1. Get exact frontend URL from Railway
2. Update backend `CORS_ORIGINS`:
   ```bash
   cd backend
   railway variables --set "CORS_ORIGINS=https://your-frontend.railway.app,http://localhost:5173"
   ```
3. Backend will auto-redeploy

### Issue: Environment variables not updating

**Symptoms:**
- Changed variables but behavior doesn't change

**Solution:**
1. After changing variables, Railway should auto-redeploy
2. If not, manually redeploy:
   ```bash
   cd backend
   railway up --detach
   ```

---

## Complete Configuration Example

### Backend API Variables

```bash
SUPABASE_URL=https://abcd1234.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=mySecurePassword123
OPENAI_API_KEY=sk-proj-abc123...
REPLICATE_API_TOKEN=r8_abc123...
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=https://frontend-abc.railway.app,http://localhost:5173,https://app.zapcut.video
PORT=8000
```

### Celery Worker Variables

```bash
SUPABASE_URL=https://abcd1234.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=mySecurePassword123
OPENAI_API_KEY=sk-proj-abc123...
REPLICATE_API_TOKEN=r8_abc123...
REDIS_URL=${{Redis.REDIS_URL}}
```

### Frontend Variables

```bash
VITE_API_URL=https://backend-api-abc.railway.app
VITE_SUPABASE_URL=https://abcd1234.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Quick Commands to Share Configuration

Run these and share the output with me:

```bash
# Backend configuration
cd backend
echo "=== Backend Variables ==="
railway variables -k
echo ""
echo "=== Backend Status ==="
railway status
echo ""
echo "=== Backend Recent Logs ==="
railway logs --limit 30

# Frontend configuration
cd ../frontend
echo "=== Frontend Variables ==="
railway variables -k
echo ""
echo "=== Frontend Status ==="
railway status
```

Also please check in Railway Dashboard:
1. What is the exact Redis service name?
2. Does Celery Worker service exist?
3. What is the Celery Worker custom start command?
4. What variables does Celery Worker have?

---

**Share this information and I can help identify what's missing!**
