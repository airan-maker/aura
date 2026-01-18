#!/bin/bash

# Aura System Test Script
# This script runs comprehensive tests on the entire Aura system

set -e

echo "================================"
echo "Aura System Test Suite"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# 1. Check Docker services
echo "1. Checking Docker services..."
docker-compose ps | grep -q "Up" && print_result 0 "Docker services running" || print_result 1 "Docker services not running"
echo ""

# 2. Check Backend health
echo "2. Checking Backend health..."
curl -s http://localhost:8000/api/v1/health | grep -q "ok" && print_result 0 "Backend health check" || print_result 1 "Backend health check"
echo ""

# 3. Check Frontend accessibility
echo "3. Checking Frontend accessibility..."
curl -s http://localhost:3000 | grep -q "Aura" && print_result 0 "Frontend accessibility" || print_result 1 "Frontend accessibility"
echo ""

# 4. Check Database connection
echo "4. Checking Database..."
docker-compose exec -T backend python -c "from app.database import engine; import asyncio; asyncio.run(engine.dispose())" && print_result 0 "Database connection" || print_result 1 "Database connection"
echo ""

# 5. Run Backend unit tests
echo "5. Running Backend unit tests..."
docker-compose exec -T backend pytest tests/ -v --tb=short 2>&1 | tee /tmp/backend-test-output.txt
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_result 0 "Backend unit tests"
else
    print_result 1 "Backend unit tests"
fi
echo ""

# 6. Test API endpoint - Create analysis
echo "6. Testing API - Create analysis..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analysis \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}')

REQUEST_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$REQUEST_ID" ]; then
    print_result 0 "Create analysis API"
    echo "Request ID: $REQUEST_ID"
else
    print_result 1 "Create analysis API"
fi
echo ""

# 7. Test API endpoint - Get status
echo "7. Testing API - Get status..."
if [ -n "$REQUEST_ID" ]; then
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/analysis/$REQUEST_ID)
    echo $STATUS_RESPONSE | grep -q '"url":"https://example.com"' && print_result 0 "Get status API" || print_result 1 "Get status API"
else
    print_result 1 "Get status API (no request ID)"
fi
echo ""

# 8. Wait for analysis to complete
if [ -n "$REQUEST_ID" ]; then
    echo "8. Waiting for analysis to complete (max 2 minutes)..."
    TIMEOUT=120
    ELAPSED=0
    STATUS="pending"

    while [ $ELAPSED -lt $TIMEOUT ] && [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/analysis/$REQUEST_ID)
        STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        PROGRESS=$(echo $STATUS_RESPONSE | grep -o '"progress":[0-9]*' | cut -d':' -f2)
        echo "Status: $STATUS, Progress: $PROGRESS%"
    done

    if [ "$STATUS" = "completed" ]; then
        print_result 0 "Analysis completion"
    else
        print_result 1 "Analysis completion (status: $STATUS)"
    fi
fi
echo ""

# 9. Test API endpoint - Get results
if [ -n "$REQUEST_ID" ] && [ "$STATUS" = "completed" ]; then
    echo "9. Testing API - Get results..."
    RESULTS=$(curl -s http://localhost:8000/api/v1/analysis/$REQUEST_ID/results)
    echo $RESULTS | grep -q '"seo_score"' && echo $RESULTS | grep -q '"aeo_score"' && print_result 0 "Get results API" || print_result 1 "Get results API"

    # Display scores
    SEO_SCORE=$(echo $RESULTS | grep -o '"seo_score":[0-9.]*' | cut -d':' -f2)
    AEO_SCORE=$(echo $RESULTS | grep -o '"aeo_score":[0-9.]*' | cut -d':' -f2)
    echo "SEO Score: $SEO_SCORE"
    echo "AEO Score: $AEO_SCORE"
else
    echo "9. Skipping Get results test (analysis not completed)"
    print_result 1 "Get results API (analysis not completed)"
fi
echo ""

# 10. Run Frontend E2E tests (optional - requires Playwright setup)
if command -v npm &> /dev/null; then
    echo "10. Running Frontend E2E tests..."
    cd frontend
    if [ -d "node_modules/@playwright/test" ]; then
        npm test 2>&1 | tee /tmp/frontend-test-output.txt
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_result 0 "Frontend E2E tests"
        else
            print_result 1 "Frontend E2E tests"
        fi
    else
        echo "Playwright not installed. Skipping E2E tests."
        echo "Run: cd frontend && npm install && npx playwright install"
    fi
    cd ..
else
    echo "10. Skipping Frontend tests (npm not found)"
fi
echo ""

# Summary
echo "================================"
echo "Test Summary"
echo "================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
