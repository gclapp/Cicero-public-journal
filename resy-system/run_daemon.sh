#!/bin/bash

# Run the scheduler as a background daemon

cd "$(dirname "$0")"

mkdir -p logs

echo "🍽️  Starting Resy Scheduler Daemon"
echo "   Runs scanner every 12 hours"
echo "   Logs: logs/scheduler.log"
echo ""

# Check if already running
if pgrep -f "scheduler.py" > /dev/null; then
    echo "⚠️  Scheduler already running!"
    echo "   PID: $(pgrep -f scheduler.py)"
    echo "   To stop: pkill -f scheduler.py"
    exit 1
fi

# Run in background
nohup python3 scheduler.py > logs/daemon.out 2>&1 &

sleep 2

if pgrep -f "scheduler.py" > /dev/null; then
    echo "✅ Scheduler started!"
    echo "   PID: $(pgrep -f scheduler.py)"
    echo ""
    echo "Commands:"
    echo "  View logs:  tail -f logs/scheduler.log"
    echo "  Stop:       pkill -f scheduler.py"
    echo "  Status:     pgrep -f scheduler.py"
else
    echo "❌ Failed to start scheduler"
    echo "   Check logs/daemon.out for errors"
fi
