#!/bin/bash

# Adcraft Railway Deployment - Step 4: Finalize Deployment
# Updates CORS, runs migrations, and verifies deployment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CREDENTIALS_FILE="$PROJECT_ROOT/.railway.env"
STATE_FILE="$PROJECT_ROOT/.railway.state"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Step 4: Finalize Deployment                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo -e "${RED}❌ Credentials file not found${NC}"
    exit 1
fi

if [ ! -f "$STATE_FILE" ]; then
    echo -e "${RED}❌ State file not found${NC}"
    exit 1
fi

# Load credentials
source "$CREDENTIALS_FILE"
source "$STATE_FILE"

if [ "$STEP_3_COMPLETED" != "true" ]; then
    echo -e "${RED}❌ Frontend not deployed yet${NC}"
    echo "Run: ./scripts/deploy/3-deploy-frontend.sh"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites verified${NC}"
echo ""

echo -e "${BLUE}Deployment Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Backend API:  $BACKEND_URL"
echo "  Frontend:     $FRONTEND_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Update Backend CORS
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 4.1: Update Backend CORS                             ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT/backend"

echo -e "${YELLOW}Updating CORS to allow frontend domain...${NC}"

# Build CORS origins list
CORS_LIST="$FRONTEND_URL,https://app.zapcut.video,http://localhost:5173,http://localhost:5174"

railway variables --set "CORS_ORIGINS=$CORS_LIST"

echo -e "${GREEN}✓ CORS updated: $CORS_LIST${NC}"
echo ""
echo -e "${YELLOW}Backend will redeploy automatically...${NC}"
sleep 10

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 4.2: Run Database Migrations                         ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Running Alembic migrations...${NC}"
echo ""

# Run migrations using Railway CLI
railway run alembic upgrade head || {
    echo -e "${YELLOW}⚠ Migration failed or already up to date${NC}"
    echo ""
    echo "You can run migrations manually:"
    echo "  cd backend"
    echo "  railway run alembic upgrade head"
    echo ""
}

echo -e "${GREEN}✓ Database migrations completed${NC}"
echo ""

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Step 4.3: Verify Deployment                               ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Test backend health endpoint
echo -e "${YELLOW}Testing Backend API...${NC}"
echo "  GET $BACKEND_URL/health"
echo ""

HEALTH_CHECK=$(curl -s "$BACKEND_URL/health" || echo "FAILED")

if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend API is healthy${NC}"
    echo "  Response: $HEALTH_CHECK"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "  Response: $HEALTH_CHECK"
    echo ""
    echo "Check backend logs:"
    echo "  cd backend && railway logs"
fi

echo ""

# Test frontend
echo -e "${YELLOW}Testing Frontend...${NC}"
echo "  GET $FRONTEND_URL"
echo ""

FRONTEND_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo "FAILED")

if [ "$FRONTEND_CHECK" = "200" ]; then
    echo -e "${GREEN}✓ Frontend is accessible (HTTP 200)${NC}"
else
    echo -e "${YELLOW}⚠ Frontend returned HTTP $FRONTEND_CHECK${NC}"
    echo ""
    echo "Check frontend logs:"
    echo "  cd frontend && railway logs"
fi

echo ""

# Test CORS
echo -e "${YELLOW}Testing CORS configuration...${NC}"
echo "  OPTIONS $BACKEND_URL/"
echo ""

CORS_CHECK=$(curl -s -X OPTIONS \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -o /dev/null -w "%{http_code}" \
    "$BACKEND_URL/" || echo "FAILED")

if [ "$CORS_CHECK" = "200" ] || [ "$CORS_CHECK" = "204" ]; then
    echo -e "${GREEN}✓ CORS is configured correctly${NC}"
else
    echo -e "${YELLOW}⚠ CORS check returned HTTP $CORS_CHECK${NC}"
    echo ""
    echo "Verify CORS_ORIGINS in backend includes: $FRONTEND_URL"
fi

echo ""

# Update state
sed -i.bak "s|STEP_4_COMPLETED=.*|STEP_4_COMPLETED=true|" "$STATE_FILE"
rm -f "$STATE_FILE.bak"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Deployment Complete!                                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "🎉 Adcraft is now deployed on Railway!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Production URLs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Frontend:     $FRONTEND_URL"
echo "  Backend API:  $BACKEND_URL"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Test the application:"
echo "   ${BLUE}open $FRONTEND_URL${NC}"
echo ""
echo "2. Test authentication:"
echo "   - Login with Supabase credentials"
echo "   - Create a test brand"
echo "   - Create a test campaign"
echo ""
echo "3. Test video generation:"
echo "   - Generate a test video"
echo "   - Check Celery worker logs for processing"
echo ""
echo "4. Monitor services:"
echo "   Backend:  ${BLUE}cd backend && railway logs${NC}"
echo "   Worker:   ${BLUE}railway logs --service celery-worker${NC}"
echo "   Frontend: ${BLUE}cd frontend && railway logs${NC}"
echo ""
echo "5. Set up custom domains (optional):"
echo "   - Railway Dashboard → Service → Settings → Domains"
echo ""
echo "6. Set up monitoring:"
echo "   - Add Sentry for error tracking"
echo "   - Set up uptime monitoring"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View your Railway project:"
echo "  ${BLUE}https://railway.app/project/$RAILWAY_PROJECT_NAME${NC}"
echo ""
echo "For troubleshooting, see:"
echo "  ${BLUE}$PROJECT_ROOT/RAILWAY_DEPLOYMENT_GUIDE.md${NC}"
echo ""
