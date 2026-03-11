#!/usr/bin/env python3
"""
Whoop OAuth Helper - Generate auth URL with offline scope
"""

import json
import urllib.parse
from pathlib import Path

CONFIG_FILE = Path.home() / ".openclaw" / "credentials" / "whoop-config.json"

def main():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    client_id = config['client_id']
    redirect_uri = config['redirect_uri']
    
    # Build auth URL with offline scope (for refresh token)
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'offline read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement',
        'state': 'whoop_auth_2026'
    }
    
    auth_url = f"https://api.prod.whoop.com/oauth/oauth2/auth?{urllib.parse.urlencode(params)}"
    
    print("="*70)
    print("🔗 Whoop Authorization Required")
    print("="*70)
    print("\nOpen this URL in your browser:")
    print(auth_url)
    print("\n" + "="*70)
    print("\nAfter granting access, you'll be redirected to GitHub Pages.")
    print("Copy the CODE from the URL (the part after 'code=')")
    print("\nThen run:")
    print("python3 ~/.openclaw/workspace/scripts/whoop_exchange.py 'YOUR_CODE'")

if __name__ == "__main__":
    main()
