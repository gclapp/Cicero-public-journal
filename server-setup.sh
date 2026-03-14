#!/bin/bash
# DigitalOcean Server Setup Script
# Run this on a fresh Ubuntu 22.04 droplet

set -e

echo "🏛️ Setting up Geoff & Cicero Private Server"
echo "============================================"

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install essential packages
echo "🔧 Installing essentials..."
apt-get install -y \
    nginx \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    redis-server \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    htop \
    ufw

# Setup firewall
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Setup PostgreSQL
echo "🐘 Setting up PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER cicero WITH PASSWORD 'secure_password_here';
CREATE DATABASE cicero_db OWNER cicero;
GRANT ALL PRIVILEGES ON DATABASE cicero_db TO cicero;
\q
EOF

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /var/www/cicero
chown -R $USER:$USER /var/www/cicero

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
cd /var/www/cicero
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install \
    flask \
    flask-sqlalchemy \
    flask-login \
    flask-cors \
    gunicorn \
    psycopg2-binary \
    redis \
    celery \
    requests \
    beautifulsoup4 \
    scrapling \
    playwright

# Install Playwright browsers
playwright install chromium

# Setup Node.js for frontend
echo "📦 Setting up Node.js..."
cd /var/www/cicero
npm init -y
npm install -g pm2

# Create directory structure
echo "📂 Creating project structure..."
mkdir -p /var/www/cicero/{backend,frontend,database,logs,scripts}
mkdir -p /var/www/cicero/backend/{api,models,services,tasks}
mkdir -p /var/www/cicero/frontend/{public,src}
mkdir -p /var/www/cicero/database/migrations

# Setup Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/cicero << 'NGINX_EOF'
server {
    listen 80;
    server_name geoffandcicero.com www.geoffandcicero.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /var/www/cicero/frontend/build/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /api {
        proxy_pass http://127.0.0.1:5000/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/cicero /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
systemctl enable nginx

# Setup SSL (run after DNS points to server)
echo "🔒 SSL will be configured after DNS setup"
echo "Run: certbot --nginx -d geoffandcicero.com -d www.geoffandcicero.com"

# Create systemd service for Flask app
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/cicero-api.service << 'SERVICE_EOF'
[Unit]
Description=Cicero API Server
After=network.target postgresql.service redis.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/cicero/backend
Environment="PATH=/var/www/cicero/venv/bin"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
Environment="DATABASE_URL=postgresql://cicero:secure_password_here@localhost/cicero_db"
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/var/www/cicero/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable cicero-api

# Setup Celery for background tasks
cat > /etc/systemd/system/cicero-worker.service << 'WORKER_EOF'
[Unit]
Description=Cicero Background Worker
After=network.target postgresql.service redis.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/cicero/backend
Environment="PATH=/var/www/cicero/venv/bin"
Environment="DATABASE_URL=postgresql://cicero:secure_password_here@localhost/cicero_db"
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/var/www/cicero/venv/bin/celery -A tasks worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
WORKER_EOF

systemctl enable cicero-worker

# Setup Celery beat for scheduled tasks
cat > /etc/systemd/system/cicero-beat.service << 'BEAT_EOF'
[Unit]
Description=Cicero Scheduled Task Runner
After=network.target postgresql.service redis.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/cicero/backend
Environment="PATH=/var/www/cicero/venv/bin"
Environment="DATABASE_URL=postgresql://cicero:secure_password_here@localhost/cicero_db"
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/var/www/cicero/venv/bin/celery -A tasks beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
BEAT_EOF

systemctl enable cicero-beat

echo ""
echo "============================================"
echo "✅ Server setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Point DNS for geoffandcicero.com to this server IP"
echo "2. Run: certbot --nginx -d geoffandcicero.com"
echo "3. Deploy application code to /var/www/cicero/"
echo "4. Start services: systemctl start cicero-api cicero-worker cicero-beat"
echo ""
echo "Server IP: $(curl -s ifconfig.me)"
echo ""
