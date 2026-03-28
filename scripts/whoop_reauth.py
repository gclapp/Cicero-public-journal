#!/usr/bin/env python3
"""
Whoop OAuth Re-authorization Helper
Generates the authorization URL for Geoff to re-authorize Whoop
"""

import json
import secrets
import urllib.parse
from pathlib import Path

CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "whoop-config.json"

def generate_auth_url():
    """Generate Whoop OAuth authorization URL"""
    
    # Load config
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    
    client_id = config['client_id']
    redirect_uri = config['redirect_uri']
    
    # Generate PKCE verifier
    code_verifier = secrets.token_urlsafe(64)
    
    # Save verifier for later
    verifier_file = Path.home() / ".openclaw" / "workspace" / "config" / "whoop-pkce-verifier.txt"
    verifier_file.write_text(code_verifier)
    
    # Generate code challenge
    import hashlib
    import base64
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    # Build auth URL
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'read:recovery read:sleep read:cycles read:workout read:profile read:body_measurement offline',
        'state': secrets.token_urlsafe(16),
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://api.prod.whoop.com/oauth/oauth2/auth?{urllib.parse.urlencode(params)}"
    
    return auth_url, params['state']

if __name__ == "__main__":
    url, state = generate_auth_url()
    print("=" * 70)
    print("WHOOP RE-AUTHORIZATION REQUIRED")
    print("=" * 70)
    print("\n1. Click this link to authorize:")
    print(f"\n{url}\n")
    print(f"State (for verification): {state}")
    print("\n2. After authorizing, you'll be redirected to a page with a CODE")
    print("3. Copy that CODE and send it to me")
    print("4. I'll complete the OAuth flow and save your new token")
    print("=" * 70)
