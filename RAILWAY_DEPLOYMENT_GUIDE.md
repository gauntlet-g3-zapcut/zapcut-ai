# Adcraft Railway Deployment Guide

Complete guide to deploy Adcraft on Railway from scratch.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         ADCRAFT RAILWAY PROJECT                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Redis Instance                              │
│     └─ Message broker for Celery               │
│                                                 │
│  2. Backend API (FastAPI)                       │
│     ├─ Handles HTTP requests                   │
│     ├─ Enqueues video generation tasks         │
│     └─ Connects to: Redis, Supabase DB         │
│                                                 │
│  3. Celery Worker                               │
│     ├─ Processes video generation tasks        │
│     ├─ Long-running async operations           │
│     └─ Connects to: Redis, Supabase DB         │
│                                                 │
│  4. Frontend (React/Vite SPA)                   │
│     ├─ Static site served via Nixpacks         │
│     └─ Connects to: Backend API, Supabase Auth │
│                                                 │
│  External Services:                             │
│  - Supabase PostgreSQL (database)              │
│  - Supabase Auth (authentication)              │
│  - OpenAI API (AI generation)                  │
│  - Replicate API (video generation)            │
│  - AWS S3 (file storage)                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional but recommended)
   ```bash
   npm install -g @railway/cli
   railway login
   ```
3. Existing credentials:
   - Supabase project URL and keys
   - OpenAI API key
   - Replicate API token
   - AWS S3 credentials (if using)

## Step 1: Create New Railway Project

1. Go to https://railway.app/new
2. Click "Empty Project"
3. Name it: `adcraft-production`

## Step 2: Add Redis Service

1. In your Railway project, click "New Service"
2. Select "Database" → "Redis"
3. Railway will auto-provision Redis
4. Copy the `REDIS_URL` from the service variables (you'll need this later)

## Step 3: Deploy Backend API

### 3.1 Create Backend Service

1. Click "New Service" → "GitHub Repo"
2. Connect your repository
3. Select the repository
4. Set root directory: `/backend`
5. Railway will detect the configuration from `backend/railway.json`

### 3.2 Configure Backend Environment Variables

Add these environment variables to the Backend API service:

**Required Variables:**
```
DATABASE_URL=<from Supabase or leave blank to auto-construct>
REDIS_URL=${{Redis.REDIS_URL}}
OPENAI_API_KEY=<your-openai-key>
REPLICATE_API_TOKEN=<your-replicate-token>
SUPABASE_URL=<your-supabase-url>
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-key>
SUPABASE_DB_PASSWORD=<your-supabase-db-password>
CORS_ORIGINS=https://app.zapcut.video,${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
PORT=8000
```

**How to reference Redis:**
- Railway automatically creates connection variables
- Use `${{Redis.REDIS_URL}}` to reference the Redis service URL

**Frontend URL:**
- Initially, deploy backend first, then come back and add frontend URL
- Or use a placeholder and update later

### 3.3 Deploy Backend

1. Backend will auto-deploy on push
2. Check logs for successful startup
3. Note the public domain (e.g., `backend-production.railway.app`)

### 3.4 Run Database Migrations

After first deployment, run migrations:

1. Open Railway service → "Settings" → "Deployments"
2. Click on latest deployment → "Deploy Logs"
3. OR use Railway CLI:
   ```bash
   railway run alembic upgrade head
   ```

## Step 4: Deploy Celery Worker

### 4.1 Create Worker Service

1. Click "New Service" → "GitHub Repo"
2. Select the SAME repository
3. Set root directory: `/backend`
4. Under "Settings" → "Deploy":
   - Change the start command to use worker config
   - Or manually set: `celery -A app.celery_app worker --loglevel=info --concurrency=2`

### 4.2 Configure Service Settings

1. Go to service "Settings"
2. Under "Deploy" → "Custom Start Command":
   ```
   celery -A app.celery_app worker --loglevel=info --concurrency=2
   ```
3. OR create a separate deployment with `backend/railway.worker.json`

### 4.3 Set Worker Environment Variables

**Copy ALL environment variables from Backend API service:**
```
DATABASE_URL=<same as backend>
REDIS_URL=${{Redis.REDIS_URL}}
OPENAI_API_KEY=<same as backend>
REPLICATE_API_TOKEN=<same as backend>
SUPABASE_URL=<same as backend>
SUPABASE_SERVICE_ROLE_KEY=<same as backend>
SUPABASE_DB_PASSWORD=<same as backend>
```

**Note:** Worker does NOT need PORT or CORS_ORIGINS

### 4.4 Deploy Worker

Worker will auto-deploy. Check logs for:
```
[tasks]
  . app.tasks.video_generation.generate_video_task
[INFO/MainProcess] Connected to redis://...
[INFO/MainProcess] celery@... ready.
```

## Step 5: Deploy Frontend

### 5.1 Create Frontend Service

1. Click "New Service" → "GitHub Repo"
2. Select the SAME repository
3. Set root directory: `/frontend`
4. Railway will detect configuration from `frontend/railway.json`

### 5.2 Configure Frontend Environment Variables

```
VITE_API_URL=https://<backend-domain>.railway.app
VITE_SUPABASE_URL=<your-supabase-url>
VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

**Important:**
- Replace `<backend-domain>` with your actual backend Railway domain
- Get Supabase anon key from Supabase dashboard → Settings → API

### 5.3 Deploy Frontend

1. Frontend will auto-deploy
2. Build takes ~2-3 minutes
3. Note the public domain (e.g., `frontend-production.railway.app`)

### 5.4 Update Backend CORS

Go back to Backend API service and update `CORS_ORIGINS`:
```
CORS_ORIGINS=https://<frontend-domain>.railway.app,https://app.zapcut.video,http://localhost:5173
```

Redeploy backend after updating CORS.

## Step 6: Configure Custom Domains (Optional)

### 6.1 Backend Domain
1. Go to Backend service → "Settings" → "Domains"
2. Click "Generate Domain" for Railway subdomain
3. OR add custom domain: `api.adcraft.com`
4. Update DNS records as shown

### 6.2 Frontend Domain
1. Go to Frontend service → "Settings" → "Domains"
2. Add custom domain: `app.adcraft.com`
3. Update DNS with CNAME record

### 6.3 Update Environment Variables

After adding custom domains, update:
- Frontend: `VITE_API_URL` to use custom backend domain
- Backend: `CORS_ORIGINS` to include custom frontend domain

## Step 7: Verify Deployment

### 7.1 Check All Services are Running

Visit Railway dashboard and verify:
- ✅ Redis: Status "Running"
- ✅ Backend API: Status "Running"
- ✅ Celery Worker: Status "Running"
- ✅ Frontend: Status "Running"

### 7.2 Test Backend API

```bash
curl https://<backend-domain>.railway.app/health
# Should return: {"status":"healthy"}

curl https://<backend-domain>.railway.app/
# Should return: {"message":"AdCraft API","status":"running"}
```

### 7.3 Test Frontend

1. Visit `https://<frontend-domain>.railway.app`
2. Should load Adcraft login page
3. Try logging in with Supabase credentials

### 7.4 Test Video Generation Pipeline

1. Log into frontend
2. Create a test campaign
3. Generate a video
4. Check Celery Worker logs for task processing:
   ```
   [INFO/ForkPoolWorker-1] Task app.tasks.video_generation.generate_video_task[...]
   [INFO/ForkPoolWorker-1] Video generation started...
   ```

### 7.5 Check Database Connection

Backend logs should show:
```
INFO:     Application startup complete.
🌐 CORS allowed origins: ['https://...']
```

No database connection errors.

## Troubleshooting

### Backend won't start

**Check logs for:**
- Missing environment variables
- Database connection errors
- Redis connection errors

**Fix:**
1. Verify all env vars are set
2. Check `DATABASE_URL` format
3. Verify `${{Redis.REDIS_URL}}` reference is correct

### Celery Worker not processing tasks

**Check:**
1. Worker logs show "Connected to redis"
2. Worker and API use same `REDIS_URL`
3. Worker has all required env vars (DATABASE_URL, API keys)

**Debug:**
```bash
# In Railway CLI
railway logs --service <worker-service-name>
```

### Frontend can't connect to backend

**Check:**
1. `VITE_API_URL` is correct
2. Backend `CORS_ORIGINS` includes frontend URL
3. Backend is running and accessible
4. No HTTPS/HTTP mismatch

**Debug:**
Open browser console on frontend, check for CORS errors

### Database migration issues

**Run manually:**
```bash
railway run --service backend-api alembic upgrade head
```

### Redis connection timeout

**Check:**
1. Redis service is running
2. `REDIS_URL` format is correct: `redis://...`
3. Both API and Worker can reach Redis

## Cost Estimates

Railway pricing (as of 2024):
- **Starter Plan**: $5/month (required)
- **Redis**: ~$5/month (512MB)
- **Compute**: Usage-based
  - Backend API: ~$5-10/month
  - Worker: ~$5-10/month
  - Frontend: ~$2-5/month

**Total estimate**: $20-35/month

**Free tier**: Railway offers $5 in free credits per month

## Monitoring & Logs

### View Logs

**Via Dashboard:**
1. Go to service
2. Click "Deployments"
3. Click latest deployment
4. View "Deploy Logs" or "Build Logs"

**Via CLI:**
```bash
railway logs --service backend-api
railway logs --service celery-worker
railway logs --service frontend
```

### Set up Alerts

1. Go to Project Settings → "Integrations"
2. Connect Slack/Discord for deployment notifications
3. Get notified on deploy failures

## Deployment Automation

### Auto-deploy on Git Push

Railway auto-deploys on push to main branch by default.

**To disable:**
1. Service Settings → "Deployments"
2. Toggle "Automatic Deployments" off

### Deploy Specific Branch

1. Service Settings → "Deployments"
2. Set "Deploy Branch" to your preferred branch (e.g., `production`)

## Rollback

### Rollback to Previous Deployment

1. Go to service → "Deployments"
2. Find working deployment
3. Click "⋮" menu → "Redeploy"

## Scaling

### Vertical Scaling (More Resources)

1. Service Settings → "Resources"
2. Adjust memory/CPU limits
3. Redeploy

### Horizontal Scaling (More Workers)

For Celery workers:
1. Increase `--concurrency` value in start command
2. OR deploy multiple worker services

**Example:**
```
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

## Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **Service Keys**: Use Railway's built-in secret management
3. **CORS**: Only allow specific origins (don't use `*`)
4. **HTTPS**: Railway provides SSL automatically
5. **Rate Limiting**: Add to FastAPI for production

## Next Steps

After successful deployment:

1. ✅ Set up monitoring (e.g., Sentry)
2. ✅ Configure custom domains
3. ✅ Set up CI/CD for automated testing
4. ✅ Add rate limiting and API authentication
5. ✅ Configure backups for database
6. ✅ Set up error tracking (Sentry, LogRocket)
7. ✅ Add performance monitoring (DataDog, New Relic)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Adcraft Issues: Check your repository issues

---

**Deployment Date**: ___________
**Deployed By**: ___________
**Backend URL**: ___________
**Frontend URL**: ___________
**Redis Instance**: ___________
