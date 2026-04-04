#!/usr/bin/env python3
"""
Token Auto-Refresh System
Refreshes tokens before they expire to prevent service interruptions
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Token file paths
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
TOKEN_FILES = {
    "whoop": {
        "access_token": Path.home() / ".whoop_token",
        "refresh_token": Path.home() / ".whoop_refresh_token",
        "config": Path.home() / ".openclaw/workspace/config/whoop-config.json",
        "credentials": CREDENTIALS_DIR / "whoop-tokens.json",
        "refresh_days": 25,  # Refresh after 25 days (expires ~30)
        "refresh_function": "refresh_whoop"
    },
    "google_calendar": {
        "token": CREDENTIALS_DIR / "calendar-token.pickle",
        "refresh_days": 5,  # Refresh after 5 days (threshold: 6)
        "refresh_function": "refresh_google_calendar"
    },
    "google_docs": {
        "token": CREDENTIALS_DIR / "gdocs-token.pickle",
        "refresh_days": 5,  # Refresh after 5 days (threshold: 6)
        "refresh_function": "refresh_google_docs"
    },
    "gmail_smtp": {
        "config": Path.home() / ".openclaw/email_config.json",
        "refresh_days": 25,  # Monitor after 25 days (threshold: 30)
        "refresh_function": "monitor_gmail"
    }
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def get_file_age_days(filepath):
    """Get age of file in days"""
    if not filepath.exists():
        return None
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    age = (datetime.now() - mtime).days
    return age

def refresh_whoop():
    """Refresh Whoop token using refresh token"""
    try:
        # Load config
        with open(TOKEN_FILES["whoop"]["config"]) as f:
            config = json.load(f)
        
        # Load refresh token
        refresh_token_path = TOKEN_FILES["whoop"]["refresh_token"]
        if not refresh_token_path.exists():
            log("❌ Whoop refresh token not found")
            return False
        
        refresh_token = refresh_token_path.read_text().strip()
        
        # Exchange for new tokens
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'redirect_uri': config['redirect_uri']
        }
        
        response = requests.post('https://api.prod.whoop.com/oauth/oauth2/token', data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            
            # Save access token
            TOKEN_FILES["whoop"]["access_token"].write_text(tokens['access_token'])
            
            # Update credentials file
            with open(TOKEN_FILES["whoop"]["credentials"], 'w') as f:
                json.dump(tokens, f, indent=2)
            
            # Update refresh token if provided
            if 'refresh_token' in tokens:
                TOKEN_FILES["whoop"]["refresh_token"].write_text(tokens['refresh_token'])
            
            # Set secure permissions
            os.chmod(TOKEN_FILES["whoop"]["access_token"], 0o600)
            os.chmod(TOKEN_FILES["whoop"]["refresh_token"], 0o600)
            os.chmod(TOKEN_FILES["whoop"]["credentials"], 0o600)
            
            log("✅ Whoop token auto-refreshed")
            return True
        else:
            log(f"❌ Whoop refresh failed: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"❌ Whoop refresh error: {e}")
        return False

def check_and_refresh_tokens():
    """Check all tokens and refresh if needed"""
    log("=" * 60)
    log("Starting Token Auto-Refresh Check")
    log("=" * 60)
    
    refreshed = []
    needs_attention = []
    
    for name, config in TOKEN_FILES.items():
        # Determine which file to check for age
        if "access_token" in config:
            check_file = config["access_token"]
        elif "token" in config:
            check_file = config["token"]
        elif "config" in config:
            check_file = config["config"]
        else:
            continue
        
        age = get_file_age_days(check_file)
        
        if age is None:
            log(f"⚠️  {name}: Token file not found")
            needs_attention.append(name)
            continue
        
        threshold = config["refresh_days"]
        
        if age >= threshold:
            log(f"🔄 {name}: Token is {age} days old (threshold: {threshold}) — refreshing...")
            
            if config.get("refresh_function") == "refresh_whoop":
                if refresh_whoop():
                    refreshed.append(name)
                else:
                    needs_attention.append(name)
            else:
                # For Google tokens, we can't auto-refresh without user interaction
                # Just log that attention is needed
                log(f"⚠️  {name}: Requires manual re-authorization")
                needs_attention.append(name)
        else:
            log(f"✅ {name}: Token is {age} days old (healthy)")
    
    log("=" * 60)
    log(f"Refreshed: {len(refreshed)} | Needs attention: {len(needs_attention)}")
    log("=" * 60)
    
    return refreshed, needs_attention

if __name__ == "__main__":
    check_and_refresh_tokens()
