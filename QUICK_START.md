# Quick Start: Railway + Supabase Setup

## Problem
Railway backend needs to connect to your **existing Supabase database** (with existing tables).

## Solution (2 Minutes)

### For Railway Production

**Option 1: Manual (Railway Dashboard)**
1. Go to: https://railway.app → Your Project → Backend Service → Variables
2. Verify these variables exist:
   - ✅ `SUPABASE_URL` = `https://rksxuhhegcxqmkjopudx.supabase.co`
   - ✅ `SUPABASE_DB_PASSWORD` = `RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!`
   - ✅ `SUPABASE_SERVICE_ROLE_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
3. Add/Update these variables:
   - `REDIS_URL` = `redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379`
   - `CORS_ORIGINS` = `http://localhost:5173,https://app.zapcut.video,https://zapcut-ai-production.up.railway.app`
4. **Remove** `DATABASE_URL` if it says just `postgresql://` (incomplete)
5. Click "Deploy" button

**Option 2: Railway CLI**
```bash
cd backend

# Switch to backend service (select from interactive list)
railway service

# Set REDIS_URL
railway variables --set 'REDIS_URL=redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379'

# Set CORS_ORIGINS
railway variables --set "CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video,https://zapcut-ai-production.up.railway.app"

# Deploy
railway up --detach

# Check logs
railway logs --tail
```

### For Local Development

**One-Time Setup:**
```bash
cd backend
cp .env.example .env
```

**Edit `backend/.env`:**
```bash
# Supabase Configuration (connects to SAME database as production)
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJrc3h1aGhlZ2N4cW1ram9wdWR4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDk4OTg4NCwiZXhwIjoyMDQ2NTY1ODg0fQ.eFvWh9kvPgkCU0aXHj3M3kzr6JIuPgMnM_gLDUhxwRk
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-_SlZjo2aEzlsGwzyzBTQlrHtIz3-... (get from Railway or OpenAI dashboard)

# Replicate Configuration
REPLICATE_API_TOKEN=r8_... (get from Railway or Replicate dashboard)

# Redis Configuration (local development)
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5174,http://localhost:5173,http://localhost:3000
```

**Start Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

---

## How It Works

Your backend **automatically constructs** the database URL from Supabase credentials:

```
SUPABASE_URL + SUPABASE_DB_PASSWORD
    ↓
postgresql://postgres:RyanMeow76!!!...@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

This is handled in `backend/app/config.py`:
- ✅ URL-encodes password automatically (special characters like `!`)
- ✅ Uses same database for production and local
- ✅ No need to manually set `DATABASE_URL`

---

## Verify It Works

### Production (Railway)
```bash
cd backend
railway run python -c "from app.config import settings; print(settings.database_url)"
```

Should output:
```
postgresql://postgres:RyanMeow76%21%21%21...@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

### Local
```bash
cd backend
python -c "from app.config import settings; print(settings.database_url)"
```

Should output the **same URL** (confirming same database).

### Test Database Tables
```bash
cd backend
python -c "
from app.database import SessionLocal
from app.models.brand import Brand
db = SessionLocal()
brands = db.query(Brand).all()
print(f'Found {len(brands)} brands in database')
db.close()
"
```

---

## Troubleshooting

### "DATABASE_URL is required" Error
- **Cause:** Missing `SUPABASE_URL` or `SUPABASE_DB_PASSWORD`
- **Fix:** Set both variables in Railway or `.env`

### "relation 'brands' does not exist" Error
- **Cause:** Tables not created yet
- **Fix:** `python create_tables.py` (only if tables truly don't exist)
- **Note:** You said tables already exist, so this shouldn't happen

### Cannot Connect to Database
- **Check 1:** Verify Supabase project is active (https://supabase.com/dashboard)
- **Check 2:** Verify password is correct (test in Supabase SQL editor)
- **Check 3:** Check Railway logs: `railway logs --tail`

---

## Summary

| Environment | Database URL Source | Connection String |
|-------------|---------------------|-------------------|
| **Production (Railway)** | Auto-constructed from `SUPABASE_URL` + `SUPABASE_DB_PASSWORD` | `postgresql://postgres:...@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres` |
| **Local Development** | Auto-constructed from `.env` file | Same as production |

✅ Both environments use the **same Supabase database**
✅ Existing tables are **reused** (not recreated)
✅ Password encoding handled **automatically**

---

## Next Steps

1. ✅ Set up Railway variables (see above)
2. ✅ Set up local `.env` file (see above)
3. Deploy frontend with correct backend URL
4. Test the "Continue to Storyline" flow
5. Check production logs for debugging

**For detailed setup:** See `SUPABASE_SETUP_GUIDE.md`
