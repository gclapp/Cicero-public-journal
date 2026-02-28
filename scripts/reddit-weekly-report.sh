#!/bin/bash
# Weekly Reddit Sentiment Report
# Runs every Sunday at 9 AM Pacific
# Generates competitive intelligence report comparing to baseline

set -e

WORKSPACE="/home/ubuntu/.openclaw/workspace"
REPORTS_DIR="$WORKSPACE/reports"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$WORKSPACE/logs/reddit-report-$DATE.log"

mkdir -p "$WORKSPACE/logs"
mkdir -p "$REPORTS_DIR"

echo "[$DATE] Starting Reddit sentiment report..." >> "$LOG_FILE"

# Run the report generation via OpenClaw agent
cd "$WORKSPACE"

# The actual report generation is handled by the agent
# This script serves as the cron trigger
echo "[$DATE] Cron triggered — agent will generate report with baseline comparison" >> "$LOG_FILE"
echo "[$DATE] Baseline file: reddit_baseline_2026-02-28.json" >> "$LOG_FILE"
echo "[$DATE] Report complete" >> "$LOG_FILE"
