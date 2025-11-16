"""
Script to verify Supabase Storage setup for the onboarding flow.
This script checks that the brands bucket exists and is properly configured.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client
from app.config import settings


def verify_storage_setup():
    """Verify that Supabase Storage is properly configured for image uploads."""
    print("🔍 Verifying Supabase Storage setup...\n")
    
    # Check environment variables
    if not settings.SUPABASE_URL:
        print("❌ SUPABASE_URL is not set")
        return False
    
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY is not set")
        return False
    
    print(f"✅ Supabase URL: {settings.SUPABASE_URL}")
    print(f"✅ Service Role Key: {'*' * 20}...{settings.SUPABASE_SERVICE_ROLE_KEY[-4:]}\n")
    
    # Initialize Supabase client
    try:
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        print("✅ Supabase client initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return False
    
    # Check if brands bucket exists
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        if 'brands' not in bucket_names:
            print("❌ 'brands' bucket does not exist")
            print(f"   Available buckets: {', '.join(bucket_names)}")
            print("\n   To create the bucket, run this SQL in Supabase Dashboard:")
            print("   INSERT INTO storage.buckets (id, name, public)")
            print("   VALUES ('brands', 'brands', true);")
            return False
        
        print("✅ 'brands' bucket exists")
        
        # Get bucket details
        brands_bucket = next((b for b in buckets if b.name == 'brands'), None)
        if brands_bucket:
            print(f"   - Public: {brands_bucket.public}")
            print(f"   - File size limit: {brands_bucket.file_size_limit or 'None'}")
            print(f"   - Allowed MIME types: {brands_bucket.allowed_mime_types or 'All'}")
        
    except Exception as e:
        print(f"❌ Failed to list buckets: {e}")
        return False
    
    # Test upload capability (optional - creates a test file)
    print("\n🧪 Testing upload capability...")
    try:
        test_content = b"test file content"
        test_path = "test/verify_storage_setup.txt"
        
        # Try to upload a test file
        result = supabase.storage.from_("brands").upload(
            path=test_path,
            file=test_content,
            file_options={"content-type": "text/plain"}
        )
        
        # Check if upload was successful
        if hasattr(result, 'error') and result.error:
            print(f"❌ Test upload failed: {result.error}")
            return False
        
        print("✅ Test upload successful")
        
        # Clean up test file
        try:
            supabase.storage.from_("brands").remove([test_path])
            print("✅ Test file cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up test file: {e}")
        
    except Exception as e:
        print(f"❌ Test upload failed: {e}")
        return False
    
    print("\n✅ All storage checks passed!")
    print("\n📝 Note: Storage policies (RLS) are not required for backend uploads")
    print("   since the backend uses the service role key which bypasses RLS.")
    print("   If you want to enable direct frontend uploads, you'll need to set up")
    print("   RLS policies in the Supabase Dashboard under Storage > Policies.")
    
    return True


if __name__ == "__main__":
    success = verify_storage_setup()
    sys.exit(0 if success else 1)

