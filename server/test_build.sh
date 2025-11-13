#!/bin/bash
# Test Docker build locally before deploying

set -e

echo "======================================================"
echo "Testing Docker build for persistent storage server"
echo "======================================================"
echo ""

# Check if we're in the server directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Please run this script from the server/ directory"
    exit 1
fi

echo "Step 1: Verifying required files..."
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    "standalone_server.py"
    "persistent_server.py"
    "replication-0.9.10-py3-none-any.whl"
    "requirements.txt"
    ".env.example"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file - MISSING!"
        exit 1
    fi
done

echo ""
echo "Step 2: Creating .env if needed..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "✓ .env already exists"
fi

echo ""
echo "Step 3: Building Docker image..."
docker-compose build

echo ""
echo "======================================================"
echo "✓ Build successful!"
echo "======================================================"
echo ""
echo "To start the server:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
