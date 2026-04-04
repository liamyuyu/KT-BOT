#!/bin/bash
# ==============================================================================
# KT-BOT Health Check Script
# ==============================================================================
# Verifies all services are running and healthy
#
# Usage:
#   ./scripts/deployment/health-check.sh [--verbose]
#
# Exit codes:
#   0 - All services healthy
#   1 - One or more services unhealthy
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
VERBOSE="${1:-}"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

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

check_pass() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    echo -e "${RED}✗${NC} $1"
}

check_docker() {
    log_info "Checking Docker..."
    
    if command -v docker &> /dev/null; then
        check_pass "Docker is installed"
    else
        check_fail "Docker is not installed"
        return 1
    fi
    
    if docker ps &> /dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not accessible"
        return 1
    fi
}

check_container_status() {
    log_info "Checking container status..."
    
    local containers=("ktbot-app" "ktbot-postgres" "ktbot-redis" "ktbot-ollama")
    
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local status=$(docker inspect -f '{{.State.Status}}' "$container")
            if [ "$status" = "running" ]; then
                check_pass "Container $container is running"
            else
                check_fail "Container $container is $status"
            fi
        else
            check_fail "Container $container is not found"
        fi
    done
}

check_container_health() {
    log_info "Checking container health..."
    
    local containers=("ktbot-app" "ktbot-postgres" "ktbot-redis")
    
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local health=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck")
            
            if [ "$health" = "healthy" ]; then
                check_pass "Container $container is healthy"
            elif [ "$health" = "no healthcheck" ]; then
                check_pass "Container $container has no healthcheck"
            else
                check_fail "Container $container health: $health"
            fi
        fi
    done
}

check_api_health() {
    log_info "Checking API health endpoint..."
    
    local url="http://localhost:7860/api/v1/health"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        check_pass "API health endpoint responding (HTTP $response)"
        
        if [ "$VERBOSE" = "--verbose" ]; then
            local health_data=$(curl -s "$url" 2>/dev/null || echo "{}")
            echo "$health_data" | jq '.' 2>/dev/null || echo "$health_data"
        fi
    else
        check_fail "API health endpoint not responding (HTTP $response)"
    fi
}

check_gradio() {
    log_info "Checking Gradio UI..."
    
    local url="http://localhost:7861"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        check_pass "Gradio UI is accessible (HTTP $response)"
    else
        check_fail "Gradio UI not accessible (HTTP $response)"
    fi
}

check_postgres() {
    log_info "Checking PostgreSQL connection..."
    
    if docker exec ktbot-postgres pg_isready -U ktbot &> /dev/null; then
        check_pass "PostgreSQL is accepting connections"
    else
        check_fail "PostgreSQL is not accepting connections"
    fi
}

check_redis() {
    log_info "Checking Redis connection..."
    
    if docker exec ktbot-redis redis-cli ping | grep -q "PONG"; then
        check_pass "Redis is responding"
    else
        check_fail "Redis is not responding"
    fi
}

check_ollama() {
    log_info "Checking Ollama service..."
    
    local url="http://localhost:11434/api/tags"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        check_pass "Ollama service is responding"
        
        if [ "$VERBOSE" = "--verbose" ]; then
            local models=$(curl -s "$url" 2>/dev/null | jq '.models[].name' 2>/dev/null || echo "[]")
            log_info "Available models: $models"
        fi
    else
        check_fail "Ollama service not responding (HTTP $response)"
    fi
}

check_disk_space() {
    log_info "Checking disk space..."
    
    local usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt 90 ]; then
        check_pass "Disk space: ${usage}% used"
    elif [ "$usage" -lt 95 ]; then
        check_warn "Disk space: ${usage}% used (warning threshold)"
    else
        check_fail "Disk space: ${usage}% used (critical)"
    fi
}

check_memory() {
    log_info "Checking memory usage..."
    
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
        
        if [ "$mem_usage" -lt 90 ]; then
            check_pass "Memory usage: ${mem_usage}%"
        else
            check_warn "Memory usage: ${mem_usage}% (high)"
        fi
    else
        check_pass "Memory check skipped (free command not available)"
    fi
}

show_summary() {
    echo ""
    echo "========================================"
    echo "Health Check Summary"
    echo "========================================"
    echo -e "Total checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo "========================================"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        log_info "All health checks passed!"
        return 0
    else
        log_error "$FAILED_CHECKS health check(s) failed"
        return 1
    fi
}

# Main health check flow
main() {
    echo "========================================"
    echo "KT-BOT Health Check"
    echo "========================================"
    echo "Timestamp: $(date)"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    # Run all checks
    check_docker || true
    check_container_status || true
    check_container_health || true
    check_postgres || true
    check_redis || true
    check_ollama || true
    check_api_health || true
    check_gradio || true
    check_disk_space || true
    check_memory || true
    
    # Show summary and exit with appropriate code
    if show_summary; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main

