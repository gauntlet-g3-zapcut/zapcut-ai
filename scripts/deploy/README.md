# Adcraft Railway Deployment Scripts

Automated deployment scripts for deploying Adcraft to Railway.

## Quick Start

```bash
# Make scripts executable (first time only)
chmod +x scripts/deploy/*.sh

# Run the master deployment script
./scripts/deploy/deploy.sh
```

That's it! The script will guide you through the entire deployment process.

## What Gets Deployed

1. **Redis** - Message broker for Celery
2. **Backend API** - FastAPI application (handles HTTP requests)
3. **Celery Worker** - Background task processor (video generation)
4. **Frontend** - React/Vite static site

## Prerequisites

Before running the deployment scripts:

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

Or with Homebrew:
```bash
brew install railway
```

### 2. Login to Railway

```bash
railway login
```

### 3. Have Your Credentials Ready

You'll need:
- **Supabase**: URL, Anon Key, Service Role Key, DB Password
- **OpenAI**: API Key
- **Replicate**: API Token
- **Railway**: Account (free tier works)

### 4. Connect GitHub Repository

Ensure your repository is pushed to GitHub and accessible.

## Deployment Scripts

### Master Script (Recommended)

```bash
./scripts/deploy/deploy.sh
```

Runs all steps sequentially with guided prompts.

### Individual Scripts

Run these in order if you want more control:

```bash
# Step 0: Setup credentials
./scripts/deploy/0-setup-credentials.sh

# Step 1: Create Railway project and Redis
./scripts/deploy/1-deploy-infrastructure.sh

# Step 2: Deploy backend API and Celery worker
./scripts/deploy/2-deploy-backend.sh

# Step 3: Deploy frontend
./scripts/deploy/3-deploy-frontend.sh

# Step 4: Update CORS, run migrations, verify
./scripts/deploy/4-finalize-deployment.sh
```

## Script Features

### Automated
- ✅ Railway project creation
- ✅ Redis provisioning
- ✅ Environment variable configuration
- ✅ Service deployment
- ✅ Domain assignment
- ✅ CORS configuration
- ✅ Database migrations
- ✅ Health checks

### Interactive
- Credential collection with validation
- Step-by-step confirmation
- Resume from last completed step
- Clear progress indicators
- Colored output for readability

### Safe
- Credentials stored in gitignored `.railway.env`
- State tracking in `.railway.state`
- Error handling and rollback support
- Pre-deployment validation

## Files Created

During deployment, these files are created (all gitignored):

- `.railway.env` - Your credentials and configuration
- `.railway.state` - Deployment progress tracking
- `.railway-worker-vars.txt` - Helper file for manual worker setup

**⚠️ Never commit these files to git!**

## Manual Steps Required

### Celery Worker Service

Railway CLI doesn't support creating multiple services from the same repo directory easily. You'll need to manually:

1. Go to Railway dashboard
2. Create new service from GitHub repo
3. Set root directory to `/backend`
4. Set custom start command to: `celery -A app.celery_app worker --loglevel=info --concurrency=2`
5. Copy environment variables from backend service

The script will pause and guide you through this step.

## Troubleshooting

### "Railway CLI not found"

```bash
npm install -g @railway/cli
```

### "Not logged in to Railway"

```bash
railway login
```

### "Backend health check failed"

Check backend logs:
```bash
cd backend
railway logs
```

Common issues:
- Database connection error → Verify Supabase credentials
- Redis connection error → Verify Redis service is running
- Missing environment variables → Check `.railway.env`

### "Frontend shows CORS error"

Ensure backend `CORS_ORIGINS` includes frontend URL. The finalization script handles this automatically.

### "Migrations failed"

Run manually:
```bash
cd backend
railway run alembic upgrade head
```

### Resume Deployment

If deployment is interrupted, just run the script again:
```bash
./scripts/deploy/deploy.sh
```

It will detect previous progress and resume from the last completed step.

### Start Over

To completely reset and start fresh:
```bash
rm -f .railway.env .railway.state .railway-worker-vars.txt
./scripts/deploy/deploy.sh
```

## Post-Deployment

After successful deployment:

### 1. Test the Application

```bash
# Open frontend
open $FRONTEND_URL

# Test backend health
curl $BACKEND_URL/health
```

### 2. Monitor Logs

```bash
# Backend API logs
cd backend && railway logs

# Celery Worker logs
railway logs --service celery-worker

# Frontend logs
cd frontend && railway logs
```

### 3. Set Up Custom Domains (Optional)

1. Go to Railway dashboard
2. Select service → Settings → Domains
3. Add custom domain
4. Update DNS records
5. Re-run finalization script to update CORS

### 4. Configure Monitoring

- Set up Sentry for error tracking
- Add uptime monitoring (UptimeRobot, Pingdom)
- Configure Railway alerts

### 5. Test Video Generation

1. Login to frontend
2. Create a test brand
3. Create a test campaign
4. Generate a video
5. Check worker logs for task processing

## Cost Estimates

Railway pricing (approximate):
- Starter Plan: $5/month (required)
- Redis: ~$5/month
- Backend API: ~$5-10/month
- Celery Worker: ~$5-10/month
- Frontend: ~$2-5/month

**Total: $20-35/month**

Free tier: $5/month in credits

## Advanced Usage

### Deploy Specific Service

```bash
cd backend
railway up  # Deploy backend only

cd frontend
railway up  # Deploy frontend only
```

### Update Environment Variables

```bash
cd backend
railway variables set KEY=value
```

### View All Variables

```bash
railway variables
```

### Link to Existing Project

```bash
railway link
```

### Switch Projects

```bash
railway project  # List projects
railway link <project-id>
```

## Deployment Checklist

Before deployment:
- [ ] Railway CLI installed
- [ ] Logged into Railway
- [ ] GitHub repo pushed and accessible
- [ ] Supabase credentials ready
- [ ] OpenAI API key ready
- [ ] Replicate API token ready

After deployment:
- [ ] All services showing "Active" in Railway
- [ ] Backend health check returns `{"status":"healthy"}`
- [ ] Frontend loads in browser
- [ ] No CORS errors in browser console
- [ ] Can login with Supabase credentials
- [ ] Database migrations completed
- [ ] Celery worker connected to Redis
- [ ] Test video generation works

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Full Deployment Guide**: `../../RAILWAY_DEPLOYMENT_GUIDE.md`
- **Environment Variables**: `../../RAILWAY_ENV_TEMPLATE.md`

## Security Notes

1. **Never commit `.railway.env` to git** (already in .gitignore)
2. **Rotate API keys regularly**
3. **Use different credentials for dev/prod**
4. **Review CORS origins** (don't use `*`)
5. **Enable Railway 2FA** for your account

## License

Same as Adcraft project.

---

**Questions?** Check the main deployment guide: `RAILWAY_DEPLOYMENT_GUIDE.md`
