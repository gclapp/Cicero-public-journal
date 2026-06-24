#!/bin/bash
# daily-github-sync.sh - Commit changes and sync journal entries
# Runs at 11:59 AM and 11:59 PM PT daily

WORKSPACE="/home/ubuntu/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/github-sync.log"
GITHUB_TOKEN_FILE="$HOME/.openclaw/credentials/github-token.txt"
DATE=$(date '+%Y-%m-%d %H:%M:%S %Z')
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')

echo "[$DATE] Starting daily GitHub sync..." >> "$LOG_FILE"

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

# Change to workspace
cd "$WORKSPACE" || exit 1
setup_git_auth || exit 1

# Check if there are changes to commit
if [[ -n $(git status --porcelain) ]]; then
    echo "[$DATE] Uncommitted changes found, committing..." >> "$LOG_FILE"
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    git commit -m "Daily sync: $TIMESTAMP" >> "$LOG_FILE" 2>&1
    
    # Push to GitHub
    git push origin main >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "[$DATE] ✅ GitHub sync complete" >> "$LOG_FILE"
    else
        echo "[$DATE] ❌ GitHub push failed" >> "$LOG_FILE"
    fi
else
    echo "[$DATE] No changes to commit" >> "$LOG_FILE"
fi

# Check for journal entries needing public versions
echo "[$DATE] Checking for journal entries to publish..." >> "$LOG_FILE"

python3 "$WORKSPACE/scripts/sync_public_journal.py" >> "$LOG_FILE" 2>&1

# Update content analytics
echo "[$DATE] Updating content analytics..." >> "$LOG_FILE"
if [ -f "$WORKSPACE/scripts/content_analytics_collector.py" ]; then
    python3 "$WORKSPACE/scripts/content_analytics_collector.py" report >> "$LOG_FILE" 2>&1
else
    echo "[$DATE] Content analytics collector not installed; skipping." >> "$LOG_FILE"
fi

echo "[$DATE] Daily sync complete" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
