#!/bin/bash
# Verify travel automation is properly configured

echo "=========================================="
echo "TRAVEL AUTOMATION VERIFICATION"
echo "=========================================="
echo ""

# Check cron job
echo "1. Checking cron job..."
if crontab -l | grep -q "travel_automation"; then
    echo "   ✅ Travel automation cron job found"
    crontab -l | grep "travel_automation"
else
    echo "   ❌ Travel automation cron job NOT found"
fi
echo ""

# Check script exists
echo "2. Checking script files..."
if [ -f "/home/ubuntu/.openclaw/workspace/scripts/travel_automation_v2.py" ]; then
    echo "   ✅ travel_automation_v2.py exists"
else
    echo "   ❌ travel_automation_v2.py missing"
fi

if [ -f "/home/ubuntu/.openclaw/workspace/scripts/travel_automation_cron.sh" ]; then
    echo "   ✅ travel_automation_cron.sh exists"
else
    echo "   ❌ travel_automation_cron.sh missing"
fi
echo ""

# Check log directory
echo "3. Checking log directory..."
if [ -d "/home/ubuntu/.openclaw/workspace/logs" ]; then
    echo "   ✅ logs directory exists"
else
    echo "   ❌ logs directory missing"
fi
echo ""

# Check for recent log
echo "4. Checking for recent runs..."
if [ -f "/home/ubuntu/.openclaw/workspace/logs/travel-automation-v2.log" ]; then
    LAST_RUN=$(stat -c %Y /home/ubuntu/.openclaw/workspace/logs/travel-automation-v2.log)
    NOW=$(date +%s)
    HOURS_AGO=$(( (NOW - LAST_RUN) / 3600 ))
    echo "   ✅ Log file exists (last run: $HOURS_AGO hours ago)"
    tail -3 /home/ubuntu/.openclaw/workspace/logs/travel-automation-v2.log
else
    echo "   ⚠️ No log file yet (will be created on first run)"
fi
echo ""

# Count travel tasks
echo "5. Counting travel tasks in Todoist..."
TASK_COUNT=$(todoist list -f "travel" 2>/dev/null | wc -l)
echo "   Found $TASK_COUNT travel-related tasks"
echo ""

echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
