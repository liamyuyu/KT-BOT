#!/bin/bash
# ==============================================================================
# KT-BOT Backup Script
# ==============================================================================
# Creates backups of database, Redis, ChromaDB, and uploaded files
#
# Usage:
#   ./scripts/deployment/backup.sh [backup_name]
#
# Arguments:
#   backup_name - optional custom backup name (default: timestamp)
#
# Example:
#   ./scripts/deployment/backup.sh before-upgrade
# ==============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
BACKUP_NAME="${1:-$(date +%Y%m%d-%H%M%S)}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

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

create_backup_dir() {
    log_info "Creating backup directory: $BACKUP_PATH"
    mkdir -p "$BACKUP_PATH"
}

backup_postgres() {
    log_info "Backing up PostgreSQL database..."
    
    docker-compose exec -T postgres pg_dump -U ktbot ktbot | gzip > "$BACKUP_PATH/postgres.sql.gz"
    
    if [ -f "$BACKUP_PATH/postgres.sql.gz" ]; then
        log_info "PostgreSQL backup completed: $(du -h "$BACKUP_PATH/postgres.sql.gz" | cut -f1)"
    else
        log_error "PostgreSQL backup failed"
        return 1
    fi
}

backup_redis() {
    log_info "Backing up Redis..."
    
    # Trigger Redis save
    docker-compose exec -T redis redis-cli BGSAVE
    sleep 2
    
    # Copy dump file
    docker cp ktbot-redis:/data/dump.rdb "$BACKUP_PATH/redis-dump.rdb" 2>/dev/null || {
        log_warn "Redis backup file not found, skipping"
        return 0
    }
    
    if [ -f "$BACKUP_PATH/redis-dump.rdb" ]; then
        log_info "Redis backup completed: $(du -h "$BACKUP_PATH/redis-dump.rdb" | cut -f1)"
    fi
}

backup_chroma() {
    log_info "Backing up ChromaDB..."
    
    if [ -d "$PROJECT_ROOT/data/chroma_db" ]; then
        tar -czf "$BACKUP_PATH/chroma_db.tar.gz" -C "$PROJECT_ROOT/data" chroma_db
        log_info "ChromaDB backup completed: $(du -h "$BACKUP_PATH/chroma_db.tar.gz" | cut -f1)"
    else
        log_warn "ChromaDB directory not found, skipping"
    fi
}

backup_uploads() {
    log_info "Backing up uploaded files..."
    
    if [ -d "$PROJECT_ROOT/data/uploads" ]; then
        tar -czf "$BACKUP_PATH/uploads.tar.gz" -C "$PROJECT_ROOT/data" uploads
        log_info "Uploads backup completed: $(du -h "$BACKUP_PATH/uploads.tar.gz" | cut -f1)"
    else
        log_warn "Uploads directory not found, skipping"
    fi
}

backup_config() {
    log_info "Backing up configuration files..."
    
    # Backup .env (without sensitive data)
    if [ -f "$PROJECT_ROOT/.env" ]; then
        grep -v -E "PASSWORD|TOKEN|SECRET|KEY" "$PROJECT_ROOT/.env" > "$BACKUP_PATH/env.example" || true
    fi
    
    # Backup config directory
    if [ -d "$PROJECT_ROOT/config" ]; then
        tar -czf "$BACKUP_PATH/config.tar.gz" -C "$PROJECT_ROOT" config
        log_info "Config backup completed"
    fi
}

create_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "$BACKUP_PATH/manifest.json" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hostname": "$(hostname)",
  "git_commit": "$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'N/A')",
  "app_version": "$(grep APP_VERSION "$PROJECT_ROOT/.env" | cut -d= -f2 || echo 'N/A')",
  "files": $(find "$BACKUP_PATH" -type f -exec du -b {} \; | awk '{print $2}' | jq -R -s -c 'split("\n")[:-1]')
}
EOF
    
    log_info "Manifest created"
}

cleanup_old_backups() {
    log_info "Cleaning up old backups (keeping last 30 days)..."
    
    find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Main backup flow
main() {
    log_info "Starting backup: $BACKUP_NAME"
    
    create_backup_dir
    
    # Perform backups
    backup_postgres || log_warn "PostgreSQL backup failed"
    backup_redis || log_warn "Redis backup failed"
    backup_chroma || log_warn "ChromaDB backup failed"
    backup_uploads || log_warn "Uploads backup failed"
    backup_config
    
    # Create manifest and cleanup
    create_manifest
    cleanup_old_backups
    
    # Calculate total backup size
    TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    
    log_info "Backup completed successfully!"
    log_info "Backup location: $BACKUP_PATH"
    log_info "Total size: $TOTAL_SIZE"
    
    # List backup contents
    echo ""
    log_info "Backup contents:"
    ls -lh "$BACKUP_PATH"
}

# Run main function
main

