#!/bin/bash

# Railway Configuration Checker
# This script checks your Railway deployment configuration

echo "======================================"
echo "Railway Configuration Checker"
echo "======================================"
echo ""

echo "1. Checking Backend API Service"
echo "--------------------------------------"
cd backend 2>/dev/null || cd ../backend 2>/dev/null || { echo "Error: Can't find backend directory"; exit 1; }

echo "Current directory: $(pwd)"
echo ""

echo "Environment Variables (Backend API):"
railway variables -k 2>&1
echo ""

echo "Service Status:"
railway status 2>&1
echo ""

echo "Recent Logs (last 20 lines):"
railway logs --limit 20 2>&1
echo ""

echo ""
echo "2. Checking if you have multiple services"
echo "--------------------------------------"
echo "Please manually check Railway dashboard for:"
echo "  - Celery Worker service"
echo "  - Redis service"
echo ""

echo ""
echo "======================================"
echo "Configuration Checklist"
echo "======================================"
echo ""
echo "Backend API should have:"
echo "  [ ] SUPABASE_URL"
echo "  [ ] SUPABASE_SERVICE_ROLE_KEY"
echo "  [ ] SUPABASE_DB_PASSWORD"
echo "  [ ] OPENAI_API_KEY"
echo "  [ ] REPLICATE_API_TOKEN"
echo "  [ ] REDIS_URL (referencing Redis service)"
echo "  [ ] CORS_ORIGINS"
echo "  [ ] PORT (optional)"
echo ""
echo "Celery Worker should have (same as backend):"
echo "  [ ] SUPABASE_URL"
echo "  [ ] SUPABASE_SERVICE_ROLE_KEY"
echo "  [ ] SUPABASE_DB_PASSWORD"
echo "  [ ] OPENAI_API_KEY"
echo "  [ ] REPLICATE_API_TOKEN"
echo "  [ ] REDIS_URL (referencing Redis service)"
echo ""
echo "Celery Worker custom start command should be:"
echo "  celery -A app.celery_app worker --loglevel=info --concurrency=2"
echo ""
