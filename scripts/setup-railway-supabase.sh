#!/bin/bash

# Quick Setup Script: Configure Railway Backend to Use Existing Supabase Database
# This script sets up the correct environment variables in Railway production

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Railway + Supabase Setup Script                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/../backend" || exit 1

echo -e "${YELLOW}Current Railway Status:${NC}"
railway status
echo ""

echo -e "${YELLOW}Step 1: Switching to Backend Service${NC}"
echo "Please select the 'backend' service from the list..."
railway service
echo ""

echo -e "${YELLOW}Step 2: Verifying Current Variables${NC}"
echo "Checking SUPABASE configuration..."
railway variables | grep -E "(SUPABASE|DATABASE|REDIS)" || true
echo ""

echo -e "${YELLOW}Step 3: Setting REDIS_URL${NC}"
echo "Using Railway internal Redis connection..."
railway variables --set 'REDIS_URL=redis://default:WujxXDjpyMzDqvhnSTrIZpMUmykkyXzE@redis-adcraft.railway.internal:6379'
echo -e "${GREEN}✓ REDIS_URL set${NC}"
echo ""

echo -e "${YELLOW}Step 4: Setting CORS_ORIGINS${NC}"
railway variables --set "CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video,https://zapcut-ai-production.up.railway.app"
echo -e "${GREEN}✓ CORS_ORIGINS set${NC}"
echo ""

echo -e "${YELLOW}Step 5: Verifying DATABASE Configuration${NC}"
echo "The system should auto-construct DATABASE_URL from:"
echo "  - SUPABASE_URL"
echo "  - SUPABASE_DB_PASSWORD"
echo ""
railway variables | grep -E "SUPABASE_URL|SUPABASE_DB_PASSWORD"
echo ""

echo -e "${YELLOW}Step 6: Deploying Backend${NC}"
railway up --detach
echo -e "${GREEN}✓ Backend deployment started${NC}"
echo ""

echo -e "${YELLOW}Step 7: Getting Backend URL${NC}"
BACKEND_URL=$(railway domain 2>&1 | grep -oE 'https://[a-zA-Z0-9.-]+\.railway\.app' | head -1)
echo -e "${GREEN}Backend URL: ${BACKEND_URL}${NC}"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Railway Setup Complete                                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backend URL:${NC} $BACKEND_URL"
echo ""
echo -e "${BLUE}Test database connection:${NC}"
echo "  railway run python -c \"from app.config import settings; print('DB:', settings.database_url)\""
echo ""
echo -e "${BLUE}Check logs:${NC}"
echo "  railway logs --tail"
echo ""
echo -e "${BLUE}Verify health endpoint:${NC}"
echo "  curl ${BACKEND_URL}/health"
echo ""
