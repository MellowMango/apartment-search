# 🚀 Lynnapse Backend Microservice Deployment Guide

## Overview

Lynnapse is designed with a clean microservice architecture that separates the core scraping functionality from the optional web interface. This allows for reliable, scalable deployment in production environments.

## 🏗️ Architecture

### Backend Microservice
- **Core scraping and processing functionality**
- **Complete CLI interface for all operations**
- **MongoDB integration for data storage**
- **No web dependencies required**
- **Lightweight and production-ready**

### Frontend Web Interface (Optional)
- **Interactive web UI for development/demo**
- **Communicates with backend via REST API**
- **Can be completely removed without affecting functionality**

## 📦 Deployment Options

### 1. Backend-Only Deployment (Recommended for Production)

```bash
# Quick deployment
./deploy-backend.sh

# Manual deployment
docker-compose -f docker-compose.backend.yml up -d
```

**Services:**
- `lynnapse-backend`: Core scraping microservice
- `mongodb`: Database for data storage

**Ports:**
- MongoDB: `27017`

### 2. Full Stack Deployment (Development)

```bash
# Deploy both backend and frontend
docker-compose up -d
```

**Services:**
- `lynnapse-backend`: Core scraping microservice
- `lynnapse-frontend`: Web interface
- `mongodb`: Database for data storage

**Ports:**
- Frontend: `8000`
- MongoDB: `27017`

### 3. Dependencies-Only Installation

```bash
# Install only backend dependencies (35 packages)
pip install -r backend-requirements.txt

# Run directly
python -m lynnapse.cli.adaptive_scrape "University Name" -d department
```

## 🔧 Usage Examples

### CLI Operations (Backend Microservice)

```bash
# Comprehensive faculty extraction
docker exec -it lynnapse-backend python -m lynnapse.cli.adaptive_scrape "Carnegie Mellon University" -d psychology --lab-discovery -v

# Convert data to ID-based architecture
docker exec -it lynnapse-backend python -m lynnapse.cli.convert_data /app/data/faculty_data.json

# Enhance faculty profiles
docker exec -it lynnapse-backend python -m lynnapse.cli.enhance_data /app/data/faculty_data.json --verbose

# Smart link processing
docker exec -it lynnapse-backend python -m lynnapse.cli.process_links --input /app/data/faculty_data.json --mode comprehensive

# Comprehensive link enrichment
docker exec -it lynnapse-backend python -m lynnapse.cli.enrich_links /app/data/faculty_data.json --analysis comprehensive
```

### File Management

```bash
# Access container shell
docker exec -it lynnapse-backend bash

# View results
docker exec -it lynnapse-backend ls -la /app/scrape_results/

# Copy results to host
docker cp lynnapse-backend:/app/scrape_results/ ./local_results/
```

## 📊 Resource Requirements

### Backend Microservice Only
- **RAM**: 2-4 GB
- **Storage**: 10-20 GB
- **CPU**: 2 cores minimum
- **Network**: Standard HTTP/HTTPS access

### Full Stack
- **RAM**: 3-6 GB
- **Storage**: 15-25 GB
- **CPU**: 2-4 cores
- **Network**: Standard HTTP/HTTPS access + port 8000

## 🔒 Security Considerations

### Environment Variables

```bash
# Required
MONGODB_URL=mongodb://admin:password@mongodb:27017/lynnapse?authSource=admin

# Optional
OPENAI_API_KEY=your_api_key_here  # For AI-assisted discovery
LYNNAPSE_ENV=production
PLAYWRIGHT_HEADLESS=true
```

### Network Security
- Backend microservice doesn't expose web ports by default
- MongoDB is only accessible within Docker network
- All scraping operations use standard HTTP/HTTPS

## 📈 Monitoring & Health Checks

### Health Check Endpoint

```bash
# Check backend service health
docker exec -it lynnapse-backend python -c "from lynnapse.cli import app; print('Backend OK')"
```

### Logging

```bash
# View backend logs
docker-compose -f docker-compose.backend.yml logs -f lynnapse-backend

# View MongoDB logs
docker-compose -f docker-compose.backend.yml logs -f mongodb
```

### Service Management

```bash
# Start services
docker-compose -f docker-compose.backend.yml up -d

# Stop services
docker-compose -f docker-compose.backend.yml down

# Restart services
docker-compose -f docker-compose.backend.yml restart

# Update and rebuild
docker-compose -f docker-compose.backend.yml build --no-cache
docker-compose -f docker-compose.backend.yml up -d
```

## 🧪 Testing Deployment

### Validate Backend Functionality

```bash
# Test basic CLI functionality
docker exec -it lynnapse-backend python -m lynnapse.cli --help

# Test adaptive scraping (small test)
docker exec -it lynnapse-backend python -m lynnapse.cli.adaptive_scrape "University of Vermont" -d psychology -m 5 -v

# Test database connection
docker exec -it lynnapse-backend python -c "
from lynnapse.config.settings import get_settings
print('MongoDB URL:', get_settings().mongodb_url)
"
```

### Performance Testing

```bash
# Run comprehensive extraction test
docker exec -it lynnapse-backend python -m lynnapse.cli.adaptive_scrape "Carnegie Mellon University" -d psychology --lab-discovery --comprehensive -v
```

## 🚀 Production Deployment Checklist

- [ ] Docker and Docker Compose installed
- [ ] `backend-requirements.txt` dependencies verified
- [ ] MongoDB connection configured
- [ ] Environment variables set appropriately
- [ ] Storage volumes configured for persistence
- [ ] Network security configured (firewall, etc.)
- [ ] Backup strategy for MongoDB data
- [ ] Monitoring and alerting configured
- [ ] Health check endpoints configured
- [ ] Log rotation and management configured

## 🔍 Troubleshooting

### Common Issues

1. **Docker daemon not running**
   ```bash
   # Start Docker service
   sudo systemctl start docker
   ```

2. **MongoDB connection errors**
   ```bash
   # Check MongoDB container
   docker-compose -f docker-compose.backend.yml logs mongodb
   ```

3. **Web scraping blocked**
   ```bash
   # Check network connectivity
   docker exec -it lynnapse-backend curl -I https://www.cmu.edu
   ```

4. **Memory issues**
   ```bash
   # Monitor resource usage
   docker stats lynnapse-backend
   ```

### Support

For additional support or custom deployment configurations, refer to:
- [API Reference](docs/API_REFERENCE.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Deployment Documentation](docs/DEPLOYMENT.md) 