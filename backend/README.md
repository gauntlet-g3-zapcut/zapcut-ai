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

## Deployment to Fly.io

### Initial Setup

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly.io:
```bash
fly auth login
```

3. Create app (if not exists):
```bash
fly apps create zapcut-api
```

4. Set secrets (environment variables):
```bash
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set SUPABASE_URL="https://..."
fly secrets set SUPABASE_SERVICE_ROLE_KEY="..."
fly secrets set OPENAI_API_KEY="..."
```

5. Deploy:
```bash
fly deploy
```

### Database Setup

1. Create PostgreSQL database:
```bash
fly postgres create --name zapcut-db
```

2. Attach database to app:
```bash
fly postgres attach zapcut-db --app zapcut-api
```

3. Initialize database tables:
```bash
# After deployment, call the init endpoint
curl https://zapcut-api.fly.dev/init-db
```

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

Fly.io will automatically check `/health` endpoint every 30 seconds.

