#!/bin/bash
# daily-competitor-report-v3.sh - Overhauled competitive intelligence
# Run twice daily: 7 AM and 2 PM PT

set -e

# Source centralized API keys
source "$HOME/.openclaw/workspace/config/api-keys.env" 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$WORKSPACE_DIR/logs/competitor-v3-cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting competitive intelligence v3..." >> "$LOG_FILE"

# Step 1: Run enhanced RSS + web search monitoring
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: RSS + Web search..." >> "$LOG_FILE"
python3 "$SCRIPT_DIR/competitor_intelligence_v3.py" >> "$LOG_FILE" 2>&1 || true

# Step 2: Run LinkedIn + job change monitoring
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: LinkedIn + job changes..." >> "$LOG_FILE"
python3 "$SCRIPT_DIR/linkedin_monitor.py" >> "$LOG_FILE" 2>&1 || true

# Step 3: Generate email report
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Generating email..." >> "$LOG_FILE"
python3 "$SCRIPT_DIR/competitor_email_v3.py" >> "$LOG_FILE" 2>&1 || true

# Step 4: Send email if articles found
ARTICLES_FILE="$WORKSPACE_DIR/config/competitor-articles-v3.json"
EMAIL_FILE="$WORKSPACE_DIR/config/competitor-email-v3.html"

# Check if email file exists and has content
if [ -f "$EMAIL_FILE" ]; then
    # Check if there are recent articles (last 30 days)
    EMAIL_SIZE=$(stat -f%z "$EMAIL_FILE" 2>/dev/null || stat -c%s "$EMAIL_FILE" 2>/dev/null || echo "0")
    
    if [ "$EMAIL_SIZE" -gt 1000 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sending competitive intelligence email..." >> "$LOG_FILE"
        
        python3 "$SCRIPT_DIR/send_email.py" \
            --to "[REDACTED],geoffrey.clapp@progyny.com" \
            --cc "steven.leist@progyny.com" \
            --subject "Competitive Intelligence Report - $(date '+%A, %B %d')" \
            --body-file "$EMAIL_FILE" \
            --html >> "$LOG_FILE" 2>&1 || true
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Email sent" >> "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Email file too small, skipping send" >> "$LOG_FILE"
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No email file generated" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Complete" >> "$LOG_FILE"