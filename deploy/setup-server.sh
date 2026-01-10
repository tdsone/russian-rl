#!/bin/bash
# Initial server setup script for Ubuntu 22.04/24.04 on AWS EC2
# Run this once when you first SSH into your new instance

set -e  # Exit on any error

echo "=== Ugolki Server Setup ==="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing dependencies..."
sudo apt install -y \
    nginx \
    git \
    curl \
    build-essential \
    python3-dev

# Install uv (Python package manager)
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# Install Node.js 20.x for frontend build
echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Clone the repository (or pull if exists)
if [ -d "/home/ubuntu/russian-rl" ]; then
    echo "Repository exists, pulling latest..."
    cd /home/ubuntu/russian-rl
    git pull
else
    echo "Cloning repository..."
    cd /home/ubuntu
    git clone https://github.com/YOUR_USERNAME/russian-rl.git
    cd russian-rl
fi

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    JWT_SECRET=$(openssl rand -hex 32)
    cat > .env << EOF
JWT_SECRET_KEY=${JWT_SECRET}
DATABASE_URL=sqlite+aiosqlite:///./ugolki.db
ALLOWED_ORIGINS=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
EOF
    echo "Generated .env with random JWT secret"
fi

# Setup systemd service
echo "Setting up systemd service..."
sudo cp deploy/ugolki.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ugolki
sudo systemctl start ugolki

# Setup nginx
echo "Configuring nginx..."
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ugolki
sudo ln -sf /etc/nginx/sites-available/ugolki /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Your app should be accessible at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status ugolki    # Check backend status"
echo "  sudo journalctl -u ugolki -f    # View backend logs"
echo "  sudo systemctl restart ugolki   # Restart backend"
echo "  sudo systemctl restart nginx    # Restart nginx"
echo ""
echo "Next steps:"
echo "  1. Update ALLOWED_ORIGINS in .env with your domain"
echo "  2. Setup SSL with: sudo certbot --nginx"
echo ""
