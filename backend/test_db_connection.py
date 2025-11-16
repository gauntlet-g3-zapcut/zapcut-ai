"""
Test database connection and show connection string format
"""
from app.config import settings
import re

# Get the database URL
db_url = settings.database_url

# Mask the password for display
def mask_connection_string(url):
    """Mask password in connection string for safe display"""
    # Pattern to match password in postgresql:// connection strings
    # Format: postgresql://user:password@host:port/db
    pattern = r'(postgresql://[^:]+:)([^@]+)(@.+)'
    match = re.match(pattern, url)
    if match:
        return f"{match.group(1)}***MASKED***{match.group(3)}"
    return url

masked_url = mask_connection_string(db_url)

print("=" * 80)
print("DATABASE CONNECTION DIAGNOSTICS")
print("=" * 80)
print(f"\n1. Connection String Format:")
print(f"   {masked_url}")

# Parse the connection string to show components
pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
match = re.match(pattern, db_url)

if match:
    user, password, host, port, database = match.groups()
    print(f"\n2. Connection Components:")
    print(f"   User:     {user}")
    print(f"   Password: ***{password[-4:]} (showing last 4 chars)")
    print(f"   Host:     {host}")
    print(f"   Port:     {port}")
    print(f"   Database: {database}")

    # Check if using pooler or direct connection
    if 'pooler' in host:
        print(f"\n3. Connection Mode: POOLER (transaction mode)")
        print(f"   Note: Pooler connections use port 6543")

        # Extract project ref from pooler host
        # Format: aws-0-{region}.pooler.supabase.com
        print(f"\n4. Troubleshooting:")
        print(f"   - Verify your Supabase project is in the correct region")
        print(f"   - Verify password matches your database password (not service role key)")
        print(f"   - For pooler, format should be:")
        print(f"     postgresql://postgres.[PROJECT_REF]:[PASSWORD]@{host}:6543/postgres")
    else:
        print(f"\n3. Connection Mode: DIRECT")
        print(f"   Note: Direct connections use port 5432")

        # Extract project ref from direct host
        # Format: db.{project_ref}.supabase.co
        if 'db.' in host and 'supabase.co' in host:
            project_ref = host.replace('db.', '').replace('.supabase.co', '')
            print(f"   Project Ref: {project_ref}")

        print(f"\n4. Recommended Format (Direct Connection):")
        print(f"   postgresql://postgres:[YOUR_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres")

print(f"\n5. Environment Variables:")
print(f"   SUPABASE_URL: {settings.SUPABASE_URL or 'Not set'}")
print(f"   DATABASE_URL: {'Set' if settings.DATABASE_URL else 'Not set (constructed from SUPABASE_URL + SUPABASE_DB_PASSWORD)'}")

print("\n" + "=" * 80)
print("To fix 'Tenant or user not found' error:")
print("=" * 80)
print("1. Go to your Supabase dashboard: https://app.supabase.com")
print("2. Select your project")
print("3. Go to Settings > Database")
print("4. Copy the 'Connection string' under 'Connection parameters'")
print("5. Replace [YOUR-PASSWORD] with your actual database password")
print("6. Update DATABASE_URL in backend/.env with this connection string")
print("7. Restart the backend server")
print("=" * 80 + "\n")

# Try to connect
print("Testing connection...")
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    print(f"\nError type: {type(e).__name__}")
