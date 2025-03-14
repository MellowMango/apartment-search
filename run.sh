#!/bin/bash

# Start the entire system

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker and try again."
  exit 1
fi

# Build and start all services
echo "Starting all services with Docker Compose..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Check if services are running
echo "Checking if services are running..."
docker-compose ps

# Print access URLs
echo ""
echo "Access the services at:"
echo "- FastAPI Backend: http://localhost:8000/api/v1/docs"
echo "- MCP Firecrawl Server: http://localhost:3000"
echo "- MCP Playwright Server: http://localhost:3001"
echo ""
echo "To stop the services, run: docker-compose down" 