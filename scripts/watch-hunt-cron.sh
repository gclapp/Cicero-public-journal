#!/bin/bash
# watch-hunt-cron.sh - Automated watch search and dashboard update
# Runs twice daily via cron

set -e

REPO_DIR="$HOME/.openclaw/workspace/dashboard"
LOG_FILE="$HOME/.openclaw/workspace/logs/watch-hunt.log"
GITHUB_TOKEN_FILE="$HOME/.openclaw/credentials/github-token.txt"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$DATE] Starting watch hunt update..." >> "$LOG_FILE"

setup_git_auth() {
    if [ ! -r "$GITHUB_TOKEN_FILE" ]; then
        echo "[$DATE] GitHub token file not readable: $GITHUB_TOKEN_FILE" >> "$LOG_FILE"
        return 1
    fi

    GIT_ASKPASS_FILE=$(mktemp)
    chmod 700 "$GIT_ASKPASS_FILE"
    cat > "$GIT_ASKPASS_FILE" <<'EOF'
#!/bin/sh
case "$1" in
    *Username*) echo "x-access-token" ;;
    *Password*) cat "$HOME/.openclaw/credentials/github-token.txt" ;;
    *) echo "" ;;
esac
EOF
    export GIT_ASKPASS="$GIT_ASKPASS_FILE"
    export GIT_TERMINAL_PROMPT=0
    trap 'rm -f "$GIT_ASKPASS_FILE"' EXIT
}

cd "$REPO_DIR"
setup_git_auth || exit 1

# Pull latest changes first (in case of manual updates)
git pull origin main >> "$LOG_FILE" 2>&1 || true

# Activate the Scrapling virtual environment and run the multi-search scraper
source "$HOME/.openclaw/venvs/scrapling/bin/activate"
python3 "$HOME/.openclaw/workspace/scripts/watch_search_multi.py" >> "$LOG_FILE" 2>&1

# Download images for new watches
python3 "$HOME/.openclaw/workspace/scripts/download_watch_images.py" >> "$LOG_FILE" 2>&1

# Check if there are dashboard changes
if git diff --quiet -- watch-data.json search-config.json images && [ -z "$(git status --porcelain -- images)" ]; then
    echo "[$DATE] No new watches found." >> "$LOG_FILE"
else
    # Stage, commit, and push
    git add watch-data.json search-config.json images
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
