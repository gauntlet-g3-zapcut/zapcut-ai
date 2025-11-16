#!/bin/bash
# Deploy both API and Worker apps to Fly.io

set -e

echo "🚀 Deploying Zapcut API and Worker to Fly.io"
echo ""

# Check if fly CLI is available
if ! command -v fly &> /dev/null; then
    echo "❌ Error: fly CLI not found. Please install it first:"
    echo "   https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Deploy API
echo "📦 Deploying API (zapcut-api)..."
fly deploy --config fly.api.toml -a zapcut-api

echo ""
echo "✅ API deployed successfully!"
echo ""

# Deploy Worker
echo "📦 Deploying Worker (zapcut-worker)..."
fly deploy --config fly.worker.toml -a zapcut-worker

echo ""
echo "✅ Worker deployed successfully!"
echo ""

# Show status
echo "📊 Checking deployment status..."
echo ""
echo "API Status:"
fly status -a zapcut-api

echo ""
echo "Worker Status:"
fly status -a zapcut-worker

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Test API health: curl https://zapcut-api.fly.dev/health"
echo "View logs: fly logs -a zapcut-api"

