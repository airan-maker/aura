#!/bin/bash

# Aura Production Health Check Script
# Monitors all production services and provides detailed status

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
NGINX_URL="http://localhost"
COMPOSE_FILE="docker-compose.prod.yml"

echo "==================================="
echo "Aura Production Health Check"
echo "==================================="
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local name=$2
    local expected_codes=${3:-"200"}

    echo -n "Checking $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if echo "$expected_codes" | grep -q "$response"; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local container=$1
    local name=$2

    echo -n "Checking $name container... "

    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "$container.*Up"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to check database connection
check_database() {
    echo -n "Checking database connection... "

    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U aura &>/dev/null; then
        echo -e "${GREEN}✓ Connected${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect${NC}"
        return 1
    fi
}

# Track overall health
HEALTH_STATUS=0

echo -e "${BLUE}[1/3] Docker Containers${NC}"
echo "-----------------------------------"
check_container "db" "PostgreSQL" || HEALTH_STATUS=1
check_container "backend" "Backend API" || HEALTH_STATUS=1
check_container "frontend" "Frontend" || HEALTH_STATUS=1
check_container "nginx" "Nginx" || HEALTH_STATUS=1
echo ""

echo -e "${BLUE}[2/3] Database${NC}"
echo "-----------------------------------"
check_database || HEALTH_STATUS=1

# Show database stats
if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U aura &>/dev/null; then
    echo -n "Database size: "
    DB_SIZE=$(docker-compose -f "$COMPOSE_FILE" exec -T db psql -U aura -d aura -t -c "SELECT pg_size_pretty(pg_database_size('aura'));" 2>/dev/null | xargs)
    echo "$DB_SIZE"

    echo -n "Active connections: "
    CONNECTIONS=$(docker-compose -f "$COMPOSE_FILE" exec -T db psql -U aura -d aura -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='aura';" 2>/dev/null | xargs)
    echo "$CONNECTIONS"
fi
echo ""

echo -e "${BLUE}[3/3] HTTP Endpoints${NC}"
echo "-----------------------------------"
check_http "$BACKEND_URL/api/v1/health" "Backend Health" "200" || HEALTH_STATUS=1
check_http "$FRONTEND_URL" "Frontend" "200 404" || HEALTH_STATUS=1
check_http "$NGINX_URL" "Nginx Proxy" "200 301 302" || HEALTH_STATUS=1
echo ""

# Test analysis API endpoint
echo -e "${BLUE}API Functionality Test${NC}"
echo "-----------------------------------"
echo -n "Testing analysis endpoint... "

TEST_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/analysis" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}' \
    -w "\n%{http_code}" 2>/dev/null || echo -e "\n000")

HTTP_CODE=$(echo "$TEST_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Working${NC} (HTTP $HTTP_CODE)"
else
    echo -e "${RED}✗ Failed${NC} (HTTP $HTTP_CODE)"
    HEALTH_STATUS=1
fi
echo ""

# Resource usage
echo -e "${BLUE}Resource Usage${NC}"
echo "-----------------------------------"
docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "Container CPU & Memory:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose -f "$COMPOSE_FILE" ps -q) 2>/dev/null || echo "Unable to get stats"
echo ""

# Disk usage
echo "Disk Usage:"
df -h . | tail -1
echo ""

# Recent logs check
echo -e "${BLUE}Recent Errors in Logs${NC}"
echo "-----------------------------------"
echo "Backend errors (last 5):"
docker-compose -f "$COMPOSE_FILE" logs --tail=100 backend 2>/dev/null | grep -i "error" | tail -5 || echo "No recent errors"
echo ""

# Overall status
echo "==================================="
if [ $HEALTH_STATUS -eq 0 ]; then
    echo -e "${GREEN}Overall Status: HEALTHY ✓${NC}"
else
    echo -e "${RED}Overall Status: UNHEALTHY ✗${NC}"
    echo ""
    echo "To view detailed logs:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f"
fi
echo "==================================="
echo ""

exit $HEALTH_STATUS
