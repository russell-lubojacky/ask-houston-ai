# Production Deployment Guide - Ask Houston AI

This guide provides step-by-step instructions for deploying Ask Houston AI to a Linode server (or any Linux server) for beta testing.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Setup](#application-setup)
4. [Security Configuration](#security-configuration)
5. [SSL/TLS Setup](#ssltls-setup)
6. [Deployment](#deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- Linode server (recommended: 4GB RAM minimum, 2 CPU cores)
- Ubuntu 22.04 LTS or similar Linux distribution
- Domain name pointed to your server's IP address
- SSH access to the server
- Ollama installed and running (for LLM functionality)

### Required Software
- Docker & Docker Compose
- Git
- Nginx (optional if using docker-compose.prod.yml with built-in nginx)

---

## Server Setup

### 1. Initial Server Configuration

```bash
# SSH into your Linode server
ssh root@your-server-ip

# Update system packages
apt update && apt upgrade -y

# Install required packages
apt install -y git curl wget nano ufw

# Create a non-root user (recommended)
adduser houston-ai
usermod -aG sudo houston-ai

# Switch to the new user
su - houston-ai
```

### 2. Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
# Then SSH back in

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 3. Install and Configure Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull the mistral model (or your preferred model)
ollama pull mistral

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

---

## Application Setup

### 1. Clone the Repository

```bash
# Navigate to your preferred directory
cd /home/houston-ai

# Clone the repository
git clone <your-repo-url> ask-houston-ai
cd ask-houston-ai
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your production values
nano .env
```

**Important: Update these values in `.env`:**

```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD_HERE_MIN_20_CHARS
POSTGRES_DB=houston_311_db

# Read-only Database User (for application)
DB_HOST=postgres
DB_PORT=5432
DB_USER=readonly_311
DB_PASSWORD=YOUR_STRONG_READONLY_PASSWORD_HERE
DB_NAME=houston_311_db

# LLM Configuration
LLM_MODEL=mistral
OLLAMA_HOST=http://host.docker.internal:11434

# CORS Configuration
# Replace with your actual domain
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Application URLs
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://yourdomain.com/api

# Environment
ENVIRONMENT=production
```

**Generate strong passwords:**
```bash
# Generate strong passwords using openssl
openssl rand -base64 32
```

### 3. Update readonly_311 Password in Database Init

Edit `postgres/init.sql` and update the password on line 61:

```sql
CREATE USER readonly_311 WITH PASSWORD 'SAME_PASSWORD_AS_ENV_FILE';
```

---

## Security Configuration

### 1. Configure Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (important - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Ollama (only from localhost)
sudo ufw deny 11434

# Check firewall status
sudo ufw status
```

### 2. Secure PostgreSQL

The production `docker-compose.prod.yml` already:
- ✅ Does NOT expose PostgreSQL port 5432 externally
- ✅ Uses internal Docker network for database access
- ✅ Requires authentication
- ✅ Uses read-only user for application queries

### 3. Review Security Safeguards

All security safeguards are already implemented:
- ✅ Frontend input validation
- ✅ Intent classification
- ✅ SQL query validation
- ✅ Read-only database user
- ✅ CORS restrictions
- ✅ Rate limiting (via nginx)

See `docs/SECURITY_TESTING.md` for details.

---

## SSL/TLS Setup (Optional but Recommended)

### Option 1: Using Certbot (Let's Encrypt - Free)

```bash
# Install Certbot
sudo apt install -y certbot

# Stop nginx if running
sudo systemctl stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Option 2: Using Linode's SSL/TLS Manager

Follow Linode's documentation to generate and install SSL certificates.

### Configure SSL in Nginx

After obtaining certificates:

```bash
# Create SSL directory for nginx
mkdir -p nginx/ssl

# Copy certificates (adjust paths as needed)
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/

# Set proper permissions
sudo chown -R $USER:$USER nginx/ssl
chmod 600 nginx/ssl/*
```

Then uncomment the HTTPS server block in `nginx/nginx.conf` and update the `server_name`.

---

## Deployment

### 1. Build and Start Services

```bash
# Make sure you're in the project directory
cd /home/houston-ai/ask-houston-ai

# Build and start all services using production compose file
docker compose -f docker-compose.prod.yml up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Press Ctrl+C to stop following logs
```

### 2. Verify Services are Running

```bash
# Check all containers are healthy
docker compose -f docker-compose.prod.yml ps

# Test health endpoint
curl http://localhost/health

# Expected response:
# {"status":"healthy","database":"connected","environment":"production"}
```

### 3. Create Read-Only Database User (if not auto-created)

```bash
# Connect to PostgreSQL container
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d houston_311_db

# Run these SQL commands:
CREATE USER readonly_311 WITH PASSWORD 'YOUR_READONLY_PASSWORD';
GRANT CONNECT ON DATABASE houston_311_db TO readonly_311;
GRANT USAGE ON SCHEMA houston_311 TO readonly_311;
GRANT SELECT ON houston_311.incidents TO readonly_311;

# Exit psql
\q

# Restart app container
docker compose -f docker-compose.prod.yml restart app
```

### 4. Test the Application

```bash
# Test from server
curl "http://localhost/ask?q=Show%20me%20all%20pothole%20incidents"

# Test from your browser
# Navigate to: http://your-server-ip
# or https://yourdomain.com (if SSL configured)
```

---

## Monitoring & Maintenance

### 1. View Logs

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs

# View logs for specific service
docker compose -f docker-compose.prod.yml logs app
docker compose -f docker-compose.prod.yml logs postgres
docker compose -f docker-compose.prod.yml logs frontend
docker compose -f docker-compose.prod.yml logs nginx

# Follow logs in real-time
docker compose -f docker-compose.prod.yml logs -f app
```

### 2. Health Checks

```bash
# Check application health
curl http://localhost/health

# Check all container status
docker compose -f docker-compose.prod.yml ps
```

### 3. Backup Database

```bash
# Create backup directory
mkdir -p ~/backups

# Backup database
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres houston_311_db > ~/backups/houston_311_$(date +%Y%m%d_%H%M%S).sql

# Automate backups with cron
crontab -e

# Add this line for daily backups at 2 AM:
# 0 2 * * * cd /home/houston-ai/ask-houston-ai && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres houston_311_db > ~/backups/houston_311_$(date +\%Y\%m\%d).sql
```

### 4. Update Application

```bash
# Pull latest changes
cd /home/houston-ai/ask-houston-ai
git pull

# Rebuild and restart services
docker compose -f docker-compose.prod.yml up -d --build

# Remove old images
docker image prune -f
```

### 5. Monitor Resources

```bash
# View container resource usage
docker stats

# View disk usage
docker system df
```

---

## Troubleshooting

### Issue: Containers won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check specific service
docker compose -f docker-compose.prod.yml logs app

# Restart all services
docker compose -f docker-compose.prod.yml restart
```

### Issue: Database connection errors

```bash
# Verify postgres is running
docker compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker compose -f docker-compose.prod.yml logs postgres

# Verify credentials in .env file
cat .env | grep DB_

# Connect manually to verify
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d houston_311_db
```

### Issue: 502 Bad Gateway

```bash
# Check if backend is running
docker compose -f docker-compose.prod.yml ps app

# Check backend logs
docker compose -f docker-compose.prod.yml logs app

# Verify nginx configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Issue: Ollama connection errors

```bash
# Verify Ollama is running
sudo systemctl status ollama

# Check if mistral model is installed
ollama list

# Test Ollama API
curl http://localhost:11434/api/tags

# Restart Ollama
sudo systemctl restart ollama
```

### Issue: Out of disk space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old backups
rm ~/backups/*.sql.old
```

---

## Post-Deployment Checklist

- [ ] All environment variables are set correctly in `.env`
- [ ] Strong passwords are used for database users
- [ ] Firewall is configured (ports 80, 443 allowed; 5432, 11434 blocked externally)
- [ ] SSL/TLS certificates are installed (if using HTTPS)
- [ ] Health endpoint returns "healthy": `curl http://localhost/health`
- [ ] Application is accessible from browser
- [ ] Database backups are scheduled (cron job)
- [ ] Logs are being generated and accessible
- [ ] CORS is configured for your domain
- [ ] Ollama is running and accessible
- [ ] All containers are in "healthy" state

---

## Additional Security Recommendations

1. **Regular Updates**: Keep system and Docker images updated
   ```bash
   sudo apt update && sudo apt upgrade
   docker compose -f docker-compose.prod.yml pull
   ```

2. **Monitor Logs**: Set up log monitoring for security events
   ```bash
   # Failed validation attempts
   docker compose -f docker-compose.prod.yml logs app | grep "Security validation failed"
   ```

3. **Rate Limiting**: Nginx is configured with rate limiting. Adjust as needed in `nginx/nginx.conf`

4. **Database Backups**: Ensure automated backups are running and test restoration

5. **Monitoring**: Consider adding monitoring tools (Prometheus, Grafana, etc.)

6. **Secrets Management**: For enterprise deployment, use proper secrets management (HashiCorp Vault, AWS Secrets Manager, etc.)

---

## Support & Troubleshooting

If you encounter issues:

1. Check logs: `docker compose -f docker-compose.prod.yml logs -f`
2. Verify health: `curl http://localhost/health`
3. Review security testing guide: `docs/SECURITY_TESTING.md`
4. Check disk space: `df -h`
5. Verify all environment variables are set correctly

For additional help, check the main README.md and CLAUDE.md files.

---

## Rolling Back

If something goes wrong:

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Restore from backup (if needed)
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres houston_311_db < ~/backups/houston_311_YYYYMMDD.sql

# Checkout previous git commit
git log  # Find the commit hash
git checkout <commit-hash>

# Rebuild and start
docker compose -f docker-compose.prod.yml up -d --build
```
