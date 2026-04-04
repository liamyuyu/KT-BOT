#!/bin/bash
# ==============================================================================
# KT-BOT Deployment Script
# ==============================================================================
# Automates the deployment process for KT-BOT application
#
# Usage:
#   ./scripts/deployment/deploy.sh [environment]
#
# Arguments:
#   environment - deployment environment: dev, staging, prod (default: dev)
#
# Example:
#   ./scripts/deployment/deploy.sh prod
# ==============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV="${1:-dev}"
COMPOSE_FILE="docker-compose.yml"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    local env_file=".env"
    if [ "$ENV" = "prod" ]; then
        env_file=".env.prod"
        COMPOSE_FILE="docker-compose.prod.yml"
    elif [ "$ENV" = "staging" ]; then
        env_file=".env.staging"
    fi
    
    if [ ! -f "$PROJECT_ROOT/$env_file" ]; then
        log_error "Environment file $env_file not found"
        log_info "Copy .env.example to $env_file and configure it"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

backup_before_deploy() {
    log_info "Creating backup before deployment..."
    
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        bash "$SCRIPT_DIR/backup.sh" "pre-deploy-$(date +%Y%m%d-%H%M%S)"
    else
        log_warn "Backup script not found, skipping backup"
    fi
}

pull_latest_code() {
    log_info "Pulling latest code..."
    cd "$PROJECT_ROOT"
    
    if [ -d ".git" ]; then
        git pull origin main || log_warn "Failed to pull latest code"
    else
        log_warn "Not a git repository, skipping git pull"
    fi
}

build_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$COMPOSE_FILE" build --pull --no-cache
}

stop_services() {
    log_info "Stopping existing services..."
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$COMPOSE_FILE" down || true
}

start_services() {
    log_info "Starting services..."
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$COMPOSE_FILE" up -d
}

wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
            log_info "Services are healthy!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Services not ready yet..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "Services failed to become healthy"
    return 1
}

run_migrations() {
    log_info "Running database migrations..."
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$COMPOSE_FILE" exec -T app python scripts/migrate.py || log_warn "Migration script not found or failed"
}

show_status() {
    log_info "Deployment status:"
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$COMPOSE_FILE" ps
}

show_logs() {
    log_info "Recent logs:"
    cd "$PROJECT_ROOT"
    
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
}

# Main deployment flow
main() {
    log_info "Starting deployment for environment: $ENV"
    log_info "Using compose file: $COMPOSE_FILE"
    
    # Pre-deployment
    check_prerequisites
    
    if [ "$ENV" = "prod" ]; then
        log_warn "Deploying to PRODUCTION"
        read -p "Are you sure? (yes/no): " -r
        if [ "$REPLY" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
        backup_before_deploy
    fi
    
    # Deployment
    pull_latest_code
    build_images
    stop_services
    start_services
    
    # Post-deployment
    if wait_for_health; then
        run_migrations
        show_status
        log_info "Deployment completed successfully!"
        
        log_info "Application URLs:"
        log_info "  - API: http://localhost:7860/api/v1/health"
        log_info "  - UI: http://localhost:7861"
        
        if [ "$ENV" = "prod" ]; then
            log_info "  - Production: https://ktbot.example.com"
        fi
    else
        log_error "Deployment failed - services are not healthy"
        show_logs
        exit 1
    fi
}

# Run main function
main

