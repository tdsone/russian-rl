# Ugolki Deployment Guide

This guide walks you through deploying Ugolki on AWS EC2.

## Prerequisites

- AWS account
- SSH key pair (create one in AWS Console → EC2 → Key Pairs)
- Your code pushed to a Git repository (GitHub, GitLab, etc.)

## Step 1: Launch EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**

2. Configure the instance:
   - **Name**: `ugolki-server`
   - **AMI**: Ubuntu Server 24.04 LTS (or 22.04)
   - **Instance type**: `t3.small` (or `t3.micro` for free tier)
   - **Key pair**: Select your SSH key
   - **Network settings**: 
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow HTTPS (port 443) from anywhere

3. Click **Launch Instance**

4. Note your instance's **Public IPv4 address** from the EC2 dashboard

## Step 2: Connect to Your Instance

```bash
# Replace with your key file and instance IP
ssh -i "your-key.pem" ubuntu@YOUR_EC2_IP
```

## Step 3: Initial Server Setup

Option A - **Quick setup** (if repo is public):

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/russian-rl.git
cd russian-rl

# Run setup script
chmod +x deploy/setup-server.sh
./deploy/setup-server.sh
```

Option B - **Manual setup**:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y nginx git curl build-essential python3-dev

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Clone repo and install
git clone https://github.com/YOUR_USERNAME/russian-rl.git
cd russian-rl
uv sync

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite+aiosqlite:///./ugolki.db
ALLOWED_ORIGINS=http://YOUR_EC2_IP
EOF

# Setup systemd service
sudo cp deploy/ugolki.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ugolki
sudo systemctl start ugolki

# Setup nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ugolki
sudo ln -sf /etc/nginx/sites-available/ugolki /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## Step 4: Verify Deployment

Visit `http://YOUR_EC2_IP` in your browser. You should see the Ugolki app!

Check backend status:
```bash
sudo systemctl status ugolki
sudo journalctl -u ugolki -f  # View logs
```

## Step 5: Setup SSL (HTTPS) - Recommended

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Update .env with HTTPS origin
nano .env
# Change: ALLOWED_ORIGINS=https://yourdomain.com

# Restart backend
sudo systemctl restart ugolki
```

## Deploying Updates

After pushing changes to git:

```bash
cd /home/ubuntu/russian-rl
./deploy/deploy.sh
```

Or manually:
```bash
git pull
uv sync
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart ugolki
```

## Useful Commands

```bash
# Backend
sudo systemctl status ugolki       # Check status
sudo systemctl restart ugolki      # Restart
sudo journalctl -u ugolki -f       # View logs
sudo journalctl -u ugolki --since "1 hour ago"

# Nginx
sudo systemctl status nginx
sudo nginx -t                      # Test config
sudo systemctl restart nginx

# Database backup
cp ugolki.db ugolki.db.backup
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u ugolki -n 50

# Try running manually
cd /home/ubuntu/russian-rl
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 502 Bad Gateway
The backend isn't running. Check systemd logs and restart:
```bash
sudo systemctl restart ugolki
```

### WebSocket not connecting
Check nginx config has the `/ws/` location block and restart nginx.

### CORS errors
Update `ALLOWED_ORIGINS` in `.env` to match your domain exactly, then restart the backend.

## Cost Estimate

| Resource | Cost |
|----------|------|
| t3.micro (free tier) | $0/month for 1 year |
| t3.small | ~$15/month |
| Domain (optional) | ~$12/year |
| SSL Certificate | Free (Let's Encrypt) |

## Architecture

```
┌─────────────────────────────────────────────┐
│                  EC2 Instance                │
│                                             │
│  ┌─────────┐    ┌──────────────────────┐   │
│  │  Nginx  │───▶│  Static Files (React) │   │
│  │  :80    │    └──────────────────────┘   │
│  │  :443   │                                │
│  │         │    ┌──────────────────────┐   │
│  │  /api/* │───▶│  FastAPI (uvicorn)   │   │
│  │  /ws/*  │    │  :8000               │   │
│  └─────────┘    └──────────┬───────────┘   │
│                            │                │
│                    ┌───────▼───────┐       │
│                    │   SQLite DB   │       │
│                    └───────────────┘       │
└─────────────────────────────────────────────┘
```
