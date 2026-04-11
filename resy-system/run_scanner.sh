#!/bin/bash

# Run the calendar scanner once
cd "$(dirname "$0")"

# Create logs directory
mkdir -p logs

# Run scanner with timestamp
python3 calendar_scanner.py 2>&1 | tee "logs/scanner-$(date +%Y%m%d-%H%M%S).log"
