#!/bin/bash
# KT-BOT Backup Script - Backup data and database
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ktbot_backup_${TIMESTAMP}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  KT-BOT Backup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo -e "${YELLOW}[1/4] Creating backup directory...${NC}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "${BACKUP_PATH}"
echo -e "${GREEN}✓ Created: ${BACKUP_PATH}${NC}"

# Backup PostgreSQL database
echo -e "\n${YELLOW}[2/4] Backing up PostgreSQL database...${NC}"
docker exec ktbot-postgres pg_dump -U ktbot ktbot > "${BACKUP_PATH}/database.sql"
echo -e "${GREEN}✓ Database backed up${NC}"

# Backup data directory
echo -e "\n${YELLOW}[3/4] Backing up data directory...${NC}"
cp -r ./data "${BACKUP_PATH}/"
echo -e "${GREEN}✓ Data directory backed up${NC}"

# Backup configuration
echo -e "\n${YELLOW}[4/4] Backing up configuration...${NC}"
cp .env "${BACKUP_PATH}/.env" 2>/dev/null || true
cp -r ./config "${BACKUP_PATH}/" 2>/dev/null || true
echo -e "${GREEN}✓ Configuration backed up${NC}"

# Create archive
echo -e "\n${YELLOW}Creating compressed archive...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"
cd - > /dev/null

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "Backup file: ${GREEN}${BACKUP_DIR}/${BACKUP_NAME}.tar.gz${NC}"
echo -e "Size: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)"
echo -e ""
echo -e "To restore: ./scripts/restore.sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
