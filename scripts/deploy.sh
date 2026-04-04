#!/bin/bash
# KT-BOT Deployment Script - One-click deployment
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  KT-BOT Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Check if .env file exists
echo -e "\n${YELLOW}[2/8] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env from template${NC}"
        echo -e "${YELLOW}Please review and update .env file with your credentials${NC}"
        read -p "Press enter to continue after updating .env..."
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi

# Create necessary directories
echo -e "\n${YELLOW}[3/8] Creating directories...${NC}"
mkdir -p data logs config nginx/ssl
echo -e "${GREEN}✓ Directories created${NC}"

# Build Docker image
echo -e "\n${YELLOW}[4/8] Building Docker image...${NC}"
docker build -t kt-bot:latest .
echo -e "${GREEN}✓ Docker image built${NC}"

# Pull dependent images
echo -e "\n${YELLOW}[5/8] Pulling dependent images...${NC}"
docker-compose pull ollama postgres redis
echo -e "${GREEN}✓ Images pulled${NC}"

# Stop existing containers
echo -e "\n${YELLOW}[6/8] Stopping existing containers...${NC}"
docker-compose down || true
echo -e "${GREEN}✓ Stopped${NC}"

# Start services
echo -e "\n${YELLOW}[7/8] Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "\n${YELLOW}[8/8] Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "\n${YELLOW}Checking service health...${NC}"
for i in {1..30}; do
    if curl -sf http://localhost:7860/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is healthy!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Display service status
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "Services:"
echo -e "  ${GREEN}✓${NC} FastAPI:    http://localhost:7860"
echo -e "  ${GREEN}✓${NC} Gradio UI:  http://localhost:7861"
echo -e "  ${GREEN}✓${NC} API Docs:   http://localhost:7860/docs"
echo -e ""
echo -e "Management commands:"
echo -e "  View logs:      docker-compose logs -f"
echo -e "  Stop services:  ./scripts/stop.sh"
echo -e "  Restart:        docker-compose restart"
echo -e "  Status:         docker-compose ps"
echo -e ""
echo -e "${YELLOW}Note: First startup may take a few minutes to download models${NC}"
