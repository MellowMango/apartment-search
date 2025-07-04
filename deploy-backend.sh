#!/bin/bash

# Lynnapse Backend Microservice Deployment Script
# This script deploys only the core scraping functionality without web interface

echo "🚀 Deploying Lynnapse Backend Microservice..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker daemon."
    exit 1
fi

echo "📦 Building backend Docker image..."
docker-compose -f docker-compose.backend.yml build

echo "🏃 Starting backend services..."
docker-compose -f docker-compose.backend.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose -f docker-compose.backend.yml ps | grep -q "Up"; then
    echo "✅ Backend microservice deployed successfully!"
    echo ""
    echo "📋 Available services:"
    echo "  - Lynnapse Backend: Use 'docker exec -it lynnapse-backend bash' to access"
    echo "  - MongoDB: Available at localhost:27017"
    echo ""
    echo "🔧 Example usage:"
    echo "  docker exec -it lynnapse-backend python -m lynnapse.cli.adaptive_scrape 'Carnegie Mellon University' -d psychology"
    echo ""
    echo "📊 View logs:"
    echo "  docker-compose -f docker-compose.backend.yml logs -f"
    echo ""
    echo "🛑 Stop services:"
    echo "  docker-compose -f docker-compose.backend.yml down"
else
    echo "❌ Failed to start services. Check logs:"
    docker-compose -f docker-compose.backend.yml logs
    exit 1
fi 