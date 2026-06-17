#!/usr/bin/env python3
"""
Token Auto-Refresh System v2 - Bulletproof
Refreshes tokens before they expire with retry logic and validation
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# Token file paths
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "token-refresh.log"
ALERT_STATE_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "token-alert-state.json"

TOKEN_CONFIG = {
    "whoop": {
        "access_token": Path.home() / ".whoop_token",
        "refresh_token": Path.home() / ".whoop_refresh_token",
        "config": Path.home() / ".openclaw" / "workspace" / "config" / "whoop-config.json",
        "credentials": CREDENTIALS_DIR / "whoop-tokens.json",
        "refresh_minutes": 45,  # Refresh every 45 minutes (expires in 60)
        "max_retries": 3,
        "retry_delay": 5
    },
    "google_calendar": {
        "token": CREDENTIALS_DIR / "calendar-token.pickle",
        "alert_days": 5,  # Alert when 5+ days old
        "max_age_days": 7  # Critical at 7 days
    },
    "google_docs": {
        "token": CREDENTIALS_DIR / "gdocs-token.pickle",
        "alert_days": 5,
        "max_age_days": 7
    },
    "gmail_smtp": {
        "config": Path.home() / ".openclaw" / "email_config.json",
        "alert_days": 25,
        "max_age_days": 60
    }
}

def log(msg, level="INFO"):
    """Log with timestamp and level"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{ts}] [{level}] {msg}"
    print(log_line)
    
    # Also write to log file
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + "\n")

def get_file_age_minutes(filepath):
    """Get age of file in minutes"""
    if not filepath.exists():
        return None
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    age_minutes = (datetime.now() - mtime).total_seconds() / 60
    return age_minutes

def get_file_age_days(filepath):
    """Get age of file in days"""
    if not filepath.exists():
        return None
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    age_days = (datetime.now() - mtime).days
    return age_days

def validate_whoop_token(token):
    """Test if Whoop token is valid by making API call"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://api.prod.whoop.com/developer/v2/user/profile/basic",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"Token validation error: {e}", "ERROR")
        return False

def refresh_whoop_with_retry():
    """Refresh Whoop token with retry logic"""
    config = TOKEN_CONFIG["whoop"]
    max_retries = config["max_retries"]
    retry_delay = config["retry_delay"]
    
    for attempt in range(1, max_retries + 1):
        try:
            log(f"Whoop refresh attempt {attempt}/{max_retries}...")
            
            # Load config
            with open(config["config"]) as f:
                whoop_config = json.load(f)
            
            # Load refresh token
            if not config["refresh_token"].exists():
                log("❌ Whoop refresh token not found", "ERROR")
                return False
            
            refresh_token = config["refresh_token"].read_text().strip()
            
            # Exchange for new tokens
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': whoop_config['client_id'],
                'client_secret': whoop_config['client_secret'],
                'redirect_uri': whoop_config['redirect_uri']
            }
            
            response = requests.post(
                'https://api.prod.whoop.com/oauth/oauth2/token',
                data=data,
                timeout=15
            )
            
            if response.status_code == 200:
                tokens = response.json()
                
                # Validate new token before saving
                if not validate_whoop_token(tokens['access_token']):
                    log("❌ New token failed validation", "ERROR")
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    return False
                
                # Save access token
                config["access_token"].write_text(tokens['access_token'])
                
                # Update credentials file
                with open(config["credentials"], 'w') as f:
                    json.dump(tokens, f, indent=2)
                
                # Update refresh token if provided
                if 'refresh_token' in tokens:
                    config["refresh_token"].write_text(tokens['refresh_token'])
                
                # Set secure permissions
                os.chmod(config["access_token"], 0o600)
                os.chmod(config["refresh_token"], 0o600)
                os.chmod(config["credentials"], 0o600)
                
                log("✅ Whoop token refreshed and validated", "SUCCESS")
                return True
                
            elif response.status_code == 401:
                log(f"❌ Whoop refresh failed: Invalid credentials (401)", "ERROR")
                # Don't retry on auth failure
                return False
            else:
                log(f"❌ Whoop refresh failed: {response.status_code}", "ERROR")
                if attempt < max_retries:
                    log(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                return False
                
        except requests.exceptions.Timeout:
            log(f"❌ Whoop refresh timeout (attempt {attempt})", "ERROR")
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
            return False
        except Exception as e:
            log(f"❌ Whoop refresh error: {e}", "ERROR")
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
            return False
    
    return False

def check_whoop_token():
    """Check and refresh Whoop token if needed"""
    config = TOKEN_CONFIG["whoop"]
    
    # Check current token age
    age_minutes = get_file_age_minutes(config["access_token"])
    
    if age_minutes is None:
        log("⚠️ Whoop access token not found", "WARNING")
        # Try to refresh anyway
        return refresh_whoop_with_retry()
    
    # Check if token is still valid
    current_token = config["access_token"].read_text().strip()
    if validate_whoop_token(current_token):
        if age_minutes < config["refresh_minutes"]:
            log(f"✅ Whoop token valid and fresh ({age_minutes:.0f} min old)")
            return True
        else:
            log(f"🔄 Whoop token valid but old ({age_minutes:.0f} min) — refreshing...")
            return refresh_whoop_with_retry()
    else:
        log(f"🔄 Whoop token invalid ({age_minutes:.0f} min old) — refreshing...")
        return refresh_whoop_with_retry()

def check_google_token(name, config):
    """Check Google token status (can't auto-refresh)"""
    age_days = get_file_age_days(config["token"])
    
    if age_days is None:
        log(f"⚠️ {name}: Token file not found", "WARNING")
        return "missing"
    
    if age_days >= config["max_age_days"]:
        log(f"🔴 {name}: Token is {age_days} days old — CRITICAL", "ERROR")
        return "critical"
    elif age_days >= config["alert_days"]:
        log(f"🟡 {name}: Token is {age_days} days old — needs refresh soon", "WARNING")
        return "warning"
    else:
        log(f"✅ {name}: Token is {age_days} days old (healthy)")
        return "healthy"

def check_gmail_smtp():
    """Check Gmail SMTP config"""
    config = TOKEN_CONFIG["gmail_smtp"]
    age_days = get_file_age_days(config["config"])
    
    if age_days is None:
        log("⚠️ Gmail SMTP: Config not found", "WARNING")
        return "missing"
    
    if age_days >= config["max_age_days"]:
        log(f"🔴 Gmail SMTP: Config is {age_days} days old — verify still working", "WARNING")
        return "warning"
    elif age_days >= config["alert_days"]:
        log(f"🟡 Gmail SMTP: Config is {age_days} days old — monitor", "WARNING")
        return "warning"
    else:
        log(f"✅ Gmail SMTP: Config is {age_days} days old (healthy)")
        return "healthy"

def should_send_alert(issue_key, cooldown_hours=4):
    """Check if we should send alert (rate limiting)"""
    try:
        if ALERT_STATE_FILE.exists():
            with open(ALERT_STATE_FILE) as f:
                state = json.load(f)
        else:
            state = {}
        
        now = datetime.now()
        last_alert = state.get(issue_key)
        
        if last_alert:
            last_time = datetime.fromisoformat(last_alert)
            hours_since = (now - last_time).total_seconds() / 3600
            if hours_since < cooldown_hours:
                return False
        
        # Update state
        state[issue_key] = now.isoformat()
        ALERT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_STATE_FILE, 'w') as f:
            json.dump(state, f)
        
        return True
    except Exception as e:
        log(f"Error checking alert state: {e}", "ERROR")
        return True  # Send alert if we can't check state

def send_alert(message, is_critical=True, issue_key="general"):
    """Send alert via email and Telegram"""
    import subprocess
    
    # Rate limiting
    if not should_send_alert(issue_key, cooldown_hours=4):
        log(f"Alert suppressed (rate limit): {message[:50]}...")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PT")
    emoji = "🔴" if is_critical else "🟡"
    
    # Send email
    try:
        email_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
        if email_script.exists():
            subject = f"{emoji} Token Alert: {'CRITICAL' if is_critical else 'Warning'}"
            body = f"<h3>{emoji} Token Health Alert</h3><p><strong>{message}</strong></p><p>Time: {timestamp}</p><p>Run: python3 /home/ubuntu/.openclaw/workspace/scripts/calendar_reader.py</p>"
            subprocess.run([
                "python3", str(email_script),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", body,
                "--html"
            ], capture_output=True, timeout=30)
    except Exception as e:
        log(f"Failed to send email alert: {e}", "ERROR")
    
    # Send Telegram
    try:
        telegram_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_telegram.py"
        if telegram_script.exists():
            telegram_msg = f"{emoji} **Token Alert**\n\n{message}\n\nTime: {timestamp}\n\nAction needed: Run calendar_reader.py"
            subprocess.run([
                "python3", str(telegram_script), telegram_msg
            ], capture_output=True, timeout=30)
    except Exception as e:
        log(f"Failed to send Telegram alert: {e}", "ERROR")

def run_health_check():
    """Run full token health check"""
    log("=" * 70)
    log("TOKEN HEALTH CHECK - Bulletproof v2")
    log("=" * 70)
    
    results = {
        "whoop": check_whoop_token(),
        "google_calendar": check_google_token("Google Calendar", TOKEN_CONFIG["google_calendar"]),
        "google_docs": check_google_token("Google Docs", TOKEN_CONFIG["google_docs"]),
        "gmail_smtp": check_gmail_smtp()
    }
    
    log("=" * 70)
    
    # Summary
    healthy = sum(1 for r in results.values() if r in [True, "healthy"])
    warning = sum(1 for r in results.values() if r in ["warning"])
    critical = sum(1 for r in results.values() if r in [False, "critical", "missing"])
    
    log(f"Summary: {healthy} healthy | {warning} warning | {critical} critical")
    log("=" * 70)
    
    # Send alerts for critical issues
    critical_issues = []
    for name, status in results.items():
        if status in ["critical", "missing"]:
            if name == "google_calendar":
                critical_issues.append("Google Calendar token expired — re-auth required")
            elif name == "google_docs":
                critical_issues.append("Google Docs token expired — re-auth required")
    
    if critical_issues:
        alert_msg = "\n".join(f"• {issue}" for issue in critical_issues)
        send_alert(alert_msg, is_critical=True, issue_key="google_tokens_critical")
    
    return results

if __name__ == "__main__":
    results = run_health_check()
    
    # Exit with error code if anything is critical
    critical_count = sum(1 for r in results.values() if r in [False, "critical", "missing"])
    if critical_count > 0:
        exit(1)
    exit(0)