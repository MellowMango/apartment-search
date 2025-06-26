# 🚀 Lynnapse Deployment Guide

## Overview

This guide covers deployment options for Lynnapse in various environments, from local development to production deployment with Docker containers.

## Quick Deployment (Recommended)

### One-Command Docker Deployment

```bash
# Clone and deploy
git clone https://github.com/yourusername/lynnapse-scraper.git
cd lynnapse-scraper
./deploy.sh
```

The deploy script will:
1. ✅ Check Docker availability
2. 🏗️ Build the Lynnapse container
3. 🚀 Start MongoDB + Lynnapse + Mongo Express
4. ⏳ Wait for services to be ready
5. 📋 Display usage instructions

**Services Started:**
- 🗄️ **MongoDB**: `localhost:27017`
- 🕸️ **Lynnapse**: Ready for CLI commands
- 👀 **Mongo Express**: `http://localhost:8081` (admin/admin)

## Deployment Options

### 1. Docker Compose (Production-Ready)

#### Full Stack Deployment
```bash
# Build and start services
docker-compose build
docker-compose up -d

# Verify services
docker-compose ps
```

#### Service Configuration
```yaml
# docker-compose.yml
services:
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
  
  lynnapse:
    build: .
    depends_on:
      - mongodb
    environment:
      - MONGODB_URL=mongodb://admin:password@mongodb:27017/lynnapse?authSource=admin
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
```

#### Environment Configuration
```bash
# Copy and configure environment
cp env.template .env

# Edit configuration
nano .env
```

#### Commands in Docker
```bash
# Test scraper
docker-compose exec lynnapse python -m lynnapse.cli test-scraper

# Scrape faculty data
docker-compose exec lynnapse python -m lynnapse.cli scrape-university arizona-psychology

# Access container shell
docker-compose exec lynnapse bash

# View logs
docker-compose logs -f lynnapse
```

### 2. Local Development

#### Prerequisites
- Python 3.11+
- Git
- Optional: MongoDB (local or cloud)

#### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/lynnapse-scraper.git
cd lynnapse-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov black isort

# Install Playwright browsers
playwright install chromium
```

#### Configuration
```bash
# Copy environment template
cp env.template .env

# Configure for local development
export MONGODB_URL="mongodb://localhost:27017/lynnapse"
export LOG_LEVEL="DEBUG"
```

#### Running Locally
```bash
# Test database connection (optional if using Docker MongoDB)
python -m lynnapse.cli test-db

# Test scraper
python -m lynnapse.cli test-scraper arizona-psychology

# Run full scrape
python -m lynnapse.cli scrape-university arizona-psychology --output local_faculty.json
```

### 3. Cloud Deployment

#### AWS ECS Deployment

##### 1. Build and Push to ECR
```bash
# Build image
docker build -t lynnapse:latest .

# Tag for ECR
docker tag lynnapse:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/lynnapse:latest

# Push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/lynnapse:latest
```

##### 2. ECS Task Definition
```json
{
  "family": "lynnapse",
  "cpu": "512",
  "memory": "1024",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "lynnapse",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/lynnapse:latest",
      "environment": [
        {
          "name": "MONGODB_URL",
          "value": "mongodb+srv://user:pass@cluster.mongodb.net/lynnapse"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/lynnapse",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Google Cloud Run Deployment

##### 1. Build and Deploy
```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/lynnapse

# Deploy to Cloud Run
gcloud run deploy lynnapse \
  --image gcr.io/PROJECT_ID/lynnapse \
  --platform managed \
  --region us-central1 \
  --set-env-vars MONGODB_URL="mongodb+srv://..." \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600
```

##### 2. Scheduled Jobs with Cloud Scheduler
```bash
# Create scheduled scraping job
gcloud scheduler jobs create http lynnapse-daily-scrape \
  --schedule="0 6 * * *" \
  --uri="https://lynnapse-SERVICE-ID.a.run.app/scrape" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"university": "arizona-psychology"}'
```

#### Azure Container Instances

##### Deploy to ACI
```bash
# Create resource group
az group create --name lynnapse-rg --location eastus

# Deploy container
az container create \
  --resource-group lynnapse-rg \
  --name lynnapse \
  --image lynnapse:latest \
  --environment-variables MONGODB_URL="mongodb+srv://..." \
  --cpu 1 \
  --memory 2 \
  --restart-policy OnFailure
```

## Production Configuration

### Environment Variables

#### Required Settings
```bash
# Database
MONGODB_URL=mongodb://admin:password@host:27017/lynnapse?authSource=admin
MONGODB_DATABASE=lynnapse

# Application
LYNNAPSE_ENV=production
LOG_LEVEL=INFO
```

#### Optional Settings
```bash
# Scraping Configuration
PLAYWRIGHT_HEADLESS=true
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=1.0
USER_AGENT="Mozilla/5.0 (compatible; LynnapseBot/1.0)"

# Performance
DEBUG=false
```

### MongoDB Setup

#### Atlas Cloud (Recommended)
```bash
# Connection string format
mongodb+srv://username:password@cluster.mongodb.net/lynnapse?retryWrites=true&w=majority
```

#### Self-Hosted MongoDB
```bash
# Docker MongoDB with authentication
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=strongpassword \
  -v mongodb_data:/data/db \
  mongo:7
```

#### Database Initialization
```javascript
// init-mongo.js
db = db.getSiblingDB('lynnapse');

// Create collections
db.createCollection('faculty');
db.createCollection('programs');
db.createCollection('lab_sites');

// Create indexes for performance
db.faculty.createIndex({ "university": 1, "department": 1 });
db.faculty.createIndex({ "email": 1 }, { unique: true, sparse: true });
db.faculty.createIndex({ "personal_website": 1 }, { sparse: true });
```

### Security Considerations

#### Container Security
```dockerfile
# Use non-root user
RUN groupadd -r lynnapse && useradd -r -g lynnapse lynnapse
USER lynnapse

# Minimal base image
FROM python:3.11-slim

# Security scanning
RUN apt-get update && apt-get upgrade -y
```

#### Network Security
```yaml
# docker-compose.yml
networks:
  lynnapse-network:
    driver: bridge
    internal: true  # Isolate from external networks

services:
  lynnapse:
    networks:
      - lynnapse-network
```

#### Secrets Management
```bash
# Use Docker secrets
echo "strongpassword" | docker secret create mongodb_password -

# Reference in compose
services:
  mongodb:
    secrets:
      - mongodb_password
    environment:
      MONGO_INITDB_ROOT_PASSWORD_FILE: /run/secrets/mongodb_password
```

## Monitoring & Logging

### Health Checks

#### Container Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from lynnapse.cli import app; print('OK')" || exit 1
```

#### Application Health Check
```bash
# Test database connectivity
docker-compose exec lynnapse python -m lynnapse.cli test-db

# Test scraper functionality
docker-compose exec lynnapse python -m lynnapse.cli test-scraper arizona-psychology --no-save
```

### Logging Configuration

#### Docker Logging
```yaml
# docker-compose.yml
services:
  lynnapse:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### Application Logging
```python
# lynnapse/config/settings.py
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = 'json' if os.getenv('LYNNAPSE_ENV') == 'production' else 'console'
```

#### Log Aggregation
```bash
# Ship logs to external service
docker run -d \
  --log-driver=syslog \
  --log-opt syslog-address=tcp://logserver:514 \
  lynnapse:latest
```

### Metrics & Monitoring

#### Basic Monitoring
```bash
# Resource usage
docker stats lynnapse-app

# Service status
docker-compose ps

# Application metrics
docker-compose exec lynnapse python -c "
import asyncio
from lynnapse.scrapers.university.arizona_psychology import ArizonaPsychologyScraper

async def main():
    async with ArizonaPsychologyScraper() as scraper:
        start = time.time()
        faculty = await scraper.scrape_faculty_list()
        duration = time.time() - start
        print(f'Scraped {len(faculty)} faculty in {duration:.2f}s')

asyncio.run(main())
"
```

## Backup & Recovery

### Data Backup

#### MongoDB Backup
```bash
# Create backup
docker-compose exec mongodb mongodump --db lynnapse --out /backup

# Restore backup
docker-compose exec mongodb mongorestore --db lynnapse /backup/lynnapse
```

#### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/lynnapse_$DATE"

# Create backup
docker-compose exec -T mongodb mongodump --db lynnapse --archive | \
  gzip > "$BACKUP_DIR.gz"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR.gz" s3://my-backups/lynnapse/

# Cleanup old backups (keep last 7 days)
find /backups -name "lynnapse_*.gz" -mtime +7 -delete
```

### Disaster Recovery

#### Service Recovery
```bash
# Restore from backup
docker-compose down
docker volume rm lynnapse-scraper_mongodb_data
docker-compose up -d
# Restore data from backup
```

#### Configuration Recovery
```bash
# Backup configuration
tar -czf config_backup.tar.gz .env docker-compose.yml seeds/

# Restore configuration
tar -xzf config_backup.tar.gz
```

## Performance Optimization

### Scaling Considerations

#### Vertical Scaling
```yaml
# docker-compose.yml
services:
  lynnapse:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### Horizontal Scaling
```bash
# Scale scraper instances
docker-compose up --scale lynnapse=3

# Load balancing with nginx
# See nginx.conf for configuration
```

### Database Optimization

#### MongoDB Indexes
```javascript
// Performance indexes
db.faculty.createIndex({ "university": 1, "department": 1 });
db.faculty.createIndex({ "research_areas": 1 });
db.faculty.createIndex({ "scraped_at": 1 });

// Compound indexes for common queries
db.faculty.createIndex({ "university": 1, "personal_website": 1 });
```

#### Connection Pooling
```python
# MongoDB connection optimization
MONGODB_MAX_POOL_SIZE = 50
MONGODB_MIN_POOL_SIZE = 5
MONGODB_MAX_IDLE_TIME_MS = 30000
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check MongoDB status
docker-compose ps mongodb

# Check logs
docker-compose logs mongodb

# Test connection
docker-compose exec lynnapse python -m lynnapse.cli test-db
```

#### Scraping Failures
```bash
# Enable verbose logging
docker-compose exec lynnapse python -m lynnapse.cli scrape-university arizona-psychology --verbose

# Check network connectivity
docker-compose exec lynnapse ping psychology.arizona.edu

# Verify Playwright setup
docker-compose exec lynnapse python -c "from playwright.async_api import async_playwright; print('Playwright OK')"
```

#### Memory Issues
```bash
# Monitor resource usage
docker stats

# Increase memory limits
# Edit docker-compose.yml resources section
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m lynnapse.cli scrape-university arizona-psychology --verbose
```

#### Interactive Debugging
```bash
# Access container shell
docker-compose exec lynnapse bash

# Python debugging session
docker-compose exec lynnapse python
>>> from lynnapse.scrapers.university.arizona_psychology import ArizonaPsychologyScraper
>>> scraper = ArizonaPsychologyScraper()
>>> # Interactive debugging
```

This deployment guide covers comprehensive deployment scenarios for Lynnapse. Choose the option that best fits your infrastructure and requirements. 