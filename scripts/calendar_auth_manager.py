#!/usr/bin/env python3
"""
Calendar Auth - Store PKCE parameters for later use
"""

import pickle
import json
from pathlib import Path
from google_auth_oauthlib.flow import Flow

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
AUTH_STATE_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-auth-state.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def generate_auth_url():
    """Generate auth URL and save state"""
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    auth_url, state = flow.authorization_url(prompt='consent')
    
    # Save the flow's code verifier
    auth_state = {
        'auth_url': auth_url,
        'state': state,
        'code_verifier': flow.code_verifier
    }
    
    with open(AUTH_STATE_FILE, 'w') as f:
        json.dump(auth_state, f)
    
    print(f"\n{'='*70}")
    print("🔐 Google Calendar Authorization")
    print(f"{'='*70}")
    print(f"\nURL: {auth_url}")
    print("\n1. Open the URL above")
    print("2. Sign in and grant access")
    print("3. Copy the code")
    print("4. Run: python3 scripts/complete_calendar_auth.py 'YOUR_CODE'")
    print(f"{'='*70}\n")

def complete_auth(code):
    """Complete auth with saved state"""
    if not AUTH_STATE_FILE.exists():
        print("❌ No auth state found. Run generate_auth_url() first.")
        return False
    
    with open(AUTH_STATE_FILE, 'r') as f:
        auth_state = json.load(f)
    
    # Recreate flow with same code verifier
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob',
        state=auth_state['state']
    )
    
    # Restore code verifier
    flow.code_verifier = auth_state['code_verifier']
    
    try:
        flow.fetch_token(code=code)
        
        # Save credentials
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(flow.credentials, f)
        
        # Clean up
        AUTH_STATE_FILE.unlink()
        
        print("\n✅ SUCCESS! Calendar authenticated.")
        print("You can now run: python3 scripts/calendar_reader.py")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("The code may have expired. Please generate a new URL.")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        complete_auth(sys.argv[1])
    else:
        generate_auth_url()
