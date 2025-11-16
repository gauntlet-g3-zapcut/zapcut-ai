# How to Fix Database Connection Error

## Current Problem
❌ Error: `could not translate host name "db.rksxuhhegcxqmkjopudx.supabase.co"`

This means the Supabase project reference in your `.env` file is invalid or doesn't exist.

## Step-by-Step Fix

### Step 1: Go to Supabase Dashboard
1. Open your browser and go to: **https://app.supabase.com**
2. Log in to your Supabase account
3. You should see a list of your projects

### Step 2: Select or Create a Project
**Option A: If you have an existing project for zapcut-ai**
- Click on that project

**Option B: If you need to create a new project**
- Click **"New Project"**
- Choose your organization
- Enter project name: `zapcut-ai` (or any name you prefer)
- Enter a strong database password (SAVE THIS - you'll need it!)
- Select a region (choose closest to you, e.g., `us-east-1`)
- Click **"Create new project"**
- Wait 2-3 minutes for project to be provisioned

### Step 3: Get Your Database Connection String
1. In your project dashboard, click **Settings** (gear icon in left sidebar)
2. Click **Database** in the settings menu
3. Scroll down to **"Connection string"** section
4. Click the **"URI"** tab
5. You'll see a connection string like this:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
6. Click the **copy** button to copy it

### Step 4: Get Your Database Password
If the connection string shows `[YOUR-PASSWORD]`:
1. In the same **Database** settings page
2. Look for **"Database password"** section
3. If you don't know your password:
   - Click **"Reset Database Password"**
   - Copy the new password immediately (you can't see it again!)
   - Save it somewhere safe

### Step 5: Update Your `.env` File
1. Open `backend/.env` in your editor
2. Find the line that starts with `DATABASE_URL=`
3. Replace the entire line with your connection string from Step 3
4. Replace `[YOUR-PASSWORD]` with your actual database password from Step 4

Example:
```bash
# Before (invalid):
DATABASE_URL=postgresql://postgres:somepassword@db.rksxuhhegcxqmkjopudx.supabase.co:5432/postgres

# After (with real credentials):
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:MyActualPassword123!@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**IMPORTANT:** Make sure there are NO spaces around the `=` sign and NO quotes around the URL.

### Step 6: Save and Test Connection
1. Save the `.env` file
2. The backend server should automatically reload (you'll see it in the terminal)
3. Test the connection:
   ```bash
   cd backend
   source venv/bin/activate
   python test_db_connection.py
   ```
4. You should see: ✅ Connection successful!

### Step 7: Create Database Tables
Once connection is successful, create the tables:
```bash
curl -X POST http://localhost:8000/init-db
```

Or visit in your browser:
```
http://localhost:8000/init-db
```

Expected response:
```json
{
  "status": "success",
  "message": "Database tables created",
  "tables": ["users", "brands", "creative_bibles", "campaigns", "generation_jobs"]
}
```

## Alternative: Use Supabase Direct Connection (If Pooler Doesn't Work)

If the pooler connection fails, try the direct connection:

### Get Direct Connection String:
1. In Supabase Dashboard → Settings → Database
2. Under **"Connection string"**, click the **"Session pooling"** dropdown
3. Select **"Direct connection"**
4. Copy the connection string (format):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```
5. Update `DATABASE_URL` in `.env` with this string

## Troubleshooting

### Error: "Tenant or user not found"
- Wrong database password
- Solution: Reset your password in Supabase dashboard

### Error: "could not translate host name"
- Wrong project reference in URL
- Solution: Double-check you copied the correct connection string from Supabase

### Error: "relation does not exist"
- ✅ This is GOOD! Connection works, just need to create tables
- Solution: Run `/init-db` endpoint

### Error: "Extra inputs are not permitted"
- This should be fixed now with the updated config.py
- If still happening, make sure you updated config.py with `extra="ignore"`

## Quick Checklist
- [ ] Logged into Supabase dashboard
- [ ] Found or created project
- [ ] Copied connection string (URI format)
- [ ] Got database password
- [ ] Updated backend/.env with real credentials
- [ ] Replaced [YOUR-PASSWORD] with actual password
- [ ] Saved .env file (no spaces, no quotes)
- [ ] Tested connection with test_db_connection.py
- [ ] Created tables with /init-db endpoint
- [ ] Verified tables created successfully

## Need Help?
If you're still stuck, run the diagnostic:
```bash
cd backend
source venv/bin/activate
python test_db_connection.py
```

This will show you exactly what's wrong with your connection.
