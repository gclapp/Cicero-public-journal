#!/usr/bin/env python3
"""
Complete Calendar Authorization with Code
Usage: python3 calendar_auth_complete.py 'YOUR_AUTH_CODE'
"""

import sys
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import Flow

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 calendar_auth_complete.py 'YOUR_AUTH_CODE'")
        sys.exit(1)
    
    code = sys.argv[1]
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    print("Fetching token...")
    flow.fetch_token(code=code)
    
    # Save credentials
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(flow.credentials, f)
    
    print("✅ Calendar access granted and saved!")
    print(f"Token saved to: {TOKEN_FILE}")
    print("\nYou can now run: python3 ~/.openclaw/workspace/scripts/calendar_reader.py")

if __name__ == "__main__":
    main()
