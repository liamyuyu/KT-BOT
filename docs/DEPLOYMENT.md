# KT-BOT Deployment Guide

Complete guide for deploying KT-BOT in development, staging, and production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Backup & Restore](#backup--restore)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## Prerequisites

### System Requirements

**Minimum (Development)**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Linux (Ubuntu 20.04+), macOS 10.15+

**Recommended (Production)**:
- CPU: 8 cores
- RAM: 16 GB
- Disk: 200 GB SSD
- OS: Linux (Ubuntu 22.04 LTS)

### Software Requirements

- Docker: 20.10+ ([Install Guide](https://docs.docker.com/engine/install/))
- Docker Compose: 2.0+ ([Install Guide](https://docs.docker.com/compose/install/))
- Git: 2.30+
- curl: 7.68+
- jq: 1.6+ (optional, for JSON processing)

### Network Requirements

- Outbound HTTPS (443) for:
  - Jira/Confluence API access
  - Ollama model downloads
  - Docker image pulls
- Inbound ports:
  - 80/443: HTTP/HTTPS (production)
  - 7860: FastAPI backend
  - 7861: Gradio UI

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/KT-BOT.git
cd KT-BOT
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum required settings**:
```env
# Application
SECRET_KEY=your-generated-secret-key  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Database
POSTGRES_PASSWORD=change-this-password

# Redis
REDIS_PASSWORD=change-this-password

# Jira (if using)
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-token

# Confluence (if using)
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-token
```

### 3. Start Services

```bash
# Using deployment script (recommended)
./scripts/deployment/deploy.sh dev

# Or using docker-compose directly
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Run health check
./scripts/deployment/health-check.sh --verbose

# Or check manually
curl http://localhost:7860/api/v1/health
```

### 5. Access Application

- **API**: http://localhost:7860
- **UI**: http://localhost:7861
- **API Docs**: http://localhost:7860/docs

---

## Development Deployment

### Using Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Development Configuration

```env
# .env for development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DEV_MODE=true
DEV_RELOAD=true  # Auto-reload on code changes
```

### Local Development (Without Docker)

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start external services
docker-compose up -d postgres redis ollama

# Run application
python src/main.py
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Server meets minimum requirements
- [ ] SSL certificates obtained
- [ ] Domain DNS configured
- [ ] Firewall rules configured
- [ ] Backup strategy in place
- [ ] Monitoring tools ready
- [ ] Security hardening completed

### Production Deployment Steps

#### 1. Prepare Environment

```bash
# Create production environment file
cp .env.example .env.prod

# Edit with production values
nano .env.prod
```

**Critical production settings**:
```env
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=generate-strong-secret-key-here

# Database
POSTGRES_PASSWORD=strong-random-password
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_PASSWORD=strong-random-password
REDIS_MAX_MEMORY=1gb

# Security
ENABLE_SECURITY_HEADERS=true
FORCE_HTTPS=true
CORS_ORIGINS=https://ktbot.yourcompany.com

# Performance
WORKERS=4
CONTAINER_MEMORY_LIMIT=4g
CONTAINER_CPU_LIMIT=4.0
```

#### 2. Configure SSL Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone \
  -d ktbot.example.com \
  -d www.ktbot.example.com \
  --email admin@example.com \
  --agree-tos

# Copy to nginx directory
sudo cp /etc/letsencrypt/live/ktbot.example.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/ktbot.example.com/privkey.pem nginx/ssl/
```

**Option B: Self-Signed (Development Only)**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=ktbot.example.com"
```

#### 3. Update Nginx Configuration

Edit `nginx/nginx.conf`:
- Replace `ktbot.example.com` with your domain
- Adjust rate limits if needed
- Review security headers

#### 4. Deploy

```bash
# Using deployment script (recommended)
./scripts/deployment/deploy.sh prod

# Or using docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

#### 5. Verify Production Deployment

```bash
# Run comprehensive health check
./scripts/deployment/health-check.sh --verbose

# Test HTTPS
curl https://ktbot.example.com/health

# Test API
curl https://ktbot.example.com/api/v1/health

# SSL Test
https://www.ssllabs.com/ssltest/analyze.html?d=ktbot.example.com
```

### Production Optimization

#### Database Optimization

```sql
-- Connect to PostgreSQL
docker-compose exec postgres psql -U ktbot

-- Create indices for better performance
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX idx_sync_logs_status ON sync_logs(status);

-- Analyze tables
ANALYZE documents;
ANALYZE chat_history;
```

#### Redis Optimization

```bash
# Monitor Redis memory
docker-compose exec redis redis-cli INFO memory

# Check key distribution
docker-compose exec redis redis-cli --scan --pattern '*' | wc -l
```

---

## Configuration

### Environment Variables

See [.env.example](.env.example) for complete list of configuration options.

**Key Configuration Sections**:

1. **Application Settings**: Basic app configuration
2. **Ollama Configuration**: LLM model settings
3. **Jira/Confluence**: Data source integration
4. **Database**: PostgreSQL connection and pooling
5. **Redis**: Cache configuration
6. **RAG**: Retrieval and generation settings
7. **Security**: Authentication and HTTPS settings
8. **Performance**: Worker and resource limits

### Docker Compose Profiles

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Start without nginx
docker-compose up -d app postgres redis ollama
```

### Resource Limits

Adjust in `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4g
    reservations:
      cpus: '2.0'
      memory: 2g
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Automated health check
./scripts/deployment/health-check.sh

# Manual checks
docker-compose ps
docker-compose logs -f app
curl http://localhost:7860/api/v1/health
```

### Monitoring Stack (Optional)

Start Prometheus and Grafana:

```bash
docker-compose --profile monitoring up -d
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Log Management

```bash
# View logs
docker-compose logs -f app

# Export logs
docker-compose logs --no-color > logs.txt

# Log rotation is configured automatically
# See docker-compose.yml logging section
```

### Maintenance Tasks

```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up old images
docker system prune -a

# Vacuum PostgreSQL
docker-compose exec postgres vacuumdb -U ktbot -d ktbot -fz

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB
```

---

## Backup & Restore

### Automated Backups

```bash
# Create backup
./scripts/deployment/backup.sh

# Create backup with custom name
./scripts/deployment/backup.sh "before-upgrade"

# Backups are stored in ./backups/ directory
```

### Backup Schedule (Cron)

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /path/to/KT-BOT && ./scripts/deployment/backup.sh
```

### Restore from Backup

```bash
# List available backups
ls -lh backups/

# Restore specific backup
./scripts/deployment/restore.sh 20240209-143000
```

### Manual Backup

```bash
# PostgreSQL
docker-compose exec postgres pg_dump -U ktbot ktbot > backup.sql

# Redis
docker-compose exec redis redis-cli BGSAVE
docker cp ktbot-redis:/data/dump.rdb ./redis-backup.rdb

# ChromaDB
tar -czf chroma-backup.tar.gz data/chroma_db

# Uploads
tar -czf uploads-backup.tar.gz data/uploads
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs app

# Common causes:
# - Missing .env file
# - Invalid environment variables
# - Port already in use
# - Insufficient resources

# Solution:
docker-compose down
docker-compose up -d
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U ktbot

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. Ollama Models Not Loading

```bash
# Check Ollama service
docker-compose logs ollama

# Pull models manually
docker-compose exec ollama ollama pull qwen2.5:7b
docker-compose exec ollama ollama pull bge-large-zh
```

#### 4. High Memory Usage

```bash
# Check container stats
docker stats

# Adjust limits in docker-compose.yml
# Restart affected services
docker-compose restart app
```

#### 5. SSL Certificate Issues

```bash
# Verify certificate files
ls -lh nginx/ssl/

# Test nginx configuration
docker-compose exec nginx nginx -t

# Renew Let's Encrypt certificate
sudo certbot renew
docker-compose restart nginx
```

### Debug Mode

Enable debug logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
SQL_ECHO=true
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Monitor PostgreSQL
docker-compose exec postgres psql -U ktbot -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis
docker-compose exec redis redis-cli INFO stats

# Profile application (development only)
ENABLE_PROFILING=true python src/main.py
```

---

## Security Best Practices

### 1. Environment Variables

- **Never** commit `.env` files to version control
- Use strong random passwords (min 32 characters)
- Rotate secrets regularly
- Use different passwords for each service

### 2. Network Security

```bash
# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Use private Docker network
# Already configured in docker-compose.yml
```

### 3. SSL/TLS

- Use Let's Encrypt for free SSL certificates
- Enable HSTS (configured in nginx.conf)
- Use TLS 1.2+ only
- Regular certificate renewal

### 4. Container Security

- Run containers as non-root user (already configured)
- Use official base images
- Regular security updates:
  ```bash
  docker-compose pull
  docker-compose up -d
  ```

### 5. Application Security

- Enable rate limiting (configured in nginx.conf)
- Use strong SECRET_KEY
- Enable CORS only for trusted origins
- Regular security audits

### 6. Database Security

- Use strong passwords
- Enable SSL connections
- Regular backups
- Limit network exposure

### 7. Monitoring

- Enable security logs
- Monitor failed login attempts
- Set up alerts for suspicious activity
- Regular security audits

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Security](https://redis.io/topics/security)
- [Nginx Security](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/KT-BOT/issues
- Documentation: https://github.com/yourusername/KT-BOT/wiki
- Email: support@ktbot.com

---

**Last Updated**: 2026-02-09
**Version**: 0.3.0
