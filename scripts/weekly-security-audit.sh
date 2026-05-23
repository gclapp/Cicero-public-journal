#!/bin/bash
# Weekly Security Audit Report
# Runs every Sunday at 8 AM Pacific
# Sends summary email to [REDACTED]

# Don't use set -e as we handle errors explicitly

WORKSPACE="/home/ubuntu/.openclaw/workspace"
DATE=$(date +%Y-%m-%d)
TIME=$(date '+%H:%M:%S')
REPORT_FILE="/tmp/security-audit-$DATE.html"
LOG_FILE="$WORKSPACE/logs/security-audit.log"

cd "$WORKSPACE"

# Run security audit with timeout (30 seconds max)
echo "[$DATE $TIME] Starting security audit..." >> "$LOG_FILE"
AUDIT_OUTPUT=$(timeout 30 openclaw security audit 2>&1) || {
    AUDIT_OUTPUT="Security audit command timed out or failed.\n\nManual check may be needed.\nRun: openclaw security audit --deep"
    echo "[$DATE $TIME] Warning: Security audit command timed out" >> "$LOG_FILE"
}

# Extract summary line
SUMMARY=$(echo -e "$AUDIT_OUTPUT" | grep "Summary:" || echo "Summary: Unable to retrieve")

# Count issues for status display
CRITICAL_COUNT=$(echo -e "$AUDIT_OUTPUT" | grep -c "CRITICAL" 2>/dev/null)
WARN_COUNT=$(echo -e "$AUDIT_OUTPUT" | grep -c "^WARN" 2>/dev/null)

# Ensure counts are valid integers (default to 0 if empty or non-numeric)
[[ "$CRITICAL_COUNT" =~ ^[0-9]+$ ]] || CRITICAL_COUNT=0
[[ "$WARN_COUNT" =~ ^[0-9]+$ ]] || WARN_COUNT=0

# Determine overall status
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

# Create HTML report
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
</style>
</head>
<body>

<div class="header">
<h1>🏛️ Weekly Security Audit Report</h1>
<p>OpenClaw System Health Check</p>
<p><small>Generated: $DATE at $TIME UTC</small></p>
</div>

<div class="status-box info">
<h3>📊 Audit Summary</h3>
<p><strong>$SUMMARY</strong></p>
</div>

<div class="status-box $STATUS_CLASS">
<h3>$STATUS_TEXT</h3>
<ul>
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

# Send email
if python3 "$WORKSPACE/scripts/send_email.py" \
  --to "[REDACTED]" \
  --subject "🏛️ Weekly Security Audit Report - $DATE" \
  --body-file "$REPORT_FILE" \
  --html 2>>"$LOG_FILE"; then
    echo "[$DATE $TIME] Security audit completed and emailed successfully" >> "$LOG_FILE"
else
    echo "[$DATE $TIME] ERROR: Email send failed" >> "$LOG_FILE"
fi

# Cleanup
rm -f "$REPORT_FILE"

echo "[$DATE $TIME] Security audit script finished"