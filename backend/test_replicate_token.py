"""Test Replicate API token to verify authentication"""
import os
from dotenv import load_dotenv
import replicate

# Load environment variables
load_dotenv()

print("="*80)
print("🧪 REPLICATE API TOKEN TEST")
print("="*80)

# Check if token exists in environment
token = os.getenv("REPLICATE_API_TOKEN")
print(f"\n1. Token exists in .env: {bool(token)}")
if token:
    print(f"   Token preview: {token[:10]}...{token[-5:]}")
    print(f"   Token length: {len(token)} characters")
else:
    print("   ❌ No token found!")
    exit(1)

# Test the token with Replicate API
print("\n2. Testing token with Replicate API...")
try:
    client = replicate.Client(api_token=token)

    # Try to list models (lightweight API call)
    print("   Attempting to authenticate with Replicate...")

    # Try a simple prediction with a real model we're using
    print("   Running test prediction with Flux Pro model...")
    output = client.run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": "A simple test image of a red circle",
            "aspect_ratio": "1:1",
            "output_format": "png",
            "output_quality": 80
        }
    )

    print("   ✅ SUCCESS! Token is valid and working")
    print(f"   Test output: {output}")

except replicate.exceptions.ReplicateError as e:
    print(f"   ❌ REPLICATE ERROR: {e}")
    if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
        print("   → This is an authentication error. Token is invalid/expired.")
    else:
        print(f"   → This is a different error: {type(e).__name__}")
except Exception as e:
    print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")

print("\n" + "="*80)
