# Fly.io: Separating FastAPI and Celery Workers

## Problem
Running Celery and FastAPI in the same machine causes:
- Health check failures (Celery startup delays FastAPI)
- Machine lease issues (proxy can't route traffic)
- Request timeouts (30+ seconds)
- Proxy errors: "could not find a good candidate within 1 attempts"

## Solution: Separate Machines

### Current Setup (Problematic)
```
Machine: zapcut-api
├── FastAPI (uvicorn)
└── Celery Worker (background process)
```

### Recommended Setup
```
Machine 1: zapcut-api
└── FastAPI (uvicorn) only

Machine 2: zapcut-worker (new app)
└── Celery Worker only
```

## Implementation Steps

### Option 1: Separate Fly.io App (Recommended)

1. **Create new app for Celery worker:**
```bash
cd backend
fly apps create zapcut-worker
```

2. **Create fly.worker.toml:**
```toml
app = "zapcut-worker"
primary_region = "iad"

[build]

[env]
  REDIS_URL = "rediss://..."  # Same Redis as main app

[processes]
  worker = "celery -A app.celery_app worker --loglevel=info --pool=solo"

[[services]]
  processes = ["worker"]
  protocol = "tcp"
  internal_port = 8000
```

3. **Update start.sh to NOT run Celery:**
```bash
# Already done - Celery only runs if RUN_CELERY_WORKER=true
```

4. **Deploy worker:**
```bash
fly deploy --app zapcut-worker --config fly.worker.toml
```

### Option 2: Same App, Different Processes (Alternative)

1. **Update fly.toml:**
```toml
[processes]
  app = "./start.sh"           # FastAPI only
  worker = "celery -A app.celery_app worker --loglevel=info --pool=solo"

[[services]]
  processes = ["app"]
  # ... existing config

[[services]]
  processes = ["worker"]
  protocol = "tcp"
  internal_port = 8001  # Different port
```

2. **Scale processes:**
```bash
fly scale count app=1 worker=1 --app zapcut-api
```

## Current Status

- ✅ `start.sh` updated to NOT run Celery by default
- ✅ Health check timeout reduced to 3s
- ✅ Health endpoint optimized
- ⚠️ Still need to separate machines for production

## Testing

After separation, test:
```bash
# Test FastAPI health
curl https://zapcut-api.fly.dev/health

# Test campaign answers endpoint
curl -X POST https://zapcut-api.fly.dev/api/brands/{brandId}/campaign-answers \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"answers": {"style":"x","audience":"y","emotion":"z","pacing":"p","colors":"c"}}'

# Check worker logs
fly logs --app zapcut-worker
```

## Temporary Workaround

If you need Celery in same machine temporarily:
```bash
fly secrets set RUN_CELERY_WORKER=true --app zapcut-api
```

But this will likely cause the same issues. Separation is the proper fix.

