#!/bin/bash
# Migration script: Move travel automation to Aero agent
# Run this to switch from old scripts to Aero

echo "=============================================="
echo "Aero Travel Manager Migration"
echo "=============================================="
echo ""

# Check if running from correct directory
if [ ! -f "agents/travel-bot/aero_travel_manager.py" ]; then
    echo "❌ Error: Must run from workspace root"
    echo "   cd /home/ubuntu/.openclaw/workspace"
    exit 1
fi

# Backup current crontab
echo "📦 Backing up current crontab..."
crontab -l > ~/.crontab.backup.$(date +%Y%m%d_%H%M%S)
echo "   ✓ Backup saved"
echo ""

# Remove old travel cron jobs
echo "🗑️  Removing old travel cron jobs..."
(crontab -l 2>/dev/null | grep -v "calendar-travel-checker" | grep -v "travel_automation" | grep -v "flight_monitor" | grep -v "flight_alert") | crontab -
echo "   ✓ Old jobs removed"
echo ""

# Add new Aero cron jobs
echo "➕ Adding Aero cron jobs..."
(
crontab -l 2>/dev/null
echo ""
echo "# Aero Travel Manager - Task Creation (Mon/Wed/Fri 4 PM PT)"
echo "0 16 * * 1,3,5 /home/ubuntu/.openclaw/workspace/agents/travel-bot/aero-cron-tasks.sh"
echo ""
echo "# Aero Travel Manager - Day-of-Travel Monitoring (every 30 min)"
echo "*/30 * * * * /home/ubuntu/.openclaw/workspace/agents/travel-bot/aero-cron-monitor.sh"
echo ""
echo "# Aero Travel Manager - Full Run (daily 6 AM PT)"
echo "0 6 * * * /home/ubuntu/.openclaw/workspace/agents/travel-bot/aero-cron-full.sh"
) | crontab -
echo "   ✓ New jobs added"
echo ""

# Create state directory
echo "📁 Creating state directories..."
mkdir -p ~/.openclaw/workspace/state
mkdir -p ~/.openclaw/workspace/logs
echo "   ✓ Directories ready"
echo ""

# Test Aero installation
echo "🧪 Testing Aero installation..."
python3 agents/travel-bot/aero_travel_manager.py test
echo ""

# Show new cron jobs
echo "📋 New cron jobs:"
echo "----------------------------------------------"
crontab -l | grep -A1 "Aero Travel"
echo "----------------------------------------------"
echo ""

echo "=============================================="
echo "✅ Migration Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Set up FlightAware API key:"
echo "   python3 agents/travel-bot/aero_travel_manager.py setup YOUR_API_KEY"
echo ""
echo "2. Test task creation:"
echo "   python3 agents/travel-bot/aero_travel_manager.py tasks"
echo ""
echo "3. Test monitoring:"
echo "   python3 agents/travel-bot/aero_travel_manager.py monitor"
echo ""
echo "4. View logs:"
echo "   tail -f ~/.openclaw/workspace/logs/aero-cron.log"
echo ""
echo "5. Archive old scripts (optional):"
echo "   mv scripts/calendar_travel_checker.py scripts/archive/"
echo "   mv scripts/travel_flight_monitor.py scripts/archive/"
echo ""
