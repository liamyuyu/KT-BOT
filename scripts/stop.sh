#!/bin/bash
# KT-BOT Stop Script - Graceful shutdown
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping KT-BOT services...${NC}"

# Graceful shutdown
docker-compose stop

echo -e "${GREEN}✓ Services stopped${NC}"

# Option to remove containers
read -p "Remove containers? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down
    echo -e "${GREEN}✓ Containers removed${NC}"
fi

# Option to remove volumes
read -p "Remove data volumes? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}WARNING: This will delete all data!${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        echo -e "${GREEN}✓ Volumes removed${NC}"
    fi
fi

echo -e "${GREEN}Shutdown complete${NC}"
