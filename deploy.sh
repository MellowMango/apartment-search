#!/bin/bash

# Lynnapse Deployment Script
# Builds and runs the containerized scraping environment

set -e

echo "🚀 Lynnapse Deployment Script"
echo "=================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
echo "🏗️  Building Lynnapse Docker image..."
docker-compose build

# Start the services
echo "🌟 Starting services..."
docker-compose up -d

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
sleep 10

# Show running containers
echo "📋 Running containers:"
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Available services:"
echo "   • MongoDB: localhost:27017"
echo "   • Mongo Express: http://localhost:8081 (admin/admin)"
echo ""
echo "🛠️  Usage examples:"
echo "   # Test the scraper"
echo "   docker-compose exec lynnapse python -m lynnapse.cli test-scraper"
echo ""
echo "   # Scrape Arizona Psychology faculty"
echo "   docker-compose exec lynnapse python -m lynnapse.cli scrape-university arizona-psychology"
echo ""
echo "   # Scrape with detailed profiles (slower)"
echo "   docker-compose exec lynnapse python -m lynnapse.cli scrape-university arizona-psychology --profiles"
echo ""
echo "   # Check logs"
echo "   docker-compose logs -f lynnapse"
echo ""
echo "   # Stop services"
echo "   docker-compose down"
echo ""
echo "📁 Output files will be saved to ./output/ directory" 