#!/usr/bin/env python3
"""
Calendar Auth - Process saved auth code
"""

import pickle
from pathlib import Path
from google_auth_oauthlib.flow import Flow

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
CODE_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-auth-code.txt"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def process_auth_code():
    """Process saved auth code"""
    if not CODE_FILE.exists():
        print("❌ No auth code file found")
        return False
    
    with open(CODE_FILE, 'r') as f:
        code = f.read().strip()
    
    if not code:
        print("❌ Auth code is empty")
        return False
    
    print(f"Processing auth code: {code[:20]}...")
    
    try:
        flow = Flow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            scopes=SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        
        # Generate the same auth URL to get the code challenge
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # Now fetch token with the code
        flow.fetch_token(code=code)
        
        # Save credentials
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(flow.credentials, f)
        
        # Clean up
        CODE_FILE.unlink()
        
        print("✅ Calendar access granted!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if process_auth_code():
        print("\nYou can now run: python3 scripts/calendar_reader.py")
    else:
        print("\nFailed to process auth code. Please try again.")
