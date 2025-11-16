#!/bin/bash
# Railway startup script

set -e

echo "=========================================="
echo "Starting AdCraft API Server"
echo "=========================================="
echo "PORT: ${PORT:-8000}"
echo "PYTHON_VERSION: $(python --version 2>&1)"
echo "Working directory: $(pwd)"
echo "=========================================="

# Log environment variables (without sensitive values)
echo "Environment variables:"
env | grep -E "^(DATABASE_URL|REDIS_URL|OPENAI_API_KEY|SUPABASE|CORS|PORT)=" | sed 's/=.*/=***/' || echo "No relevant env vars found"
echo "=========================================="

# Set default PORT if not provided
export PORT=${PORT:-8000}

# Test app import
echo "Testing app import..."
python -c "
import sys
try:
    from app.main import app
    print(f'✅ App imported successfully: {app.title}', file=sys.stderr)
except Exception as e:
    print(f'❌ Failed to import app: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
" || exit 1

echo "=========================================="
echo "Starting uvicorn server on port $PORT..."
echo "=========================================="

# Start uvicorn server
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
