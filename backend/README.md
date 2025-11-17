# AdCraft Backend API

FastAPI backend for AdCraft video generation platform.

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/db"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

3. Run the server:
```bash
uvicorn app.main:app --reload
```

## Deployment to Railway

### Initial Setup

1. Create Railway account: https://railway.app

2. Create project and connect repository:
   - Go to Railway dashboard → New Project
   - Connect your GitHub repository or deploy from dashboard

3. Add databases:
   - Click "New" → "Database" → "Add PostgreSQL"
   - Click "New" → "Database" → "Add Redis"
   - Railway automatically sets `DATABASE_URL` and `REDIS_URL`

4. Create API service:
   - Click "New" → "GitHub Repo" or "Empty Service"
   - Set root directory to `backend`
   - Railway auto-detects Python and uses `railway.toml` or `start.sh`

5. Set environment variables in Railway dashboard:
   - `API_URL` - Your Railway API domain
   - `SUPABASE_URL` - Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
   - `SUPABASE_JWT_SECRET` - JWT secret (optional)
   - `OPENAI_API_KEY` - OpenAI API key
   - `REPLICATE_API_TOKEN` - Replicate API token
   - `ELEVENLABS_API_KEY` - ElevenLabs API key
   - `CORS_ORIGINS` - Comma-separated allowed origins

6. Deploy:
   - Railway automatically deploys on push (if GitHub connected)
   - Or click "Deploy" in dashboard
   - Or use CLI: `railway up`

### Database Setup

1. PostgreSQL is automatically created when you add it in Railway
2. `DATABASE_URL` is automatically set for all services in the project
3. Initialize database tables after deployment:
```bash
# Replace with your Railway domain
curl -X POST https://your-api.railway.app/init-db
```

For detailed deployment instructions, see [DEPLOY.md](./DEPLOY.md) and [DEPLOYMENT.md](./DEPLOYMENT.md).

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /cors-info` - CORS configuration info

### Authentication
- `POST /api/auth/verify` - Verify token
- `GET /api/auth/me` - Get current user

### Brands
- `GET /api/brands` - List brands
- `POST /api/brands` - Create brand
- `GET /api/brands/{id}` - Get brand

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign
- `GET /api/campaigns/{id}/status` - Get campaign status

### Chat
- `POST /api/brands/{id}/campaign-answers` - Submit answers
- `GET /api/brands/{id}/storyline/{creative_bible_id}` - Get storyline

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_JWT_SECRET` - Supabase JWT secret (optional, for HS256)
- `OPENAI_API_KEY` - OpenAI API key
- `REPLICATE_API_TOKEN` - Replicate API token
- `REDIS_URL` - Redis connection string (optional, for Celery)
- `CORS_ORIGINS` - Comma-separated CORS origins

## Health Checks

Railway automatically monitors the `/health` endpoint. The endpoint should respond quickly (< 3s) and return 200 OK to indicate the service is healthy.

