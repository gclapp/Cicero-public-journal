#!/bin/bash
# Daily Competitive Intelligence Report Generator
# Runs at 6 AM PT (14:00 UTC) daily
# Sends email only if there are new articles
# Includes PGNY alongside competitors as primary entity

WORKSPACE="/home/ubuntu/.openclaw/workspace"
cd "$WORKSPACE"

# Set PATH for Go
export PATH=$PATH:/usr/local/go/bin

# Run the monitor to check for new articles
python3 scripts/competitor_monitor.py > /tmp/competitor_scan.log 2>&1

# Check if there are new articles
if [ -f config/competitor-new-articles.json ] && [ -s config/competitor-new-articles.json ]; then
    # Generate HTML email (includes PGNY + competitors)
    python3 scripts/competitor_email.py
    
    # Check if email HTML was generated
    if [ -f config/competitor-email.html ]; then
        # Send the email
        python3 scripts/send_email.py \
            --to "geoffrey.clapp@progyny.com" \
            --subject "Competitive Intelligence Report - $(date '+%B %d, %Y')" \
            --body-file config/competitor-email.html \
            --html
        
        echo "[$(date)] Competitive report sent (includes PGNY + 5 competitors)" >> logs/competitor-reports.log
    fi
else
    echo "[$(date)] No new competitive intelligence to report" >> logs/competitor-reports.log
fi
