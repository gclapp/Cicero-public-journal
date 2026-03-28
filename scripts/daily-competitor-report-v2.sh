#!/bin/bash
# daily-competitor-report-v2.sh - Enhanced competitive intelligence
# Run twice daily: 7 AM and 2 PM PT

set -e

# Export API keys for scripts
export BRAVE_API_KEY="BSAQvzsdCTmv48KVZCYZxO2Uc2-Wgbf"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$WORKSPACE_DIR/logs/competitor-v2-cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting competitive intelligence v2..." >> "$LOG_FILE"

# Step 1: Run enhanced RSS + web search monitoring
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: RSS + Web search..." >> "$LOG_FILE"
python3 "$SCRIPT_DIR/competitor_intelligence_v2.py" >> "$LOG_FILE" 2>&1 || true

# Step 2: Run LinkedIn + job change monitoring
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: LinkedIn + job changes..." >> "$LOG_FILE"
python3 "$SCRIPT_DIR/linkedin_monitor.py" >> "$LOG_FILE" 2>&1 || true

# Step 3: Generate email report
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Generating email..." >> "$LOG_FILE"
python3 "$SCRIPT_DIR/competitor_email_v2.py" >> "$LOG_FILE" 2>&1 || true

# Step 4: Send email if articles found
ARTICLES_FILE="$WORKSPACE_DIR/config/competitor-articles-v2.json"
LINKEDIN_FILE="$WORKSPACE_DIR/config/linkedin-updates.json"
EMAIL_FILE="$WORKSPACE_DIR/config/competitor-email-v2.html"

# Check if there are recent articles (last 6 hours)
if [ -f "$ARTICLES_FILE" ] || [ -f "$LINKEDIN_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sending competitive intelligence email..." >> "$LOG_FILE"
    
    python3 "$SCRIPT_DIR/send_email.py" \
        --to "[REDACTED],geoffrey.clapp@progyny.com" \
        --cc "steven.leist@progyny.com" \
        --subject "Competitive Intelligence Report - $(date '+%A, %B %d')" \
        --body-file "$EMAIL_FILE" \
        --html >> "$LOG_FILE" 2>&1 || true
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Email sent" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No new articles to send" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Complete" >> "$LOG_FILE"
