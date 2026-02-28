#!/bin/bash
# watch-hunt-cron.sh - Automated watch search and dashboard update
# Runs twice daily via cron

set -e

REPO_DIR="$HOME/.openclaw/workspace/dashboard"
LOG_FILE="$HOME/.openclaw/workspace/logs/watch-hunt.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$DATE] Starting watch hunt update..." >> "$LOG_FILE"

cd "$REPO_DIR"

# Pull latest changes first (in case of manual updates)
git pull origin main >> "$LOG_FILE" 2>&1 || true

# Run the Python watch search script
python3 "$HOME/.openclaw/workspace/scripts/watch_search.py" >> "$LOG_FILE" 2>&1

# Check if there are changes
if git diff --quiet watch-data.json; then
    echo "[$DATE] No new watches found." >> "$LOG_FILE"
else
    # Stage, commit, and push
    git add watch-data.json
    git commit -m "Auto-update: New watch listings found at $DATE" >> "$LOG_FILE" 2>&1
    git push origin main >> "$LOG_FILE" 2>&1
    echo "[$DATE] Pushed updates to GitHub." >> "$LOG_FILE"
    
    # Notify Geoff via Telegram
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=🏛️ New watch listings found! Check your dashboard: https://gclapp.github.io/geoff-watch-hunt/" \
        >> "$LOG_FILE" 2>&1 || true
fi

echo "[$DATE] Update complete." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"