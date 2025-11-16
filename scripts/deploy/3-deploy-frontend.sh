#!/bin/bash

# Adcraft Railway Deployment - Step 3: Deploy Frontend
# Deploys React/Vite frontend application

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
echo -e "${BLUE}║  Step 3: Deploy Frontend                                  ║${NC}"
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

if [ "$STEP_2_COMPLETED" != "true" ]; then
    echo -e "${RED}❌ Backend not deployed yet${NC}"
    echo "Run: ./scripts/deploy/2-deploy-backend.sh"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites verified${NC}"
echo ""

# Check if backend URL is available
if [ -z "$BACKEND_URL" ] || [ "$BACKEND_URL" = "<pending>" ]; then
    echo -e "${YELLOW}⚠ Backend URL not available${NC}"
    echo ""
    read -p "Enter your Backend API URL (e.g., https://backend.railway.app): " BACKEND_URL

    # Save it
    sed -i.bak "s|BACKEND_URL=.*|BACKEND_URL=\"$BACKEND_URL\"|" "$CREDENTIALS_FILE"
    sed -i.bak "s|BACKEND_URL=.*|BACKEND_URL=\"$BACKEND_URL\"|" "$STATE_FILE"
    rm -f "$CREDENTIALS_FILE.bak" "$STATE_FILE.bak"
fi

echo ""
echo -e "${BLUE}Backend API URL: ${BACKEND_URL}${NC}"
echo ""

# Navigate to frontend directory
cd "$PROJECT_ROOT/frontend"

echo -e "${YELLOW}Deploying Frontend...${NC}"
echo ""

# Deploy using Railway CLI
railway up --detach || {
    echo -e "${YELLOW}⚠ Service might already exist. Continuing...${NC}"
}

echo ""
echo -e "${YELLOW}Setting environment variables for Frontend...${NC}"

# Set environment variables
railway variables --set "VITE_API_URL=$BACKEND_URL"
railway variables --set "VITE_SUPABASE_URL=$SUPABASE_URL"
railway variables --set "VITE_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY"

echo ""
echo -e "${GREEN}✓ Frontend environment variables set${NC}"
echo ""

# Wait for deployment
echo -e "${YELLOW}Waiting for Frontend to build and deploy...${NC}"
echo "This may take 3-5 minutes (Vite build + deploy)..."
echo ""

sleep 45  # Frontend builds take longer

# Get the frontend URL
echo -e "${YELLOW}Getting Frontend URL...${NC}"
DOMAIN_OUTPUT=$(railway domain 2>&1 || echo "")

# Extract URL from Railway CLI output (handles different output formats)
FRONTEND_URL=$(echo "$DOMAIN_OUTPUT" | grep -oE 'https://[a-zA-Z0-9.-]+\.railway\.app' | head -1)

if [ -z "$FRONTEND_URL" ]; then
    echo -e "${YELLOW}⚠ Frontend URL not yet available${NC}"
    echo "Railway CLI output: $DOMAIN_OUTPUT"
    echo ""
    echo "Please get the Frontend URL from Railway dashboard:"
    echo "https://railway.app/project/$RAILWAY_PROJECT_NAME"
    echo ""
    read -p "Enter the Frontend URL: " FRONTEND_URL
fi

if [ -n "$FRONTEND_URL" ]; then
    # Ensure it has https://
    if [[ ! "$FRONTEND_URL" =~ ^https?:// ]]; then
        FRONTEND_URL="https://$FRONTEND_URL"
    fi
    echo -e "${GREEN}✓ Frontend URL: ${FRONTEND_URL}${NC}"
else
    echo -e "${RED}❌ Could not get frontend URL${NC}"
    exit 1
fi

# Update state with frontend URL
sed -i.bak "s|FRONTEND_URL=.*|FRONTEND_URL=\"$FRONTEND_URL\"|" "$STATE_FILE" 2>/dev/null || {
    echo "FRONTEND_URL=\"$FRONTEND_URL\"" >> "$STATE_FILE"
}

sed -i.bak "s|STEP_3_COMPLETED=.*|STEP_3_COMPLETED=true|" "$STATE_FILE"
rm -f "$STATE_FILE.bak"

# Also save to credentials file
sed -i.bak "s|FRONTEND_URL=.*|FRONTEND_URL=\"$FRONTEND_URL\"|" "$CREDENTIALS_FILE" 2>/dev/null || {
    echo "FRONTEND_URL=\"$FRONTEND_URL\"" >> "$CREDENTIALS_FILE"
}
rm -f "$CREDENTIALS_FILE.bak"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Frontend Deployment Complete                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "Test the frontend:"
echo "  ${BLUE}open $FRONTEND_URL${NC}"
echo ""
echo "⚠ IMPORTANT: The backend CORS needs to be updated with this URL"
echo ""
echo "Next step:"
echo "  ${BLUE}./scripts/deploy/4-finalize-deployment.sh${NC}"
echo ""
