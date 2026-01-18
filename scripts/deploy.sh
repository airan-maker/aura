#!/bin/bash

# Aura Production Deployment Script
# This script automates the production deployment process

set -e  # Exit on error

echo "==================================="
echo "Aura Production Deployment"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your environment variables"
    exit 1
fi

# Validate critical environment variables
echo "Validating environment variables..."
source .env

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY not set in .env${NC}"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo -e "${RED}Error: SECRET_KEY not set in .env${NC}"
    exit 1
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}Error: POSTGRES_PASSWORD not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables validated${NC}"
echo ""

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

# Backup database if it exists
echo "Checking for existing database..."
if docker ps -a | grep -q aura-db; then
    echo -e "${YELLOW}Creating database backup...${NC}"
    ./scripts/backup-db.sh
    echo -e "${GREEN}✓ Database backup completed${NC}"
    echo ""
fi

# Pull latest code (if using git)
if [ -d .git ]; then
    echo "Pulling latest code from repository..."
    git pull origin main || git pull origin master
    echo -e "${GREEN}✓ Code updated${NC}"
    echo ""
fi

# Build and start services
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo ""
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Run database migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
echo -e "${GREEN}✓ Database migrations completed${NC}"
echo ""

# Health check
echo "Performing health check..."
sleep 5

# Check backend health
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)
if [ "$BACKEND_HEALTH" -eq 200 ]; then
    echo -e "${GREEN}✓ Backend is healthy (HTTP $BACKEND_HEALTH)${NC}"
else
    echo -e "${RED}✗ Backend health check failed (HTTP $BACKEND_HEALTH)${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

# Check frontend
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_HEALTH" -eq 200 ]; then
    echo -e "${GREEN}✓ Frontend is accessible (HTTP $FRONTEND_HEALTH)${NC}"
else
    echo -e "${YELLOW}⚠ Frontend returned HTTP $FRONTEND_HEALTH (may be normal during build)${NC}"
fi

# Check nginx
NGINX_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
if [ "$NGINX_HEALTH" -eq 200 ] || [ "$NGINX_HEALTH" -eq 301 ] || [ "$NGINX_HEALTH" -eq 302 ]; then
    echo -e "${GREEN}✓ Nginx is running (HTTP $NGINX_HEALTH)${NC}"
else
    echo -e "${YELLOW}⚠ Nginx returned HTTP $NGINX_HEALTH${NC}"
fi

echo ""
echo "==================================="
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "==================================="
echo ""
echo "Services status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Nginx: http://localhost"
echo ""
