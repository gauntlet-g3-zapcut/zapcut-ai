# Railway Deployment Architecture

## Overview

AdCraft is deployed on Railway with a microservices architecture consisting of 4 main components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Railway Project: "AdCraft"                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND SERVICE                           │
│  Name: frontend                                                     │
│  Root: /frontend                                                    │
│  Command: npm run build + static serve                              │
│  Domain: https://app.zapcut.video                                   │
│                                                                     │
│  Env Variables:                                                     │
│  - VITE_API_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}                 │
│  - VITE_SUPABASE_URL                                               │
│  - VITE_SUPABASE_ANON_KEY                                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │ HTTP requests
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND API SERVICE                          │
│  Name: backend                                                      │
│  Root: /backend                                                     │
│  Command: uvicorn app.main:app                                      │
│  Domain: https://backend-adcraft-production.up.railway.app          │
│                                                                     │
│  Env Variables:                                                     │
│  - SUPABASE_URL                                                     │
│  - SUPABASE_SERVICE_ROLE_KEY                                       │
│  - DATABASE_URL                                                     │
│  - REDIS_URL=${{Redis.REDIS_URL}}  ← Service reference              │
│  - OPENAI_API_KEY                                                   │
│  - REPLICATE_API_TOKEN                                             │
│  - PORT=8000                                                        │
└──────────┬────────────────────┬────────────────────────────────────┘
           │                    │
           │ Enqueue tasks      │ Read/Write data
           ↓                    ↓
┌──────────────────────┐  ┌──────────────────────────────────────────┐
│   REDIS SERVICE      │  │       EXTERNAL: SUPABASE                 │
│  Name: Redis         │  │  - PostgreSQL Database                   │
│  Type: Database      │  │  - Storage (S3-compatible)               │
│  Auto-provisioned    │  │  - Auth                                  │
│                      │  │  URL: rksxuhhegcxqmkjopudx.supabase.co   │
│  Exposes:            │  └──────────────────────────────────────────┘
│  - REDIS_URL         │              ↑                    ↑
└──────────┬───────────┘              │                    │
           ↑                          │                    │
           │ Consume tasks    Read/Write data     Upload files
           │                          │                    │
┌──────────┴──────────────────────────┴────────────────────┴─────────┐
│                      CELERY WORKER SERVICE                          │
│  Name: celery-worker                                                │
│  Root: /backend                                                     │
│  Command: celery -A app.celery_app worker --loglevel=info \        │
│           --concurrency=2                                           │
│  No public domain (internal service)                                │
│                                                                     │
│  Env Variables (SAME as backend):                                  │
│  - SUPABASE_URL                                                     │
│  - SUPABASE_SERVICE_ROLE_KEY                                       │
│  - DATABASE_URL                                                     │
│  - REDIS_URL=${{Redis.REDIS_URL}}  ← Service reference              │
│  - OPENAI_API_KEY                                                   │
│  - REPLICATE_API_TOKEN                                             │
└────────────────────────┬───────────────────┬────────────────────────┘
                         │                   │
                         │ API calls         │ API calls
                         ↓                   ↓
              ┌──────────────────┐  ┌──────────────────┐
              │  EXTERNAL:       │  │  EXTERNAL:       │
              │  OpenAI API      │  │  Replicate API   │
              │  (GPT-4, etc.)   │  │  (Video gen)     │
              └──────────────────┘  └──────────────────┘
```

---

## Services Detail

### 1. Frontend Service

**Purpose:** React SPA serving the user interface

**Configuration:**
- **Root Directory:** `/frontend`
- **Build Command:** `npm run build`
- **Start Command:** Auto-detected by Nixpacks (serves static files)
- **Domain:** Custom domain `app.zapcut.video`

**Environment Variables:**
```bash
VITE_API_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}
VITE_SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
VITE_SUPABASE_ANON_KEY=<supabase-anon-key>
```

**Notes:**
- Uses service reference `${{backend.RAILWAY_PUBLIC_DOMAIN}}` to auto-discover backend URL
- Only uses Supabase ANON key (safe for client-side)
- Built as static site, served by Railway's static hosting

---

### 2. Backend API Service

**Purpose:** FastAPI REST API server

**Configuration:**
- **Root Directory:** `/backend`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Domain:** Auto-generated Railway domain

**Environment Variables:**
```bash
# Supabase
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key>
SUPABASE_DB_PASSWORD=<db-password>
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-us-west-2.pooler.supabase.com:6543/postgres

# Redis (message broker)
REDIS_URL=${{Redis.REDIS_URL}}

# External APIs
OPENAI_API_KEY=<openai-key>
REPLICATE_API_TOKEN=<replicate-token>

# API Configuration
PORT=8000
CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video
```

**Responsibilities:**
- Handle HTTP requests from frontend
- User authentication & authorization
- Create background tasks (push to Redis)
- Serve campaign data & status
- Proxy file uploads to Supabase Storage

**Key Endpoints:**
- `POST /api/campaigns/{id}/generate` - Trigger video generation
- `GET /api/campaigns/{id}` - Get campaign status & progress
- `GET /api/campaigns/{id}/jobs` - Get generation job details

---

### 3. Celery Worker Service

**Purpose:** Background task processor for video generation

**Configuration:**
- **Root Directory:** `/backend` (same codebase as backend API)
- **Start Command:** `celery -A app.celery_app worker --loglevel=info --concurrency=2`
- **No public domain** (internal service only)

**Environment Variables:**
```bash
# IDENTICAL to Backend API (both services use same code)
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key>
SUPABASE_DB_PASSWORD=<db-password>
DATABASE_URL=postgresql://postgres.<project-ref>:<password>@aws-0-us-west-2.pooler.supabase.com:6543/postgres
REDIS_URL=${{Redis.REDIS_URL}}
OPENAI_API_KEY=<openai-key>
REPLICATE_API_TOKEN=<replicate-token>
```

**Responsibilities:**
- Pull tasks from Redis queue
- Generate reference images (Replicate API)
- Generate storylines & prompts (OpenAI API)
- Generate video scenes (Replicate/Sora API)
- Generate voiceovers (Replicate API)
- Generate background music (Replicate/Suno API)
- Compose final video (FFmpeg)
- Upload assets to Supabase Storage
- Update database with progress & results

**Key Tasks:**
- `generate_campaign_video_test_mode` - Full video generation pipeline
- `generate_campaign_video` - Production video generation with continuity

**Scaling:**
- Concurrency: 2 (can be increased for more parallel processing)
- Can deploy multiple worker instances for horizontal scaling

---

### 4. Redis Service

**Purpose:** Message broker for Celery task queue

**Configuration:**
- **Type:** Railway Database (auto-provisioned)
- **Name:** `Redis` or `Redis-AdCraft`
- **Exposes:** `REDIS_URL` environment variable

**Usage:**
- Backend API pushes tasks to queue
- Celery workers pull tasks from queue
- Ensures reliable async task processing

**Notes:**
- Fully managed by Railway
- Automatic backups & monitoring
- Private network connection to other services

---

## External Services

### Supabase (External)

**Components:**
1. **PostgreSQL Database**
   - Stores: campaigns, brands, users, generation jobs
   - Connection: `DATABASE_URL` via connection pooler

2. **Storage (S3-compatible)**
   - Stores: videos, images, audio files
   - Access: `SUPABASE_SERVICE_ROLE_KEY` for admin access
   - Public URLs for video playback

3. **Auth (Not yet implemented)**
   - Future: User authentication
   - Uses: `SUPABASE_ANON_KEY` in frontend

**Why External:**
- Easier database management
- Built-in S3-compatible storage
- Global CDN for video delivery
- Free tier supports development

---

## Data Flow Example

### User Generates a Video

1. **User** clicks "Generate Video" in Frontend
2. **Frontend** → `POST /api/campaigns/{id}/generate` → **Backend API**
3. **Backend API** → Creates Celery task → Pushes to **Redis**
4. **Backend API** → Returns `202 Accepted` to Frontend immediately
5. **Frontend** → Starts polling `GET /api/campaigns/{id}` for status

**Meanwhile, in the background:**

6. **Celery Worker** → Pulls task from **Redis**
7. **Celery Worker** → Updates campaign `status="generating"` in **Supabase DB**
8. **Celery Worker** → Calls **OpenAI API** (generate prompts)
9. **Celery Worker** → Calls **Replicate API** (generate videos)
10. **Celery Worker** → Downloads generated videos
11. **Celery Worker** → Uploads videos to **Supabase Storage**
12. **Celery Worker** → Composes final video with FFmpeg
13. **Celery Worker** → Uploads final video to **Supabase Storage**
14. **Celery Worker** → Updates campaign `status="completed"`, `final_video_url` in **Supabase DB**

**User sees progress:**

15. **Frontend** → Polls Backend API → Gets updated `generation_progress`
16. **Frontend** → Displays progress bar (0% → 100%)
17. **Frontend** → Gets `final_video_url` when complete
18. **Frontend** → Plays video from Supabase Storage CDN

---

## Service Dependencies

### Frontend
- **Depends on:** Backend API (for data)
- **Depends on:** Supabase (for auth, public files)

### Backend API
- **Depends on:** Redis (for task queue)
- **Depends on:** Supabase DB (for data storage)
- **Depends on:** Supabase Storage (for file uploads)

### Celery Worker
- **Depends on:** Redis (for task queue)
- **Depends on:** Supabase DB (for data storage)
- **Depends on:** Supabase Storage (for file uploads)
- **Depends on:** OpenAI API (for AI generation)
- **Depends on:** Replicate API (for video/audio generation)
- **Depends on:** FFmpeg (for video composition)

### Redis
- **No dependencies** (standalone)

---

## Railway Service References

Railway allows services to reference each other using the syntax:

```bash
${{ServiceName.VARIABLE_NAME}}
```

**Examples in this project:**

```bash
# Frontend references Backend domain
VITE_API_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}

# Backend references Redis URL
REDIS_URL=${{Redis.REDIS_URL}}

# Celery Worker references Redis URL
REDIS_URL=${{Redis.REDIS_URL}}
```

**Benefits:**
- Automatic service discovery
- No hardcoded URLs
- Works across environments (staging, production)
- Updates automatically when services change

---

## Environment Variables Summary

### Shared Across Backend + Worker

Both services need identical environment variables:

```bash
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_DB_PASSWORD
DATABASE_URL
REDIS_URL=${{Redis.REDIS_URL}}
OPENAI_API_KEY
REPLICATE_API_TOKEN
```

### Frontend Only

```bash
VITE_API_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
```

### Backend API Only

```bash
PORT=8000
CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video
```

---

## Deployment Process

See deployment scripts in order:

1. **`0-setup-credentials.sh`** - Collect all credentials
2. **`1-deploy-infrastructure.sh`** - Create Railway project + Redis
3. **`2-deploy-backend.sh`** - Deploy Backend API + Celery Worker
4. **`3-deploy-frontend.sh`** - Deploy Frontend

---

## Scaling Considerations

### Horizontal Scaling

**Celery Workers:**
- Add more worker instances for parallel processing
- Each worker processes tasks independently
- Redis handles task distribution automatically

**Backend API:**
- Stateless design allows multiple instances
- Railway auto-scales based on load

### Vertical Scaling

**Worker Concurrency:**
```bash
# Increase from 2 to 4 concurrent tasks per worker
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

**Resource Limits:**
- Railway Pro plan: More memory/CPU per service
- Useful for FFmpeg video processing

---

## Monitoring & Debugging

### Celery Worker Logs

```bash
railway logs --service celery-worker
```

### Backend API Logs

```bash
railway logs --service backend
```

### Redis Monitoring

```bash
# Check Redis connection from worker
railway run --service celery-worker redis-cli -u $REDIS_URL ping
```

### Database Monitoring

Check Supabase dashboard for:
- Active connections
- Query performance
- Storage usage

---

## Security Notes

1. **Service Role Key** - Only used server-side (Backend + Worker)
2. **Anon Key** - Safe for frontend (row-level security enforced)
3. **API Keys** - Never exposed to frontend
4. **Redis** - Private network only (not publicly accessible)
5. **CORS** - Restricted to specific origins

---

## Cost Optimization

### Railway Free Tier

- 500 hours/month execution time (shared across services)
- $5 credit/month
- Suitable for development/testing

### Production Recommendations

1. **Use Railway Pro** - Better performance & uptime
2. **Optimize worker concurrency** - Balance speed vs. cost
3. **Monitor Supabase usage** - Storage & bandwidth limits
4. **Cache responses** - Reduce database queries

---

## Future Improvements

1. **Add monitoring service** (Sentry, DataDog)
2. **Implement rate limiting** (Redis-based)
3. **Add caching layer** (Redis for API responses)
4. **Deploy staging environment** (separate Railway project)
5. **Implement CI/CD** (GitHub Actions → Railway)
6. **Add health check endpoints** (for Railway monitoring)
7. **Implement horizontal worker autoscaling** (based on queue depth)
