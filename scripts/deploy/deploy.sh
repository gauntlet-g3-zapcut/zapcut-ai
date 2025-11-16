#!/bin/bash

# Adcraft Railway Deployment - Master Script
# Orchestrates all deployment steps

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_FILE="$PROJECT_ROOT/.railway.state"

clear

echo -e "${CYAN}${BOLD}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     █████╗ ██████╗  ██████╗██████╗  █████╗ ███████╗████████╗║
║    ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝║
║    ███████║██║  ██║██║     ██████╔╝███████║█████╗     ██║   ║
║    ██╔══██║██║  ██║██║     ██╔══██╗██╔══██║██╔══╝     ██║   ║
║    ██║  ██║██████╔╝╚██████╗██║  ██║██║  ██║██║        ██║   ║
║    ╚═╝  ╚═╝╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝   ║
║                                                              ║
║            Railway Deployment Automation Script             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${BLUE}This script will deploy Adcraft to Railway in 4 steps:${NC}"
echo ""
echo "  1️⃣  Setup credentials and configuration"
echo "  2️⃣  Deploy infrastructure (Railway project + Redis)"
echo "  3️⃣  Deploy backend services (API + Celery Worker)"
echo "  4️⃣  Deploy frontend (React/Vite app)"
echo "  5️⃣  Finalize (CORS, migrations, verification)"
echo ""
echo -e "${YELLOW}Prerequisites:${NC}"
echo "  ✓ Railway CLI installed (npm install -g @railway/cli)"
echo "  ✓ Logged into Railway (railway login)"
echo "  ✓ GitHub repository connected to Railway"
echo "  ✓ Supabase project credentials ready"
echo "  ✓ OpenAI and Replicate API keys ready"
echo ""
echo -e "${CYAN}Estimated time: 20-30 minutes${NC}"
echo ""

read -p "Ready to start? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""

# Check if we're resuming from a previous run
if [ -f "$STATE_FILE" ]; then
    source "$STATE_FILE"

    echo -e "${YELLOW}Found previous deployment state:${NC}"
    echo ""
    echo "  Step 0 (Credentials): $([ "$STEP_0_COMPLETED" = "true" ] && echo "✓ Done" || echo "⏸ Pending")"
    echo "  Step 1 (Infrastructure): $([ "$STEP_1_COMPLETED" = "true" ] && echo "✓ Done" || echo "⏸ Pending")"
    echo "  Step 2 (Backend): $([ "$STEP_2_COMPLETED" = "true" ] && echo "✓ Done" || echo "⏸ Pending")"
    echo "  Step 3 (Frontend): $([ "$STEP_3_COMPLETED" = "true" ] && echo "✓ Done" || echo "⏸ Pending")"
    echo "  Step 4 (Finalize): $([ "$STEP_4_COMPLETED" = "true" ] && echo "✓ Done" || echo "⏸ Pending")"
    echo ""

    if [ "$STEP_4_COMPLETED" = "true" ]; then
        echo -e "${GREEN}Deployment already completed!${NC}"
        echo ""
        echo "To redeploy, delete: $STATE_FILE"
        exit 0
    fi

    read -p "Resume from last completed step? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting fresh deployment..."
        rm -f "$STATE_FILE"
    fi
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Beginning Deployment Process${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 0: Setup Credentials
if [ "$STEP_0_COMPLETED" != "true" ]; then
    echo -e "${BOLD}${BLUE}[Step 0/4] Setting up credentials...${NC}"
    echo ""
    bash "$SCRIPT_DIR/0-setup-credentials.sh"
    echo ""
    read -p "Press Enter to continue to Step 1..."
    echo ""
else
    echo -e "${GREEN}✓ Step 0: Credentials already set up${NC}"
    echo ""
fi

# Step 1: Deploy Infrastructure
if [ "$STEP_1_COMPLETED" != "true" ]; then
    echo -e "${BOLD}${BLUE}[Step 1/4] Deploying infrastructure...${NC}"
    echo ""
    bash "$SCRIPT_DIR/1-deploy-infrastructure.sh"
    echo ""
    read -p "Press Enter to continue to Step 2..."
    echo ""
else
    echo -e "${GREEN}✓ Step 1: Infrastructure already deployed${NC}"
    echo ""
fi

# Step 2: Deploy Backend
if [ "$STEP_2_COMPLETED" != "true" ]; then
    echo -e "${BOLD}${BLUE}[Step 2/4] Deploying backend services...${NC}"
    echo ""
    bash "$SCRIPT_DIR/2-deploy-backend.sh"
    echo ""
    read -p "Press Enter to continue to Step 3..."
    echo ""
else
    echo -e "${GREEN}✓ Step 2: Backend already deployed${NC}"
    echo ""
fi

# Step 3: Deploy Frontend
if [ "$STEP_3_COMPLETED" != "true" ]; then
    echo -e "${BOLD}${BLUE}[Step 3/4] Deploying frontend...${NC}"
    echo ""
    bash "$SCRIPT_DIR/3-deploy-frontend.sh"
    echo ""
    read -p "Press Enter to continue to Step 4 (finalization)..."
    echo ""
else
    echo -e "${GREEN}✓ Step 3: Frontend already deployed${NC}"
    echo ""
fi

# Step 4: Finalize Deployment
if [ "$STEP_4_COMPLETED" != "true" ]; then
    echo -e "${BOLD}${BLUE}[Step 4/4] Finalizing deployment...${NC}"
    echo ""
    bash "$SCRIPT_DIR/4-finalize-deployment.sh"
    echo ""
else
    echo -e "${GREEN}✓ Step 4: Deployment already finalized${NC}"
    echo ""
fi

# Final summary
clear

echo -e "${GREEN}${BOLD}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                   ✓ DEPLOYMENT COMPLETE!                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Load final state
source "$STATE_FILE"
source "$PROJECT_ROOT/.railway.env"

echo ""
echo -e "${CYAN}Your Adcraft application is now live on Railway!${NC}"
echo ""
echo -e "${BOLD}Production URLs:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 Frontend:  ${BLUE}$FRONTEND_URL${NC}"
echo "  🔧 Backend:   ${BLUE}$BACKEND_URL${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BOLD}Quick Links:${NC}"
echo ""
echo "  📊 Railway Dashboard:"
echo "     ${BLUE}https://railway.app/project/$RAILWAY_PROJECT_NAME${NC}"
echo ""
echo "  📖 View Logs:"
echo "     Backend:  ${BLUE}cd backend && railway logs${NC}"
echo "     Frontend: ${BLUE}cd frontend && railway logs${NC}"
echo ""
echo "  🔄 Redeploy:"
echo "     ${BLUE}railway up${NC} (in backend/ or frontend/ directory)"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo "  1. Test your application: ${BLUE}open $FRONTEND_URL${NC}"
echo "  2. Monitor logs for any issues"
echo "  3. Set up custom domains (optional)"
echo "  4. Configure monitoring and alerts"
echo "  5. Test video generation end-to-end"
echo ""
echo -e "${YELLOW}Important Files Created:${NC}"
echo "  • .railway.env (credentials - gitignored)"
echo "  • .railway.state (deployment state)"
echo "  • .railway-worker-vars.txt (worker env vars)"
echo ""
echo -e "${GREEN}Thank you for using Adcraft Railway Deployment!${NC}"
echo ""
