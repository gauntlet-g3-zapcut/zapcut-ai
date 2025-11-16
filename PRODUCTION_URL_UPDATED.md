# ✅ Production Frontend URL Updated

## Changes Applied

Your production setup has been updated from:
```
❌ OLD: https://app.zapcut.video
```

To:
```
✅ NEW: https://frontend-adcraft-production.up.railway.app
```

---

## What Was Changed

### 1. Backend CORS Configuration ✅

**Updated Files:**
- `backend/app/config.py` - Default CORS_ORIGINS updated
- `backend/app/main.py` - Hardcoded CORS origins updated (kept both old and new for compatibility)

**Railway Environment Variable:**
```bash
CORS_ORIGINS=http://localhost:5173,https://frontend-adcraft-production.up.railway.app
```

### 2. Frontend API Configuration ✅

**Railway Environment Variables:**
```bash
VITE_API_URL=https://backend-adcraft-production.up.railway.app
VITE_PROD=true
```

### 3. Deployments Started ✅

- ✅ Backend deploying to Railway
- ✅ Frontend deploying to Railway

---

## Production URLs Reference

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | `https://frontend-adcraft-production.up.railway.app` | User-facing application |
| **Backend API** | `https://backend-adcraft-production.up.railway.app` | API server |
| **Database** | `db.rksxuhhegcxqmkjopudx.supabase.co` | Supabase PostgreSQL |

---

## Verification Steps

### 1. Check Backend CORS Configuration

```bash
curl https://backend-adcraft-production.up.railway.app/cors-info
```

**Expected response:**
```json
{
  "cors_origins": [
    "https://frontend-adcraft-production.up.railway.app",
    "http://localhost:5173",
    ...
  ],
  "settings_cors_origins": "http://localhost:5173,https://frontend-adcraft-production.up.railway.app"
}
```

### 2. Test Backend Health

```bash
curl https://backend-adcraft-production.up.railway.app/health
```

**Expected:** `{"status":"healthy"}`

### 3. Test Backend API

```bash
curl https://backend-adcraft-production.up.railway.app/api/brands/
```

**Expected:** Array of brands from database

### 4. Test Frontend

1. Open: `https://frontend-adcraft-production.up.railway.app`
2. Open browser DevTools → Console
3. Look for:
   ```
   🔧 API Configuration:
     VITE_API_URL: https://backend-adcraft-production.up.railway.app
     VITE_PROD: true
   🚀 Final API_URL: https://backend-adcraft-production.up.railway.app
   ```

### 5. Test "Continue to Storyline" Flow

1. Create or select a brand
2. Answer all questions
3. Click "Continue to Storyline" button
4. **Watch browser console** - you should see:
   ```
   🚀 BRAND CHAT - Continue to Storyline button clicked
   ✅ Validation passed
   📤 Step 1: Calling createCreativeBible API...
   📡 API Request: POST https://backend-adcraft-production.up.railway.app/api/brands/.../creative-bible
   📡 API Response: 200 OK
   ✅ API Success: {creative_bible_id: "..."}
   📤 Step 2: Navigating to storyline review page...
   ```

5. **Watch Railway backend logs:**
   ```bash
   cd backend && railway logs --tail
   ```

   You should see:
   ```
   📥 POST /api/brands/.../creative-bible | IP: ... | Origin: https://frontend-adcraft-production.up.railway.app
   🎨 CREATE CREATIVE BIBLE - Request received
   ✅ Brand found: ...
   ✅ OpenAI generation successful
   ✅ SUCCESS: Creative bible operation completed
   ```

---

## Troubleshooting

### Issue: CORS Error in Browser Console

```
Access to fetch at 'https://backend-adcraft-production.up.railway.app/...'
from origin 'https://frontend-adcraft-production.up.railway.app'
has been blocked by CORS policy
```

**Diagnosis:**
```bash
# Check CORS configuration
curl https://backend-adcraft-production.up.railway.app/cors-info
```

**Fix:**
```bash
cd backend
railway variables --set "CORS_ORIGINS=http://localhost:5173,https://frontend-adcraft-production.up.railway.app"
railway up --detach
```

### Issue: Frontend Shows Wrong API URL

**Symptoms:** Console shows:
```
🚀 Final API_URL: https://zapcut-ai-production.up.railway.app
```

**Fix:**
```bash
cd frontend
railway variables --set "VITE_API_URL=https://backend-adcraft-production.up.railway.app"
railway variables --set "VITE_PROD=true"
railway up --detach
```

### Issue: "Load failed" Error

**Debug:**
1. Open browser console - check for detailed error logs
2. Check Railway backend logs:
   ```bash
   cd backend && railway logs --tail
   ```
3. Look for the error in the comprehensive logging we added

**Common causes:**
- CORS not configured (see Issue 1)
- Frontend using wrong backend URL (see Issue 2)
- Backend not deployed yet (wait for deployment to complete)
- Database connection issue (check Railway logs for database errors)

---

## Railway Services Overview

### Backend Service

**Name:** `backend`
**URL:** `https://backend-adcraft-production.up.railway.app`

**Environment Variables:**
- `SUPABASE_URL` = `https://rksxuhhegcxqmkjopudx.supabase.co`
- `SUPABASE_DB_PASSWORD` = `RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!`
- `SUPABASE_SERVICE_ROLE_KEY` = (your service role key)
- `OPENAI_API_KEY` = (your OpenAI key)
- `REPLICATE_API_TOKEN` = (your Replicate token)
- `REDIS_URL` = `redis://default:...@redis-adcraft.railway.internal:6379`
- `CORS_ORIGINS` = `http://localhost:5173,https://frontend-adcraft-production.up.railway.app`

### Frontend Service

**Name:** `frontend`
**URL:** `https://frontend-adcraft-production.up.railway.app`

**Environment Variables:**
- `VITE_API_URL` = `https://backend-adcraft-production.up.railway.app`
- `VITE_PROD` = `true`
- `VITE_SUPABASE_URL` = `https://rksxuhhegcxqmkjopudx.supabase.co`
- `VITE_SUPABASE_ANON_KEY` = (your anon key)

---

## Local Development

Your local `.env` files should match production URLs:

### backend/.env
```bash
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
# ... other variables ...
CORS_ORIGINS=http://localhost:5174,http://localhost:5173,http://localhost:3000,https://frontend-adcraft-production.up.railway.app
```

### frontend/.env.local (if you create one)
```bash
VITE_API_URL=http://localhost:8000  # Points to local backend
VITE_PROD=false
```

---

## Summary

✅ **Backend** - CORS updated to allow new frontend URL
✅ **Frontend** - Configured to call correct backend API
✅ **Database** - Using existing Supabase database (no changes needed)
✅ **Deployments** - Both services deploying to Railway
✅ **Logging** - Comprehensive logging enabled for debugging

**Wait for deployments to complete (2-3 minutes), then test the flow!**

---

## Quick Commands

```bash
# Check backend deployment status
cd backend && railway logs --tail

# Check frontend deployment status
cd frontend && railway logs --tail

# Test backend health
curl https://backend-adcraft-production.up.railway.app/health

# Test backend CORS config
curl https://backend-adcraft-production.up.railway.app/cors-info

# Open frontend
open https://frontend-adcraft-production.up.railway.app
```

---

## Next Steps

1. ✅ Wait for deployments to complete (check Railway dashboard)
2. ✅ Verify backend health endpoint
3. ✅ Verify CORS configuration
4. ✅ Test frontend loads correctly
5. ✅ Test "Continue to Storyline" flow end-to-end
6. ✅ Check comprehensive logs for any issues

**Your production frontend URL has been successfully updated!** 🚀
