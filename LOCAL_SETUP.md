# Local Development Setup - Quick Fix

## The Problem
You're getting `ModuleNotFoundError` because Python dependencies aren't installed in your local environment.

## Quick Solution (2 minutes)

### Step 1: Activate Virtual Environment
```bash
cd /Users/reena/gauntletai/zapcut-ai/backend

# Activate virtual environment
source venv/bin/activate
```

You should see `(venv)` appear in your terminal prompt.

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages including:
- fastapi
- pydantic-settings
- sqlalchemy
- supabase
- etc.

### Step 3: Verify Database Connection
```bash
# Now this command will work:
python -c "from app.config import settings; print('DB:', settings.database_url)"
```

**Expected output:**
```
DB: postgresql://postgres:RyanMeow76%21%21%21RyanMeow76%21%21%21RyanMeow76%21%21%21@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

### Step 4: Run the Verification Script
```bash
python verify_supabase_connection.py
```

**Expected output:**
```
================================================================================
🔍 Supabase Database Connection Verification
================================================================================

📋 Step 1: Checking environment variables...
  ✅ SUPABASE_URL: https://rksxuhhegcxqmkjopudx.supabase.co
  ✅ SUPABASE_DB_PASSWORD: ******************** (hidden)
  ✅ SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiI... (truncated)

📋 Step 2: Checking DATABASE_URL construction...
  ✅ DATABASE_URL: postgresql://postgres:*****@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres

📋 Step 3: Testing database connection...
  ✅ Connection successful!
  PostgreSQL version: PostgreSQL 15.1 (Ubuntu 15.1-1.pgdg20.04+1) on x86_64-pc-linux-gnu...

📋 Step 4: Checking for existing tables...
  ✅ Found X tables in database:
     - users
     - brands
     - creative_bibles
     - campaigns
     - videos
     - (etc.)

================================================================================
✅ Verification Complete!
================================================================================
```

### Step 5: Start Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

Open browser to: http://localhost:8000/docs

---

## Alternative: Check Railway Production (Without Installing Locally)

If you just want to check the production Railway database configuration without setting up locally:

```bash
cd backend

# Check environment variables in Railway
railway variables | grep -E "(DATABASE|SUPABASE)"
```

**You should see:**
```
SUPABASE_URL                      │ https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_DB_PASSWORD              │ RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
SUPABASE_SERVICE_ROLE_KEY         │ eyJhbGciOiJIUzI1NiI...
DATABASE_URL                      │ (should be empty or wrong, that's OK)
```

**Note:** If `DATABASE_URL` shows just `postgresql://` (incomplete), that's fine! The backend auto-constructs it from `SUPABASE_URL` + `SUPABASE_DB_PASSWORD`.

### Check Railway Logs
```bash
railway logs --tail
```

Look for database connection logs when the service starts.

---

## Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'pydantic_settings'"
**Cause:** Virtual environment not activated or dependencies not installed

**Fix:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 2: "No such file or directory: '.env'"
**Cause:** Missing `.env` file

**Fix:**
```bash
cp .env.example .env
# Edit .env and add your credentials (see QUICK_START.md)
```

### Issue 3: Virtual environment activation doesn't work
**Fix:**
```bash
# Delete and recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Complete Local Setup Checklist

- [ ] Navigate to backend directory: `cd backend`
- [ ] Activate virtual environment: `source venv/bin/activate`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file: `cp .env.example .env`
- [ ] Edit `.env` with your credentials (see QUICK_START.md)
- [ ] Verify connection: `python verify_supabase_connection.py`
- [ ] Start backend: `uvicorn app.main:app --reload --port 8000`
- [ ] Test API: Open http://localhost:8000/docs

---

## Environment Variables Required in `.env`

```bash
# Supabase Configuration
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJrc3h1aGhlZ2N4cW1ram9wdWR4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDk4OTg4NCwiZXhwIjoyMDQ2NTY1ODg0fQ.eFvWh9kvPgkCU0aXHj3M3kzr6JIuPgMnM_gLDUhxwRk
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!

# Get from Railway dashboard → Backend service → Variables
OPENAI_API_KEY=sk-proj-...
REPLICATE_API_TOKEN=r8_...

# Redis Configuration (local)
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5174,http://localhost:5173,http://localhost:3000
```

**To get API keys from Railway:**
```bash
railway variables | grep -E "(OPENAI|REPLICATE)"
```

---

## Next Steps After Setup

1. ✅ Start backend: `uvicorn app.main:app --reload --port 8000`
2. Start frontend: `cd ../frontend && npm run dev`
3. Test the app at: http://localhost:5173
4. Test "Continue to Storyline" flow
5. Check logs in terminal and browser console

**See SETUP_COMPLETE.md for full production deployment steps.**
