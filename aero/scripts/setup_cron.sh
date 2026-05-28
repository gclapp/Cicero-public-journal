#!/bin/bash
# Setup Aero Travel Automation Cron Jobs
# 
# This script installs the cron jobs for Aero travel automation.
# It replaces the old Cicero travel automation with Aero.

set -e

WORKSPACE_DIR="$HOME/.openclaw/workspace"
AERO_DIR="$WORKSPACE_DIR/aero"
SCRIPTS_DIR="$AERO_DIR/scripts"
CONFIG_DIR="$WORKSPACE_DIR/config"

# Create backup of existing crontab
backup_crontab() {
    echo "Backing up existing crontab..."
    mkdir -p "$CONFIG_DIR"
    crontab -l > "$CONFIG_DIR/crontab.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
}

# Remove old travel automation cron jobs
remove_old_jobs() {
    echo "Removing old travel automation cron jobs..."
    
    # Create temp file without old jobs
    TEMP_CRON=$(mktemp)
    crontab -l 2>/dev/null | grep -v \
        -e "travel_flight_monitor" \
        -e "travel_car_check" \
        -e "travel_automation" \
        -e "calendar-travel-checker" \
        -e "flight_alert_system" \
        -e "flight_monitor" \
        > "$TEMP_CRON" || true
    
    # Install cleaned crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "✅ Old jobs removed"
}

# Install new Aero cron jobs
install_aero_jobs() {
    echo "Installing Aero travel automation cron jobs..."
    
    TEMP_CRON=$(mktemp)
    
    # Get existing crontab (without old travel jobs)
    crontab -l 2>/dev/null | grep -v \
        -e "aero_travel" \
        -e "aero-travel" \
        > "$TEMP_CRON" || true
    
    # Add Aero travel automation jobs
    cat >> "$TEMP_CRON" << EOF

# Aero Travel Automation Jobs
# ============================

# Full automation (task creation + monitoring) - twice daily
# 9 AM PT (16:00 UTC) and 9 PM PT (04:00 UTC next day)
0 16,4 * * * $SCRIPTS_DIR/aero_travel_cron.sh full >> $WORKSPACE_DIR/logs/aero-cron.log 2>&1

# Flight monitoring - regular checks every 30 minutes
*/30 * * * * $SCRIPTS_DIR/aero_travel_cron.sh monitor >> $WORKSPACE_DIR/logs/aero-cron.log 2>&1

# Flight monitoring - frequent checks every 5 minutes
# This runs more often but the script will only check flights that are
# within 24 hours of departure
*/5 * * * * $SCRIPTS_DIR/aero_travel_cron.sh monitor-frequent >> $WORKSPACE_DIR/logs/aero-cron.log 2>&1

EOF
    
    # Install new crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "✅ Aero cron jobs installed"
}

# Verify installation
verify_installation() {
    echo ""
    echo "Verifying installation..."
    echo ""
    
    echo "Installed cron jobs:"
    echo "-------------------"
    crontab -l | grep -A 20 "Aero Travel Automation"
    
    echo ""
    echo "Checking script permissions..."
    
    if [ -x "$SCRIPTS_DIR/aero_travel_cron.sh" ]; then
        echo "✅ aero_travel_cron.sh is executable"
    else
        echo "❌ aero_travel_cron.sh is not executable"
        chmod +x "$SCRIPTS_DIR/aero_travel_cron.sh"
        echo "   Fixed: Made executable"
    fi
    
    if [ -x "$SCRIPTS_DIR/aero_travel_monitor.sh" ]; then
        echo "✅ aero_travel_monitor.sh is executable"
    else
        echo "❌ aero_travel_monitor.sh is not executable"
        chmod +x "$SCRIPTS_DIR/aero_travel_monitor.sh"
        echo "   Fixed: Made executable"
    fi
    
    echo ""
    echo "Checking Python modules..."
    
    export PYTHONPATH="$AERO_DIR/src:$PYTHONPATH"
    
    if python3 -c "import flightaware_client" 2>/dev/null; then
        echo "✅ flightaware_client module available"
    else
        echo "❌ flightaware_client module not found"
    fi
    
    if python3 -c "import aero_tracker" 2>/dev/null; then
        echo "✅ aero_tracker module available"
    else
        echo "❌ aero_tracker module not found"
    fi
    
    if python3 -c "import travel_monitor" 2>/dev/null; then
        echo "✅ travel_monitor module available"
    else
        echo "❌ travel_monitor module not found"
    fi
    
    if python3 -c "import aero_travel_automation" 2>/dev/null; then
        echo "✅ aero_travel_automation module available"
    else
        echo "❌ aero_travel_automation module not found"
    fi
}

# Main function
main() {
    echo "=========================================="
    echo "Aero Travel Automation - Cron Setup"
    echo "=========================================="
    echo ""
    
    # Check if running in correct directory
    if [ ! -d "$AERO_DIR" ]; then
        echo "❌ Error: Aero directory not found at $AERO_DIR"
        exit 1
    fi
    
    # Backup existing crontab
    backup_crontab
    
    # Remove old jobs
    remove_old_jobs
    
    # Install new jobs
    install_aero_jobs
    
    # Verify
    verify_installation
    
    echo ""
    echo "=========================================="
    echo "Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Aero travel automation is now active."
    echo ""
    echo "Schedule:"
    echo "  - Full automation (tasks + monitoring): 9 AM & 9 PM PT"
    echo "  - Flight monitoring (regular): Every 30 minutes"
    echo "  - Flight monitoring (frequent): Every 5 minutes"
    echo ""
    echo "Logs: $WORKSPACE_DIR/logs/aero-*.log"
    echo ""
    echo "To test manually:"
    echo "  $SCRIPTS_DIR/aero_travel_cron.sh full"
    echo "  $SCRIPTS_DIR/aero_travel_cron.sh monitor"
    echo ""
}

# Run main function
main "$@"
