#!/bin/bash
# Setup cron jobs for travel automation
# Includes flight monitoring and car reservation checks

WORKSPACE_DIR="$HOME/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE_DIR/scripts"
LOGS_DIR="$WORKSPACE_DIR/logs"

# Create logs directory
mkdir -p "$LOGS_DIR"

# Backup existing crontab
crontab -l > "$WORKSPACE_DIR/config/crontab.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true

echo "Setting up travel automation cron jobs..."

# Create temporary crontab file
TEMP_CRON=$(mktemp)

# Get existing crontab (excluding our travel jobs for clean update)
crontab -l 2>/dev/null | grep -v "travel_flight_monitor\|travel_car_check\|travel_automation" > "$TEMP_CRON" || true

# Add travel automation jobs
cat >> "$TEMP_CRON" << 'EOF'

# Travel Automation Jobs
# ======================

# Daily flight status check - 8 AM PT (runs every morning)
0 15 * * * cd $HOME/.openclaw/workspace && python3 scripts/travel_flight_monitor.py >> logs/flight-monitor.log 2>&1

# Car reservation check - runs every 4 hours to catch flights 5-24 hours out
0 */4 * * * cd $HOME/.openclaw/workspace && python3 scripts/travel_car_check.py >> logs/car-check.log 2>&1

# Travel task generation - runs twice daily (9 AM and 9 PM PT)
0 16,4 * * * cd $HOME/.openclaw/workspace && python3 scripts/travel_automation_v2.py >> logs/travel-automation.log 2>&1

EOF

# Install new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Travel automation cron jobs installed!"
echo ""
echo "Jobs added:"
echo "  1. Flight monitor - Daily at 8 AM PT (checks flight status)"
echo "  2. Car check - Every 4 hours (alerts if no car booked 5h before flight)"
echo "  3. Travel automation - 9 AM & 9 PM PT (creates Todoist tasks)"
echo ""
echo "Logs location: $LOGS_DIR/"
echo ""
echo "Current crontab:"
crontab -l | grep -A 20 "Travel Automation"
