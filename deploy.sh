#!/bin/bash
# JARVIS v9.0 ULTRA - Quick Deploy Script

echo "=========================================="
echo "JARVIS v9.0 ULTRA - Docker Deployment"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    exit 1
fi

echo "✅ Docker found"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your API keys"
    echo "   Then run this script again."
    exit 1
fi

echo "✅ Environment file found"

# Build images
echo ""
echo "🔨 Building Docker images..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"

# Start services
echo ""
echo "🚀 Starting JARVIS services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services"
    exit 1
fi

echo "✅ Services started"

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."
curl -s http://localhost:8000/health > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ JARVIS API is healthy"
else
    echo "⚠️  JARVIS API not responding yet (may need more time)"
fi

curl -s http://localhost:3002/health > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ WhatsApp Bridge is healthy"
else
    echo "⚠️  WhatsApp Bridge not responding yet (may need more time)"
fi

# Show status
echo ""
echo "=========================================="
echo "📊 Deployment Status"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "🎉 JARVIS v9.0 ULTRA Deployed!"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  - Main API: http://localhost:8000/docs"
echo "  - WhatsApp: http://localhost:3002"
echo "  - Health: http://localhost:8000/health"
echo ""
echo "Management:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop: docker-compose stop"
echo "  - Restart: docker-compose restart"
echo ""
