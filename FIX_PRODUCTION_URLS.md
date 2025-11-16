# Fix Production URLs - Backend & Frontend Connection

## Issue Found

Your **backend** is working perfectly at:
```
https://backend-adcraft-production.up.railway.app
```

But your **frontend** is configured to use a different URL:
```
https://zapcut-ai-production.up.railway.app  ❌ WRONG
```

This is why "Continue to Storyline" fails - the frontend is calling the wrong backend!

---

## Quick Fix (5 Minutes)

### Step 1: Update Backend CORS Settings

The backend needs to allow requests from your frontend domain.

```bash
cd backend

# Set CORS to allow frontend domain
railway variables --set "CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video,https://frontend-adcraft-production.up.railway.app"

# Redeploy
railway up --detach
```

**Or via Railway Dashboard:**
1. Go to: https://railway.app → AdCraft → Backend Service → Variables
2. Update `CORS_ORIGINS` to:
   ```
   http://localhost:5173,https://app.zapcut.video,https://frontend-adcraft-production.up.railway.app
   ```
3. Click "Deploy"

### Step 2: Update Frontend Backend URL

The frontend needs to know where the backend is.

```bash
cd ../frontend

# Set the backend API URL
railway variables --set "VITE_API_URL=https://backend-adcraft-production.up.railway.app"

# Set production flag
railway variables --set "VITE_PROD=true"

# Redeploy
railway up --detach
```

**Or via Railway Dashboard:**
1. Go to: https://railway.app → AdCraft → Frontend Service → Variables
2. Add:
   - `VITE_API_URL` = `https://backend-adcraft-production.up.railway.app`
   - `VITE_PROD` = `true`
3. Click "Deploy"

### Step 3: Verify Deployment

**Check Backend:**
```bash
curl https://backend-adcraft-production.up.railway.app/health
# Should return: {"status":"healthy"}

curl https://backend-adcraft-production.up.railway.app/api/brands/
# Should return: Array of brands
```

**Check Frontend:**
1. Go to your frontend URL (check Railway dashboard for the domain)
2. Open browser DevTools → Console
3. Look for: `🚀 Final API_URL: https://backend-adcraft-production.up.railway.app`
4. Try "Continue to Storyline" flow
5. Check that API calls go to `backend-adcraft-production.up.railway.app`

---

## What's Currently Happening

Looking at your backend logs, I can see:
- ✅ Database is connected and working
- ✅ 12 brands exist in database
- ✅ API endpoints are responding correctly
- ✅ Comprehensive logging is working
- ⚠️ Frontend is calling wrong backend URL

---

## Complete URL Configuration

After fixing, your production setup should be:

| Service | URL | Environment Variables |
|---------|-----|----------------------|
| **Backend** | `https://backend-adcraft-production.up.railway.app` | `CORS_ORIGINS` = includes frontend URL |
| **Frontend** | `https://[frontend-domain].up.railway.app` | `VITE_API_URL` = backend URL |
| **Database** | `db.rksxuhhegcxqmkjopudx.supabase.co` | Auto-constructed from `SUPABASE_URL` + `SUPABASE_DB_PASSWORD` |

---

## Verification Checklist

After deploying:

- [ ] Backend health check works:
  ```bash
  curl https://backend-adcraft-production.up.railway.app/health
  ```

- [ ] Backend brands endpoint works:
  ```bash
  curl https://backend-adcraft-production.up.railway.app/api/brands/
  ```

- [ ] Frontend console shows correct API URL:
  ```
  🚀 Final API_URL: https://backend-adcraft-production.up.railway.app
  ```

- [ ] CORS headers allow frontend domain:
  ```bash
  curl -H "Origin: https://[your-frontend-domain]" \
       -H "Access-Control-Request-Method: POST" \
       -X OPTIONS \
       https://backend-adcraft-production.up.railway.app/api/campaigns
  ```

- [ ] "Continue to Storyline" flow works end-to-end

---

## Check Frontend Domain

To find your frontend URL:

```bash
cd frontend
railway domain
```

Or check Railway Dashboard → Frontend Service → Settings → Domains

---

## Troubleshooting

### Issue: CORS Error in Browser Console
```
Access to fetch at 'https://backend-adcraft-production.up.railway.app/...'
from origin 'https://[frontend-domain]' has been blocked by CORS policy
```

**Fix:** Update `CORS_ORIGINS` in backend to include frontend domain (see Step 1)

### Issue: Frontend Still Calls Old URL
```
🚀 Final API_URL: https://zapcut-ai-production.up.railway.app
```

**Fix:** Set `VITE_API_URL` in frontend Railway variables (see Step 2)

### Issue: 404 Not Found on API Calls

**Check:** Is the backend URL correct?
```bash
curl https://backend-adcraft-production.up.railway.app/health
```

If this works, the backend is fine. Problem is frontend configuration.

---

## Summary

Your backend is **100% working** - database connected, APIs responding, logging enabled.

The issue is just URL configuration:
1. ✅ **Backend URL:** `https://backend-adcraft-production.up.railway.app`
2. ❌ **Frontend needs:** `VITE_API_URL` environment variable set
3. ❌ **Backend needs:** `CORS_ORIGINS` updated to include frontend domain

**Fix both, redeploy, and you're done!** 🚀
