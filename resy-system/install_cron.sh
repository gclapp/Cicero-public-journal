#!/bin/bash

echo "🕐 Installing Resy 12-Hour Scanner Cron Job"
echo "============================================"
echo ""

# Get the absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCANNER_SCRIPT="$SCRIPT_DIR/calendar_scanner.py"
LOG_DIR="$SCRIPT_DIR/logs"

# Create logs directory
mkdir -p "$LOG_DIR"

# Create cron job entry
CRON_JOB="0 */12 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCANNER_SCRIPT >> $LOG_DIR/cron-scan.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "calendar_scanner.py"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove existing job
    crontab -l 2>/dev/null | grep -v "calendar_scanner.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job installed!"
echo ""
echo "Schedule: Every 12 hours (00:00 and 12:00 UTC)"
echo "Log file: $LOG_DIR/cron-scan.log"
echo ""
echo "Current crontab:"
crontab -l | grep "calendar_scanner" | head -1
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To remove:"
echo "  crontab -l | grep -v 'calendar_scanner.py' | crontab -"
