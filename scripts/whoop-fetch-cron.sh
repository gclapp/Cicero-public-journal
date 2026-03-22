#!/bin/bash
# whoop-fetch-cron.sh - Fetch Whoop data twice daily (noon and 6pm PT)
# Saves data to ~/.openclaw/workspace/data/whoop/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$WORKSPACE_DIR/data/whoop"
LOG_FILE="$WORKSPACE_DIR/logs/whoop-fetch.log"

mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Get today's date
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting Whoop data fetch..." >> "$LOG_FILE"

# Change to skill directory
SKILL_DIR="$WORKSPACE_DIR/skills/whoop-openclaw-skill"
cd "$SKILL_DIR" || exit 1

# Fetch today's data
python3 scripts/whoop_client.py --action today --json > "$DATA_DIR/whoop-${TODAY}.json" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] ✅ Whoop data saved to whoop-${TODAY}.json" >> "$LOG_FILE"
    
    # Also fetch last 7 days for trend analysis
    python3 scripts/whoop_client.py --action recovery --days 7 --json > "$DATA_DIR/recovery-trend-${TODAY}.json" 2>> "$LOG_FILE"
    python3 scripts/whoop_client.py --action sleep --days 7 --json > "$DATA_DIR/sleep-trend-${TODAY}.json" 2>> "$LOG_FILE"
    python3 scripts/whoop_client.py --action workout --days 7 --json > "$DATA_DIR/workout-trend-${TODAY}.json" 2>> "$LOG_FILE"
    
    echo "[$TIMESTAMP] ✅ Trend data updated" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ❌ Whoop fetch failed" >> "$LOG_FILE"
fi
