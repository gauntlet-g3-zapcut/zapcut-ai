# Railway Deployment Guide

This guide covers deploying the FastAPI API and Celery worker as separate Railway services.

## Architecture

- **API Service**: FastAPI application handling HTTP requests
- **Worker Service**: Celery worker processing background tasks

Both services share the same codebase but run different processes. They can run in the same Railway project and share databases/environment variables.

## Prerequisites

1. Railway account: https://railway.app
2. Railway CLI (optional): `npm i -g @railway/cli`
3. Redis instance (Railway provides managed Redis)

## Initial Setup

### 1. Create Railway Project

1. Go to Railway dashboard → New Project
2. Connect your GitHub repository or deploy from CLI

### 2. Add PostgreSQL Database

1. In Railway project, click "New" → "Database" → "Add PostgreSQL"
2. Railway automatically sets `DATABASE_URL` for all services in the project

### 3. Add Redis Database

1. In Railway project, click "New" → "Database" → "Add Redis"
2. Railway automatically sets `REDIS_URL` for all services in the project
3. Both API and Worker services will use this Redis instance

### 4. Create API Service

#### Via Dashboard:
1. Click "New" → "GitHub Repo" or "Empty Service"
2. Set root directory to `backend`
3. Railway will auto-detect Python and use `railway.toml` or `start.sh`

#### Via CLI:
```bash
cd backend
railway init
railway service create api
railway up
```

### 5. Create Worker Service

#### Via Dashboard:
1. Click "New" → "Empty Service" in the same project
2. Set root directory to `backend`
3. Set start command to `./start-worker.sh`
4. No public domain needed (background service)

#### Via CLI:
```bash
railway service create worker
railway service use worker
railway variables set START_COMMAND="./start-worker.sh"
railway up
```

### 6. Set Environment Variables

Set these in Railway dashboard for both services (or use shared variables):

**Required:**
- `DATABASE_URL` - Automatically set from PostgreSQL
- `REDIS_URL` - Automatically set from Redis
- `API_URL` - Your Railway API domain (e.g., `https://your-api.railway.app`)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret for token validation
- `OPENAI_API_KEY` - OpenAI API key
- `REPLICATE_API_TOKEN` - Replicate API token
- `ELEVENLABS_API_KEY` - ElevenLabs API key

**Optional:**
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `REPLICATE_WEBHOOK_SECRET` - For webhook verification

**Note:** Railway automatically provides `PORT` - don't set it manually.

## Deployment

### Deploy API Service

Railway will automatically deploy on:
- Push to connected branch (if GitHub integration enabled)
- Manual deploy from dashboard
- CLI: `railway up` (in API service context)

### Deploy Worker Service

1. Switch to worker service in Railway dashboard
2. Deploy manually or via CLI: `railway service use worker && railway up`

## Health Checks

The API includes a `/health` endpoint that Railway monitors automatically:

```bash
# Test health check (replace with your Railway domain)
curl https://your-api.railway.app/health
```

Expected response:
```json
{"status": "ok", "service": "fastapi"}
```

## Monitoring

### Check API Status

Via Dashboard:
1. Go to API service → Deployments
2. View logs and metrics

Via CLI:
```bash
railway service use api
railway status
railway logs
```

### Check Worker Status

Via Dashboard:
1. Go to Worker service → Deployments
2. View logs for task processing

Via CLI:
```bash
railway service use worker
railway status
railway logs
```

### Run Commands

```bash
# In API service context
railway run python -c "from app.database import get_engine; print('DB connected')"

# In Worker service context
railway run celery -A app.celery_app inspect active
```

## Scaling

Railway automatically scales based on traffic. You can also:

1. Go to service → Settings → Resources
2. Adjust CPU and Memory limits
3. Railway handles horizontal scaling automatically

## Troubleshooting

### API Not Responding

1. Check health endpoint: `curl https://your-api.railway.app/health`
2. View logs in Railway dashboard
3. Check service status: `railway status`
4. Verify environment variables are set correctly

### Worker Not Processing Tasks

1. Check Redis connection in worker logs
2. Verify `REDIS_URL` is set in worker service
3. Check worker logs: `railway logs` (in worker service context)
4. Verify worker service is running (not paused)

### Database Connection Issues

1. Verify `DATABASE_URL` is set (automatically set if PostgreSQL is in same project)
2. Check database is running in Railway dashboard
3. Test connection: `railway run python -c "from app.database import get_engine; engine = get_engine(); print('Connected')"`

### Both Services on Same Service

If you see both processes running in one service:
1. Verify you created separate services in Railway
2. Check API service uses `./start.sh` (default)
3. Check Worker service uses `./start-worker.sh` as start command
4. Ensure services are separate in Railway dashboard

## Environment Variables

Both services need these variables (can be shared in Railway project):

**Required:**
- `DATABASE_URL`: PostgreSQL connection (auto-set from Railway PostgreSQL)
- `REDIS_URL`: Redis connection (auto-set from Railway Redis)
- `API_URL`: Public API domain for webhook callbacks
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `SUPABASE_JWT_SECRET`: JWT secret for token validation
- `OPENAI_API_KEY`: OpenAI API key
- `REPLICATE_API_TOKEN`: Replicate API token
- `ELEVENLABS_API_KEY`: ElevenLabs API key

**Optional:**
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `REPLICATE_WEBHOOK_SECRET`: For webhook verification

**Auto-provided by Railway:**
- `PORT`: Automatically set - don't configure manually

## Service Configuration

### API Service
- **Root Directory:** `backend`
- **Start Command:** `./start.sh` (uses `railway.toml` or auto-detected)
- **Public Domain:** Automatically generated or custom domain
- **Health Check:** `/health` (monitored automatically)

### Worker Service
- **Root Directory:** `backend`
- **Start Command:** `./start-worker.sh`
- **Public Domain:** Not needed (background service)
- **Health Check:** Not applicable (no HTTP endpoint)

## Notes

- Railway automatically provides `$PORT` environment variable
- Services in the same project can share databases and environment variables
- Railway handles SSL certificates automatically
- Health check endpoint at `/health` is monitored automatically
- Worker service runs continuously to process background tasks
- Solo pool is used for Celery to reduce memory usage
- Railway supports both Dockerfile and Nixpacks builds
