#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/resy-system
rm -f data/scan_state.json
/usr/bin/python3 calendar_scanner.py 2>&1
