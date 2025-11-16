#!/bin/bash
# Railway Celery worker startup script with comprehensive logging

# Don't exit on error - we want to see all errors
set +e

# Ensure we're in the right directory
if [ -f "queue/celery_app.py" ]; then
    echo "✅ Found queue/celery_app.py in current directory"
elif [ -f "backend/queue/celery_app.py" ]; then
    echo "✅ Found backend/queue/celery_app.py, changing directory"
    cd backend
elif [ -f "../backend/queue/celery_app.py" ]; then
    echo "✅ Found backend/queue/celery_app.py in parent, changing directory"
    cd ../backend
fi

echo "=========================================="
echo "Starting Celery Worker"
echo "=========================================="
echo "PYTHON_VERSION: $(python --version 2>&1 || echo 'not found')"
echo "Working directory: $(pwd)"
echo "Python path: $(which python)"
echo "Files in current dir: $(ls -la | head -5)"
echo "=========================================="

# Log environment variables (without sensitive values)
echo "Environment variables:"
env | grep -E "^(DATABASE_URL|REDIS_URL|OPENAI_API_KEY|SUPABASE|CORS)=" | sed 's/=.*/=***/' || echo "No relevant env vars found"
echo "=========================================="

# Check if REDIS_URL is set
if [ -z "$REDIS_URL" ]; then
    echo "⚠️  WARNING: REDIS_URL environment variable not set"
    echo "⚠️  Celery worker will not be able to connect to Redis"
    echo "⚠️  Worker will start but tasks will not be processed"
fi

# Try to import and test celery_app before starting
echo "Testing celery_app import..."
CELERY_AVAILABLE=$(python -c "
import sys
import traceback
try:
    from queue.celery_app import celery_app
    if celery_app is not None:
        print('OK', file=sys.stderr)
        sys.exit(0)
    else:
        print('NONE', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(2)
" 2>&1)

CELERY_STATUS=$?

if [ $CELERY_STATUS -eq 2 ]; then
    echo "❌ Failed to import celery_app, exiting"
    exit 1
elif [ $CELERY_STATUS -eq 1 ]; then
    echo "⚠️  Celery app is None (Redis not configured)"
    echo "⚠️  Worker cannot start without Redis connection"
    echo "⚠️  Please set REDIS_URL environment variable"
    exit 1
fi

echo "✅ Celery app imported successfully"

echo "=========================================="
echo "Starting Celery worker..."
echo "=========================================="

# Start Celery worker with explicit error handling and logging
exec celery -A queue.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --time-limit=3600 \
    --soft-time-limit=3000 \
    2>&1

