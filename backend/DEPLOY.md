# Railway Deployment Guide

## Prerequisites

1. Create a Railway account: https://railway.app
2. Install Railway CLI (optional, for local management):
```bash
npm i -g @railway/cli
```

## Initial Deployment

### 1. Create Railway Project

1. Go to https://railway.app and create a new project
2. Connect your GitHub repository or deploy from the Railway dashboard

### 2. Create Services

Railway supports multiple services from one repository. You'll need:

1. **API Service** - FastAPI application
2. **Worker Service** - Celery worker (optional, can run in same service or separate)

#### Option A: Deploy via Railway Dashboard

1. Click "New" → "GitHub Repo" → Select your repository
2. Select the `backend` directory as the root directory
3. Railway will auto-detect the Python project and use Nixpacks

#### Option B: Deploy via Railway CLI

```bash
cd backend
railway login
railway init
railway up
```

### 3. Add PostgreSQL Database

1. In Railway dashboard, click "New" → "Database" → "Add PostgreSQL"
2. Railway will automatically set `DATABASE_URL` environment variable
3. The database will be available to all services in the project

### 4. Add Redis (Required for Celery)

1. In Railway dashboard, click "New" → "Database" → "Add Redis"
2. Railway will automatically set `REDIS_URL` environment variable
3. Share this Redis instance with both API and Worker services

### 5. Set Environment Variables

In Railway dashboard, go to your service → Variables tab, and add:

**Required Variables:**
- `DATABASE_URL` - Automatically set if you added PostgreSQL
- `REDIS_URL` - Automatically set if you added Redis
- `API_URL` - Your Railway public domain (e.g., `https://your-api.railway.app`) or custom domain
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - Supabase JWT secret (optional, for HS256)
- `OPENAI_API_KEY` - OpenAI API key
- `REPLICATE_API_TOKEN` - Replicate API token
- `ELEVENLABS_API_KEY` - ElevenLabs API key
- `CORS_ORIGINS` - Comma-separated list of allowed origins (e.g., `http://localhost:5173,https://app.zapcut.video`)

**Optional Variables:**
- `REPLICATE_WEBHOOK_SECRET` - For webhook verification
- `SUPABASE_DB_PASSWORD` - If not using DATABASE_URL directly
- `SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_ACCESS_KEY`, `SUPABASE_S3_SECRET_KEY` - For S3 storage

**Note:** Railway automatically provides `PORT` environment variable - no need to set it manually.

### 6. Configure Service Settings

For the API service:
- **Root Directory:** `backend`
- **Start Command:** Railway will use `railway.toml` or auto-detect from `start.sh`
- **Health Check Path:** `/health` (Railway will automatically monitor this)

For the Worker service (if separate):
- **Root Directory:** `backend`
- **Start Command:** `./start-worker.sh`
- **No public endpoint needed** - Worker runs as background service

### 7. Deploy

Railway will automatically deploy on:
- Push to connected branch (if GitHub integration is enabled)
- Manual deploy from dashboard
- Using CLI: `railway up`

### 8. Initialize Database

After deployment, initialize the database tables:

```bash
# Get your Railway service URL from the dashboard
curl -X POST https://your-api.railway.app/init-db
```

Or use Railway CLI:
```bash
railway run curl -X POST http://localhost:$PORT/init-db
```

## Updating Environment Variables

1. Go to Railway dashboard → Your service → Variables
2. Add or update variables as needed
3. Railway will automatically redeploy if "Redeploy on Variable Change" is enabled

## Viewing Logs

### Via Dashboard
1. Go to Railway dashboard → Your service → Deployments → Click on a deployment
2. View real-time logs in the Logs tab

### Via CLI
```bash
railway logs
```

## Scaling

Railway automatically scales based on traffic. You can also:

1. Go to service settings → Resources
2. Adjust CPU and Memory limits
3. Railway will handle horizontal scaling automatically

## Health Checks

Railway automatically monitors the `/health` endpoint. If it fails:
- Railway will restart the service
- You'll see alerts in the dashboard
- Check logs for errors

## Troubleshooting

### Check service status:
```bash
railway status
```

### View service info:
```bash
railway info
```

### Restart service:
Via dashboard: Service → Settings → Restart
Via CLI: Service will auto-restart on deploy

### Run commands in service:
```bash
railway run <command>
```

## Custom Domain

1. Go to Railway dashboard → Your service → Settings → Domains
2. Click "Generate Domain" or "Add Custom Domain"
3. For custom domains, update DNS records as instructed
4. Railway will automatically provision SSL certificate

## Monitoring

- View metrics in Railway dashboard (CPU, Memory, Network)
- Set up alerts for service failures
- Monitor logs in real-time
- View deployment history and rollback if needed

## Worker Service Setup

If running Celery worker as a separate service:

1. Create a new service in the same Railway project
2. Set root directory to `backend`
3. Set start command to `./start-worker.sh`
4. Share the same environment variables (especially `REDIS_URL` and `DATABASE_URL`)
5. No public domain needed - worker runs as background service

## Notes

- Railway automatically provides `$PORT` environment variable
- Railway supports both Dockerfile and Nixpacks builds
- Services in the same project can share databases and environment variables
- Railway handles SSL certificates automatically
- Health check endpoint at `/health` is monitored automatically
