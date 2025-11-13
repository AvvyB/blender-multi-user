#!/bin/bash
# Quick update script for adding persistent storage to existing server
# Run this on your server machine

set -e  # Exit on error

echo "========================================================"
echo "Multi-User Server - Persistent Storage Upgrade"
echo "========================================================"
echo ""

# Check if we're in the server directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Please run this script from the server/ directory"
    exit 1
fi

# Backup current setup
echo "Step 1: Creating backup..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "../$BACKUP_FILE" . 2>/dev/null || true
echo "✓ Backup created: ../$BACKUP_FILE"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env from .env.example first"
    exit 1
fi

# Add persistent storage settings if not present
echo "Step 2: Updating .env configuration..."
if ! grep -q "SAVE_INTERVAL" .env; then
    cat >> .env << 'EOF'

# === Persistent Storage Settings ===
# Auto-save interval in seconds (default: 120 = 2 minutes)
SAVE_INTERVAL=120

# Maximum number of backup snapshots to keep (default: 10)
MAX_BACKUPS=10
EOF
    echo "✓ Added persistent storage settings to .env"
else
    echo "✓ .env already has persistent storage settings"
fi
echo ""

# Check if persistent_server.py exists
if [ ! -f "persistent_server.py" ]; then
    echo "Error: persistent_server.py not found!"
    echo "Please upload the new server files first"
    exit 1
fi

# Stop current server
echo "Step 3: Stopping current server..."
docker-compose down
echo "✓ Server stopped"
echo ""

# Rebuild container
echo "Step 4: Rebuilding Docker container with persistent storage..."
docker-compose build
echo "✓ Container rebuilt"
echo ""

# Create data directory if it doesn't exist
echo "Step 5: Creating data directory..."
mkdir -p data
mkdir -p data/backups
echo "✓ Data directory ready"
echo ""

# Start server
echo "Step 6: Starting server with persistent storage..."
docker-compose up -d
echo "✓ Server started"
echo ""

# Wait for server to start
echo "Step 7: Verifying server status..."
sleep 3

# Check if container is running
if [ "$(docker inspect -f '{{.State.Running}}' blender-multiuser-server 2>/dev/null)" = "true" ]; then
    echo "✓ Server is running"
else
    echo "✗ Server failed to start"
    echo ""
    echo "Check logs with: docker-compose logs"
    exit 1
fi

# Show logs to verify persistence is enabled
echo ""
echo "========================================================"
echo "Checking server logs for persistent storage..."
echo "========================================================"
docker-compose logs --tail 20 | grep -E "(Persistent Storage|Auto-save enabled|Data Directory)" || true
echo ""

echo "========================================================"
echo "✓ Upgrade Complete!"
echo "========================================================"
echo ""
echo "Persistent storage is now enabled:"
echo "  • Auto-save interval: $(grep SAVE_INTERVAL .env | cut -d= -f2) seconds"
echo "  • Max backups: $(grep MAX_BACKUPS .env | cut -d= -f2)"
echo "  • Data directory: $(pwd)/data/"
echo ""
echo "Next steps:"
echo "  1. Monitor logs: docker-compose logs -f"
echo "  2. Wait 2 minutes for first auto-save"
echo "  3. Test recovery: docker-compose restart"
echo ""
echo "Documentation:"
echo "  • Full guide: PERSISTENT_STORAGE.md"
echo "  • Upgrade guide: UPGRADE_TO_PERSISTENT.md"
echo ""
