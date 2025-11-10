#!/bin/bash
# Quick deployment script for Multi-User Blender Server

set -e

echo "======================================================"
echo "Multi-User Blender Server - Deployment Script"
echo "======================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Warning: Running as root. Consider using a regular user."
    echo ""
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Would you like to install it? (y/n)"
    read -r install_docker

    if [ "$install_docker" = "y" ]; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh

        # Add current user to docker group
        if [ "$EUID" -ne 0 ]; then
            sudo usermod -aG docker $USER
            echo "Added $USER to docker group. Please log out and back in."
        fi
    else
        echo "Docker is required. Please install it manually."
        exit 1
    fi
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env

    # Generate random passwords
    ADMIN_PASS=$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-32)

    # Update .env with generated password
    sed -i.bak "s/your_secure_admin_password_here/$ADMIN_PASS/" .env
    rm .env.bak 2>/dev/null || true

    echo ""
    echo "✓ Configuration file created at .env"
    echo ""
    echo "========================================"
    echo "IMPORTANT: Save these credentials!"
    echo "========================================"
    echo "Admin Password: $ADMIN_PASS"
    echo ""
    echo "You can edit .env to customize settings."
    echo ""
    read -p "Press Enter to continue..."
else
    echo "Using existing .env configuration"
fi

# Check if replication wheel exists in current directory
if [ ! -f "replication-0.9.10-py3-none-any.whl" ]; then
    echo ""
    echo "⚠ Warning: replication-0.9.10-py3-none-any.whl not found in current directory"
    echo "Please ensure you copied the wheel file from ../multi_user/wheels/"
    echo ""
    echo "Run this command to fix:"
    echo "  cp ../multi_user/wheels/replication-0.9.10-py3-none-any.whl ."
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Configure firewall if ufw is available
if command -v ufw &> /dev/null; then
    echo ""
    echo "Configuring firewall..."

    # Get port from .env or use default
    PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
    PORT=${PORT:-5555}

    sudo ufw allow ${PORT}/tcp
    sudo ufw allow $((PORT+1))/tcp
    sudo ufw allow $((PORT+2))/tcp

    echo "✓ Firewall configured for ports ${PORT}-$((PORT+2))"
else
    echo "⚠ UFW not found. Please configure firewall manually:"
    echo "  Allow TCP ports 5555, 5556, 5557"
fi

echo ""
echo "Building and starting the server..."
docker-compose up -d --build

echo ""
echo "======================================================"
echo "Server deployed successfully!"
echo "======================================================"
echo ""
echo "Server Status:"
docker-compose ps
echo ""
echo "View logs with: docker-compose logs -f"
echo "Stop server with: docker-compose down"
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me || echo "Unable to detect")
echo "Your server's public IP: $PUBLIC_IP"
echo ""
echo "Configure Blender clients to connect to: $PUBLIC_IP:5555"
echo "======================================================"
