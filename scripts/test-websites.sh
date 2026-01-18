#!/bin/bash

# Script to test Aura with multiple real websites

echo "================================"
echo "Aura Website Testing Script"
echo "================================"
echo ""

# Test websites
WEBSITES=(
    "https://example.com"
    "https://www.ietf.org"
    "https://www.w3.org"
    "https://developer.mozilla.org"
    "https://github.com"
)

# Function to test a website
test_website() {
    URL=$1
    echo "Testing: $URL"

    # Create analysis
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analysis \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$URL\"}")

    REQUEST_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

    if [ -z "$REQUEST_ID" ]; then
        echo "  ✗ Failed to create analysis"
        return 1
    fi

    echo "  Request ID: $REQUEST_ID"
    echo "  Waiting for completion..."

    # Poll for completion
    TIMEOUT=180
    ELAPSED=0
    STATUS="pending"

    while [ $ELAPSED -lt $TIMEOUT ] && [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/analysis/$REQUEST_ID)
        STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        PROGRESS=$(echo $STATUS_RESPONSE | grep -o '"progress":[0-9]*' | cut -d':' -f2)
        printf "\r  Progress: %d%% (%s)" $PROGRESS $STATUS
    done

    echo ""

    if [ "$STATUS" = "completed" ]; then
        # Get results
        RESULTS=$(curl -s http://localhost:8000/api/v1/analysis/$REQUEST_ID/results)
        SEO_SCORE=$(echo $RESULTS | grep -o '"seo_score":[0-9.]*' | cut -d':' -f2)
        AEO_SCORE=$(echo $RESULTS | grep -o '"aeo_score":[0-9.]*' | cut -d':' -f2)
        DURATION=$(echo $RESULTS | grep -o '"analysis_duration":[0-9.]*' | cut -d':' -f2)

        echo "  ✓ Completed"
        echo "  SEO Score: $SEO_SCORE"
        echo "  AEO Score: $AEO_SCORE"
        echo "  Duration: ${DURATION}s"
        echo ""
        return 0
    else
        ERROR=$(echo $STATUS_RESPONSE | grep -o '"error_message":"[^"]*"' | cut -d'"' -f4)
        echo "  ✗ Failed: $ERROR"
        echo ""
        return 1
    fi
}

# Test each website
PASSED=0
FAILED=0

for WEBSITE in "${WEBSITES[@]}"; do
    if test_website "$WEBSITE"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

# Summary
echo "================================"
echo "Summary"
echo "================================"
echo "Total: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "All websites tested successfully! ✓"
    exit 0
else
    echo "Some tests failed."
    exit 1
fi
