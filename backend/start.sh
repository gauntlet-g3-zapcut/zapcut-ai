#!/bin/bash
# Start script for FastAPI API service
# This script runs ONLY FastAPI - Celery worker runs on separate service

set -e

# Use PORT environment variable (provided by Railway) or default to 8000 for local development
PORT=${PORT:-8000}

# Start FastAPI application
echo "Starting FastAPI application..."
echo "Binding to 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
