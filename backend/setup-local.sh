#!/bin/bash

# Local Backend Setup Script
# Activates virtual environment, installs dependencies, and verifies database connection

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Local Backend Setup                                       ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if we're in backend directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Must be run from backend directory${NC}"
    echo "Run: cd backend && ./setup-local.sh"
    exit 1
fi

# Step 1: Activate virtual environment
echo -e "${YELLOW}Step 1: Activating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 3: Check .env file
echo -e "${YELLOW}Step 3: Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit backend/.env and add your credentials${NC}"
    echo ""
    exit 0
fi
echo -e "${GREEN}✓ .env file exists${NC}"
echo ""

# Step 4: Verify database connection
echo -e "${YELLOW}Step 4: Verifying database connection...${NC}"
python verify_supabase_connection.py
echo ""

# Step 5: Show next steps
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Local Setup Complete!                                   ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Virtual environment is activated.${NC}"
echo ""
echo -e "${BLUE}Start backend server:${NC}"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo -e "${BLUE}Test API:${NC}"
echo "  curl http://localhost:8000/health"
echo "  open http://localhost:8000/docs"
echo ""
echo -e "${BLUE}Run frontend (in another terminal):${NC}"
echo "  cd frontend && npm run dev"
echo ""
