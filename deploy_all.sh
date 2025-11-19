#!/bin/bash
# Deploy both Frontend and Backend

set -e

echo "🚀 Deploying Zapcut Frontend and Backend"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"
BACKEND_DIR="${SCRIPT_DIR}/backend"

# Deploy Frontend
echo "📦 Deploying Frontend..."
cd "${FRONTEND_DIR}"
npm run deploy

echo ""
echo "✅ Frontend deployed successfully!"
echo ""

# Deploy Backend API
echo "📦 Deploying Backend API (zapcut-api)..."
cd "${BACKEND_DIR}"

# Check if fly CLI is available
if ! command -v fly &> /dev/null; then
    echo "❌ Error: fly CLI not found. Please install it first:"
    echo "   https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

fly deploy --config fly.api.toml -a zapcut-api

echo ""
echo "✅ Backend API deployed successfully!"
echo ""

echo "🎉 Deployment complete!"
echo ""
echo "Frontend: Deployed to Cloudflare Pages"
echo "Backend API: https://zapcut-api.fly.dev"
echo ""
echo "View API logs: fly logs -a zapcut-api"

