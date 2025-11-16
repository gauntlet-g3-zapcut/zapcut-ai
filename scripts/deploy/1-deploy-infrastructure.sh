#!/bin/bash

# Adcraft Railway Deployment - Step 1: Deploy Infrastructure
# Creates Railway project and Redis service

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
echo -e "${BLUE}║  Step 1: Deploy Infrastructure                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if credentials file exists
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo -e "${RED}❌ Credentials file not found: $CREDENTIALS_FILE${NC}"
    echo ""
    echo "Please run the credentials setup first:"
    echo "  ./scripts/deploy/0-setup-credentials.sh"
    exit 1
fi

# Load credentials
source "$CREDENTIALS_FILE"
[ -f "$STATE_FILE" ] && source "$STATE_FILE"

echo -e "${GREEN}✓ Credentials loaded${NC}"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI is not installed${NC}"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Railway${NC}"
    echo "Please run: railway login"
    exit 1
fi

echo -e "${BLUE}Project Name: ${RAILWAY_PROJECT_NAME}${NC}"
echo ""

# Create new Railway project
echo -e "${YELLOW}Creating Railway project...${NC}"
echo ""
echo "You'll be prompted to create a new project in Railway."
echo "Project name: $RAILWAY_PROJECT_NAME"
echo ""
read -p "Press Enter to continue..."

# Initialize Railway project
railway init --name "$RAILWAY_PROJECT_NAME" || {
    echo -e "${YELLOW}⚠ Project might already exist. Trying to link...${NC}"
    railway link
}

echo -e "${GREEN}✓ Railway project initialized${NC}"
echo ""

# Add Redis service
echo -e "${YELLOW}Adding Redis service...${NC}"
echo ""
echo "Redis will be used as the message broker for Celery."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MANUAL STEP: Add Redis to Your Railway Project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The Railway CLI doesn't support adding databases programmatically."
echo "You need to add Redis manually via the Railway dashboard:"
echo ""
echo "1. Open your Railway project:"
echo "   ${BLUE}https://railway.app/project${NC}"
echo ""
echo "2. Click '${BLUE}+ New${NC}' button"
echo ""
echo "3. Select '${BLUE}Database${NC}'"
echo ""
echo "4. Choose '${BLUE}Redis${NC}'"
echo ""
echo "5. Railway will provision Redis (takes ~30 seconds)"
echo ""
echo "6. Once it shows '${GREEN}Active${NC}', you're done!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter once you've added Redis to your project..."
echo ""
echo -e "${GREEN}✓ Redis service ready${NC}"
echo ""

# Update state file
cat > "$STATE_FILE" << EOF
# Deployment state
STEP_0_COMPLETED=true
STEP_1_COMPLETED=true
STEP_2_COMPLETED=false
STEP_3_COMPLETED=false
STEP_4_COMPLETED=false
RAILWAY_PROJECT_NAME="$RAILWAY_PROJECT_NAME"
EOF

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Infrastructure Deployment Complete                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Railway project created: $RAILWAY_PROJECT_NAME"
echo "Redis service added and ready"
echo ""
echo "View your project: https://railway.app/project"
echo ""
echo "Next step:"
echo "  ${BLUE}./scripts/deploy/2-deploy-backend.sh${NC}"
echo ""
