# Supabase Database Setup Guide

## Current Status
❌ Database connection is failing with DNS resolution error
- This means the SUPABASE_URL in your `.env` file is incorrect or the project doesn't exist

## Step-by-Step Fix

### 1. Get Your Real Supabase Connection String

Go to your Supabase dashboard:
1. Open https://app.supabase.com
2. Select your project (or create a new one if needed)
3. Go to **Settings** → **Database**
4. Scroll down to **Connection string**
5. Select **URI** tab
6. Copy the connection string (it will look like):
   ```
   postgresql://postgres.PROJECT_REF:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

### 2. Get Your Database Password

If you don't know your database password:
1. In the same **Settings** → **Database** page
2. Scroll to **Database password**
3. Click **Reset Database Password** if needed
4. Copy the new password (you won't be able to see it again!)

### 3. Update Your `.env` File

Open `backend/.env` and update these lines:

```bash
# Option 1: Use the connection string directly (RECOMMENDED)
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Option 2: Or use individual credentials
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_DB_PASSWORD=your-actual-database-password-here
```

### 4. Verify Your Connection

After updating `.env`, test the connection:

```bash
cd backend
source venv/bin/activate
python test_db_connection.py
```

You should see: ✅ Connection successful!

### 5. Create Database Tables

Once the connection works, create the tables:

```bash
curl -X POST http://localhost:8000/init-db
```

Or visit in your browser:
```
http://localhost:8000/init-db
```

You should get a response like:
```json
{
  "status": "success",
  "message": "Database tables created",
  "tables": ["users", "brands", "creative_bibles", "campaigns", "generation_jobs"]
}
```

### 6. Restart Your Backend Server

After updating `.env`, restart the uvicorn server to load the new credentials.

## Troubleshooting

### Error: "Tenant or user not found"
- Wrong database password
- Wrong project reference
- Solution: Double-check your connection string from Supabase dashboard

### Error: "could not translate host name"
- Wrong SUPABASE_URL or project doesn't exist
- Solution: Verify your project exists and get the correct URL from dashboard

### Error: "relation does not exist"
- Database connection works, but tables aren't created
- Solution: This is expected! Run the `/init-db` endpoint to create tables

## Current Configuration (from diagnostic)

Based on your current `.env`:
- Project Ref: `rksxuhhegcxqmkjopudx`
- Host: `db.rksxuhhegcxqmkjopudx.supabase.co`
- Status: ❌ Cannot resolve hostname

**This project reference appears to be invalid. Please get your real project details from Supabase dashboard.**
