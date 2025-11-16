#!/bin/bash
# Test script for local server

set -e

echo "=========================================="
echo "Starting Local Server Test"
echo "=========================================="

cd "$(dirname "$0")"

# Set minimal environment variables for testing
export PORT=8000
export DATABASE_URL="postgresql://test:test@localhost:5432/test"  # Dummy for testing
export SUPABASE_URL="https://test.supabase.co"  # Dummy for testing

echo "Environment variables set"
echo "PORT: $PORT"
echo ""

# Start server in background
echo "Starting uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT > /tmp/server.log 2>&1 &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID"
echo "Waiting for server to be ready..."
sleep 3

# Test endpoints
echo ""
echo "=========================================="
echo "Testing Endpoints"
echo "=========================================="

# Test root endpoint
echo -n "Testing GET / ... "
if curl -s http://localhost:8000/ | grep -q "AdCraft API"; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
fi

# Test health endpoint
echo -n "Testing GET /health ... "
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
fi

# Test CORS info endpoint
echo -n "Testing GET /cors-info ... "
if curl -s http://localhost:8000/cors-info | grep -q "cors_origins"; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
fi

# Show server logs
echo ""
echo "=========================================="
echo "Server Logs (last 20 lines)"
echo "=========================================="
tail -20 /tmp/server.log

# Cleanup
echo ""
echo "Stopping server (PID: $SERVER_PID)..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="

