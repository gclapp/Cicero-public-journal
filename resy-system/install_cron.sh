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

# Create cron job entries
# 6:30 AM PT = 13:30 UTC
# 7:00 AM PT = 14:00 UTC
# 8:59 AM ET = 12:59 UTC (EDT)
# 9:03 AM ET = 13:03 UTC (EDT)
# 10:00 PM PT = 05:00 UTC (next day)
CRON_JOB_1="30 13 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCANNER_SCRIPT >> $LOG_DIR/cron-scan.log 2>&1"
CRON_JOB_2="0 14 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCANNER_SCRIPT >> $LOG_DIR/cron-scan.log 2>&1"
CRON_JOB_3="59 12 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCANNER_SCRIPT >> $LOG_DIR/cron-scan.log 2>&1"
CRON_JOB_4="3 13 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCANNER_SCRIPT >> $LOG_DIR/cron-scan.log 2>&1"
CRON_JOB_5="0 5 * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCANNER_SCRIPT >> $LOG_DIR/cron-scan.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "calendar_scanner.py"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove existing job
    crontab -l 2>/dev/null | grep -v "calendar_scanner.py" | crontab -
fi

# Add new cron jobs
(crontab -l 2>/dev/null; echo "$CRON_JOB_1"; echo "$CRON_JOB_2"; echo "$CRON_JOB_3"; echo "$CRON_JOB_4"; echo "$CRON_JOB_5") | crontab -

echo "✅ Cron jobs installed!"
echo ""
echo "Schedule:"
echo "  6:30 AM PT (13:30 UTC)"
echo "  7:00 AM PT (14:00 UTC)"
echo "  8:59 AM ET (12:59 UTC)"
echo "  9:03 AM ET (13:03 UTC)"
echo "  10:00 PM PT (05:00 UTC)"
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
