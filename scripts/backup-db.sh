#!/bin/bash

# Aura Database Backup Script
# Creates timestamped PostgreSQL database backups

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="aura_backup_${TIMESTAMP}.sql"
COMPOSE_FILE="docker-compose.prod.yml"

# Check if running in production mode
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${YELLOW}Production compose file not found, using development mode${NC}"
    COMPOSE_FILE="docker-compose.yml"
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "==================================="
echo "Aura Database Backup"
echo "==================================="
echo ""

# Check if database container is running
if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "db"; then
    echo -e "${RED}Error: Database container is not running${NC}"
    exit 1
fi

# Get database credentials from environment
source .env 2>/dev/null || true

DB_USER="${POSTGRES_USER:-aura}"
DB_NAME="${POSTGRES_DB:-aura}"
DB_PASSWORD="${POSTGRES_PASSWORD:-aura_password}"

echo "Creating backup: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Create backup using pg_dump
docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_DIR/$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Check backup file size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)

echo ""
echo -e "${GREEN}✓ Backup completed successfully${NC}"
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"
echo "Size: $BACKUP_SIZE"
echo ""

# List recent backups
echo "Recent backups:"
ls -lht "$BACKUP_DIR" | head -6

echo ""
echo "To restore from this backup:"
echo "  gunzip < $BACKUP_DIR/$BACKUP_FILE | docker-compose -f $COMPOSE_FILE exec -T db psql -U $DB_USER $DB_NAME"
echo ""

# Optional: Keep only last 10 backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/aura_backup_*.sql.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo -e "${YELLOW}Cleaning up old backups (keeping last 10)...${NC}"
    ls -t "$BACKUP_DIR"/aura_backup_*.sql.gz | tail -n +11 | xargs rm -f
    echo -e "${GREEN}✓ Cleanup completed${NC}"
fi

echo ""
