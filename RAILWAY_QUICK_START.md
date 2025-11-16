# Railway Quick Start Deployment Checklist

Fast-track guide to deploy Adcraft on Railway. Follow these steps in order.

## Pre-Deployment Setup

- [ ] Create Railway account at https://railway.app
- [ ] Have Supabase credentials ready
- [ ] Have OpenAI API key ready
- [ ] Have Replicate API token ready

## Step-by-Step Deployment

### 1. Create Railway Project (2 min)

1. Go to https://railway.app/new
2. Click "Empty Project"
3. Name: `adcraft-production`

### 2. Add Redis (1 min)

1. Click "+ New" → "Database" → "Redis"
2. Wait for provisioning (30 seconds)
3. ✅ Redis service created

### 3. Deploy Backend API (5 min)

1. Click "+ New" → "GitHub Repo"
2. Connect and select your repository
3. Settings:
   - **Root Directory**: `/backend`
   - **Name**: `backend-api`
4. Add environment variables (copy from `RAILWAY_ENV_TEMPLATE.md` Section 1):
   ```
   REDIS_URL=${{Redis.REDIS_URL}}
   SUPABASE_URL=https://[YOUR_PROJECT].supabase.co
   SUPABASE_SERVICE_ROLE_KEY=[YOUR_KEY]
   SUPABASE_DB_PASSWORD=[YOUR_PASSWORD]
   OPENAI_API_KEY=[YOUR_KEY]
   REPLICATE_API_TOKEN=[YOUR_TOKEN]
   CORS_ORIGINS=http://localhost:5173
   ```
5. Deploy starts automatically
6. Wait for "✓ Deployed" status
7. Copy the backend URL (e.g., `backend-api-production.railway.app`)

### 4. Run Database Migrations (2 min)

Railway CLI method:
```bash
railway link
railway run --service backend-api alembic upgrade head
```

OR via Railway dashboard:
1. Go to backend-api → "Deployments"
2. Click latest deployment → "View Logs"
3. Verify no database errors

### 5. Deploy Celery Worker (3 min)

1. Click "+ New" → "GitHub Repo"
2. Select SAME repository
3. Settings:
   - **Root Directory**: `/backend`
   - **Name**: `celery-worker`
   - **Custom Start Command**: `celery -A app.celery_app worker --loglevel=info --concurrency=2`
4. Add environment variables (copy from `RAILWAY_ENV_TEMPLATE.md` Section 2):
   ```
   REDIS_URL=${{Redis.REDIS_URL}}
   SUPABASE_URL=[SAME AS BACKEND]
   SUPABASE_SERVICE_ROLE_KEY=[SAME AS BACKEND]
   SUPABASE_DB_PASSWORD=[SAME AS BACKEND]
   OPENAI_API_KEY=[SAME AS BACKEND]
   REPLICATE_API_TOKEN=[SAME AS BACKEND]
   ```
5. Deploy starts automatically
6. Check logs for: `celery@... ready.`

### 6. Deploy Frontend (5 min)

1. Click "+ New" → "GitHub Repo"
2. Select SAME repository
3. Settings:
   - **Root Directory**: `/frontend`
   - **Name**: `frontend-app`
4. Add environment variables:
   ```
   VITE_API_URL=https://[BACKEND_DOMAIN_FROM_STEP_3].railway.app
   VITE_SUPABASE_URL=https://[YOUR_PROJECT].supabase.co
   VITE_SUPABASE_ANON_KEY=[YOUR_ANON_KEY]
   ```
5. Deploy starts automatically (takes 2-3 min)
6. Copy the frontend URL (e.g., `frontend-app-production.railway.app`)

### 7. Update Backend CORS (1 min)

1. Go to `backend-api` service
2. Update `CORS_ORIGINS` variable:
   ```
   CORS_ORIGINS=https://[FRONTEND_DOMAIN_FROM_STEP_6].railway.app,https://app.zapcut.video,http://localhost:5173
   ```
3. Backend will auto-redeploy

## Verification (5 min)

### Check All Services Running

Railway Dashboard → All services should show "✓ Active":
- [ ] Redis
- [ ] backend-api
- [ ] celery-worker
- [ ] frontend-app

### Test Backend API

```bash
curl https://[YOUR_BACKEND_DOMAIN].railway.app/health
# Expected: {"status":"healthy"}
```

### Test Frontend

1. Visit `https://[YOUR_FRONTEND_DOMAIN].railway.app`
2. Should see Adcraft login page
3. Open browser console (F12)
4. Should see NO CORS errors

### Test Full Flow

1. Login with Supabase credentials
2. Create a test brand
3. Create a test campaign
4. Generate a video
5. Check celery-worker logs for task execution

## Common First-Time Issues

### Issue: Backend shows DATABASE_URL error

**Fix:**
- Verify `SUPABASE_DB_PASSWORD` is set correctly
- Check `SUPABASE_URL` format (needs https://)
- Try setting `DATABASE_URL` directly instead

### Issue: Frontend shows CORS error

**Fix:**
- Verify `CORS_ORIGINS` includes frontend domain
- Must include `https://` prefix
- No trailing slashes
- Redeploy backend after changing

### Issue: Celery worker not connecting to Redis

**Fix:**
- Verify `REDIS_URL=${{Redis.REDIS_URL}}`
- Check Redis service is running
- Worker and API must use SAME Redis reference

### Issue: Frontend can't reach backend

**Fix:**
- Verify `VITE_API_URL` is correct backend domain
- Must include `https://` prefix
- Test backend /health endpoint directly

## Post-Deployment Tasks

- [ ] Set up custom domains (optional)
- [ ] Configure monitoring/alerts
- [ ] Set up error tracking (Sentry)
- [ ] Test video generation end-to-end
- [ ] Document production URLs
- [ ] Set up CI/CD (optional)

## Production URLs

**Record your deployed URLs:**

```
Backend API:  https://___________________.railway.app
Frontend:     https://___________________.railway.app
Redis:        (internal only)
Worker:       (internal only)
```

## Cost Tracking

Railway Dashboard → "Usage":
- View current month's usage
- Set billing alerts
- Estimated: $20-35/month

## Rollback Plan

If deployment fails:

1. Railway Dashboard → Service → "Deployments"
2. Find last working deployment
3. Click "⋮" → "Redeploy"

## Need Help?

- Full guide: `RAILWAY_DEPLOYMENT_GUIDE.md`
- Environment variables: `RAILWAY_ENV_TEMPLATE.md`
- Railway docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

---

**Total deployment time: ~20-25 minutes**

Good luck! 🚀
