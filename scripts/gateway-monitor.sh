#!/bin/bash
# Gateway Health Monitor - Restarts OpenClaw if Telegram bot is unresponsive

LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/gateway-monitor.log"
GATEWAY_PORT=18789
TELEGRAM_BOT_TOKEN_FILE="/home/ubuntu/.openclaw/credentials/telegram-bot-token"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if gateway process is running
check_gateway_process() {
    if pgrep -f "openclaw.*gateway" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if gateway port is listening
check_gateway_port() {
    if netstat -tlnp 2>/dev/null | grep -q ":$GATEWAY_PORT"; then
        return 0
    elif ss -tlnp 2>/dev/null | grep -q ":$GATEWAY_PORT"; then
        return 0
    else
        return 1
    fi
}

# Restart gateway
restart_gateway() {
    log "🔴 Gateway down - restarting..."
    
    # Kill any existing processes
    pkill -f "openclaw.*gateway" 2>/dev/null
    sleep 2
    
    # Start gateway with PM2 or directly
    if command -v pm2 &> /dev/null; then
        pm2 restart openclaw-gateway 2>/dev/null || pm2 start /usr/bin/openclaw --name openclaw-gateway -- gateway --port $GATEWAY_PORT
        pm2 save
    else
        nohup openclaw gateway --port $GATEWAY_PORT > /home/ubuntu/.openclaw/workspace/logs/gateway.log 2>&1 &
    fi
    
    sleep 5
    
    if check_gateway_process && check_gateway_port; then
        log "✅ Gateway restarted successfully"
        # Send alert email
        python3 /home/ubuntu/.openclaw/workspace/scripts/send_email.py \
            --to "[REDACTED]" \
            --subject "🔄 OpenClaw Gateway Restarted" \
            --body "<h2>Gateway Auto-Restart</h2><p>The OpenClaw gateway was detected as down and has been automatically restarted.</p><p>Time: $(date)</p><p>Port: $GATEWAY_PORT</p>" \
            --html 2>/dev/null || true
    else
        log "🔴 Gateway restart FAILED"
    fi
}

# Main check
log "Checking gateway health..."

if ! check_gateway_process; then
    log "🔴 Gateway process not found"
    restart_gateway
elif ! check_gateway_port; then
    log "🔴 Gateway port $GATEWAY_PORT not listening"
    restart_gateway
else
    log "✅ Gateway healthy"
fi
