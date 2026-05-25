#!/usr/bin/env python3
"""
Exchange Google OAuth code for token (non-interactive)
Usage: python3 gdocs_auth_exchange.py <auth_code>
"""

import sys
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

CREDENTIALS_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-credentials.json'
TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
CODE_VERIFIER_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-pkce.json'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gdocs_auth_exchange.py <auth_code>")
        print("")
        print("First run gdocs_auth_setup.py to get the URL, then paste the code here.")
        sys.exit(1)
    
    auth_code = sys.argv[1]
    
    # Load code verifier if it exists
    code_verifier = None
    if CODE_VERIFIER_PATH.exists():
        import json
        with open(CODE_VERIFIER_PATH) as f:
            pkce_data = json.load(f)
            code_verifier = pkce_data.get('verifier')  # Note: stored as 'verifier' not 'code_verifier'
    
    # Create flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    # Set code verifier if we have it
    if code_verifier:
        flow.code_verifier = code_verifier
    
    # Exchange code for token
    try:
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Save token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
        
        print("✅ Google Docs token saved successfully!")
        print(f"Token saved to: {TOKEN_PATH}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
