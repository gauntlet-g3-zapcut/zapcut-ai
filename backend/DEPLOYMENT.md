# Fly.io Deployment Guide

This guide covers deploying the FastAPI API and Celery worker as separate Fly.io applications.

## Architecture

- **zapcut-api**: FastAPI application handling HTTP requests
- **zapcut-worker**: Celery worker processing background tasks

Both applications share the same codebase but run different processes.

## Prerequisites

1. Install Fly.io CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Login to Fly.io: `fly auth login`
3. Ensure you have Redis configured (Upstash Redis recommended)

## Initial Setup

### 1. Create API Application

```bash
cd backend

# Create the API app (if it doesn't exist)
fly apps create zapcut-api

# Set secrets for API app
fly secrets set \
  DATABASE_URL="your-database-url" \
  REDIS_URL="your-redis-url" \
  SUPABASE_SERVICE_ROLE_KEY="your-key" \
  SUPABASE_JWT_SECRET="your-secret" \
  OPENAI_API_KEY="your-key" \
  REPLICATE_API_TOKEN="your-token" \
  -a zapcut-api

# Deploy API
fly deploy --config fly.api.toml -a zapcut-api
```

### 2. Create Worker Application

```bash
# Create the worker app
fly apps create zapcut-worker

# Set secrets for worker app (same as API, except worker doesn't need all of them)
fly secrets set \
  DATABASE_URL="your-database-url" \
  REDIS_URL="your-redis-url" \
  SUPABASE_SERVICE_ROLE_KEY="your-key" \
  SUPABASE_JWT_SECRET="your-secret" \
  OPENAI_API_KEY="your-key" \
  REPLICATE_API_TOKEN="your-token" \
  -a zapcut-worker

# Deploy worker
fly deploy --config fly.worker.toml -a zapcut-worker
```

## Deployment Commands

### Deploy API Only

```bash
fly deploy --config fly.api.toml -a zapcut-api
```

### Deploy Worker Only

```bash
fly deploy --config fly.worker.toml -a zapcut-worker
```

### Deploy Both

```bash
fly deploy --config fly.api.toml -a zapcut-api
fly deploy --config fly.worker.toml -a zapcut-worker
```

## Health Checks

The API includes a `/health` endpoint that responds quickly (< 3s) for Fly.io routing:

```bash
# Test health check
curl https://zapcut-api.fly.dev/health
```

Expected response:
```json
{"status": "ok", "service": "fastapi"}
```

## Monitoring

### Check API Status

```bash
fly status -a zapcut-api
fly logs -a zapcut-api
```

### Check Worker Status

```bash
fly status -a zapcut-worker
fly logs -a zapcut-worker
```

### SSH into Machines

```bash
# API machine
fly ssh console -a zapcut-api

# Worker machine
fly ssh console -a zapcut-worker
```

## Scaling

### Scale API Machines

```bash
# Scale to 2 API machines
fly scale count 2 -a zapcut-api

# Scale to 0 (auto-start enabled)
fly scale count 0 -a zapcut-api
```

### Scale Worker Machines

```bash
# Scale to 2 worker machines
fly scale count 2 -a zapcut-worker

# Keep at least 1 worker running
fly scale count 1 -a zapcut-worker
```

## Troubleshooting

### API Timeouts

1. Check health endpoint: `curl https://zapcut-api.fly.dev/health`
2. Check logs: `fly logs -a zapcut-api`
3. Verify machine is running: `fly status -a zapcut-api`

### Worker Not Processing Tasks

1. Check Redis connection: `fly logs -a zapcut-worker | grep -i redis`
2. Verify REDIS_URL secret: `fly secrets list -a zapcut-worker`
3. Check worker logs: `fly logs -a zapcut-worker`

### Both Apps on Same Machine

If you see both processes running on one machine:
1. Verify you're using separate fly.toml files
2. Check that start.sh doesn't start Celery
3. Ensure start-worker.sh is only used by worker app

## Environment Variables

Both apps need these secrets:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (required for worker)
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `SUPABASE_JWT_SECRET`: JWT secret for token validation
- `OPENAI_API_KEY`: OpenAI API key
- `REPLICATE_API_TOKEN`: Replicate API token

Optional:
- `CORS_ORIGINS`: Comma-separated list of allowed origins

## Notes

- The API uses auto-start/auto-stop to save costs
- The worker should run continuously to process tasks
- Health checks ensure only healthy API machines receive traffic
- Solo pool is used for Celery to reduce memory usage on small machines

