#!/usr/bin/env python3
"""Calendar auth with PKCE - generates URL and accepts code"""
import sys
import json
import pickle
import secrets
import hashlib
import base64
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def generate_pkce():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def save_pkce(code_verifier):
    """Save code verifier to file"""
    pkce_file = Path.home() / ".openclaw" / "credentials" / "calendar-pkce.json"
    with open(pkce_file, 'w') as f:
        json.dump({'code_verifier': code_verifier}, f)

def load_pkce():
    """Load code verifier from file"""
    pkce_file = Path.home() / ".openclaw" / "credentials" / "calendar-pkce.json"
    if pkce_file.exists():
        with open(pkce_file, 'r') as f:
            data = json.load(f)
            return data.get('code_verifier')
    return None

def generate_auth_url():
    """Generate authorization URL with PKCE"""
    code_verifier, code_challenge = generate_pkce()
    save_pkce(code_verifier)
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        code_challenge=code_challenge,
        code_challenge_method='S256'
    )
    
    return auth_url

def exchange_code(auth_code):
    """Exchange authorization code for token"""
    code_verifier = load_pkce()
    
    if not code_verifier:
        print("❌ Error: No code verifier found. Run with --url first.")
        return False
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    try:
        flow.fetch_token(code=auth_code, code_verifier=code_verifier)
        
        # Save credentials
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(flow.credentials, f)
        
        print("✅ Token saved successfully!")
        print(f"Location: {TOKEN_FILE}")
        
        # Verify by making a test call
        service = build('calendar', 'v3', credentials=flow.credentials)
        calendars = service.calendarList().list().execute()
        print(f"✅ Verified! Access to {len(calendars.get('items', []))} calendars")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 calendar_auth.py --url       # Generate auth URL")
        print("  python3 calendar_auth.py <CODE>      # Exchange code for token")
        sys.exit(1)
    
    if sys.argv[1] == '--url':
        url = generate_auth_url()
        print("\n" + "="*70)
        print("🔗 Open this URL in your browser:")
        print("="*70)
        print(url)
        print("\nThen run: python3 calendar_auth.py <CODE>")
    else:
        exchange_code(sys.argv[1])
