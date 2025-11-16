# Quick Deployment Reference

## First-Time Setup

```bash
# 1. Create API app
fly apps create zapcut-api

# 2. Create Worker app
fly apps create zapcut-worker

# 3. Set secrets for both apps
fly secrets set \
  DATABASE_URL="your-database-url" \
  REDIS_URL="your-redis-url" \
  SUPABASE_SERVICE_ROLE_KEY="your-key" \
  SUPABASE_JWT_SECRET="your-secret" \
  OPENAI_API_KEY="your-key" \
  REPLICATE_API_TOKEN="your-token" \
  -a zapcut-api

fly secrets set \
  DATABASE_URL="your-database-url" \
  REDIS_URL="your-redis-url" \
  SUPABASE_SERVICE_ROLE_KEY="your-key" \
  SUPABASE_JWT_SECRET="your-secret" \
  OPENAI_API_KEY="your-key" \
  REPLICATE_API_TOKEN="your-token" \
  -a zapcut-worker
```

## Deploy Commands

```bash
# Deploy API
fly deploy --config fly.api.toml -a zapcut-api

# Deploy Worker
fly deploy --config fly.worker.toml -a zapcut-worker

# Deploy Both
fly deploy --config fly.api.toml -a zapcut-api && \
fly deploy --config fly.worker.toml -a zapcut-worker
```

## Verify Deployment

```bash
# Check API health
curl https://zapcut-api.fly.dev/health

# Check API status
fly status -a zapcut-api

# Check Worker status
fly status -a zapcut-worker

# View logs
fly logs -a zapcut-api
fly logs -a zapcut-worker
```

## Key Files

- `fly.api.toml` - Configuration for FastAPI app
- `fly.worker.toml` - Configuration for Celery worker
- `start.sh` - Starts FastAPI only
- `start-worker.sh` - Starts Celery worker only

