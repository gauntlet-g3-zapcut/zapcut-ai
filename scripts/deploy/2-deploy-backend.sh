#!/bin/bash

# Adcraft Railway Deployment - Step 2: Deploy Backend Services
# Deploys Backend API and Celery Worker

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
echo -e "${BLUE}║  Step 2: Deploy Backend Services                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo -e "${RED}❌ Credentials file not found${NC}"
    echo "Run: ./scripts/deploy/0-setup-credentials.sh"
    exit 1
fi

if [ ! -f "$STATE_FILE" ]; then
    echo -e "${RED}❌ State file not found${NC}"
    echo "Run: ./scripts/deploy/1-deploy-infrastructure.sh"
    exit 1
fi

# Load credentials
source "$CREDENTIALS_FILE"
source "$STATE_FILE"

if [ "$STEP_1_COMPLETED" != "true" ]; then
    echo -e "${RED}❌ Infrastructure not deployed${NC}"
    echo "Run: ./scripts/deploy/1-deploy-infrastructure.sh"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites verified${NC}"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploying Backend API Service                             ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Deploy backend API
echo -e "${YELLOW}Deploying Backend API from /backend directory...${NC}"
echo ""

cd "$PROJECT_ROOT/backend"

# Deploy using Railway CLI
railway up --detach || {
    echo -e "${YELLOW}⚠ Service might already exist. Continuing...${NC}"
}

echo ""
echo -e "${YELLOW}Setting environment variables for Backend API...${NC}"

# Set environment variables
echo "Setting variables one by one..."
railway variables --set "SUPABASE_URL=$SUPABASE_URL"
railway variables --set "SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY"
railway variables --set "SUPABASE_DB_PASSWORD=$SUPABASE_DB_PASSWORD"
railway variables --set "OPENAI_API_KEY=$OPENAI_API_KEY"
railway variables --set "REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN"
railway variables --set "CORS_ORIGINS=http://localhost:5173,https://app.zapcut.video"
railway variables --set "PORT=8000"

# Set DATABASE_URL if provided, otherwise let it auto-construct
if [ -n "$DATABASE_URL" ]; then
    railway variables --set "DATABASE_URL=$DATABASE_URL"
fi

# Reference Redis service
echo ""
echo -e "${YELLOW}Setting up Redis connection...${NC}"
echo ""
echo "Railway needs to reference the Redis service you created."
echo "The service name might be 'Redis', 'redis', or similar."
echo ""
echo "You can find the exact name in your Railway project dashboard."
echo ""
echo -e "${BLUE}Common Redis service names:${NC}"
echo "  - Redis"
echo "  - redis"
echo "  - redis-production"
echo ""
read -p "Enter your Redis service name (or press Enter for 'Redis'): " REDIS_SERVICE_NAME
REDIS_SERVICE_NAME=${REDIS_SERVICE_NAME:-Redis}
echo ""

# Set Redis URL using the service reference
echo -e "${YELLOW}Setting REDIS_URL to reference service: ${REDIS_SERVICE_NAME}${NC}"
railway variables --set "REDIS_URL=\${{${REDIS_SERVICE_NAME}.REDIS_URL}}"

echo ""
echo -e "${GREEN}✓ Backend API environment variables set${NC}"
echo -e "${BLUE}  Redis reference: \${{${REDIS_SERVICE_NAME}.REDIS_URL}}${NC}"
echo ""

# Wait for deployment
echo -e "${YELLOW}Waiting for Backend API to deploy...${NC}"
echo "This may take 2-3 minutes..."
echo ""

sleep 30  # Give it time to start deploying

# Get the backend URL
echo -e "${YELLOW}Getting Backend API URL...${NC}"
DOMAIN_OUTPUT=$(railway domain 2>&1 || echo "")

# Extract URL from Railway CLI output
BACKEND_URL=$(echo "$DOMAIN_OUTPUT" | grep -oE 'https://[a-zA-Z0-9.-]+\.railway\.app' | head -1)

if [ -z "$BACKEND_URL" ]; then
    echo -e "${YELLOW}⚠ Backend URL not yet available${NC}"
    echo "Railway CLI output: $DOMAIN_OUTPUT"
    echo ""
    echo "Please get the Backend URL from Railway dashboard:"
    echo "https://railway.app/project/$RAILWAY_PROJECT_NAME"
    echo ""
    read -p "Enter the Backend API URL: " BACKEND_URL
fi

if [ -n "$BACKEND_URL" ]; then
    # Ensure it has https://
    if [[ ! "$BACKEND_URL" =~ ^https?:// ]]; then
        BACKEND_URL="https://$BACKEND_URL"
    fi
    echo -e "${GREEN}✓ Backend API URL: ${BACKEND_URL}${NC}"
else
    echo -e "${YELLOW}⚠ Backend URL will be set later${NC}"
    BACKEND_URL="<pending>"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploying Celery Worker Service                           ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# For Celery worker, we need to create a new service from same repo
# This requires manual setup via Railway dashboard or different approach

echo -e "${YELLOW}Setting up Celery Worker...${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MANUAL STEP REQUIRED                                      "
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Railway CLI doesn't support creating multiple services from"
echo "the same directory easily. You need to create the Celery"
echo "Worker service manually:"
echo ""
echo "1. Go to: https://railway.app/project/$RAILWAY_PROJECT_NAME"
echo "2. Click '+ New Service'"
echo "3. Select 'GitHub Repo' → Your repository"
echo "4. Set Root Directory: '/backend'"
echo "5. Name it: 'celery-worker'"
echo "6. Under Settings → Deploy → Custom Start Command, set:"
echo "   ${BLUE}celery -A app.celery_app worker --loglevel=info --concurrency=2${NC}"
echo ""
echo "7. Add these environment variables (same as Backend API):"
echo "   ${BLUE}SUPABASE_URL=${SUPABASE_URL}${NC}"
echo "   ${BLUE}SUPABASE_SERVICE_ROLE_KEY=<same as backend>${NC}"
echo "   ${BLUE}SUPABASE_DB_PASSWORD=<same as backend>${NC}"
echo "   ${BLUE}OPENAI_API_KEY=<same as backend>${NC}"
echo "   ${BLUE}REPLICATE_API_TOKEN=<same as backend>${NC}"
echo "   ${BLUE}REDIS_URL=\${{${REDIS_SERVICE_NAME}.REDIS_URL}}${NC}"
if [ -n "$DATABASE_URL" ]; then
    echo "   ${BLUE}DATABASE_URL=$DATABASE_URL${NC}"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save helper script for worker environment variables
cat > "$PROJECT_ROOT/.railway-worker-vars.txt" << EOF
SUPABASE_URL=$SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
SUPABASE_DB_PASSWORD=$SUPABASE_DB_PASSWORD
OPENAI_API_KEY=$OPENAI_API_KEY
REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN
REDIS_URL=\${{${REDIS_SERVICE_NAME}.REDIS_URL}}
EOF

if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL=$DATABASE_URL" >> "$PROJECT_ROOT/.railway-worker-vars.txt"
fi

echo -e "${GREEN}✓ Worker environment variables saved to: .railway-worker-vars.txt${NC}"
echo ""

read -p "Press Enter once you've created the Celery Worker service..."
echo ""

# Update state with backend URL
sed -i.bak "s|BACKEND_URL=.*|BACKEND_URL=\"$BACKEND_URL\"|" "$STATE_FILE" 2>/dev/null || {
    echo "BACKEND_URL=\"$BACKEND_URL\"" >> "$STATE_FILE"
}

sed -i.bak "s|STEP_2_COMPLETED=.*|STEP_2_COMPLETED=true|" "$STATE_FILE"
rm -f "$STATE_FILE.bak"

# Also save to credentials file for next steps
sed -i.bak "s|BACKEND_URL=.*|BACKEND_URL=\"$BACKEND_URL\"|" "$CREDENTIALS_FILE" 2>/dev/null || {
    echo "BACKEND_URL=\"$BACKEND_URL\"" >> "$CREDENTIALS_FILE"
}
rm -f "$CREDENTIALS_FILE.bak"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Backend Services Deployment Complete                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Backend API URL: $BACKEND_URL"
echo ""
echo "Verify deployment:"
echo "  ${BLUE}curl $BACKEND_URL/health${NC}"
echo ""
echo "Check logs:"
echo "  ${BLUE}railway logs${NC}"
echo ""
echo "Next step:"
echo "  ${BLUE}./scripts/deploy/3-deploy-frontend.sh${NC}"
echo ""
