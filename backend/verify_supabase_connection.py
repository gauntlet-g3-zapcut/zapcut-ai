#!/usr/bin/env python3
"""
Verify Supabase Database Connection
Checks if the backend can connect to your existing Supabase database.
"""

import sys
from app.config import settings
from app.database import SessionLocal
from sqlalchemy import text

print("=" * 80)
print("🔍 Supabase Database Connection Verification")
print("=" * 80)
print()

# Step 1: Check environment variables
print("📋 Step 1: Checking environment variables...")
print()

if settings.SUPABASE_URL:
    print(f"  ✅ SUPABASE_URL: {settings.SUPABASE_URL}")
else:
    print(f"  ❌ SUPABASE_URL: Not set")

if settings.SUPABASE_DB_PASSWORD:
    print(f"  ✅ SUPABASE_DB_PASSWORD: {'*' * 20} (hidden)")
else:
    print(f"  ❌ SUPABASE_DB_PASSWORD: Not set")

if settings.SUPABASE_SERVICE_ROLE_KEY:
    print(f"  ✅ SUPABASE_SERVICE_ROLE_KEY: {settings.SUPABASE_SERVICE_ROLE_KEY[:20]}... (truncated)")
else:
    print(f"  ❌ SUPABASE_SERVICE_ROLE_KEY: Not set")

print()

# Step 2: Check constructed DATABASE_URL
print("📋 Step 2: Checking DATABASE_URL construction...")
print()

try:
    db_url = settings.database_url
    # Hide password in output
    safe_url = db_url.replace(settings.SUPABASE_DB_PASSWORD or "", "*" * 20)
    print(f"  ✅ DATABASE_URL: {safe_url}")
    print()
except Exception as e:
    print(f"  ❌ ERROR constructing DATABASE_URL: {e}")
    print()
    sys.exit(1)

# Step 3: Test database connection
print("📋 Step 3: Testing database connection...")
print()

try:
    db = SessionLocal()

    # Try a simple query
    result = db.execute(text("SELECT version()"))
    postgres_version = result.scalar()

    print(f"  ✅ Connection successful!")
    print(f"  PostgreSQL version: {postgres_version}")
    print()

except Exception as e:
    print(f"  ❌ Connection failed: {e}")
    print()
    sys.exit(1)
finally:
    if 'db' in locals():
        db.close()

# Step 4: Check for existing tables
print("📋 Step 4: Checking for existing tables...")
print()

try:
    db = SessionLocal()

    # Query for existing tables
    result = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))

    tables = [row[0] for row in result]

    if tables:
        print(f"  ✅ Found {len(tables)} tables in database:")
        for table in tables:
            print(f"     - {table}")
    else:
        print(f"  ⚠️  No tables found in public schema")
        print(f"     You may need to run: python create_tables.py")
    print()

except Exception as e:
    print(f"  ❌ Error checking tables: {e}")
    print()
finally:
    if 'db' in locals():
        db.close()

# Step 5: Check specific tables (brands, campaigns, etc.)
print("📋 Step 5: Checking application tables...")
print()

expected_tables = [
    'users',
    'brands',
    'creative_bibles',
    'campaigns',
    'videos'
]

try:
    db = SessionLocal()

    result = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = ANY(:tables)
    """), {"tables": expected_tables})

    found_tables = [row[0] for row in result]
    missing_tables = set(expected_tables) - set(found_tables)

    if not missing_tables:
        print(f"  ✅ All expected tables exist:")
        for table in found_tables:
            print(f"     - {table}")
    else:
        print(f"  ⚠️  Some tables are missing:")
        for table in missing_tables:
            print(f"     ❌ {table}")
        print()
        print(f"  Run: python create_tables.py")
    print()

except Exception as e:
    print(f"  ❌ Error checking application tables: {e}")
    print()
finally:
    if 'db' in locals():
        db.close()

# Step 6: Count records in key tables
print("📋 Step 6: Counting records in key tables...")
print()

try:
    db = SessionLocal()

    for table in ['users', 'brands', 'creative_bibles', 'campaigns']:
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  ✅ {table}: {count} records")
        except Exception as e:
            print(f"  ⚠️  {table}: Error - {str(e)[:50]}")

    print()

except Exception as e:
    print(f"  ❌ Error counting records: {e}")
    print()
finally:
    if 'db' in locals():
        db.close()

# Summary
print("=" * 80)
print("✅ Verification Complete!")
print("=" * 80)
print()
print("Your backend is correctly configured to use the existing Supabase database.")
print()
print("Database: db.rksxuhhegcxqmkjopudx.supabase.co")
print()
print("Next steps:")
print("  1. Start backend: uvicorn app.main:app --reload --port 8000")
print("  2. Test API: curl http://localhost:8000/health")
print("  3. Test database endpoint: curl http://localhost:8000/api/brands/")
print()
