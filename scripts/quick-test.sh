#!/bin/bash

# Quick test script for development

echo "Aura Quick Test"
echo "==============="
echo ""

# Test Backend health
echo "Testing Backend..."
if curl -s http://localhost:8000/api/v1/health | grep -q "ok"; then
    echo "✓ Backend is healthy"
else
    echo "✗ Backend is not responding"
    exit 1
fi

# Test Frontend
echo "Testing Frontend..."
if curl -s http://localhost:3000 | grep -q "Aura"; then
    echo "✓ Frontend is accessible"
else
    echo "✗ Frontend is not responding"
    exit 1
fi

# Quick analysis test
echo ""
echo "Running quick analysis test..."
echo "URL: https://example.com"

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analysis \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}')

REQUEST_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$REQUEST_ID" ]; then
    echo "✓ Analysis created: $REQUEST_ID"
    echo ""
    echo "Monitor progress at:"
    echo "  http://localhost:3000/analysis/$REQUEST_ID"
    echo ""
    echo "Or check API:"
    echo "  curl http://localhost:8000/api/v1/analysis/$REQUEST_ID"
else
    echo "✗ Failed to create analysis"
    exit 1
fi

echo ""
echo "All quick tests passed! ✓"
