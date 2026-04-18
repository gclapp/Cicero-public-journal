#!/bin/bash
# Run scanner for May trip specifically

cd /home/ubuntu/.openclaw/workspace/resy-system

# Force a fresh scan by clearing scan state
rm -f data/scan_state.json

echo "Running scanner for May 2026 trip..."
python3 calendar_scanner.py 2>&1 | tee logs/may-scan-$(date +%Y%m%d-%H%M%S).log