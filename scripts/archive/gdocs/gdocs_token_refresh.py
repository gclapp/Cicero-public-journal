#!/usr/bin/env python3
"""
Google Docs Token Auto-Refresh
Runs via cron to keep token fresh
"""

import os
import pickle
from datetime import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
LOG_FILE = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'gdocs-refresh.log'

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{ts}] {msg}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + "\n")

def refresh_token():
    """Refresh Google Docs token if needed"""
    if not TOKEN_PATH.exists():
        log("❌ Token file not found")
        return False
    
    try:
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
        
        # Check if refresh needed
        if creds.valid:
            log("✅ Token still valid")
            return True
        
        if creds.expired and creds.refresh_token:
            log("🔄 Token expired, refreshing...")
            creds.refresh(Request())
            
            # Save refreshed token
            with open(TOKEN_PATH, 'wb') as f:
                pickle.dump(creds, f)
            os.chmod(TOKEN_PATH, 0o600)
            
            log("✅ Token refreshed successfully")
            return True
        else:
            log("❌ Token cannot be refreshed - re-auth required")
            return False
            
    except Exception as e:
        log(f"❌ Refresh error: {e}")
        return False

if __name__ == "__main__":
    success = refresh_token()
    exit(0 if success else 1)
