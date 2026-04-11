#!/bin/bash

echo "🍽️  Resy Automation System Status"
echo "================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check web app
echo "🌐 Web Interface:"
if pgrep -f "app.py" > /dev/null; then
    echo "   ✅ Running (PID: $(pgrep -f app.py))"
    echo "   🌐 http://localhost:5000"
else
    echo "   ❌ Not running"
    echo "   Start with: ./start.sh"
fi
echo ""

# Check scheduler daemon
echo "🕐 Scheduler Daemon:"
if pgrep -f "scheduler.py" > /dev/null; then
    echo "   ✅ Running (PID: $(pgrep -f scheduler.py))"
else
    echo "   ❌ Not running"
fi
echo ""

# Check cron job
echo "⏰ Cron Job:"
if crontab -l 2>/dev/null | grep -q "calendar_scanner.py"; then
    echo "   ✅ Installed"
    echo "   Schedule: $(crontab -l | grep calendar_scanner | awk '{print $1, $2, $3, $4, $5}')"
else
    echo "   ❌ Not installed"
fi
echo ""

# Check data files
echo "📁 Data Files:"
for file in data/restaurants.json data/users.json data/reservations.json; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        count=$(cat "$SCRIPT_DIR/$file" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get(list(d.keys())[0], [])))" 2>/dev/null || echo "0")
        echo "   ✅ $file ($count items)"
    else
        echo "   ❌ $file missing"
    fi
done
echo ""

# Check credentials
echo "🔐 Credentials:"
if [ -f ~/.openclaw/config/resy-credentials.json ]; then
    echo "   ✅ Resy API credentials"
else
    echo "   ❌ Resy API credentials missing"
fi

if [ -f ~/.openclaw/credentials/calendar-token.pickle ]; then
    echo "   ✅ Google Calendar credentials"
else
    echo "   ❌ Google Calendar credentials missing"
fi
echo ""

# Recent logs
echo "📜 Recent Activity:"
if [ -f "$SCRIPT_DIR/logs/scheduler.log" ]; then
    echo "   Last scheduler run:"
    tail -3 "$SCRIPT_DIR/logs/scheduler.log" | sed 's/^/     /'
elif [ -f "$SCRIPT_DIR/logs/cron-scan.log" ]; then
    echo "   Last cron scan:"
    tail -3 "$SCRIPT_DIR/logs/cron-scan.log" | sed 's/^/     /'
else
    echo "   No logs found"
fi
echo ""

# Trips
echo "🗽 Upcoming Trips:"
if [ -f "$SCRIPT_DIR/data/trips_cache.json" ]; then
    trip_count=$(cat "$SCRIPT_DIR/data/trips_cache.json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('trips', [])))" 2>/dev/null || echo "0")
    echo "   Found $trip_count upcoming trip(s)"
    echo "   View at: http://localhost:5000/trips"
else
    echo "   No trips cached yet"
fi
echo ""

# Summary
echo "📊 Summary:"
echo "   Run scanner now:    ./run_scanner.sh"
echo "   Install cron:       ./install_cron.sh"
echo "   Start daemon:       ./run_daemon.sh"
echo "   View all logs:      ls -la logs/"
