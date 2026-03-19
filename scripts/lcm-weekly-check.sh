#!/bin/bash
# Weekly LCM Health Check
# Runs every Saturday to verify lossless-claw is working properly

cd /home/ubuntu/.openclaw/workspace

# Run the Python check script
python3 scripts/lcm_weekly_check.py >> logs/lcm-weekly-check.log 2>&1

# If there are issues, send an alert (optional)
if [ $? -ne 0 ]; then
    echo "LCM weekly check failed at $(date)" | tee -a logs/lcm-weekly-check.log
fi
