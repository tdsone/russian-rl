# Ugolki Deployment Documentation

This document describes the production deployment of the Ugolki application on AWS EC2.

## Current Production Environment

| Component | Details |
|-----------|---------|
| **Server** | AWS EC2 t3.micro (eu-west-2) |
| **Public IP** | 3.8.190.167 |
| **OS** | Ubuntu 24.04 LTS |
| **URL** | http://3.8.190.167 |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   EC2 Instance                   │
│                                                  │
│  ┌──────────┐     ┌─────────────────────────┐   │
│  │  Nginx   │────▶│  Static Files (React)   │   │
│  │  :80     │     │  /home/ubuntu/russian-rl│   │
│  │          │     │  /frontend/dist/        │   │
│  │  /api/*  │     └─────────────────────────┘   │
│  │  /ws/*   │                                    │
│  │    │     │     ┌─────────────────────────┐   │
│  │    └─────│────▶│  FastAPI (uvicorn)      │   │
│  └──────────┘     │  127.0.0.1:8000         │   │
│                   └───────────┬─────────────┘   │
│                               │                  │
│                       ┌───────▼───────┐         │
│                       │   SQLite DB   │         │
│                       │   ugolki.db   │         │
│                       └───────────────┘         │
└─────────────────────────────────────────────────┘
```

## File Locations on Server

| Purpose | Path |
|---------|------|
| Application code | `/home/ubuntu/russian-rl/` |
| Frontend build | `/home/ubuntu/russian-rl/frontend/dist/` |
| Environment variables | `/home/ubuntu/russian-rl/.env` |
| SQLite database | `/home/ubuntu/russian-rl/ugolki.db` |
| Systemd service | `/etc/systemd/system/ugolki.service` |
| Nginx config | `/etc/nginx/sites-enabled/ugolki` |

## Environment Variables

The `.env` file on the server contains:

```bash
JWT_SECRET_KEY=<generated-secret>
DATABASE_URL=sqlite+aiosqlite:///./ugolki.db
ALLOWED_ORIGINS=http://3.8.190.167
```

## Frontend Build Configuration

The frontend must be built with the correct API URL for production:

```bash
# frontend/.env.production
VITE_API_URL=/api
```

This makes the frontend use `/api/*` paths which nginx proxies to the backend.

## Services

### Backend Service (systemd)

```bash
# Check status
sudo systemctl status ugolki

# View logs
sudo journalctl -u ugolki -f

# Restart
sudo systemctl restart ugolki

# Stop/Start
sudo systemctl stop ugolki
sudo systemctl start ugolki
```

### Nginx

```bash
# Check status
sudo systemctl status nginx

# Test config
sudo nginx -t

# Restart
sudo systemctl restart nginx

# View error logs
sudo tail -f /var/log/nginx/error.log
```

## Deployment Process

### Initial Setup (already done)

The `deploy/setup-server.sh` script handles initial server setup.

### Automatic Deployment (CI/CD)

The app is automatically deployed via GitHub Actions when you push to the `main` branch.

**Workflow file:** `.github/workflows/deploy.yml`

#### Setting Up GitHub Secrets

You need to configure two secrets in your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `EC2_HOST` | `3.8.190.167` (your EC2 public IP) |
| `EC2_SSH_KEY` | Contents of your `ugolki-keys.pem` file |

To get your SSH key contents:
```bash
cat ugolki-keys.pem
```
Copy the entire output including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` lines.

#### How It Works

1. Push code to `main` branch
2. GitHub Actions triggers the deploy workflow
3. Workflow SSHs into EC2 and runs:
   - `git fetch && git reset --hard origin/main`
   - `uv sync` (update Python dependencies)
   - `npm ci && npm run build` (rebuild frontend)
   - `sudo systemctl restart ugolki` (restart backend)
4. Deployment status is verified and shown in GitHub Actions

#### Manual Trigger

You can also trigger deployment manually:
1. Go to **Actions** tab in GitHub
2. Select **Deploy to AWS EC2** workflow
3. Click **Run workflow** → **Run workflow**

#### Viewing Deployment Status

- Check the **Actions** tab in your GitHub repository
- Green ✅ = successful deployment
- Red ❌ = failed deployment (check logs for details)

### Manual Deployment

If you need to deploy manually, SSH into the server and run:

```bash
cd ~/russian-rl
git pull
uv sync
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart ugolki
```

Or use the deploy script:

```bash
./deploy/deploy.sh
```

### What Requires Rebuilding

| Change Type | Action Required |
|-------------|-----------------|
| Backend Python code | `sudo systemctl restart ugolki` |
| Frontend code | `cd frontend && npm run build` |
| Python dependencies | `uv sync && sudo systemctl restart ugolki` |
| Frontend dependencies | `cd frontend && npm install && npm run build` |
| Nginx config | `sudo cp deploy/nginx.conf /etc/nginx/sites-available/ugolki && sudo nginx -t && sudo systemctl restart nginx` |
| Systemd service | `sudo cp deploy/ugolki.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl restart ugolki` |
| Environment variables | Edit `.env` then `sudo systemctl restart ugolki` |

## SSH Access

```bash
ssh -i "ugolki-keys.pem" ubuntu@3.8.190.167
```

## Troubleshooting

### 500 Internal Server Error
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Usually a permission issue - ensure nginx can read frontend files

### Backend not responding
- Check service: `sudo systemctl status ugolki`
- Check logs: `sudo journalctl -u ugolki -f`
- Test directly: `curl http://127.0.0.1:8000/health`

### CORS errors in browser
- Frontend calling wrong URL (should be `/api/*`, not `localhost:8000`)
- Rebuild frontend: `cd frontend && npm run build`
- Check `ALLOWED_ORIGINS` in `.env` matches your domain

### WebSocket connection issues
- Check nginx config has proper WebSocket headers
- Check browser console for connection errors

## Backup

### Database Backup

```bash
# On server
cp ~/russian-rl/ugolki.db ~/russian-rl/ugolki.db.backup

# Download to local machine
scp -i "ugolki-keys.pem" ubuntu@3.8.190.167:~/russian-rl/ugolki.db ./backup/
```

## Future Improvements

- [ ] Add SSL/HTTPS with Let's Encrypt (`sudo certbot --nginx`)
- [ ] Set up a domain name
- [ ] Add database backups to S3
- [ ] Set up monitoring/alerting
- [ ] Consider PostgreSQL for higher traffic
- [x] ~~Set up CI/CD with GitHub Actions~~ (Done!)