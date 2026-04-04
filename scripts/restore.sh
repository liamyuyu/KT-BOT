#!/bin/bash
# KT-BOT Restore Script - Restore from backup
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  KT-BOT Restore Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check argument
if [ -z "$1" ]; then
    echo -e "${RED}Error: Backup file path required${NC}"
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

# Warning
echo -e "${YELLOW}WARNING: This will replace current data!${NC}"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Extract backup
echo -e "\n${YELLOW}[1/4] Extracting backup...${NC}"
TEMP_DIR=$(mktemp -d)
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
BACKUP_NAME=$(basename "${BACKUP_FILE}" .tar.gz)
BACKUP_PATH="${TEMP_DIR}/${BACKUP_NAME}"
echo -e "${GREEN}✓ Extracted to ${TEMP_DIR}${NC}"

# Stop services
echo -e "\n${YELLOW}[2/4] Stopping services...${NC}"
docker-compose stop
echo -e "${GREEN}✓ Services stopped${NC}"

# Restore database
echo -e "\n${YELLOW}[3/4] Restoring database...${NC}"
docker exec -i ktbot-postgres psql -U ktbot -d ktbot < "${BACKUP_PATH}/database.sql"
echo -e "${GREEN}✓ Database restored${NC}"

# Restore data
echo -e "\n${YELLOW}[4/4] Restoring data directory...${NC}"
rm -rf ./data
cp -r "${BACKUP_PATH}/data" ./data
echo -e "${GREEN}✓ Data restored${NC}"

# Restore configuration (optional)
if [ -f "${BACKUP_PATH}/.env" ]; then
    cp "${BACKUP_PATH}/.env" ./.env
    echo -e "${GREEN}✓ Configuration restored${NC}"
fi

# Cleanup
rm -rf "${TEMP_DIR}"

# Restart services
echo -e "\n${YELLOW}Restarting services...${NC}"
docker-compose start

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Restore Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "Services restarted. Check logs:"
echo -e "  docker-compose logs -f"
