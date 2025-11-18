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
- `SUPABASE_S3_ENDPOINT` - Supabase S3 storage endpoint URL
- `SUPABASE_S3_ACCESS_KEY` - Supabase S3 access key
- `SUPABASE_S3_SECRET_KEY` - Supabase S3 secret key
- `SUPABASE_S3_VIDEO_BUCKET` - S3 bucket name for videos (default: "videos")
- `OPENAI_API_KEY` - OpenAI API key
- `REPLICATE_API_TOKEN` - Replicate API token
- `REPLICATE_WEBHOOK_SECRET` - Replicate webhook secret for signature verification
- `REDIS_URL` - Redis connection string (optional, for Celery)
- `CORS_ORIGINS` - Comma-separated CORS origins

### S3 Storage Setup

The application requires Supabase S3 storage buckets with public-read ACL:
- `videos` - Stores generated scene videos (must be public-read)
- `soundtracks` - Stores generated audio files (must be public-read)
- `brand-images` - Stores brand images (must be public-read)

## Health Checks

Fly.io will automatically check `/health` endpoint every 30 seconds.

## Testing

### Unit Tests

Run unit tests with pytest:
```bash
pytest tests/
```

### Manual Verification of S3 Video Storage

To verify that videos are being uploaded to S3 before saving URLs to the database:

1. **Check Webhook Logs**: When a Replicate webhook is received for a completed scene, you should see logs indicating:
   - Download from Replicate: `Downloading video from Replicate | campaign={id} | scene={num}`
   - Upload to S3: `Uploading video to S3 | campaign={id} | scene={num} | bucket=videos`
   - S3 URL saved: `Scene {num} S3 video URL saved | campaign={id} | s3_url={url}`

2. **Verify Database URLs**: Query the `campaigns` table and check `video_urls` JSON field. All `video_url` values should be Supabase S3 URLs (format: `https://{project}.supabase.co/storage/v1/object/public/videos/generated/{campaign_id}/scene-{num}/prediction-{id}.mp4`), not Replicate URLs.

3. **Test Webhook Endpoint**: You can simulate a webhook call using curl:
```bash
curl -X POST "http://localhost:8000/webhooks/replicate?campaign_id={campaign_id}&scene_num=1" \
  -H "Content-Type: application/json" \
  -H "X-Replicate-Content-SHA256: {signature}" \
  -d '{
    "id": "test-prediction-id",
    "status": "succeeded",
    "output": "https://replicate.delivery/pbxt/test-video.mp4"
  }'
```

4. **Verify S3 Bucket**: Check the Supabase Storage dashboard to confirm files are uploaded to the `videos` bucket with the expected structure: `generated/{campaign_id}/scene-{scene_num}/prediction-{prediction_id}.mp4`

5. **Test Retry Path**: If a scene fails and retries, verify that:
   - A new prediction is created with a new prediction_id
   - The new video is uploaded with the new prediction_id in the key
   - The scene's video_url is updated to the new S3 URL

