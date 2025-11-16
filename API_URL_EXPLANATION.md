# API_URL Configuration Explained

## The Confusion: Multiple API_URLs

There are **two different `API_URL` variables** in different contexts:

### 1. Backend's `API_URL` (backend/app/config.py)
```python
API_URL: str = "http://localhost:8000"
```

**Purpose:** This is the backend telling itself what its own URL is.
**Used by:** Backend code (if it needs to reference itself)
**Default value:** `http://localhost:8000` (for local development)

**⚠️ This does NOT control where the frontend calls the backend!**

### 2. Frontend's `VITE_API_URL` (Railway environment variable)
```bash
VITE_API_URL=https://backend-adcraft-production.up.railway.app
```

**Purpose:** This tells the frontend where to find the backend API.
**Used by:** Frontend code (`frontend/src/services/api.js`)
**Production value:** `https://backend-adcraft-production.up.railway.app`

**✅ This DOES control where the frontend calls the backend!**

---

## What Matters for Frontend-Backend Communication

For your frontend to call the backend correctly, you need:

### ✅ Frontend Configuration
```bash
# Railway frontend environment variable
VITE_API_URL=https://backend-adcraft-production.up.railway.app
```

This is used in `frontend/src/services/api.js`:
```javascript
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL  // Uses this in production
  }
  // ... fallback logic
}
```

### ✅ Backend CORS Configuration
```bash
# Railway backend environment variable
CORS_ORIGINS=http://localhost:5173,https://frontend-adcraft-production.up.railway.app
```

This allows the backend to accept requests from your frontend.

---

## Should You Change Backend's API_URL?

**No, you don't need to!** Here's why:

The `API_URL` in `backend/app/config.py` is rarely used. It's there for:
- Backend to know its own URL (in case it needs to generate links to itself)
- Default configuration value
- Legacy/future use cases

**It does NOT affect:**
- ❌ Where the frontend calls the backend
- ❌ CORS configuration
- ❌ Database connections
- ❌ API endpoints

**What DOES affect where frontend calls backend:**
- ✅ `VITE_API_URL` environment variable in Railway frontend service
- ✅ `getApiUrl()` function in `frontend/src/services/api.js`

---

## Current Configuration (Correct!)

### Production

**Frontend knows backend is at:**
```
VITE_API_URL = https://backend-adcraft-production.up.railway.app
```

**Backend allows requests from:**
```
CORS_ORIGINS = http://localhost:5173,https://frontend-adcraft-production.up.railway.app
```

**Backend's self-reference (not used for frontend-backend communication):**
```
API_URL = http://localhost:8000 (default, doesn't matter)
```

### Local Development

**Frontend knows backend is at:**
```
VITE_API_URL = (not set, falls back to http://localhost:8000)
```

**Backend allows requests from:**
```
CORS_ORIGINS = http://localhost:5173,http://localhost:5174,http://localhost:3000,...
```

**Backend's self-reference:**
```
API_URL = http://localhost:8000 (correct for local)
```

---

## Summary

| Variable | File/Location | Purpose | Production Value |
|----------|---------------|---------|------------------|
| **Backend `API_URL`** | `backend/app/config.py` | Backend's self-reference (rarely used) | `http://localhost:8000` (default, OK to leave) |
| **Frontend `VITE_API_URL`** | Railway frontend env var | Where frontend calls backend | `https://backend-adcraft-production.up.railway.app` ✅ |
| **Backend `CORS_ORIGINS`** | Railway backend env var | Which origins can call backend | Includes `https://frontend-adcraft-production.up.railway.app` ✅ |

---

## TL;DR

**The `API_URL = "http://localhost:8000"` in backend config is fine!**

It's just a default value for the backend's self-reference and doesn't control where your frontend calls the backend. What matters is:

1. ✅ Frontend's `VITE_API_URL` = `https://backend-adcraft-production.up.railway.app`
2. ✅ Backend's `CORS_ORIGINS` = includes `https://frontend-adcraft-production.up.railway.app`

Both of these are already correctly configured! 🎉
