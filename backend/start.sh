#!/bin/bash
# Start script for FastAPI API service on Fly.io
# This script runs ONLY FastAPI - Celery worker runs on separate machine

set -e

# Start FastAPI application
echo "Starting FastAPI application..."
echo "Binding to 0.0.0.0:8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
