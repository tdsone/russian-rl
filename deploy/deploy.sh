#!/bin/bash
# Deployment script - run this to deploy updates
# Usage: ./deploy/deploy.sh

set -e

echo "=== Deploying Ugolki Updates ==="

cd /home/ubuntu/russian-rl

# Pull latest code
echo "Pulling latest code..."
git pull

# Update Python dependencies
echo "Updating Python dependencies..."
uv sync

# Rebuild frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Restart backend
echo "Restarting backend service..."
sudo systemctl restart ugolki

echo ""
echo "=== Deployment Complete! ==="
echo "Check status: sudo systemctl status ugolki"
