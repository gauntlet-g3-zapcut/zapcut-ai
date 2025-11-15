# AdCraft AI - Deployment Guide

## Deployed URLs

- **Frontend**: https://adcraft-blond.vercel.app/
- **Backend**: (To be deployed on Railway)

---

## Step-by-Step Deployment

### 1. Frontend (Vercel) - ✅ DEPLOYED

Your frontend is already live at: https://adcraft-blond.vercel.app/

#### Update Environment Variables in Vercel:

Go to your Vercel project → Settings → Environment Variables:

```env
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456:web:abc123
VITE_API_URL=https://your-railway-app.up.railway.app
```

> **Note**: Update `VITE_API_URL` after deploying the backend to Railway

---

### 2. Backend (Railway)

#### A. Create Railway Project

1. Go to [railway.app](https://railway.app/)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose `nsouzaco/adcraft`

#### B. Add PostgreSQL Database

1. In your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Wait for provisioning (Railway auto-creates `DATABASE_URL`)

#### C. Add Redis

1. Click "+ New" again
2. Select "Database" → "Add Redis"
3. Wait for provisioning (Railway auto-creates `REDIS_URL`)

#### D. Configure Backend API Service

1. Click on the GitHub service (your repo)
2. Go to "Settings"
3. Configure:

**Root Directory**: `backend`

**Build Command**: 
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables**:

Click "Variables" tab and add:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

OPENAI_API_KEY=sk-your-actual-key-here
REPLICATE_API_TOKEN=r8_your-actual-token-here

AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-key-here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com

CORS_ORIGINS=https://adcraft-blond.vercel.app,http://localhost:5173

PORT=8000
```

> **Important**: Use the actual variable references for DATABASE_URL and REDIS_URL:
> - `${{Postgres.DATABASE_URL}}`
> - `${{Redis.REDIS_URL}}`

#### E. Add Celery Worker Service

1. In Railway project, click "+ New"
2. Select "GitHub Repo" → Choose `nsouzaco/adcraft` again
3. Configure as a separate service:

**Root Directory**: `backend`

**Build Command**: 
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
celery -A app.celery_app worker --loglevel=info
```

**Environment Variables**:
Copy ALL the same environment variables from the Backend API service.

#### F. Get Railway Backend URL

1. Click on your Backend API service
2. Go to "Settings" → "Domains"
3. Click "Generate Domain"
4. Copy the URL (e.g., `https://adcraft-production.up.railway.app`)

---

### 3. Connect Frontend to Backend

#### Update Vercel Environment Variable:

1. Go to [vercel.com](https://vercel.com/) → Your project
2. Settings → Environment Variables
3. Update or add:
   ```
   VITE_API_URL=https://your-railway-backend.up.railway.app
   ```
4. Redeploy:
   - Go to "Deployments"
   - Click "..." on latest deployment
   - Click "Redeploy"

---

### 4. Run Database Migrations

After Railway backend is deployed:

1. Go to Railway → Backend service → "Deployments"
2. Once deployed, click on the service
3. Click "Shell" or use Railway CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run migrations
railway run alembic upgrade head
```

---

## Environment Variables Checklist

### Vercel (Frontend) - 7 variables
- [ ] `VITE_FIREBASE_API_KEY`
- [ ] `VITE_FIREBASE_AUTH_DOMAIN`
- [ ] `VITE_FIREBASE_PROJECT_ID`
- [ ] `VITE_FIREBASE_STORAGE_BUCKET`
- [ ] `VITE_FIREBASE_MESSAGING_SENDER_ID`
- [ ] `VITE_FIREBASE_APP_ID`
- [ ] `VITE_API_URL` (Railway backend URL)

### Railway Backend API - 11 variables
- [ ] `DATABASE_URL` (auto from Postgres)
- [ ] `REDIS_URL` (auto from Redis)
- [ ] `OPENAI_API_KEY`
- [ ] `REPLICATE_API_TOKEN`
- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] `AWS_S3_BUCKET`
- [ ] `AWS_REGION`
- [ ] `FIREBASE_PROJECT_ID`
- [ ] `FIREBASE_PRIVATE_KEY`
- [ ] `FIREBASE_CLIENT_EMAIL`
- [ ] `CORS_ORIGINS` (should include `https://adcraft-blond.vercel.app`)
- [ ] `PORT` (Railway auto-provides, or set to 8000)

### Railway Celery Worker - Same as Backend API
- [ ] All same variables as Backend API

---

## Testing Deployment

### 1. Test Frontend
Visit: https://adcraft-blond.vercel.app/
- [ ] Landing page loads
- [ ] Login page works
- [ ] UI is responsive

### 2. Test Backend
Visit: https://your-railway-backend.up.railway.app/docs
- [ ] API docs load (FastAPI Swagger UI)
- [ ] Health check: `GET /health`

### 3. Test Full Flow
1. [ ] Sign up with email/password
2. [ ] Create a brand
3. [ ] Chat with Creative Director
4. [ ] Generate video
5. [ ] Watch video

---

## Troubleshooting

### Frontend Issues

**"Failed to fetch"**
- Check `VITE_API_URL` points to Railway backend
- Check CORS settings in Railway backend

**Firebase auth not working**
- Verify all Firebase env vars are set
- Check Firebase console has your domain whitelisted

### Backend Issues

**500 Errors**
- Check Railway logs: Service → "Logs"
- Verify DATABASE_URL is correct
- Check all API keys are set

**Database connection failed**
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
- Check Railway Postgres service is running

**Celery not processing**
- Check Celery worker logs in Railway
- Verify REDIS_URL is correct
- Check both services share same Redis instance

### Video Generation Issues

**Replicate API errors**
- Verify REPLICATE_API_TOKEN is correct
- Check Replicate account has credits
- Check model availability (Sora/Suno)

**S3 upload errors**
- Verify AWS credentials
- Check bucket exists and is accessible
- Verify CORS settings on S3 bucket

---

## Monitoring

### Railway
- View logs: Project → Service → "Logs"
- View metrics: Service → "Metrics"
- View builds: Service → "Deployments"

### Vercel
- View deployments: Project → "Deployments"
- View logs: Deployment → "Logs"
- View analytics: Project → "Analytics"

---

## Scaling (Later)

### Railway
- Upgrade plan for more resources
- Add multiple Celery workers
- Enable auto-scaling

### Vercel
- Automatic scaling (included)
- CDN caching (included)

---

## Cost Estimates

### Free Tier
- **Vercel**: Free (hobby plan)
- **Railway**: $5/month credit
- **OpenAI**: Pay per use (~$0.03 per GPT-4 call)
- **Replicate**: Pay per use (~$0.05-0.10 per generation)
- **AWS S3**: ~$0.023/GB storage

### Expected Monthly Cost (Low Usage)
- Railway: $5-15
- OpenAI: $5-20
- Replicate: $10-50
- S3: $1-5
- **Total**: ~$21-90/month

---

## Next Steps

1. [ ] Deploy backend to Railway
2. [ ] Get Railway backend URL
3. [ ] Update Vercel `VITE_API_URL`
4. [ ] Run database migrations
5. [ ] Test full application flow
6. [ ] Monitor logs for errors
7. [ ] Add custom domain (optional)

---

**Need Help?**
- Railway Discord: https://discord.gg/railway
- Vercel Support: https://vercel.com/support
- Check logs in both platforms

