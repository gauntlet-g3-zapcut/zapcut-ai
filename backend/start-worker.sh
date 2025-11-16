#!/bin/bash
# Railway Celery worker startup script

set -e

echo "=========================================="
echo "Starting Celery Worker"
echo "=========================================="
echo "PYTHON_VERSION: $(python --version 2>&1)"
echo "Working directory: $(pwd)"
echo "=========================================="

# Log environment variables (without sensitive values)
echo "Environment variables:"
env | grep -E "^(DATABASE_URL|REDIS_URL|OPENAI_API_KEY|SUPABASE|CORS)=" | sed 's/=.*/=***/' || echo "No relevant env vars found"
echo "=========================================="

# Check if REDIS_URL is set
if [ -z "$REDIS_URL" ]; then
    echo "❌ ERROR: REDIS_URL environment variable not set"
    echo "❌ Celery worker requires Redis connection"
    exit 1
fi

# Test celery_app import
echo "Testing celery_app import..."
python -c "
import sys
try:
    from app.celery_app import celery_app
    if celery_app is None:
        print('❌ Celery app is None (Redis not configured)', file=sys.stderr)
        sys.exit(1)
    print('✅ Celery app imported successfully', file=sys.stderr)
except Exception as e:
    print(f'❌ Failed to import celery_app: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
" || exit 1

echo "=========================================="
echo "Starting Celery worker..."
echo "=========================================="

# Start Celery worker
exec celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --time-limit=3600 \
    --soft-time-limit=3000

