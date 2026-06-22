#!/usr/bin/env python3
"""
Telegram Health Monitor - Detects when Telegram messages aren't being processed
Monitors for:
- Failed message processing
- Model fallback errors on Telegram channel
- API key failures affecting Telegram
Sends alerts when issues detected
"""

import json
import os
import sys
import subprocess
import sqlite3
import html
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Configuration
STATE_DIR = Path.home() / ".openclaw" / "workspace" / "state"
LOGS_DIR = Path("/tmp/openclaw")
WORKSPACE_LOGS = Path.home() / ".openclaw" / "workspace" / "logs"
ALERT_LOG = WORKSPACE_LOGS / "telegram-health-alerts.log"
HEALTH_STATE = STATE_DIR / "telegram-health-state.json"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
SQLITE_DB = Path.home() / ".openclaw" / "state" / "openclaw.sqlite"

# Alert thresholds
FAILED_MESSAGE_THRESHOLD = 2  # Alert after 2 failed messages
ERROR_WINDOW_MINUTES = 30
ALERT_COOLDOWN_MINUTES = 30

def log(msg):
    """Log to alert log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(ALERT_LOG.parent, exist_ok=True)
    with open(ALERT_LOG, 'a') as f:
        f.write(log_msg + '\n')

def load_state():
    """Load monitoring state"""
    if HEALTH_STATE.exists():
        try:
            with open(HEALTH_STATE) as f:
                return json.load(f)
        except:
            pass
    return {
        "failed_messages": [],
        "last_alert": None,
        "last_check": None,
        "sqlite_warning": None
    }

def save_state(data):
    """Save monitoring state"""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(HEALTH_STATE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def check_telegram_failures():
    """Check SQLite for recent Telegram message failures"""
    failures = []
    conn = None
    
    try:
        conn = sqlite3.connect(str(SQLITE_DB))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(plugin_state_entries)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {"plugin_id", "namespace", "entry_key", "value_json", "created_at"}
        if not expected_columns.issubset(columns):
            missing = ", ".join(sorted(expected_columns - columns))
            log(f"⚠️ SQLite schema unsupported for plugin_state_entries; missing: {missing}")
            return failures
        
        # Look for error messages in plugin_state_entries
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=ERROR_WINDOW_MINUTES)
        cutoff_ms = int(cutoff.timestamp() * 1000)
        
        cursor.execute("""
            SELECT namespace, entry_key, value_json, created_at
            FROM plugin_state_entries 
            WHERE plugin_id = 'telegram'
            AND (
                lower(value_json) LIKE '%error%'
                OR lower(value_json) LIKE '%fail%'
                OR lower(value_json) LIKE '%exception%'
            )
            AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (cutoff_ms,))
        
        for row in cursor.fetchall():
            failures.append({
                "key": f"{row[0]}:{row[1]}",
                "value": row[2][:200],
                "timestamp": row[3]
            })
    except Exception as e:
        log(f"⚠️ Could not query SQLite: {e}")
    finally:
        if conn:
            conn.close()
    
    return failures

def parse_gateway_log_line(line):
    """Parse one structured OpenClaw gateway log line."""
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None

    meta = record.get("_meta") or {}
    timestamp = meta.get("date") or record.get("time")
    if not timestamp:
        return None

    try:
        line_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None

    if line_time.tzinfo is None:
        line_time = line_time.replace(tzinfo=timezone.utc)

    message = str(record.get("message") or record.get("1") or "")
    name = str(meta.get("name") or record.get("0") or "")
    level_id = int(meta.get("logLevelId") or 0)
    level_name = str(meta.get("logLevelName") or "")

    return {
        "time": line_time,
        "message": message,
        "name": name,
        "level_id": level_id,
        "level_name": level_name,
        "raw": line.strip(),
    }

def is_telegram_gateway_error(entry):
    """Return True for current Telegram delivery/channel failures."""
    message = entry["message"].lower()
    name = entry["name"].lower()

    if entry["level_id"] < 5 and entry["level_name"].upper() != "ERROR":
        return False

    telegram_scope = (
        "lane=session:agent:main:telegram" in message
        or "channels/telegram" in name
        or "[telegram]" in message
    )
    if not telegram_scope:
        return False

    error_terms = (
        "error",
        "fail",
        "stall",
        "timeout",
        "unauthorized",
        "draining",
        "closed before turn completed",
    )
    return any(term in message for term in error_terms)

def check_gateway_logs():
    """Check gateway logs for Telegram errors"""
    errors = []
    
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"openclaw-{today}.log"
    
    if not log_file.exists():
        return errors
    
    try:
        with open(log_file, 'r', errors='ignore') as f:
            lines = f.readlines()
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=ERROR_WINDOW_MINUTES)
        
        for line in lines:
            entry = parse_gateway_log_line(line)
            if not entry:
                continue
            if entry["time"] < cutoff:
                continue
            if is_telegram_gateway_error(entry):
                errors.append(entry["message"][:250])
    except Exception as e:
        log(f"⚠️ Could not read gateway logs: {e}")
    
    return errors

def should_alert(state, failure_count):
    """Determine if we should send an alert"""
    if failure_count < FAILED_MESSAGE_THRESHOLD:
        return False
    
    last_alert = state.get("last_alert")
    if last_alert:
        try:
            last_alert_time = datetime.fromisoformat(last_alert)
            if datetime.now() - last_alert_time < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return False
        except:
            pass
    
    return True

def send_alert(failure_count, sqlite_failures, log_errors):
    """Send alert email"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S local")
    
    subject = f"🚨 Telegram Health Alert: {failure_count} message failures detected"
    
    # Build error details
    error_details = ""
    for err in log_errors[:3]:
        error_details += f"<li style='font-family: monospace; font-size: 11px; margin: 5px 0;'>{html.escape(err)}</li>"
    
    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #d32f2f;">🚨 Telegram Health Alert</h2>
    
    <p><strong>Time:</strong> {timestamp}</p>
    <p><strong>Failed Messages (last {ERROR_WINDOW_MINUTES} min):</strong> {failure_count}</p>
    
    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin: 20px 0;">
        <tr style="background: #ffebee;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #d32f2f;">Status</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">MESSAGES FAILING</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">SQLite Errors</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{len(sqlite_failures)}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Log Errors</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{len(log_errors)}</td>
        </tr>
    </table>
    
    <h3>Recent Errors:</h3>
    <ul>
        {error_details}
    </ul>
    
    <h3>What This Means</h3>
    <p>Telegram messages are being received but failing to process. This is likely due to:</p>
    <ul>
        <li>OpenAI API key issues (401 Unauthorized)</li>
        <li>Model fallback failures</li>
        <li>Service timeouts</li>
    </ul>
    
    <h3>Immediate Actions Needed</h3>
    <ol>
        <li>Check OpenAI API key validity</li>
        <li>Verify OpenAI account has credits</li>
        <li>Check <code>openclaw status</code> for model status</li>
        <li>Review gateway logs: <code>openclaw logs --follow</code></li>
    </ol>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">
        This is an automated alert from your Telegram Health Monitor.<br>
        Run <code>python3 scripts/telegram_health_monitor.py</code> to check manually.
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
            log(f"✅ Alert email sent")
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
    log("Telegram Health Monitor Check")
    log("=" * 60)
    
    state = load_state()
    
    # Check for failures
    sqlite_failures = check_telegram_failures()
    log_errors = check_gateway_logs()
    
    total_failures = len(sqlite_failures) + len(log_errors)
    
    log(f"SQLite failures: {len(sqlite_failures)}")
    log(f"Log errors: {len(log_errors)}")
    log(f"Total: {total_failures}")
    
    # Alert if needed
    if should_alert(state, total_failures):
        if send_alert(total_failures, sqlite_failures, log_errors):
            state["last_alert"] = datetime.now().isoformat()
    elif total_failures > 0:
        log(f"⚠️ {total_failures} failures detected but below alert threshold")
    else:
        log("✅ Telegram health check passed - no issues detected")
    
    # Update state
    state["last_check"] = datetime.now().isoformat()
    state["failed_messages"] = sqlite_failures[:10]  # Keep last 10
    save_state(state)
    
    return 0 if total_failures < FAILED_MESSAGE_THRESHOLD else 1

if __name__ == "__main__":
    sys.exit(main())
