#!/usr/bin/env python3
"""
One-time setup for Google Docs authentication
Run this, complete OAuth in browser, then docs will work
"""

import os
import sys
import pickle
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add google auth libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

CREDENTIALS_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-credentials.json'
TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'


def main():
    print("=" * 60)
    print("Google Docs Authentication Setup")
    print("=" * 60)
    print()
    
    # Create the flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH), 
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Out-of-band redirect
    )
    
    # Get the authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("1. Visit this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("2. Sign in and authorize the app")
    print()
    print("3. Copy the authorization code shown")
    print()
    code = input("4. Paste the code here: ").strip()
    print()
    
    # Exchange code for token
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save the token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
        
        print("✅ Success! Token saved to:", TOKEN_PATH)
        print()
        print("You can now use gdocs_simple.py to create and edit documents.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
