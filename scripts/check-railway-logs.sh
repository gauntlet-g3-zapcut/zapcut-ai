#!/bin/bash

# Quick script to check Railway deployment logs

echo "======================================"
echo "Railway Deploy Logs Checker"
echo "======================================"
echo ""

cd backend 2>/dev/null || cd ../backend 2>/dev/null || { echo "Error: Can't find backend directory"; exit 1; }

echo "Fetching latest deployment logs..."
echo ""

railway logs --limit 100

echo ""
echo "======================================"
echo "If you see errors above, common issues:"
echo "======================================"
echo ""
echo "1. Database Connection Error:"
echo "   - Check SUPABASE_URL is set"
echo "   - Check SUPABASE_DB_PASSWORD is correct"
echo ""
echo "2. Redis Connection Error:"
echo "   - Check REDIS_URL is set"
echo "   - Check Redis service exists and is active"
echo ""
echo "3. Missing Environment Variables:"
echo "   - Check all required vars are set"
echo "   - Run: railway variables"
echo ""
echo "4. Module Import Errors:"
echo "   - Check requirements.txt has all dependencies"
echo ""
