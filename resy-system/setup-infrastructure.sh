#!/bin/bash
# Infrastructure Setup Script for Resy System
# This script sets up the complete infrastructure for external access

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_DIR="/home/ubuntu/.openclaw/workspace/resy-system"
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-[REDACTED]}"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Resy System Infrastructure Setup                   ║"
echo "║         Secure External Access Configuration               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking Prerequisites"
    
    # Check if running on Ubuntu/Debian
    if ! command -v apt-get &> /dev/null; then
        log_error "This script requires Ubuntu/Debian system"
        exit 1
    fi
    
    # Check if root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Install required packages
install_packages() {
    log_step "Installing Required Packages"
    
    apt-get update
    
    # Core packages
    apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        nginx \
        apache2-utils \
        curl \
        wget \
        git \
        ufw \
        fail2ban \
        certbot \
        python3-certbot-nginx \
        net-tools
    
    log_info "Packages installed"
}

# Setup firewall
setup_firewall() {
    log_step "Configuring Firewall"
    
    # Reset UFW
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (important!)
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    echo "y" | ufw enable
    
    log_info "Firewall configured"
    ufw status
}

# Setup fail2ban
setup_fail2ban() {
    log_step "Configuring Fail2Ban"
    
    # Create custom jail for nginx
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

    # Restart fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log_info "Fail2Ban configured"
}

# Create application user
create_app_user() {
    log_step "Creating Application User"
    
    if ! id -u resyapp &>/dev/null; then
        useradd -m -s /bin/bash -d /home/resyapp resyapp
        usermod -aG www-data resyapp
        log_info "Created user: resyapp"
    else
        log_info "User resyapp already exists"
    fi
    
    # Set permissions
    chown -R resyapp:resyapp "$APP_DIR"
    chmod 750 "$APP_DIR"
}

# Setup Python environment
setup_python() {
    log_step "Setting up Python Environment"
    
    cd "$APP_DIR"
    
    # Create virtual environment
    sudo -u resyapp python3 -m venv venv
    
    # Install dependencies
    sudo -u resyapp "$APP_DIR/venv/bin/pip" install --upgrade pip
    sudo -u resyapp "$APP_DIR/venv/bin/pip" install flask gunicorn
    
    log_info "Python environment ready"
}

# Create systemd service
create_service() {
    log_step "Creating Systemd Service"
    
    cat > /etc/systemd/system/resy-system.service << EOF
[Unit]
Description=Resy Restaurant Reservation System
After=network.target

[Service]
Type=simple
User=resyapp
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=resy-system

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable resy-system
    
    log_info "Systemd service created"
}

# Create gunicorn config
create_gunicorn_config() {
    log_step "Creating Gunicorn Configuration"
    
    cat > "$APP_DIR/gunicorn.conf.py" << 'EOF'
import os
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/home/ubuntu/.openclaw/workspace/resy-system/logs/gunicorn-access.log"
errorlog = "/home/ubuntu/.openclaw/workspace/resy-system/logs/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "resy-system"

# Server mechanics
daemon = False
pidfile = "/home/ubuntu/.openclaw/workspace/resy-system/resy-system.pid"

# SSL
forwarded_allow_ips = "127.0.0.1"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Preload app for better memory usage
preload_app = True
EOF

    chown resyapp:resyapp "$APP_DIR/gunicorn.conf.py"
    
    # Create logs directory
    mkdir -p "$APP_DIR/logs"
    chown -R resyapp:resyapp "$APP_DIR/logs"
    
    log_info "Gunicorn configuration created"
}

# Create nginx configuration
create_nginx_config() {
    log_step "Creating Nginx Configuration"
    
    # Generate password
    ADMIN_PASSWORD=$(openssl rand -base64 16)
    
    # Create htpasswd
    echo -n "admin:" > /etc/nginx/.htpasswd-resy
    openssl passwd -apr1 "$ADMIN_PASSWORD" >> /etc/nginx/.htpasswd-resy
    chmod 640 /etc/nginx/.htpasswd-resy
    chown root:www-data /etc/nginx/.htpasswd-resy
    
    # Store password for later
    echo "$ADMIN_PASSWORD" > "$APP_DIR/.admin_password"
    chmod 600 "$APP_DIR/.admin_password"
    chown resyapp:resyapp "$APP_DIR/.admin_password"
    
    cat > /etc/nginx/sites-available/resy-system << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=resy_limit:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=resy_conn:10m;

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    
    # Hide nginx version
    server_tokens off;
    
    # Client body size
    client_max_body_size 10M;
    
    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;
    
    # Rate limiting
    limit_req zone=resy_limit burst=20 nodelay;
    limit_conn resy_conn 10;
    
    location / {
        # Basic authentication
        auth_basic "Resy Manager - Authorized Access Only";
        auth_basic_user_file /etc/nginx/.htpasswd-resy;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check (no auth)
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
        allow all;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(json|log|conf|py)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

    # Enable site
    rm -f /etc/nginx/sites-enabled/default
    ln -sf /etc/nginx/sites-available/resy-system /etc/nginx/sites-enabled/resy-system
    
    # Test nginx config
    nginx -t
    
    systemctl restart nginx
    systemctl enable nginx
    
    log_info "Nginx configured"
    log_info "Admin password saved to: $APP_DIR/.admin_password"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log_step "Setting up SSL with Let's Encrypt"
    
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
        log_info "Obtaining SSL certificate for $DOMAIN"
        
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"
        
        # Auto-renewal is set up by certbot
        log_info "SSL certificate installed"
    else
        log_warn "No domain specified. Skipping SSL setup."
        log_warn "To add SSL later, run: certbot --nginx -d yourdomain.com"
    fi
}

# Create management scripts
create_management_scripts() {
    log_step "Creating Management Scripts"
    
    # Status script
    cat > "$APP_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "Resy System Status"
echo "=================="
echo ""

# Service status
echo "Services:"
if systemctl is-active --quiet resy-system; then
    echo "  ✅ resy-system: RUNNING"
else
    echo "  ❌ resy-system: STOPPED"
fi

if systemctl is-active --quiet nginx; then
    echo "  ✅ nginx: RUNNING"
else
    echo "  ❌ nginx: STOPPED"
fi

echo ""
echo "Recent logs:"
journalctl -u resy-system --no-pager -n 5 2>/dev/null || tail -n 5 /home/ubuntu/.openclaw/workspace/resy-system/logs/gunicorn-error.log 2>/dev/null || echo "No logs available"

echo ""
echo "System resources:"
free -h | grep "Mem:"
df -h / | tail -1
EOF

    # Restart script
    cat > "$APP_DIR/restart.sh" << 'EOF'
#!/bin/bash
echo "Restarting Resy System..."
sudo systemctl restart resy-system
sudo systemctl restart nginx
echo "Done!"
EOF

    # Update script
    cat > "$APP_DIR/update.sh" << 'EOF'
#!/bin/bash
echo "Updating Resy System..."
cd /home/ubuntu/.openclaw/workspace/resy-system
git pull 2>/dev/null || echo "Not a git repository"
sudo systemctl restart resy-system
echo "Update complete!"
EOF

    chmod +x "$APP_DIR/status.sh" "$APP_DIR/restart.sh" "$APP_DIR/update.sh"
    chown resyapp:resyapp "$APP_DIR/status.sh" "$APP_DIR/restart.sh" "$APP_DIR/update.sh"
    
    log_info "Management scripts created"
}

# Create health check endpoint
create_health_endpoint() {
    log_step "Adding Health Check Endpoint"
    
    # Check if health endpoint exists
    if ! grep -q "@app.route('/health')" "$APP_DIR/app.py"; then
        cat >> "$APP_DIR/app.py" << 'EOF'

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    from monitoring import get_system_health
    from datetime import datetime
    
    try:
        health = get_system_health()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'last_scan': health.get('last_scan_time'),
            'last_booking': health.get('last_booking_time'),
            'total_bookings': health.get('total_bookings', 0)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
EOF
        log_info "Health endpoint added"
    else
        log_info "Health endpoint already exists"
    fi
    
    chown resyapp:resyapp "$APP_DIR/app.py"
}

# Start services
start_services() {
    log_step "Starting Services"
    
    systemctl start resy-system
    systemctl start nginx
    
    # Wait a moment for services to start
    sleep 2
    
    # Check if services are running
    if systemctl is-active --quiet resy-system; then
        log_info "Resy System is running"
    else
        log_error "Resy System failed to start"
        journalctl -u resy-system --no-pager -n 20
        exit 1
    fi
    
    if systemctl is-active --quiet nginx; then
        log_info "Nginx is running"
    else
        log_error "Nginx failed to start"
        exit 1
    fi
}

# Display summary
show_summary() {
    log_step "Setup Complete!"
    
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    ADMIN_PASS=$(cat "$APP_DIR/.admin_password" 2>/dev/null || echo "unknown")
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  🎉 Resy System is now running!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Access Information:"
    echo "  📍 Local:    http://localhost"
    echo "  📍 Network:  http://$IP_ADDRESS"
    if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
        echo "  📍 Domain:   https://$DOMAIN"
    fi
    echo ""
    echo "Login Credentials:"
    echo "  👤 Username: admin"
    echo "  🔑 Password: $ADMIN_PASS"
    echo ""
    echo "Management Commands:"
    echo "  ./status.sh    - Check system status"
    echo "  ./restart.sh   - Restart services"
    echo "  ./update.sh    - Update application"
    echo ""
    echo "Systemd Commands:"
    echo "  sudo systemctl status resy-system"
    echo "  sudo systemctl restart resy-system"
    echo "  sudo journalctl -u resy-system -f"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Save your admin password!${NC}"
    echo -e "${YELLOW}   It's stored in: $APP_DIR/.admin_password${NC}"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main setup function
main() {
    check_prerequisites
    install_packages
    setup_firewall
    setup_fail2ban
    create_app_user
    setup_python
    create_gunicorn_config
    create_service
    create_nginx_config
    setup_ssl
    create_management_scripts
    create_health_endpoint
    start_services
    show_summary
}

# Handle arguments
case "${1:-}" in
    --help|-h)
        echo "Resy System Infrastructure Setup"
        echo ""
        echo "Usage: sudo $0 [options]"
        echo ""
        echo "Environment Variables:"
        echo "  DOMAIN    - Your domain name (optional)"
        echo "  EMAIL     - Email for SSL certificates (default: [REDACTED])"
        echo ""
        echo "Examples:"
        echo "  sudo $0"
        echo "  sudo DOMAIN=resy.yourdomain.com $0"
        echo ""
        exit 0
        ;;
    *)
        main
        ;;
esac
