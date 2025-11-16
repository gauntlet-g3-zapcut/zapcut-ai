#!/bin/bash

# Test script for deployed backend
# Tests basic endpoints and response structure

API_URL="https://zapcut-api.fly.dev"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Testing Deployed Backend API"
echo "================================"
echo ""

# Test 1: Health Check
echo "1️⃣  Testing Health Endpoint..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Health check returned 200"
    echo "   Response: $body"
else
    echo -e "${RED}❌ FAIL${NC} - Health check returned $http_code"
    echo "   Response: $body"
fi
echo ""

# Test 2: Root Endpoint
echo "2️⃣  Testing Root Endpoint..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Root endpoint returned 200"
    echo "   Response: $body"
else
    echo -e "${RED}❌ FAIL${NC} - Root endpoint returned $http_code"
    echo "   Response: $body"
fi
echo ""

# Test 3: CORS Info
echo "3️⃣  Testing CORS Info Endpoint..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/cors-info")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} - CORS info returned 200"
    echo "   Response: $body" | jq -r '.cors_origins | length' | xargs -I {} echo "   Found {} CORS origins"
else
    echo -e "${RED}❌ FAIL${NC} - CORS info returned $http_code"
    echo "   Response: $body"
fi
echo ""

# Test 4: Protected Endpoint (should require auth)
echo "4️⃣  Testing Protected Endpoint (Campaigns List)..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/api/campaigns/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "403" ] || [ "$http_code" == "401" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Protected endpoint correctly requires authentication ($http_code)"
    echo "   Response: $body"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} - Expected 401/403, got $http_code"
    echo "   Response: $body"
fi
echo ""

# Test 5: Campaign Status Endpoint Structure (with invalid ID)
echo "5️⃣  Testing Campaign Status Endpoint (Invalid ID)..."
response=$(curl -s -w "\n%{http_code}" "$API_URL/api/campaigns/invalid-id/status")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "400" ] || [ "$http_code" == "403" ] || [ "$http_code" == "401" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Status endpoint validates input ($http_code)"
    echo "   Response: $body"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} - Unexpected status code: $http_code"
    echo "   Response: $body"
fi
echo ""

# Test 6: Check API Response Times
echo "6️⃣  Testing API Response Times..."
times=()
for i in {1..5}; do
    time=$(curl -s -o /dev/null -w "%{time_total}" "$API_URL/health")
    times+=($time)
done

avg_time=$(echo "${times[@]}" | awk '{sum=0; for(i=1;i<=NF;i++) sum+=$i; print sum/NF}')
echo -e "${GREEN}✅ Response Time Test${NC}"
echo "   Average response time: ${avg_time}s"
echo "   Individual times: ${times[@]}"
echo ""

echo "================================"
echo -e "${GREEN}✅ Basic API Tests Complete${NC}"
echo ""
echo "📝 Note: Full video generation testing requires:"
echo "   - Valid Supabase JWT token"
echo "   - Existing campaign ID"
echo "   - REPLICATE_API_TOKEN configured"
echo ""
echo "🔗 API URL: $API_URL"
echo "📊 Monitor: https://fly.io/apps/zapcut-api/monitoring"

