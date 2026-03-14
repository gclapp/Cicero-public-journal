# AWS Server Setup Guide for Geoff & Cicero

## Overview
This guide will walk you through setting up a private server on AWS to host all your projects (Watch Hunt, Health Dashboard, etc.) with a proper database backend.

**Estimated Time:** 30-45 minutes  
**Estimated Cost:** $8-15/month

---

## Step 1: Create EC2 Instance

1. **Log into AWS Console:** https://aws.amazon.com/console
2. **Navigate to EC2** (search "EC2" in the top bar)
3. **Click "Launch Instance"**
4. **Configure Instance:**
   - **Name:** cicero-server
   - **OS:** Ubuntu Server 22.04 LTS (free tier eligible)
   - **Instance Type:** t3.micro ($8.50/month) or t3.small ($16/month)
   - **Key Pair:** Create new key pair (RSA, .pem format)
     - Download and SAVE the .pem file securely
   - **Network Settings:**
     - Create security group
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow HTTPS (port 443) from anywhere
   - **Storage:** 20 GB gp2 SSD
5. **Click "Launch Instance"**

**Save These Details:**
- Instance ID
- Public IPv4 address (e.g., 54.123.45.67)
- Key pair file (.pem)

---

## Step 2: Connect to Your Server

### Option A: Terminal (Mac/Linux)
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR-SERVER-IP
```

### Option B: Windows (PuTTY)
1. Convert .pem to .ppk using PuTTYgen
2. Use PuTTY with the .ppk file

### Option C: AWS Console
1. Select your instance in EC2 dashboard
2. Click "Connect"
3. Use EC2 Instance Connect (browser-based)

---

## Step 3: Run Server Setup Script

Once connected to your server, run these commands:

```bash
# Download the setup script
curl -o setup.sh https://raw.githubusercontent.com/gclapp/cicero-backup/main/server-setup.sh

# Make it executable
chmod +x setup.sh

# Run the setup (takes 10-15 minutes)
./setup.sh
```

This will install:
- Nginx (web server)
- PostgreSQL (database)
- Python 3.11 + Flask
- Node.js
- Redis
- SSL certificates
- All project dependencies

---

## Step 4: Configure Domain (Optional but Recommended)

### Register Domain:
1. Go to Namecheap, Google Domains, or Cloudflare
2. Register: geoffandcicero.com (or your choice)
3. In DNS settings, create A record:
   - Host: @
   - Value: YOUR-SERVER-IP
   - TTL: Auto

### Or Use AWS Route 53:
1. Go to Route 53 in AWS console
2. Register domain ($12-15/year)
3. Create hosted zone
4. Point A record to your EC2 IP

---

## Step 5: Deploy Applications

### Clone Repository:
```bash
cd /var/www/cicero
git clone https://github.com/gclapp/cicero-backup.git .
```

### Set Environment Variables:
```bash
export DATABASE_URL="postgresql://cicero:YOUR_PASSWORD@localhost/cicero_db"
export SECRET_KEY="your-secret-key-here"
export REDIS_URL="redis://localhost:6379/0"
```

### Initialize Database:
```bash
cd /var/www/cicero
python3 -c "from backend.app import app, db; app.app_context().db.create_all()"
```

### Start Services:
```bash
sudo systemctl start cicero-api
sudo systemctl start cicero-worker
sudo systemctl start cicero-beat
```

---

## Step 6: Configure SSL (HTTPS)

```bash
sudo certbot --nginx -d geoffandcicero.com -d www.geoffandcicero.com
```

Follow prompts to complete SSL setup.

---

## Step 7: Verify Everything Works

Test these URLs:
- http://YOUR-SERVER-IP (should show Nginx welcome)
- http://YOUR-SERVER-IP/api/health (should return JSON)

Once domain is configured:
- https://geoffandcicero.com
- https://geoffandcicero.com/api/health

---

## What's Included

### Projects:
1. **Watch Hunt** - Full database backend, dynamic searches
2. **Health Dashboard** - Apple Health integration
3. **Competitive Intel** - Reports and alerts
4. **Admin Panel** - Manage everything

### Features:
- PostgreSQL database for all data
- Automated watch searches (twice daily)
- User authentication
- Image hosting and scraping
- SSL/HTTPS security
- Automated backups

---

## Next Steps After Setup

1. **Migrate existing data** from GitHub Pages to database
2. **Set up automated backups** to S3
3. **Configure email notifications** for new watch listings
4. **Add more search sources** (WatchRecon, Reddit, etc.)

---

## Support

If you get stuck on any step, send me:
1. Which step you're on
2. What error message you see (if any)
3. Your server IP (if comfortable sharing)

I'll help you troubleshoot.

---

## Cost Breakdown

| Service | Monthly Cost |
|---------|--------------|
| EC2 t3.micro | $8.50 |
| Data transfer | ~$1-2 |
| Domain (optional) | $1/month |
| **Total** | **~$10-12/month** |

---

Ready to start? Begin with Step 1 and let me know when you have your EC2 instance running!

🏛️ Cicero
