# Railway Deployment Guide

This guide explains how to deploy the backend to Railway with two separate services: FastAPI server and Celery worker.

## Architecture

The backend consists of two separate services that run independently:

1. **FastAPI Server** (`web` process)
   - Handles HTTP API requests
   - Serves REST API endpoints
   - Runs on port specified by `$PORT` environment variable

2. **Celery Worker** (`worker` process)
   - Processes background tasks
   - Handles video generation and other async jobs
   - Connects to Redis for task queue

## Railway Setup

### Option 1: Automatic Detection (Recommended)

Railway will automatically detect both services from the `Procfile`:

```procfile
web: bash start.sh
worker: bash start-worker.sh
```

When you deploy, Railway will:
1. Detect the Procfile
2. Create two separate services automatically
3. Each service will use the corresponding start command

### Option 2: Manual Service Creation

If automatic detection doesn't work, create services manually:

1. **Create First Service (API Server)**
   - Name: `api` or `web`
   - Root Directory: `backend`
   - Start Command: `bash start.sh`
   - Environment Variables: See below

2. **Create Second Service (Worker)**
   - Name: `worker` or `queue`
   - Root Directory: `backend`
   - Start Command: `bash start-worker.sh`
   - Environment Variables: Same as API server

## Required Environment Variables

Both services need these environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis (for Celery)
REDIS_URL=redis://host:port

# API Keys
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DB_PASSWORD=your_password

# CORS (optional, has defaults)
CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video
```

## Service-Specific Configuration

### FastAPI Server (`web`)
- Requires: `PORT` (set automatically by Railway)
- Optional: `CORS_ORIGINS` (defaults included)
- Will start even if Redis is unavailable (but queue features won't work)

### Celery Worker (`worker`)
- Requires: `REDIS_URL` (worker will start but won't process tasks if missing)
- Will gracefully handle missing Redis connection
- Uses concurrency=2 by default (adjust in `start-worker.sh` if needed)

## Verification

After deployment, verify both services:

1. **Check API Server:**
   ```bash
   curl https://your-api.railway.app/health
   # Should return: {"status": "healthy"}
   ```

2. **Check Worker:**
   - Check Railway logs for worker service
   - Should see: "✅ Celery app imported successfully"
   - Should see: "celery@hostname ready"

## Troubleshooting

### Worker not processing tasks
- Verify `REDIS_URL` is set correctly
- Check that Redis service is accessible from worker
- Check worker logs for connection errors

### API server can't connect to database
- Verify `DATABASE_URL` is set correctly
- Check database service is accessible
- Run migrations: `python -m alembic upgrade head` (from backend directory)

### Both services failing to start
- Check Python version compatibility
- Verify all dependencies in `requirements.txt` are installable
- Check Railway build logs for errors

## Local Testing

Test both services locally before deploying:

```bash
# Terminal 1: Start API server
cd backend
bash start.sh

# Terminal 2: Start worker
cd backend
bash start-worker.sh
```

Both should start successfully with proper environment variables set.

