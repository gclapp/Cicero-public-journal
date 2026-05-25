#!/usr/bin/env python3
"""
Whoop Token Exchange - Swap auth code for access + refresh tokens
"""

import json
import sys
import requests
from pathlib import Path

CONFIG_FILE = Path.home() / ".openclaw" / "credentials" / "whoop-config.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "whoop-tokens.json"

def exchange_code(auth_code):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    client_id = config['client_id']
    client_secret = config['client_secret']
    redirect_uri = config['redirect_uri']
    
    # Exchange code for tokens
    token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
    
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    
    print("Exchanging code for tokens...")
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        
        # Check for refresh token
        if 'refresh_token' in tokens:
            print("✅ SUCCESS! Refresh token received.")
        else:
            print("⚠️  Warning: No refresh token. May need to re-auth with offline scope.")
        
        # Save tokens
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"✅ Tokens saved to {TOKEN_FILE}")
        print(f"\nAccess token expires in: {tokens.get('expires_in', 'unknown')} seconds")
        print(f"Scope: {tokens.get('scope', 'unknown')}")
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 whoop_exchange.py 'AUTHORIZATION_CODE'")
        sys.exit(1)
    
    auth_code = sys.argv[1]
    
    if exchange_code(auth_code):
        print("\n🎉 Whoop authentication complete!")
        print("You can now run: python3 ~/.openclaw/workspace/scripts/whoop_fetch.py")
    else:
        print("\n❌ Authentication failed. Check the code and try again.")

if __name__ == "__main__":
    main()
