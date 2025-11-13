#!/bin/bash
# Deploy persistent storage update to remote server
# Run this from your LOCAL machine

set -e

# Configuration - EDIT THESE
SERVER_USER="your-username"
SERVER_HOST="your-server.com"
SERVER_DIR="~/blender-server"

echo "======================================================"
echo "Multi-User Server - Deploy Persistent Storage"
echo "======================================================"
echo ""
echo "This will deploy persistent storage to:"
echo "  User: $SERVER_USER"
echo "  Host: $SERVER_HOST"
echo "  Directory: $SERVER_DIR"
echo ""
read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please edit this script and set SERVER_USER, SERVER_HOST, and SERVER_DIR"
    exit 1
fi

# Check if we're in the multi-user directory
if [ ! -d "server" ]; then
    echo "Error: Please run this script from the multi-user/ directory"
    exit 1
fi

echo ""
echo "Step 1: Uploading server files..."

# Upload all necessary files
scp server/persistent_server.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/Dockerfile ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/docker-compose.yml ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/.env.example ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/update_server.sh ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/PERSISTENT_STORAGE.md ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/UPGRADE_TO_PERSISTENT.md ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/BUILD_TROUBLESHOOTING.md ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/
scp server/test_build.sh ${SERVER_USER}@${SERVER_HOST}:${SERVER_DIR}/

echo "✓ Files uploaded"

echo ""
echo "Step 2: Running update script on server..."
echo ""

# Run update script on server
ssh -t ${SERVER_USER}@${SERVER_HOST} "cd ${SERVER_DIR} && chmod +x update_server.sh && ./update_server.sh"

echo ""
echo "======================================================"
echo "✓ Deployment Complete!"
echo "======================================================"
echo ""
echo "To monitor your server:"
echo "  ssh ${SERVER_USER}@${SERVER_HOST}"
echo "  cd ${SERVER_DIR}"
echo "  docker-compose logs -f"
echo ""
