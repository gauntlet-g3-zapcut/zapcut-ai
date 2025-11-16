# Backend API

FastAPI backend server with Celery queue worker for video generation tasks.

## Structure

- `app/` - FastAPI application code
  - `api/` - API routes
  - `models/` - Database models
  - `services/` - Business logic services
  - `scripts/` - Utility scripts
  - `alembic/` - Database migrations
- `queue/` - Celery queue worker
  - `celery_app.py` - Celery configuration
  - `tasks/` - Background task definitions

## Railway Deployment

This backend is configured for Railway deployment with two separate services:

### Service 1: FastAPI Server (`web`)
- **Start Command**: `bash start.sh`
- **Port**: Uses `$PORT` environment variable
- **Purpose**: Handles HTTP API requests

### Service 2: Celery Worker (`worker`)
- **Start Command**: `bash start-worker.sh`
- **Purpose**: Processes background tasks (video generation, etc.)

### Setup Instructions

1. **Create two services in Railway:**
   - Service 1: Name it "api" or "web"
   - Service 2: Name it "worker" or "queue"

2. **Both services should:**
   - Use the same GitHub repository
   - Use the same `backend/` directory as root
   - Share the same environment variables

3. **Required Environment Variables** (set for both services):
   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   OPENAI_API_KEY=...
   REPLICATE_API_TOKEN=...
   SUPABASE_URL=...
   SUPABASE_SERVICE_ROLE_KEY=...
   SUPABASE_DB_PASSWORD=...
   CORS_ORIGINS=...
   ```

4. **Service-Specific Configuration:**
   - **Web service**: Set `RAILWAY_SERVICE_NAME=web` (optional, Railway auto-detects from Procfile)
   - **Worker service**: Set `RAILWAY_SERVICE_NAME=worker` (optional, Railway auto-detects from Procfile)

5. **Procfile Detection:**
   Railway will automatically detect the `web` and `worker` processes from the Procfile and create separate services.

## Local Development

### Start FastAPI Server
```bash
cd backend
bash start.sh
```

### Start Celery Worker (separate terminal)
```bash
cd backend
bash start-worker.sh
```

## Environment Variables

See `app/config.py` for all available configuration options.

