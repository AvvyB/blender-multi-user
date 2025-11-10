#!/bin/bash
# Preparation script - ensures all files are ready for deployment

echo "======================================================"
echo "Preparing server directory for deployment"
echo "======================================================"
echo ""

# Check if we're in the server directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Please run this script from the server/ directory"
    exit 1
fi

# Check if replication wheel exists
if [ ! -f "replication-0.9.10-py3-none-any.whl" ]; then
    echo "Copying replication wheel..."
    if [ -f "../multi_user/wheels/replication-0.9.10-py3-none-any.whl" ]; then
        cp ../multi_user/wheels/replication-0.9.10-py3-none-any.whl .
        echo "✓ Replication wheel copied"
    else
        echo "✗ Error: Could not find replication wheel at:"
        echo "  ../multi_user/wheels/replication-0.9.10-py3-none-any.whl"
        exit 1
    fi
else
    echo "✓ Replication wheel already present"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠ IMPORTANT: Edit .env and set your passwords!"
    echo "  Run: nano .env"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "======================================================"
echo "✓ Server directory is ready for deployment!"
echo "======================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your passwords: nano .env"
echo "2. Copy entire server/ directory to your cloud server"
echo "3. Run: docker-compose up -d"
echo ""
echo "Or use the automated deployment:"
echo "  ./deploy.sh"
echo ""
