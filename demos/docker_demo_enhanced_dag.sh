#!/bin/bash
# 🚀 Docker Demo: Enhanced DAG Workflow
# 
# This script demonstrates the enhanced Lynnapse DAG workflow in Docker,
# showcasing the complete pipeline: Scraping → Link Processing → Enrichment → Storage

set -e

echo "🚀 Enhanced DAG Workflow Docker Demo"
echo "===================================="
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Building Lynnapse Docker image..."
docker build -t lynnapse:enhanced-dag .

echo
echo "📦 Starting MongoDB and Lynnapse services..."
docker-compose up -d mongodb

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
sleep 10

echo
echo "🧪 Running Enhanced DAG Workflow Demo..."
echo

# Basic enhanced DAG test (no external dependencies)
echo "📋 Test 1: Basic Enhanced DAG Workflow"
docker run --rm \
    --network lynnapse-scraper_lynnapse-network \
    -e MONGODB_URL=mongodb://admin:password@mongodb:27017/lynnapse?authSource=admin \
    -e PLAYWRIGHT_HEADLESS=true \
    -e LYNNAPSE_ENV=docker \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/logs:/app/logs \
    lynnapse:enhanced-dag \
    python demo_enhanced_dag_workflow.py --docker

echo
echo "📋 Test 2: Enhanced DAG with CLI Interface"
docker run --rm \
    --network lynnapse-scraper_lynnapse-network \
    -e MONGODB_URL=mongodb://admin:password@mongodb:27017/lynnapse?authSource=admin \
    -e PLAYWRIGHT_HEADLESS=true \
    -e LYNNAPSE_ENV=docker \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/logs:/app/logs \
    lynnapse:enhanced-dag \
    python -m lynnapse.cli enhanced-flow --dry-run --verbose

# If OpenAI API key is available, test AI-enhanced workflow
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo
    echo "📋 Test 3: AI-Enhanced DAG Workflow (with OpenAI API)"
    docker run --rm \
        --network lynnapse-scraper_lynnapse-network \
        -e MONGODB_URL=mongodb://admin:password@mongodb:27017/lynnapse?authSource=admin \
        -e PLAYWRIGHT_HEADLESS=true \
        -e LYNNAPSE_ENV=docker \
        -e OPENAI_API_KEY="$OPENAI_API_KEY" \
        -v $(pwd)/output:/app/output \
        -v $(pwd)/logs:/app/logs \
        lynnapse:enhanced-dag \
        python demo_enhanced_dag_workflow.py --docker --enable-ai
else
    echo
    echo "⚠️  Skipping AI test - no OPENAI_API_KEY environment variable found"
    echo "   To test AI features, set: export OPENAI_API_KEY=your_key_here"
fi

echo
echo "🎉 Enhanced DAG Workflow Demo completed!"
echo
echo "📊 Available commands in Docker:"
echo "   docker run lynnapse:enhanced-dag python -m lynnapse.cli enhanced-flow --help"
echo "   docker run lynnapse:enhanced-dag python -m lynnapse.cli university-enhanced --help"
echo "   docker run lynnapse:enhanced-dag python -m lynnapse.cli version"
echo
echo "📁 Check output/ and logs/ directories for results"
echo "🔗 Access Mongo Express at: http://localhost:8081 (admin/admin)"

# Show docker-compose services status
echo
echo "📦 Docker services status:"
docker-compose ps 