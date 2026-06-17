#!/usr/bin/env python3
"""
Calendar Token Health Monitor
Checks if calendar token is valid and alerts before expiration
"""

import os
import sys
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "calendar-token-health.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def check_token_health():
    """Check if calendar token is healthy"""
    if not TOKEN_FILE.exists():
        log("🔴 FAIL: No token file found")
        return False, "Token file missing"
    
    try:
        with open(TOKEN_FILE, 'rb') as f:
            data = pickle.load(f)
        
        # Handle both dict and Credentials object
        if isinstance(data, dict):
            expires_at = data.get('expires_at')
            refresh_token = data.get('refresh_token')
        else:
            expires_at = data.expiry.timestamp() if data.expiry else None
            refresh_token = data.refresh_token
        
        if not refresh_token:
            log("🔴 FAIL: No refresh token - will need full re-auth")
            return False, "No refresh token"
        
        if expires_at:
            expires_dt = datetime.fromtimestamp(expires_at) if isinstance(expires_at, (int, float)) else expires_at
            time_until = expires_dt - datetime.now()
            
            if time_until.total_seconds() < 0:
                log(f"🔴 FAIL: Token expired {abs(time_until).days} days ago")
                return False, f"Token expired {abs(time_until).days} days ago"
            elif time_until.days < 2:
                log(f"🟡 WARN: Token expires in {time_until.hours:.1f} hours")
                return True, f"Token expires soon ({time_until.hours:.1f} hours)"
            else:
                log(f"🟢 OK: Token valid for {time_until.days} days")
                return True, f"Token valid for {time_until.days} days"
        else:
            log("🟡 WARN: Unknown expiration")
            return True, "Unknown expiration"
            
    except Exception as e:
        log(f"🔴 FAIL: Error reading token: {e}")
        return False, str(e)

def try_refresh():
    """Try to refresh the token"""
    try:
        from google.auth.transport.requests import Request
        
        with open(CREDENTIALS_FILE) as f:
            client_creds = json.load(f)['installed']
        
        with open(TOKEN_FILE, 'rb') as f:
            data = pickle.load(f)
        
        if isinstance(data, dict):
            creds = Credentials(
                token=data.get('access_token'),
                refresh_token=data.get('refresh_token'),
                token_uri=client_creds['token_uri'],
                client_id=client_creds['client_id'],
                client_secret=client_creds['client_secret'],
            )
        else:
            creds = data
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as f:
                pickle.dump(creds, f)
            log("🟢 SUCCESS: Token refreshed")
            return True
        
        return False
    except Exception as e:
        log(f"🔴 FAIL: Refresh failed: {e}")
        return False

def main():
    healthy, msg = check_token_health()
    
    if not healthy:
        # Try to refresh
        if try_refresh():
            sys.exit(0)
        else:
            # Send alert
            alert_msg = f"Calendar token needs re-auth: {msg}"
            log(f"ALERT: {alert_msg}")
            
            # Try to send Telegram alert
            try:
                import subprocess
                subprocess.run([
                    "python3", 
                    "/home/ubuntu/.openclaw/workspace/scripts/send_telegram.py",
                    f"⚠️ Calendar Auth Required\n\n{alert_msg}\n\nRun: python3 scripts/calendar_reader.py"
                ], check=False)
            except:
                pass
            
            sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
