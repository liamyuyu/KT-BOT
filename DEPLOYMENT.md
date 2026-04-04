# KT-BOT Deployment Guide

Complete guide for deploying KT-BOT in production and development environments using Docker.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [Development Deployment](#development-deployment)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## 🎯 Prerequisites

### Required

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **System**: Linux (recommended), macOS, or Windows with WSL2
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Disk**: Minimum 10GB free space
- **Network**: Internet connection for pulling images and models

### Recommended

- **CPU**: 4+ cores
- **GPU**: NVIDIA GPU for faster LLM inference (optional)
- **Domain**: Domain name for production deployment
- **SSL Certificate**: For HTTPS in production

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/KT-BOT.git
cd KT-BOT
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or vim/code .env
```

### 3. Deploy

```bash
# Run one-click deployment script
./scripts/deploy.sh
```

### 4. Access Application

- **Gradio UI**: http://localhost:7861
- **FastAPI Docs**: http://localhost:7860/docs
- **Health Check**: http://localhost:7860/api/v1/health

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file with your configuration:

#### Application Settings

```env
ENVIRONMENT=production
DEBUG=false
APP_VERSION=0.3.0
```

#### Database Configuration

```env
DATABASE_URL=postgresql://ktbot:ktbot_password@postgres:5432/ktbot
DB_POOL_SIZE=10
```

#### Ollama Configuration

```env
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_DEFAULT_MODEL=qwen2.5:latest
OLLAMA_EMBEDDING_MODEL=bge-large-zh:latest
```

#### Redis Configuration

```env
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL=1800
```

See `.env.example` for complete configuration options.

---

## 🏭 Production Deployment

### Step 1: Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: SSL Certificate

#### Option A: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
```

#### Option B: Self-Signed (Testing)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

### Step 3: Deploy with Nginx

```bash
# Deploy with nginx reverse proxy
docker-compose --profile production up -d

# Check status
docker-compose ps
```

### Step 4: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Step 5: Setup Auto-Restart

```bash
# Create systemd service
sudo tee /etc/systemd/system/ktbot.service << 'EOF'
[Unit]
Description=KT-BOT Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/KT-BOT
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable ktbot
sudo systemctl start ktbot
```

---

## 💻 Development Deployment

### Local Development

```bash
# Start without nginx
docker-compose up -d

# View logs
docker-compose logs -f app

# Access shell
docker exec -it ktbot-app bash
```

### Hot Reload Development

```bash
# Mount source code as volume for hot reload
docker-compose -f docker-compose.dev.yml up
```

### Running Tests

```bash
# Run tests in container
docker exec ktbot-app pytest tests/

# Run with coverage
docker exec ktbot-app pytest --cov=src tests/
```

---

## 🔧 Maintenance

### Backup Data

```bash
# Create backup
./scripts/backup.sh

# Backups saved to ./backups/ktbot_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Restore Data

```bash
# Restore from backup
./scripts/restore.sh ./backups/ktbot_backup_20260202_120000.tar.gz
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker exec ktbot-app alembic upgrade head
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app
```

### Monitor Resources

```bash
# Resource usage
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## 🔍 Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs app

# Verify configuration
docker-compose config

# Restart services
docker-compose restart
```

### Database Connection Error

```bash
# Check PostgreSQL status
docker exec ktbot-postgres pg_isready -U ktbot

# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

### Ollama Model Issues

```bash
# List available models
docker exec ktbot-ollama ollama list

# Pull required models
docker exec ktbot-ollama ollama pull qwen2.5:latest
docker exec ktbot-ollama ollama pull bge-large-zh:latest

# Check Ollama logs
docker-compose logs ollama
```

### Port Conflicts

```bash
# Check port usage
sudo lsof -i :7860
sudo lsof -i :7861

# Kill process
sudo kill -9 <PID>

# Change ports in docker-compose.yml
```

### Container Health Check Failing

```bash
# Check health status
docker inspect ktbot-app | grep -A 10 Health

# Manual health check
curl http://localhost:7860/api/v1/health

# Restart unhealthy container
docker-compose restart app
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Edit /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  }
}

# Restart Docker
sudo systemctl restart docker
```

---

## 🎓 Advanced Topics

### Horizontal Scaling

```bash
# Scale application instances
docker-compose up -d --scale app=3

# Use load balancer (nginx, traefik, etc.)
```

### Custom Network Configuration

```yaml
# docker-compose.override.yml
networks:
  ktbot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/16
```

### GPU Support for Ollama

```yaml
# docker-compose.yml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### External Database

```env
# .env
DATABASE_URL=postgresql://user:pass@external-db.example.com:5432/ktbot
```

### Monitoring with Prometheus

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          ssh user@server "cd /app && git pull && ./scripts/deploy.sh"
```

---

## 📊 Performance Tuning

### Database Optimization

```sql
-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '16MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Optimization

```bash
# docker-compose.yml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Application Workers

```env
# .env
WORKERS=4  # Adjust based on CPU cores
```

---

## 🛡️ Security Best Practices

1. **Change Default Passwords**: Update all passwords in `.env`
2. **Use Strong Secrets**: Generate random values for SECRET_KEY
3. **Enable Firewall**: Only expose necessary ports
4. **Regular Updates**: Keep Docker and images up-to-date
5. **SSL/TLS**: Always use HTTPS in production
6. **Backup Regularly**: Automate daily backups
7. **Monitor Logs**: Check for suspicious activity
8. **Limit Access**: Use IP whitelisting if possible

---

## 📞 Support

- **Documentation**: Check README.md and inline comments
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join our discussion forum

---

## 📝 License

Copyright © 2026 KT-BOT Team. All rights reserved.

---

**Last Updated**: 2026-02-02
**Version**: 0.3.0
