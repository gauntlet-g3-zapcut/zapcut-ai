# Quick Deployment Reference

## First-Time Setup

### Via Railway Dashboard

1. **Create Project**
   - Go to Railway dashboard → New Project
   - Connect GitHub repository or create empty project

2. **Add Databases**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Click "New" → "Database" → "Add Redis"

3. **Create API Service**
   - Click "New" → "GitHub Repo" or "Empty Service"
   - Set root directory to `backend`
   - Railway auto-detects Python and uses `railway.toml` or `start.sh`

4. **Create Worker Service**
   - Click "New" → "Empty Service"
   - Set root directory to `backend`
   - Set start command to `./start-worker.sh`

5. **Set Environment Variables**
   - Go to each service → Variables tab
   - Add required variables (see below)

### Via Railway CLI

```bash
cd backend

# Initialize Railway project
railway login
railway init

# Create services
railway service create api
railway service create worker

# Set environment variables (for API service)
railway service use api
railway variables set \
  API_URL="https://your-api.railway.app" \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_SERVICE_ROLE_KEY="your-key" \
  SUPABASE_JWT_SECRET="your-secret" \
  OPENAI_API_KEY="your-key" \
  REPLICATE_API_TOKEN="your-token" \
  ELEVENLABS_API_KEY="your-key" \
  CORS_ORIGINS="http://localhost:5173,https://app.zapcut.video"

# Set environment variables (for Worker service)
railway service use worker
railway variables set \
  API_URL="https://your-api.railway.app" \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_SERVICE_ROLE_KEY="your-key" \
  SUPABASE_JWT_SECRET="your-secret" \
  OPENAI_API_KEY="your-key" \
  REPLICATE_API_TOKEN="your-token" \
  ELEVENLABS_API_KEY="your-key"

# Deploy
railway service use api
railway up

railway service use worker
railway up
```

**Note:** `DATABASE_URL` and `REDIS_URL` are automatically set when you add PostgreSQL and Redis databases in Railway.

## Deploy Commands

### Via Dashboard
- Push to connected branch (auto-deploys)
- Click "Deploy" button in service

### Via CLI
```bash
# Deploy API
railway service use api
railway up

# Deploy Worker
railway service use worker
railway up

# Deploy Both (from project root)
railway service use api && railway up && \
railway service use worker && railway up
```

## Verify Deployment

```bash
# Get your Railway domain from dashboard, then:
curl https://your-api.railway.app/health

# Check API status
railway service use api
railway status
railway logs

# Check Worker status
railway service use worker
railway status
railway logs
```

## Key Files

- `railway.toml` - Railway configuration for API service
- `start.sh` - Starts FastAPI only (uses `$PORT` from Railway)
- `start-worker.sh` - Starts Celery worker only
- `Dockerfile` - Alternative build method (Railway can use this or Nixpacks)

## Environment Variables Quick Reference

**Auto-set by Railway:**
- `DATABASE_URL` - From PostgreSQL database
- `REDIS_URL` - From Redis database
- `PORT` - Automatically provided

**Required (set manually):**
- `API_URL` - Your Railway API domain
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - JWT secret
- `OPENAI_API_KEY` - OpenAI API key
- `REPLICATE_API_TOKEN` - Replicate API token
- `ELEVENLABS_API_KEY` - ElevenLabs API key

**Optional:**
- `CORS_ORIGINS` - Comma-separated allowed origins
- `REPLICATE_WEBHOOK_SECRET` - For webhook verification
