#!/bin/bash
# ==============================================================================
# KT-BOT Restore Script
# ==============================================================================
# Restores database, Redis, ChromaDB, and uploaded files from a backup
#
# Usage:
#   ./scripts/deployment/restore.sh <backup_name>
#
# Arguments:
#   backup_name - name of the backup to restore (e.g., 20240209-143000)
#
# Example:
#   ./scripts/deployment/restore.sh 20240209-143000
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
BACKUP_NAME="${1:-}"

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

check_backup() {
    if [ -z "$BACKUP_NAME" ]; then
        log_error "Backup name is required"
        echo "Usage: $0 <backup_name>"
        echo ""
        echo "Available backups:"
        ls -1 "$BACKUP_DIR" 2>/dev/null || echo "  No backups found"
        exit 1
    fi
    
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        log_error "Backup not found: $BACKUP_PATH"
        exit 1
    fi
    
    log_info "Backup found: $BACKUP_PATH"
}

show_backup_info() {
    log_info "Backup information:"
    
    if [ -f "$BACKUP_PATH/manifest.json" ]; then
        cat "$BACKUP_PATH/manifest.json" | jq '.'
    else
        log_warn "Manifest file not found"
        ls -lh "$BACKUP_PATH"
    fi
}

confirm_restore() {
    log_warn "WARNING: This will overwrite existing data!"
    read -p "Are you sure you want to restore from backup '$BACKUP_NAME'? (yes/no): " -r
    
    if [ "$REPLY" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
}

restore_postgres() {
    log_info "Restoring PostgreSQL database..."
    
    if [ ! -f "$BACKUP_PATH/postgres.sql.gz" ]; then
        log_warn "PostgreSQL backup file not found, skipping"
        return 0
    fi
    
    # Drop and recreate database
    docker-compose exec -T postgres psql -U ktbot -d postgres -c "DROP DATABASE IF EXISTS ktbot;"
    docker-compose exec -T postgres psql -U ktbot -d postgres -c "CREATE DATABASE ktbot;"
    
    # Restore from backup
    gunzip < "$BACKUP_PATH/postgres.sql.gz" | docker-compose exec -T postgres psql -U ktbot -d ktbot
    
    log_info "PostgreSQL restore completed"
}

restore_redis() {
    log_info "Restoring Redis..."
    
    if [ ! -f "$BACKUP_PATH/redis-dump.rdb" ]; then
        log_warn "Redis backup file not found, skipping"
        return 0
    fi
    
    # Stop Redis
    docker-compose stop redis
    
    # Copy dump file
    docker cp "$BACKUP_PATH/redis-dump.rdb" ktbot-redis:/data/dump.rdb
    
    # Start Redis
    docker-compose start redis
    
    log_info "Redis restore completed"
}

restore_chroma() {
    log_info "Restoring ChromaDB..."
    
    if [ ! -f "$BACKUP_PATH/chroma_db.tar.gz" ]; then
        log_warn "ChromaDB backup file not found, skipping"
        return 0
    fi
    
    # Remove existing ChromaDB
    rm -rf "$PROJECT_ROOT/data/chroma_db"
    
    # Extract backup
    tar -xzf "$BACKUP_PATH/chroma_db.tar.gz" -C "$PROJECT_ROOT/data"
    
    log_info "ChromaDB restore completed"
}

restore_uploads() {
    log_info "Restoring uploaded files..."
    
    if [ ! -f "$BACKUP_PATH/uploads.tar.gz" ]; then
        log_warn "Uploads backup file not found, skipping"
        return 0
    fi
    
    # Remove existing uploads
    rm -rf "$PROJECT_ROOT/data/uploads"
    
    # Extract backup
    tar -xzf "$BACKUP_PATH/uploads.tar.gz" -C "$PROJECT_ROOT/data"
    
    log_info "Uploads restore completed"
}

restart_services() {
    log_info "Restarting services..."
    
    docker-compose restart
    
    sleep 5
}

verify_restore() {
    log_info "Verifying restore..."
    
    # Check if services are healthy
    if bash "$SCRIPT_DIR/health-check.sh"; then
        log_info "Health check passed"
    else
        log_warn "Health check failed - please verify manually"
    fi
}

# Main restore flow
main() {
    log_info "Starting restore from backup: $BACKUP_NAME"
    
    check_backup
    show_backup_info
    confirm_restore
    
    # Create backup of current state before restore
    log_info "Creating safety backup before restore..."
    bash "$SCRIPT_DIR/backup.sh" "before-restore-$(date +%Y%m%d-%H%M%S)" || log_warn "Safety backup failed"
    
    # Perform restore
    restore_postgres || log_warn "PostgreSQL restore failed"
    restore_redis || log_warn "Redis restore failed"
    restore_chroma || log_warn "ChromaDB restore failed"
    restore_uploads || log_warn "Uploads restore failed"
    
    # Restart and verify
    restart_services
    verify_restore
    
    log_info "Restore completed successfully!"
    log_info "Please verify the application is working correctly"
}

# Run main function
main

