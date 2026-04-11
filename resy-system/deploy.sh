#!/bin/bash
# Resy System Deployment Script
# Sets up the application for production use with nginx and gunicorn

set -e

echo "🚀 Resy System Deployment"
echo "=========================="

# Configuration
APP_DIR="/home/ubuntu/.openclaw/workspace/resy-system"
APP_NAME="resy-system"
APP_PORT=5000
DOMAIN="${DOMAIN:-localhost}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for some operations
check_root() {
    if [[ $EUID -eq 0 ]]; then
        IS_ROOT=true
    else
        IS_ROOT=false
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        if $IS_ROOT; then
            apt-get update
            apt-get install -y python3-pip python3-venv nginx
        else
            log_warn "Not running as root. Skipping system package installation."
            log_warn "Please run: sudo apt-get update && sudo apt-get install -y python3-pip python3-venv nginx"
        fi
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        if $IS_ROOT; then
            yum install -y python3-pip python3-venv nginx
        else
            log_warn "Not running as root. Skipping system package installation."
        fi
    else
        log_warn "Unknown package manager. Please install python3-pip, python3-venv, and nginx manually."
    fi
}

# Setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    cd "$APP_DIR"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Created virtual environment"
    fi
    
    source venv/bin/activate
    
    # Install/upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install flask gunicorn
    
    log_info "Virtual environment ready"
}

# Create gunicorn configuration
create_gunicorn_config() {
    log_info "Creating Gunicorn configuration..."
    
    cat > "$APP_DIR/gunicorn.conf.py" << 'EOF'
# Gunicorn configuration
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
keepalive = 2
timeout = 30
graceful_timeout = 30

# Logging
accesslog = "/home/ubuntu/.openclaw/workspace/resy-system/logs/gunicorn-access.log"
errorlog = "/home/ubuntu/.openclaw/workspace/resy-system/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "resy-system"

# Server mechanics
daemon = False
pidfile = "/home/ubuntu/.openclaw/workspace/resy-system/resy-system.pid"

# SSL (handled by nginx)
forwarded_allow_ips = "127.0.0.1"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
EOF

    log_info "Gunicorn configuration created"
}

# Create systemd service file
create_systemd_service() {
    log_info "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/resy-system.service"
    
    if $IS_ROOT; then
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Resy Restaurant Reservation System
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        log_info "Systemd service created"
    else
        log_warn "Not running as root. Creating user service instead..."
        
        mkdir -p ~/.config/systemd/user
        
        cat > ~/.config/systemd/user/resy-system.service << EOF
[Unit]
Description=Resy Restaurant Reservation System
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$APP_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

        log_info "User systemd service created"
        log_info "To start: systemctl --user start resy-system"
        log_info "To enable: systemctl --user enable resy-system"
    fi
}

# Create nginx configuration
create_nginx_config() {
    log_info "Creating Nginx configuration..."
    
    NGINX_CONF="/etc/nginx/sites-available/resy-system"
    
    if $IS_ROOT; then
        cat > "$NGINX_CONF" << 'EOF'
server {
    listen 80;
    server_name _;  # Accept any hostname
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Client body size (for file uploads if needed)
    client_max_body_size 10M;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {
        # Basic authentication
        auth_basic "Resy Manager - Authorized Access Only";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (if we add them later)
    location /static {
        alias /home/ubuntu/.openclaw/workspace/resy-system/static;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint (no auth required)
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }
}
EOF

        # Enable site
        ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/resy-system
        
        # Remove default site if it exists
        rm -f /etc/nginx/sites-enabled/default
        
        # Test nginx config
        nginx -t
        
        log_info "Nginx configuration created"
    else
        log_warn "Not running as root. Skipping nginx configuration."
        log_warn "To configure nginx, run this script with sudo."
    fi
}

# Create basic auth credentials
create_basic_auth() {
    log_info "Setting up basic authentication..."
    
    HTPASSWD_FILE="/etc/nginx/.htpasswd"
    
    if $IS_ROOT; then
        # Generate random password if not set
        if [ -z "$ADMIN_PASSWORD" ]; then
            ADMIN_PASSWORD=$(openssl rand -base64 12)
            log_info "Generated admin password: $ADMIN_PASSWORD"
            log_info "Please save this password!"
        fi
        
        # Create htpasswd file
        echo -n "admin:" > "$HTPASSWD_FILE"
        openssl passwd -apr1 "$ADMIN_PASSWORD" >> "$HTPASSWD_FILE"
        
        chmod 640 "$HTPASSWD_FILE"
        chown root:www-data "$HTPASSWD_FILE"
        
        log_info "Basic authentication configured"
        log_info "Username: admin"
        log_info "Password: $ADMIN_PASSWORD"
    else
        log_warn "Not running as root. Skipping basic auth setup."
    fi
}

# Create logs directory
setup_logs() {
    log_info "Setting up log directories..."
    
    mkdir -p "$APP_DIR/logs"
    touch "$APP_DIR/logs/gunicorn-access.log"
    touch "$APP_DIR/logs/gunicorn-error.log"
    
    log_info "Log directories ready"
}

# Create start/stop scripts
create_control_scripts() {
    log_info "Creating control scripts..."
    
    # Start script
    cat > "$APP_DIR/start-production.sh" << 'EOF'
#!/bin/bash
# Start Resy System in production mode

APP_DIR="/home/ubuntu/.openclaw/workspace/resy-system"
cd "$APP_DIR"

# Check if running as systemd service
if systemctl is-active --quiet resy-system 2>/dev/null; then
    echo "Service is already running via systemd"
    echo "Use: sudo systemctl restart resy-system"
    exit 0
fi

# Check if running as user service
if systemctl --user is-active --quiet resy-system 2>/dev/null; then
    echo "Service is already running via user systemd"
    echo "Use: systemctl --user restart resy-system"
    exit 0
fi

# Start with gunicorn directly
echo "Starting Resy System..."
source venv/bin/activate
exec gunicorn -c gunicorn.conf.py app:app
EOF

    # Stop script
    cat > "$APP_DIR/stop-production.sh" << 'EOF'
#!/bin/bash
# Stop Resy System

# Try systemd first
if systemctl is-active --quiet resy-system 2>/dev/null; then
    echo "Stopping systemd service..."
    sudo systemctl stop resy-system
    exit 0
fi

# Try user systemd
if systemctl --user is-active --quiet resy-system 2>/dev/null; then
    echo "Stopping user systemd service..."
    systemctl --user stop resy-system
    exit 0
fi

# Try to find and kill process
PIDFILE="/home/ubuntu/.openclaw/workspace/resy-system/resy-system.pid"
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping process $PID..."
        kill "$PID"
        rm -f "$PIDFILE"
        echo "Stopped"
        exit 0
    fi
fi

echo "Resy System is not running"
EOF

    # Status script
    cat > "$APP_DIR/status-production.sh" << 'EOF'
#!/bin/bash
# Check Resy System status

echo "Resy System Status"
echo "=================="

# Check systemd service
if systemctl is-active --quiet resy-system 2>/dev/null; then
    echo "✅ Systemd service: RUNNING"
    systemctl status resy-system --no-pager | head -5
elif systemctl --user is-active --quiet resy-system 2>/dev/null; then
    echo "✅ User systemd service: RUNNING"
    systemctl --user status resy-system --no-pager | head -5
else
    echo "❌ Service: NOT RUNNING"
fi

# Check port
echo ""
echo "Port 5000:"
if netstat -tuln 2>/dev/null | grep -q ":5000"; then
    echo "✅ Listening"
else
    echo "❌ Not listening"
fi

# Check nginx
echo ""
echo "Nginx:"
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Recent logs
echo ""
echo "Recent logs:"
tail -n 5 /home/ubuntu/.openclaw/workspace/resy-system/logs/gunicorn-error.log 2>/dev/null || echo "No logs yet"
EOF

    chmod +x "$APP_DIR/start-production.sh"
    chmod +x "$APP_DIR/stop-production.sh"
    chmod +x "$APP_DIR/status-production.sh"
    
    log_info "Control scripts created"
}

# Create health check endpoint
create_health_endpoint() {
    log_info "Adding health check endpoint..."
    
    # Add health endpoint to app.py if not exists
    if ! grep -q "@app.route('/health')" "$APP_DIR/app.py"; then
        cat >> "$APP_DIR/app.py" << 'EOF'

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    from monitoring import get_system_health
    
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
        log_info "Health endpoint added to app.py"
    else
        log_info "Health endpoint already exists"
    fi
}

# Main deployment function
deploy() {
    log_info "Starting deployment..."
    
    check_root
    
    if $IS_ROOT; then
        log_info "Running as root - will configure system services"
    else
        log_warn "Running as regular user - some features limited"
    fi
    
    install_dependencies
    setup_venv
    setup_logs
    create_gunicorn_config
    create_systemd_service
    create_nginx_config
    create_basic_auth
    create_control_scripts
    create_health_endpoint
    
    echo ""
    echo "========================================"
    log_info "Deployment complete!"
    echo "========================================"
    echo ""
    
    if $IS_ROOT; then
        echo "To start the service:"
        echo "  sudo systemctl start resy-system"
        echo "  sudo systemctl enable resy-system"
        echo ""
        echo "To start nginx:"
        echo "  sudo systemctl start nginx"
        echo "  sudo systemctl enable nginx"
        echo ""
        echo "Access the application at:"
        echo "  http://$(hostname -I | awk '{print $1}')"
        echo ""
        echo "Login credentials:"
        echo "  Username: admin"
        if [ -n "$ADMIN_PASSWORD" ]; then
            echo "  Password: $ADMIN_PASSWORD"
        else
            echo "  Password: (set via ADMIN_PASSWORD environment variable)"
        fi
    else
        echo "To start the service:"
        echo "  ./start-production.sh"
        echo ""
        echo "Or use user systemd:"
        echo "  systemctl --user start resy-system"
        echo ""
        echo "Access the application at:"
        echo "  http://localhost:5000"
    fi
    echo ""
    echo "Status check:"
    echo "  ./status-production.sh"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Resy System Deployment Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --user         Run in user mode (no system services)"
        echo ""
        echo "Environment variables:"
        echo "  ADMIN_PASSWORD  Password for basic auth (auto-generated if not set)"
        echo "  DOMAIN          Domain name (default: localhost)"
        echo ""
        exit 0
        ;;
    --user)
        IS_ROOT=false
        deploy
        ;;
    *)
        deploy
        ;;
esac
