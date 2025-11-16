#!/bin/bash
# Start script for Celery worker service on Fly.io
# This script runs ONLY the Celery worker - FastAPI runs on separate machine

set -e

# Check if REDIS_URL is set
if [ -z "$REDIS_URL" ]; then
    echo "ERROR: REDIS_URL environment variable is not set"
    echo "Celery worker requires Redis to function"
    exit 1
fi

# Start Celery worker with solo pool (single-threaded)
# Solo pool is recommended for Fly.io small machines to reduce memory usage
echo "Starting Celery worker..."
echo "Redis URL: ${REDIS_URL:0:20}..." # Show first 20 chars for logging
echo "Using solo pool (single-threaded)"

exec celery -A app.celery_app worker \
    --loglevel=info \
    --pool=solo \
    --concurrency=1

