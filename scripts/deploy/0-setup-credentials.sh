#!/bin/bash

# Adcraft Railway Deployment - Step 0: Setup Credentials
# This script collects all credentials needed for deployment

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
echo -e "${BLUE}║  Adcraft Railway Deployment - Credentials Setup           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI is not installed${NC}"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Or using Homebrew:"
    echo "  brew install railway"
    exit 1
fi

echo -e "${GREEN}✓ Railway CLI is installed${NC}"
echo ""

# Check if user is logged in to Railway
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠ You are not logged in to Railway${NC}"
    echo ""
    echo "Please login to Railway:"
    railway login
    echo ""
fi

RAILWAY_USER=$(railway whoami 2>/dev/null || echo "unknown")
echo -e "${GREEN}✓ Logged in as: ${RAILWAY_USER}${NC}"
echo ""

# Check if credentials file already exists
if [ -f "$CREDENTIALS_FILE" ]; then
    echo -e "${YELLOW}⚠ Credentials file already exists: $CREDENTIALS_FILE${NC}"
    read -p "Do you want to overwrite it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Using existing credentials file${NC}"
        exit 0
    fi
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Collecting Credentials                                     ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "This information will be saved to: $CREDENTIALS_FILE"
echo "This file is gitignored and will NOT be committed."
echo ""

# Function to read credential
read_credential() {
    local var_name=$1
    local prompt=$2
    local default=$3
    local value

    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value=${value:-$default}
    else
        read -p "$prompt: " value
    fi

    echo "$value"
}

# Function to read secret (hidden input)
read_secret() {
    local var_name=$1
    local prompt=$2
    local value

    read -s -p "$prompt: " value
    echo  # New line after hidden input
    echo "$value"
}

# Collect Railway Project Name
echo -e "${YELLOW}Railway Configuration${NC}"
RAILWAY_PROJECT_NAME=$(read_credential "RAILWAY_PROJECT_NAME" "Railway project name" "adcraft-production")

echo ""
echo -e "${YELLOW}Supabase Configuration${NC}"
echo "Get these from: https://app.supabase.com → Your Project → Settings → API"
SUPABASE_URL=$(read_credential "SUPABASE_URL" "Supabase URL (e.g., https://xxx.supabase.co)")
SUPABASE_ANON_KEY=$(read_secret "SUPABASE_ANON_KEY" "Supabase Anon Key")
SUPABASE_SERVICE_ROLE_KEY=$(read_secret "SUPABASE_SERVICE_ROLE_KEY" "Supabase Service Role Key")

echo ""
echo "Get database password from: Settings → Database"
SUPABASE_DB_PASSWORD=$(read_secret "SUPABASE_DB_PASSWORD" "Supabase DB Password")

echo ""
read -p "Do you want to set DATABASE_URL directly? (y/n, recommended: n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    DATABASE_URL=$(read_credential "DATABASE_URL" "PostgreSQL DATABASE_URL")
else
    DATABASE_URL=""
fi

echo ""
echo -e "${YELLOW}API Keys${NC}"
echo "Get OpenAI key from: https://platform.openai.com → API Keys"
OPENAI_API_KEY=$(read_secret "OPENAI_API_KEY" "OpenAI API Key")

echo ""
echo "Get Replicate token from: https://replicate.com → API Tokens"
REPLICATE_API_TOKEN=$(read_secret "REPLICATE_API_TOKEN" "Replicate API Token")

echo ""
echo -e "${YELLOW}Optional: Custom Domains${NC}"
CUSTOM_BACKEND_DOMAIN=$(read_credential "CUSTOM_BACKEND_DOMAIN" "Custom backend domain (optional, e.g., api.adcraft.com)" "")
CUSTOM_FRONTEND_DOMAIN=$(read_credential "CUSTOM_FRONTEND_DOMAIN" "Custom frontend domain (optional, e.g., app.adcraft.com)" "")

# Write credentials to file
echo ""
echo -e "${BLUE}Writing credentials to $CREDENTIALS_FILE...${NC}"

cat > "$CREDENTIALS_FILE" << EOF
# Adcraft Railway Deployment Credentials
# Generated: $(date)
# DO NOT COMMIT THIS FILE TO GIT

# Railway Configuration
RAILWAY_PROJECT_NAME="$RAILWAY_PROJECT_NAME"

# Supabase Configuration
SUPABASE_URL="$SUPABASE_URL"
SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY"
SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
SUPABASE_DB_PASSWORD="$SUPABASE_DB_PASSWORD"
DATABASE_URL="$DATABASE_URL"

# API Keys
OPENAI_API_KEY="$OPENAI_API_KEY"
REPLICATE_API_TOKEN="$REPLICATE_API_TOKEN"

# Custom Domains (optional)
CUSTOM_BACKEND_DOMAIN="$CUSTOM_BACKEND_DOMAIN"
CUSTOM_FRONTEND_DOMAIN="$CUSTOM_FRONTEND_DOMAIN"

# Deployment State (will be updated by deployment scripts)
REDIS_SERVICE_ID=""
BACKEND_SERVICE_ID=""
WORKER_SERVICE_ID=""
FRONTEND_SERVICE_ID=""
BACKEND_URL=""
FRONTEND_URL=""
EOF

chmod 600 "$CREDENTIALS_FILE"  # Restrict permissions

echo -e "${GREEN}✓ Credentials saved successfully${NC}"
echo ""

# Validate credentials
echo -e "${BLUE}Validating credentials...${NC}"
VALIDATION_ERRORS=0

if [[ ! "$SUPABASE_URL" =~ ^https?:// ]]; then
    echo -e "${RED}❌ SUPABASE_URL should start with https://${NC}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo -e "${RED}❌ SUPABASE_ANON_KEY is required${NC}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo -e "${RED}❌ SUPABASE_SERVICE_ROLE_KEY is required${NC}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$SUPABASE_DB_PASSWORD" ]; then
    echo -e "${RED}❌ SUPABASE_DB_PASSWORD is required${NC}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY is required${NC}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$REPLICATE_API_TOKEN" ]; then
    echo -e "${RED}❌ REPLICATE_API_TOKEN is required${NC}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ $VALIDATION_ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ $VALIDATION_ERRORS validation error(s) found${NC}"
    echo "Please edit $CREDENTIALS_FILE and fix the errors"
    exit 1
fi

echo -e "${GREEN}✓ All credentials validated${NC}"
echo ""

# Create state file
cat > "$STATE_FILE" << EOF
# Deployment state
STEP_0_COMPLETED=true
STEP_1_COMPLETED=false
STEP_2_COMPLETED=false
STEP_3_COMPLETED=false
STEP_4_COMPLETED=false
EOF

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Credentials Setup Complete                             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next step: Run the deployment script"
echo ""
echo "  ${BLUE}./scripts/deploy/deploy.sh${NC}"
echo ""
echo "Or run each step manually:"
echo "  ${BLUE}./scripts/deploy/1-deploy-infrastructure.sh${NC}"
echo ""
