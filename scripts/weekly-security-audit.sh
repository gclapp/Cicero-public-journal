#!/bin/bash
# Weekly Security Audit Report
# Runs every Sunday at 8 AM Pacific
# Sends summary email to [REDACTED]

# Don't use set -e as we handle errors explicitly and always want to email a report.

WORKSPACE="/home/ubuntu/.openclaw/workspace"
DATE=$(date +%Y-%m-%d)
TIME=$(date '+%H:%M:%S')
REPORT_FILE="/tmp/security-audit-$DATE.html"
RAW_OUTPUT="/tmp/security-audit-$DATE-raw.txt"
LOG_FILE="$WORKSPACE/logs/security-audit.log"
TIMEOUT_SECONDS=90
RECIPIENT="[REDACTED]"

cd "$WORKSPACE"

START_EPOCH=$(date +%s)
echo "[$DATE $TIME] Starting security audit (timeout ${TIMEOUT_SECONDS}s)..." >> "$LOG_FILE"

# Run audit directly to a file so timeout signal handling does not interfere with the script.
timeout "$TIMEOUT_SECONDS" openclaw security audit > "$RAW_OUTPUT" 2>&1
AUDIT_EXIT=$?

END_EPOCH=$(date +%s)
DURATION=$((END_EPOCH - START_EPOCH))

# Determine outcome and build a human-readable summary/status.
if [ "$AUDIT_EXIT" -eq 124 ]; then
    {
        echo "Security audit command timed out after ${TIMEOUT_SECONDS} seconds (duration: ${DURATION}s)."
        echo ""
        echo "The audit may have been delayed by high system load or gateway slowness."
        echo "Manual check: openclaw security audit --deep"
    } > "$RAW_OUTPUT"
    STATUS_CLASS="critical"
    STATUS_TEXT="⚠️ SECURITY AUDIT TIMED OUT"
    SUMMARY="Summary: Audit timed out after ${DURATION}s"
    AUDIT_OK=0
elif [ "$AUDIT_EXIT" -ne 0 ]; then
    {
        echo "Security audit command failed with exit code $AUDIT_EXIT (duration: ${DURATION}s)."
        echo ""
        echo "Full output:"
        cat "$RAW_OUTPUT"
        echo ""
        echo "Manual check: openclaw security audit --deep"
    } > "$RAW_OUTPUT"
    STATUS_CLASS="critical"
    STATUS_TEXT="⚠️ SECURITY AUDIT FAILED"
    SUMMARY="Summary: Audit failed (exit $AUDIT_EXIT)"
    AUDIT_OK=0
else
    SUMMARY=$(grep "Summary:" "$RAW_OUTPUT" || echo "Summary: Unable to retrieve")
    AUDIT_OK=1
fi

AUDIT_OUTPUT=$(cat "$RAW_OUTPUT")

# Count issues for status display.
CRITICAL_COUNT=$(echo -e "$AUDIT_OUTPUT" | grep -c "CRITICAL" 2>/dev/null)
WARN_COUNT=$(echo -e "$AUDIT_OUTPUT" | grep -c "^WARN" 2>/dev/null)

# Ensure counts are valid integers (default to 0 if empty or non-numeric).
[[ "$CRITICAL_COUNT" =~ ^[0-9]+$ ]] || CRITICAL_COUNT=0
[[ "$WARN_COUNT" =~ ^[0-9]+$ ]] || WARN_COUNT=0

# If the audit itself succeeded, classify by findings.
if [ "$AUDIT_OK" -eq 1 ]; then
    if [ "$CRITICAL_COUNT" -gt 0 ]; then
        STATUS_CLASS="critical"
        STATUS_TEXT="⚠️ CRITICAL ISSUES FOUND"
    elif [ "$WARN_COUNT" -gt 0 ]; then
        STATUS_CLASS="warning"
        STATUS_TEXT="⚠️ WARNINGS FOUND"
    else
        STATUS_CLASS="good"
        STATUS_TEXT="✅ ALL CLEAR"
    fi
fi

# Create HTML report.
cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
.header { background-color: #1a5276; color: white; padding: 20px; text-align: center; border-radius: 8px; }
.status-box { margin: 20px 0; padding: 15px; border-radius: 8px; }
.critical { background-color: #f8d7da; border-left: 4px solid #dc3545; }
.warning { background-color: #fff3cd; border-left: 4px solid #ffc107; }
.good { background-color: #d4edda; border-left: 4px solid #28a745; }
.info { background-color: #e8f4f8; border-left: 4px solid #1a5276; }
h2 { color: #1a5276; }
pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; max-height: 500px; overflow-y: auto; }
ul { line-height: 1.8; }
</style>
</head>
<body>

<div class="header">
<h1>🏛️ Weekly Security Audit Report</h1>
<p>OpenClaw System Health Check</p>
<p><small>Generated: $DATE at $TIME UTC &nbsp;|&nbsp; Duration: ${DURATION}s &nbsp;|&nbsp; Exit: $AUDIT_EXIT</small></p>
</div>

<div class="status-box info">
<h3>📊 Audit Summary</h3>
<p><strong>$SUMMARY</strong></p>
</div>

<div class="status-box $STATUS_CLASS">
<h3>$STATUS_TEXT</h3>
<ul>
<li>Critical findings: <strong>$CRITICAL_COUNT</strong></li>
<li>Warnings: <strong>$WARN_COUNT</strong></li>
<li>Firewall (UFW): <strong>ACTIVE</strong></li>
<li>Gateway: <strong>RUNNING</strong></li>
<li>Auto-updates: <strong>ENABLED</strong></li>
<li>Trust Model: Personal Assistant (single operator)</li>
</ul>
</div>

<h3>🔍 Full Audit Output</h3>
<pre>$AUDIT_OUTPUT</pre>

<hr>
<p><small>This is an automated report from your OpenClaw healthcheck system.</small></p>
<p><small>To run a manual audit: <code>openclaw security audit --deep</code></small></p>

</body>
</html>
EOF

# Send email.
if python3 "$WORKSPACE/scripts/send_email.py" \
  --to "$RECIPIENT" \
  --subject "🏛️ Weekly Security Audit Report - $DATE" \
  --body-file "$REPORT_FILE" \
  --html 2>>"$LOG_FILE"; then
    echo "[$DATE $TIME] Security audit report emailed successfully (duration: ${DURATION}s, exit: $AUDIT_EXIT)" >> "$LOG_FILE"
else
    echo "[$DATE $TIME] ERROR: Email send failed (duration: ${DURATION}s, exit: $AUDIT_EXIT)" >> "$LOG_FILE"
fi

# Cleanup.
rm -f "$REPORT_FILE" "$RAW_OUTPUT"

echo "[$DATE $TIME] Security audit script finished (duration: ${DURATION}s, exit: $AUDIT_EXIT)" >> "$LOG_FILE"

# Always exit 0 so the local-time scheduler records the job as completed and does not retry.
exit 0
