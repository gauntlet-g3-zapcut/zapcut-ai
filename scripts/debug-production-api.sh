#!/bin/bash

# Debug Production API Script

BACKEND_URL="https://backend-adcraft-production.up.railway.app"

echo "======================================"
echo "Production API Diagnostics"
echo "======================================"
echo ""

echo "1. Testing Backend Health..."
curl -s "$BACKEND_URL/health" | jq . || curl -s "$BACKEND_URL/health"
echo ""
echo ""

echo "2. Testing Root Endpoint..."
curl -s "$BACKEND_URL/" | jq . || curl -s "$BACKEND_URL/"
echo ""
echo ""

echo "3. Testing CORS Info..."
curl -s "$BACKEND_URL/cors-info" | jq . || curl -s "$BACKEND_URL/cors-info"
echo ""
echo ""

echo "4. Testing API with Sample Data..."
echo "Creating test brand..."
curl -X POST "$BACKEND_URL/api/brands" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "name": "Test Brand",
    "industry": "Technology"
  }' \
  -v
echo ""
echo ""

echo "======================================"
echo "Check Railway Backend Logs:"
echo "  cd backend && railway logs"
echo "======================================"
