# Infrastructure Setup Guide

This guide explains how to make your Resy system accessible from anywhere with password protection.

## Quick Start (Recommended)

### Option 1: Run on Current Server (Fastest)

If you want to use this existing AWS server:

```bash
# 1. Run the infrastructure setup
sudo bash setup-infrastructure.sh

# 2. That's it! The system will be available at your server's IP
```

**Access:**
- URL: `http://YOUR_SERVER_IP`
- Username: `admin`
- Password: (shown at end of setup, also saved in `.admin_password`)

---

### Option 2: Deploy to New VPS (DigitalOcean/Linode)

For a dedicated, clean deployment:

#### Step 1: Create VPS

**DigitalOcean:**
1. Sign up at digitalocean.com (use referral for $200 credit)
2. Create Droplet:
   - **OS:** Ubuntu 22.04 LTS
   - **Plan:** Basic, $6/month (1GB RAM, 1 CPU, 25GB SSD)
   - **Datacenter:** San Francisco or Los Angeles
   - **Authentication:** SSH key (recommended) or password

**Linode:**
1. Sign up at linode.com
2. Create Linode:
   - **Distribution:** Ubuntu 22.04 LTS
   - **Plan:** Nanode 1GB ($5/month)
   - **Region:** Fremont, CA or Los Angeles, CA

#### Step 2: Connect and Setup

```bash
# SSH into your new server
ssh root@YOUR_VPS_IP

# Update system
apt-get update && apt-get upgrade -y

# Install git
cd /home/ubuntu/.openclaw/workspace/resy-system

# Run setup
sudo bash setup-infrastructure.sh
```

#### Step 3: (Optional) Add Domain

If you have a domain:

```bash
# Point domain to VPS IP in your DNS settings
# Then run:
sudo DOMAIN=yourdomain.com bash setup-infrastructure.sh
```

This will automatically set up SSL with Let's Encrypt.

---

### Option 3: Docker Deployment

For maximum portability:

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Install Docker Compose
sudo apt-get install docker-compose-plugin

# 3. Build and run
docker-compose up -d

# 4. Create admin password
docker-compose exec nginx sh -c "echo -n 'admin:' > /etc/nginx/.htpasswd && openssl passwd -apr1 YOUR_PASSWORD >> /etc/nginx/.htpasswd"
```

---

## Security Features

All deployment options include:

| Feature | Description |
|---------|-------------|
| **Basic Auth** | Username/password required |
| **Firewall (UFW)** | Blocks all ports except 22, 80, 443 |
| **Fail2Ban** | Blocks brute force attempts |
| **Rate Limiting** | 10 requests/second per IP |
| **Security Headers** | XSS, clickjacking protection |
| **HTTPS** | SSL certificates (with domain) |
| **File Protection** | Blocks access to .json, .log, .py files |

---

## Management Commands

After setup, use these commands:

```bash
# Check status
./status.sh

# Restart services
./restart.sh

# View logs
sudo journalctl -u resy-system -f

# Update application
./update.sh

# View admin password
cat .admin_password
```

---

## Troubleshooting

### Can't access the site

```bash
# Check if services are running
sudo systemctl status resy-system
sudo systemctl status nginx

# Check firewall
sudo ufw status

# Check logs
sudo journalctl -u resy-system -n 50
```

### Forgot admin password

```bash
# Generate new password
NEW_PASS=$(openssl rand -base64 12)
echo -n "admin:" > /etc/nginx/.htpasswd-resy
openssl passwd -apr1 "$NEW_PASS" >> /etc/nginx/.htpasswd-resy
echo "New password: $NEW_PASS"
```

### Update SSL certificate

```bash
sudo certbot renew
```

---

## Cost Breakdown

| Option | Monthly Cost | Best For |
|--------|-------------|----------|
| Current AWS | $0 (already paid) | Quick setup, testing |
| DigitalOcean | $6 | Clean, dedicated server |
| Linode | $5 | Budget-friendly |
| AWS Lightsail | $5 | AWS ecosystem |

**Domain (optional):** $12-15/year

---

## Next Steps

1. **Choose your deployment option**
2. **Run the setup script**
3. **Save your admin password**
4. **Test access from your phone/computer**
5. **Share with Grace (optional)**

---

## Architecture

```
┌─────────────────┐
│   Your Device   │
│  (Phone/Laptop) │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Cloudflare/    │
│  DNS (optional) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Nginx         │
│   (Port 80/443) │
│   - Basic Auth  │
│   - Rate Limit  │
│   - SSL         │
└────────┬────────┘
         │ Proxy Pass
         ▼
┌─────────────────┐
│   Gunicorn      │
│   (Port 5000)   │
│   - Flask App   │
│   - 2-4 Workers │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Data Files    │
│   - restaurants │
│   - reservations│
│   - monitoring  │
└─────────────────┘
```

---

## Questions?

Run into issues? Check:
1. `logs/gunicorn-error.log` for application errors
2. `/var/log/nginx/error.log` for nginx errors
3. `sudo journalctl -u resy-system` for service logs
