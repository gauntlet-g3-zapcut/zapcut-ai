#!/bin/bash
# Comprehensive endpoint testing script

echo "=========================================="
echo "Comprehensive Backend API Tests"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected=$3
    local description=$4
    
    echo -n "Testing $method $endpoint ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if echo "$body" | grep -q "$expected"; then
        echo "✅ PASSED (HTTP $http_code)"
        ((PASSED++))
        return 0
    else
        echo "❌ FAILED (HTTP $http_code)"
        echo "   Expected: $expected"
        echo "   Got: $body"
        ((FAILED++))
        return 1
    fi
}

test_json_endpoint() {
    local method=$1
    local endpoint=$2
    local json_key=$3
    local description=$4
    
    echo -n "Testing $method $endpoint ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if echo "$body" | python3 -m json.tool > /dev/null 2>&1 && echo "$body" | grep -q "$json_key"; then
        echo "✅ PASSED (HTTP $http_code)"
        echo "   Response: $(echo "$body" | python3 -m json.tool 2>/dev/null | head -5)"
        ((PASSED++))
        return 0
    else
        echo "❌ FAILED (HTTP $http_code)"
        echo "   Response: $body"
        ((FAILED++))
        return 1
    fi
}

# Test 1: Root endpoint
test_endpoint "GET" "/" "AdCraft API" "Root endpoint"

# Test 2: Health endpoint
test_endpoint "GET" "/health" "healthy" "Health check"

# Test 3: CORS info endpoint (JSON)
test_json_endpoint "GET" "/cors-info" "cors_origins" "CORS info endpoint"

# Test 4: Auth verify (should fail without token - expected)
echo -n "Testing POST /api/auth/verify (no token) ... "
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/auth/verify" \
    -H "Content-Type: application/json")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "403" ] || [ "$http_code" = "401" ]; then
    echo "✅ PASSED (HTTP $http_code - expected auth failure)"
    ((PASSED++))
else
    echo "❌ FAILED (HTTP $http_code - unexpected response)"
    ((FAILED++))
fi

# Test 5: Auth me (should fail without token - expected)
echo -n "Testing GET /api/auth/me (no token) ... "
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/auth/me")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "403" ] || [ "$http_code" = "401" ]; then
    echo "✅ PASSED (HTTP $http_code - expected auth failure)"
    ((PASSED++))
else
    echo "❌ FAILED (HTTP $http_code - unexpected response)"
    ((FAILED++))
fi

# Test 6: Brands endpoint (should fail without token - expected)
echo -n "Testing GET /api/brands (no token) ... "
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/brands")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "403" ] || [ "$http_code" = "401" ]; then
    echo "✅ PASSED (HTTP $http_code - expected auth failure)"
    ((PASSED++))
else
    echo "❌ FAILED (HTTP $http_code - unexpected response)"
    ((FAILED++))
fi

# Test 7: Campaigns endpoint (should fail without token - expected)
echo -n "Testing GET /api/campaigns (no token) ... "
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/campaigns")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "404" ] || [ "$http_code" = "403" ] || [ "$http_code" = "401" ]; then
    echo "✅ PASSED (HTTP $http_code - expected auth/not found)"
    ((PASSED++))
else
    echo "❌ FAILED (HTTP $http_code - unexpected response)"
    ((FAILED++))
fi

# Test 8: Invalid endpoint (should return 404)
echo -n "Testing GET /invalid-endpoint (404 expected) ... "
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/invalid-endpoint")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "404" ]; then
    echo "✅ PASSED (HTTP $http_code - expected 404)"
    ((PASSED++))
else
    echo "❌ FAILED (HTTP $http_code - expected 404)"
    ((FAILED++))
fi

# Test 9: OPTIONS request (CORS preflight)
echo -n "Testing OPTIONS / (CORS preflight) ... "
response=$(curl -s -w "\n%{http_code}" -X OPTIONS "$BASE_URL/" \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: GET")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
    echo "✅ PASSED (HTTP $http_code - CORS preflight OK)"
    ((PASSED++))
else
    echo "❌ FAILED (HTTP $http_code - CORS preflight failed)"
    ((FAILED++))
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed"
    exit 1
fi

