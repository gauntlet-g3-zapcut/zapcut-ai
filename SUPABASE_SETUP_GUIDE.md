# Supabase Database Setup Guide
## Connect Railway Backend to Existing Supabase Database

This guide shows how to configure your Railway backend to use your existing Supabase database in both **production (Railway)** and **local development**.

---

## Your Existing Supabase Database

**Project Reference:** `rksxuhhegcxqmkjopudx`
**Database URL:** `https://rksxuhhegcxqmkjopudx.supabase.co`
**Database Password:** `RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!`

---

## Option 1: Use Existing Supabase Credentials (Recommended)

The backend automatically constructs the `DATABASE_URL` from `SUPABASE_URL` + `SUPABASE_DB_PASSWORD`.

### Railway Production Setup

Your Railway environment already has these variables set correctly:
```bash
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Action Required:** Remove or fix the incomplete `DATABASE_URL` variable:
```bash
cd backend
railway variables --unset DATABASE_URL
```

The backend will automatically construct:
```
postgresql://postgres:RyanMeow76%21%21%21RyanMeow76%21%21%21RyanMeow76%21%21%21@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

### Local Development Setup

Create or update `backend/.env`:
```bash
# Supabase Configuration (Auto-constructs DATABASE_URL)
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (get from Supabase dashboard)
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-... (your OpenAI key)

# Replicate Configuration
REPLICATE_API_TOKEN=r8_... (your Replicate token)

# Redis Configuration (local development)
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5174,http://localhost:5173,http://localhost:3000,https://app.zapcut.video
```

---

## Option 2: Use Direct DATABASE_URL (Alternative)

If you prefer to set `DATABASE_URL` directly instead of using auto-construction:

### Railway Production Setup

```bash
cd backend
railway variables --set "DATABASE_URL=postgresql://postgres:RyanMeow76%21%21%21RyanMeow76%21%21%21RyanMeow76%21%21%21@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres"
```

**Note:** The `%21` is the URL-encoded version of `!` in the password.

### Local Development Setup

Create or update `backend/.env`:
```bash
# Direct Database URL (Option 2)
DATABASE_URL=postgresql://postgres:RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres

# Supabase Configuration (still needed for Storage)
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# (rest same as Option 1)
```

---

## How It Works

The `backend/app/config.py` file automatically handles database URL construction:

```python
@property
def database_url(self) -> str:
    # Priority 1: Use DATABASE_URL if it's a valid PostgreSQL connection string
    if self.DATABASE_URL and self.DATABASE_URL.startswith(('postgresql://', 'postgres://')):
        return self.DATABASE_URL

    # Priority 2: Construct from SUPABASE_URL and SUPABASE_DB_PASSWORD if available
    if self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
        project_ref = self.SUPABASE_URL.replace('https://', '').split('.')[0]
        encoded_password = quote_plus(self.SUPABASE_DB_PASSWORD)
        return f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"

    # Otherwise: Raise error
    raise ValueError("DATABASE_URL is required...")
```

---

## Step-by-Step: Fix Railway Production (Option 1 - Recommended)

### Step 1: Remove Incomplete DATABASE_URL
```bash
cd /Users/reena/gauntletai/zapcut-ai/backend
railway variables --unset DATABASE_URL
```

### Step 2: Verify Other Variables Are Set
```bash
railway variables | grep -E "(SUPABASE|REDIS|OPENAI|REPLICATE)"
```

You should see:
- ✅ SUPABASE_URL
- ✅ SUPABASE_DB_PASSWORD
- ✅ SUPABASE_SERVICE_ROLE_KEY
- ✅ OPENAI_API_KEY
- ✅ REPLICATE_API_TOKEN

### Step 3: Set REDIS_URL for Celery
```bash
# Option A: Use Railway's Redis reference
railway variables --set 'REDIS_URL=${{Redis.REDIS_URL}}'

# Option B: Construct manually
railway variables --set 'REDIS_URL=redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379'
```

### Step 4: Add CORS_ORIGINS
```bash
railway variables --set "CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video,https://zapcut-ai-production.up.railway.app"
```

### Step 5: Redeploy Backend
```bash
railway up --detach
```

### Step 6: Verify Connection
Check the logs to ensure database connection works:
```bash
railway logs --tail
```

Look for:
```
✅ Database connection successful
Connected to: postgresql://postgres:***@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

---

## Step-by-Step: Setup Local Development

### Step 1: Copy Environment Template
```bash
cd /Users/reena/gauntletai/zapcut-ai/backend
cp .env.example .env
```

### Step 2: Edit .env File
```bash
# Open in your editor
code .env  # or nano .env, vim .env, etc.
```

### Step 3: Add Your Credentials
```bash
# Supabase Configuration
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJrc3h1aGhlZ2N4cW1ram9wdWR4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDk4OTg4NCwiZXhwIjoyMDQ2NTY1ODg0fQ.eFvWh9kvPgkCU0aXHj3M3kzr6JIuPgMnM_gLDUhxwRk
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-_SlZjo2aEzlsGwzyzBTQlrHtIz3-... (your key)

# Replicate Configuration
REPLICATE_API_TOKEN=r8_... (get from Railway or Replicate dashboard)

# Redis Configuration (local development)
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:5174,http://localhost:5173,http://localhost:3000
```

### Step 4: Test Database Connection
```bash
python test_db_connection.py
```

You should see:
```
✅ Database connection successful!
✅ Successfully connected to: postgresql://postgres:***@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

### Step 5: Start Local Backend
```bash
uvicorn app.main:app --reload --port 8000
```

---

## Troubleshooting

### Issue: "DATABASE_URL is required" Error

**Cause:** Neither `DATABASE_URL` nor `SUPABASE_URL + SUPABASE_DB_PASSWORD` are set.

**Solution:**
```bash
# Railway
railway variables --set "SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co"
railway variables --set "SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!"

# Local
# Add to backend/.env:
SUPABASE_URL=https://rksxuhhegcxqmkjopudx.supabase.co
SUPABASE_DB_PASSWORD=RyanMeow76!!!RyanMeow76!!!RyanMeow76!!!
```

### Issue: "relation 'brands' does not exist" Error

**Cause:** Tables haven't been created yet.

**Solution:**
```bash
cd backend
python create_tables.py
```

### Issue: Password Contains Special Characters

**Cause:** Special characters in password need URL encoding for `DATABASE_URL`.

**Solution:** Use Option 1 (auto-construction) which handles URL encoding automatically via `quote_plus()`.

---

## Verifying Both Environments Use Same Database

### Check Production Database
```bash
cd backend
railway run python -c "from app.config import settings; print(settings.database_url)"
```

### Check Local Database
```bash
cd backend
python -c "from app.config import settings; print(settings.database_url)"
```

Both should output:
```
postgresql://postgres:RyanMeow76%21%21%21RyanMeow76%21%21%21RyanMeow76%21%21%21@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres
```

This confirms both environments connect to the **same Supabase database**.

---

## Summary

✅ **Production (Railway):** Uses `SUPABASE_URL` + `SUPABASE_DB_PASSWORD` (auto-constructs DATABASE_URL)
✅ **Local Development:** Uses same credentials in `backend/.env`
✅ **Both environments:** Connect to same Supabase database at `db.rksxuhhegcxqmkjopudx.supabase.co`
✅ **Tables:** Reused from existing database (no need to recreate)

**Next Steps:**
1. Remove incomplete `DATABASE_URL` from Railway: `railway variables --unset DATABASE_URL`
2. Set up local `.env` file with Supabase credentials
3. Test both environments connect successfully
4. Deploy and verify in production
