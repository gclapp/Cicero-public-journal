#!/usr/bin/env python3
"""
API Health Monitor - Detects API key failures and service outages
Monitors OpenAI, Moonshot, and other critical APIs
Sends alerts when failures exceed threshold
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration
LOG_DIR = Path("/tmp/openclaw")
WORKSPACE_LOGS = Path.home() / ".openclaw" / "workspace" / "logs"
ALERT_LOG = WORKSPACE_LOGS / "api-health-alerts.log"
HEALTH_STATE = WORKSPACE_LOGS / "api-health-state.json"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"

# Alert thresholds
ERROR_THRESHOLD = 3  # Alert after 3 errors in window
ERROR_WINDOW_MINUTES = 30  # Look at last 30 minutes
ALERT_COOLDOWN_MINUTES = 60  # Don't alert more than once per hour

# API patterns to monitor
API_PATTERNS = {
    "openai": {
        "name": "OpenAI",
        "error_patterns": [
            "401 Unauthorized",
            "Incorrect API key provided",
            "invalid_api_key",
            "rate limit",
            "insufficient_quota"
        ],
        "log_files": ["openclaw-*.log"],
        "critical": True
    },
    "moonshot": {
        "name": "Moonshot/Kimi",
        "error_patterns": [
            "moonshot",
            "kimi",
            "Unauthorized",
            "rate limit"
        ],
        "log_files": ["openclaw-*.log"],
        "critical": False
    },
    "telegram": {
        "name": "Telegram Bot",
        "error_patterns": [
            "telegram.*error",
            "FailoverError.*telegram"
        ],
        "log_files": ["openclaw-*.log"],
        "critical": True
    }
}

def log(msg):
    """Log to alert log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(ALERT_LOG.parent, exist_ok=True)
    with open(ALERT_LOG, 'a') as f:
        f.write(log_msg + '\n')

def load_health_state():
    """Load health monitoring state"""
    if HEALTH_STATE.exists():
        try:
            with open(HEALTH_STATE) as f:
                return json.load(f)
        except:
            pass
    return {
        "error_counts": defaultdict(list),
        "last_alert": {},
        "first_seen": {}
    }

def save_health_state(data):
    """Save health monitoring state"""
    os.makedirs(HEALTH_STATE.parent, exist_ok=True)
    # Convert defaultdict to regular dict for JSON serialization
    data["error_counts"] = dict(data["error_counts"])
    with open(HEALTH_STATE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def parse_log_timestamp(line):
    """Extract timestamp from log line"""
    # Try ISO format: 2026-06-22T14:49:50.699Z
    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
    if match:
        try:
            return datetime.fromisoformat(match.group(1).replace('Z', '+00:00'))
        except:
            pass
    return None

def scan_logs_for_errors():
    """Scan recent logs for API errors"""
    errors_found = defaultdict(list)
    cutoff_time = datetime.now() - timedelta(minutes=ERROR_WINDOW_MINUTES)
    
    # Find today's log file
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"openclaw-{today}.log"
    
    if not log_file.exists():
        log(f"⚠️ Log file not found: {log_file}")
        return errors_found
    
    try:
        with open(log_file, 'r', errors='ignore') as f:
            lines = f.readlines()
        
        for line in lines:
            # Check timestamp
            ts = parse_log_timestamp(line)
            if ts and ts < cutoff_time:
                continue
            
            # Check each API pattern
            for api_key, config in API_PATTERNS.items():
                for pattern in config["error_patterns"]:
                    if pattern.lower() in line.lower():
                        errors_found[api_key].append({
                            "timestamp": ts.isoformat() if ts else datetime.now().isoformat(),
                            "line": line.strip()[:200]  # Truncate long lines
                        })
                        break
    except Exception as e:
        log(f"❌ Error reading logs: {e}")
    
    return errors_found

def should_alert(api_key, state, error_count):
    """Determine if we should send an alert"""
    last_alert = state["last_alert"].get(api_key)
    
    if last_alert:
        try:
            last_alert_time = datetime.fromisoformat(last_alert)
            if datetime.now() - last_alert_time < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return False
        except:
            pass
    
    return error_count >= ERROR_THRESHOLD

def send_alert_email(api_key, config, error_count, recent_errors):
    """Send alert email about API failures"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PT")
    
    subject = f"🚨 API Health Alert: {config['name']} failing ({error_count} errors)"
    
    # Build error summary
    error_summary = ""
    for i, err in enumerate(recent_errors[-5:], 1):  # Show last 5 errors
        error_summary += f"<tr><td>{i}</td><td style='font-family: monospace; font-size: 11px;'>{err['line'][:150]}...</td></tr>"
    
    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #d32f2f;">🚨 API Health Alert: {config['name']}</h2>
    
    <p><strong>Time:</strong> {timestamp}</p>
    <p><strong>Error Count (last {ERROR_WINDOW_MINUTES} min):</strong> {error_count}</p>
    
    <table style="border-collapse: collapse; width: 100%; max-width: 800px; margin: 20px 0;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">API</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{config['name']}</td>
        </tr>
        <tr style="background: #ffebee;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #d32f2f;">Status</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">FAILING</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Critical</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{'Yes' if config['critical'] else 'No'}</td>
        </tr>
    </table>
    
    <h3>Recent Errors:</h3>
    <table style="border-collapse: collapse; width: 100%; max-width: 800px; margin: 20px 0; font-size: 12px;">
        <tr style="background: #f5f5f5;">
            <th style="padding: 8px; border: 1px solid #ddd;">#</th>
            <th style="padding: 8px; border: 1px solid #ddd;">Error</th>
        </tr>
        {error_summary}
    </table>
    
    <h3>What This Means</h3>
    <p>The {config['name']} API is experiencing failures. This may affect:</p>
    <ul>
        <li>Response quality and speed</li>
        <li>Model fallback to backup providers</li>
        <li>Telegram message processing</li>
    </ul>
    
    <h3>Recommended Actions</h3>
    <ul>
        <li>Check API key validity at provider dashboard</li>
        <li>Verify account has sufficient credits/quota</li>
        <li>Check provider status page for outages</li>
        <li>Review recent configuration changes</li>
    </ul>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">
        This is an automated alert from your OpenClaw API Health Monitor.<br>
        Alert cooldown: {ALERT_COOLDOWN_MINUTES} minutes
    </p>
</body>
</html>"""
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(EMAIL_SCRIPT),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", body_html,
                "--html"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            log(f"✅ Alert email sent for {api_key}")
            return True
        else:
            log(f"❌ Failed to send alert: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Error sending alert: {e}")
        return False

def main():
    """Main monitoring function"""
    log("=" * 60)
    log("API Health Monitor Check")
    log("=" * 60)
    
    # Load state
    state = load_health_state()
    
    # Scan for errors
    errors = scan_logs_for_errors()
    
    alerts_sent = 0
    
    for api_key, config in API_PATTERNS.items():
        error_list = errors.get(api_key, [])
        error_count = len(error_list)
        
        if error_count > 0:
            log(f"⚠️ {config['name']}: {error_count} errors in last {ERROR_WINDOW_MINUTES} minutes")
            
            # Check if we should alert
            if should_alert(api_key, state, error_count):
                if send_alert_email(api_key, config, error_count, error_list):
                    state["last_alert"][api_key] = datetime.now().isoformat()
                    alerts_sent += 1
            else:
                log(f"   (Alert suppressed - cooldown or below threshold)")
        else:
            log(f"✅ {config['name']}: No errors")
    
    # Save state
    save_health_state(state)
    
    log(f"\nCheck complete. Alerts sent: {alerts_sent}")
    return 0 if alerts_sent == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
