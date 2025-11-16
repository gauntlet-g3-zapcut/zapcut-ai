#!/bin/bash
# Railway startup script with comprehensive logging

# Don't exit on error - we want to see all errors
set +e

echo "=========================================="
echo "Starting AdCraft API Server"
echo "=========================================="
echo "PORT: ${PORT:-not set}"
echo "PYTHON_VERSION: $(python --version 2>&1 || echo 'not found')"
echo "Working directory: $(pwd)"
echo "Python path: $(which python)"
echo "=========================================="

# Log environment variables (without sensitive values)
echo "Environment variables:"
env | grep -E "^(DATABASE_URL|REDIS_URL|OPENAI_API_KEY|SUPABASE|CORS|PORT)=" | sed 's/=.*/=***/' || echo "No relevant env vars found"
echo "=========================================="

# Check if PORT is set
if [ -z "$PORT" ]; then
    echo "⚠️  WARNING: PORT environment variable not set, using 8000"
    export PORT=8000
fi

# Try to import and test the app before starting
echo "Testing app import..."
python -c "
import sys
import traceback
try:
    print('Importing app.main...', file=sys.stderr)
    sys.stderr.flush()
    from app.main import app
    print('✅ App imported successfully', file=sys.stderr)
    print(f'✅ App title: {app.title}', file=sys.stderr)
    sys.stderr.flush()
except Exception as e:
    print(f'❌ Failed to import app: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    sys.exit(1)
" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ App import failed, exiting"
    exit 1
fi

echo "=========================================="
echo "Starting uvicorn server on port $PORT..."
echo "=========================================="

# Start uvicorn with explicit error handling and logging
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level debug \
    2>&1

