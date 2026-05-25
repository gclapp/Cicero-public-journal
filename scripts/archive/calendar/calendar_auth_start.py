#!/usr/bin/env python3
"""
One-time Calendar Authorization
Run this, then provide the auth code
"""

import pickle
from pathlib import Path
from google_auth_oauthlib.flow import Flow

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("="*70)
    print("🔗 Open this URL in your browser:")
    print("="*70)
    print(auth_url)
    print("="*70)
    print("\nAfter granting access, you'll get an authorization code.")
    print("Run: python3 ~/.openclaw/workspace/scripts/calendar_auth_complete.py 'YOUR_CODE_HERE'")

if __name__ == "__main__":
    main()
