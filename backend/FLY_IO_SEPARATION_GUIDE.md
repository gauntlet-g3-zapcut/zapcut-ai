# Railway: Separating FastAPI and Celery Workers

## Problem
Running Celery and FastAPI in the same service can cause:
- Health check failures (Celery startup delays FastAPI)
- Resource contention (both processes competing for CPU/memory)
- Deployment complexity (both need to restart together)
- Scaling issues (can't scale API and Worker independently)

## Solution: Separate Services

### Current Setup (Problematic)
```
Service: api
├── FastAPI (uvicorn)
└── Celery Worker (background process)
```

### Recommended Setup
```
Service 1: api
└── FastAPI (uvicorn) only

Service 2: worker
└── Celery Worker only
```

## Implementation Steps

### 1. Create Separate Railway Services

#### Via Dashboard:
1. In your Railway project, click "New" → "Empty Service"
2. Name it "worker" (or "api-worker")
3. Set root directory to `backend`
4. Set start command to `./start-worker.sh`
5. No public domain needed (background service)

#### Via CLI:
```bash
cd backend
railway service create worker
railway service use worker
railway variables set START_COMMAND="./start-worker.sh"
```

### 2. Share Environment Variables

Both services need the same environment variables. In Railway:

**Option A: Set in Project (Shared)**
- Go to Project → Variables
- Variables set here are available to all services

**Option B: Set per Service**
- Go to each service → Variables
- Set the same variables for both

Required variables:
- `DATABASE_URL` - Automatically shared if PostgreSQL is in same project
- `REDIS_URL` - Automatically shared if Redis is in same project
- `API_URL` - Your Railway API domain
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `OPENAI_API_KEY`
- `REPLICATE_API_TOKEN`
- `ELEVENLABS_API_KEY`

### 3. Verify Service Separation

**API Service:**
- Root directory: `backend`
- Start command: `./start.sh` (default, or from `railway.toml`)
- Public domain: Yes (for HTTP requests)
- Health check: `/health` endpoint

**Worker Service:**
- Root directory: `backend`
- Start command: `./start-worker.sh`
- Public domain: No (background service)
- Health check: N/A (no HTTP endpoint)

### 4. Deploy Both Services

```bash
# Deploy API
railway service use api
railway up

# Deploy Worker
railway service use worker
railway up
```

## Current Status

- ✅ `start.sh` runs FastAPI only
- ✅ `start-worker.sh` runs Celery worker only
- ✅ Health check endpoint at `/health`
- ✅ Services can be deployed independently

## Testing

After separation, test:

```bash
# Test FastAPI health (replace with your Railway domain)
curl https://your-api.railway.app/health

# Test campaign answers endpoint
curl -X POST https://your-api.railway.app/api/brands/{brandId}/campaign-answers \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"answers": {"style":"x","audience":"y","emotion":"z","pacing":"p","colors":"c"}}'

# Check worker logs
railway service use worker
railway logs
```

## Monitoring

### API Service
- View logs: Railway dashboard → API service → Logs
- Check health: `curl https://your-api.railway.app/health`
- Monitor metrics: Railway dashboard → API service → Metrics

### Worker Service
- View logs: Railway dashboard → Worker service → Logs
- Check active tasks: `railway run celery -A app.celery_app inspect active`
- Monitor resource usage: Railway dashboard → Worker service → Metrics

## Benefits of Separation

1. **Independent Scaling**: Scale API and Worker based on different needs
2. **Independent Deployments**: Deploy API without restarting Worker
3. **Better Resource Management**: Allocate resources per service
4. **Clearer Monitoring**: Separate logs and metrics for each service
5. **Health Checks**: API health checks don't affect Worker

## Notes

- Railway automatically provides `$PORT` for API service
- Worker service doesn't need a port (no HTTP endpoint)
- Both services can share the same Redis and PostgreSQL instances
- Railway handles service discovery automatically
- Solo pool is used for Celery to reduce memory usage
