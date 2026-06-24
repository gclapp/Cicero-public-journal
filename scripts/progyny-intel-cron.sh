#!/bin/bash
# Progyny Intelligence Daily Cron
# Runs daily to collect and store Progyny mentions

set -euo pipefail

cd /home/ubuntu/.openclaw/workspace

echo "$(date): Starting Progyny intelligence collection..."

# Process daily mentions
python3 scripts/progyny_intel_cron.py --daily >> logs/progyny-intel.log 2>&1

# On Sundays, also generate weekly summary
if [ "$(date +%u)" -eq 7 ]; then
    echo "$(date): Generating weekly summary..."
    python3 scripts/progyny_intel_cron.py --weekly >> logs/progyny-intel.log 2>&1
    
    # Send weekly email
    python3 scripts/send_email.py \
        --to "[REDACTED],geoffrey.clapp@progyny.com,steven.leist@progyny.com" \
        --subject "🏛️ Progyny Weekly Intelligence Report" \
        --body-file config/progyny-weekly-summary.html \
        --html >> logs/progyny-intel.log 2>&1
fi

echo "$(date): Progyny intelligence collection complete"
