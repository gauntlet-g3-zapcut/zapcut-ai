#!/bin/bash
# Deploy Frontend, Backend API, and Backend Worker

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

# Deploy Backend (API and Worker) using backend deploy script
echo "📦 Deploying Backend (API and Worker)..."
cd "${BACKEND_DIR}"
bash deploy-both.sh

echo ""
echo "🎉 All deployments complete!"
echo ""
echo "Frontend: Deployed to Cloudflare Pages"
echo "Backend API: https://zapcut-api.fly.dev"
echo "Backend Worker: zapcut-worker"

