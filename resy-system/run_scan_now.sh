#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/resy-system
rm -f data/scan_state.json
./venv/bin/python3 -u calendar_scanner.py 2>&1
