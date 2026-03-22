#!/usr/bin/env python3
"""Quick calendar auth with provided code"""
import sys
from google_auth_oauthlib.flow import Flow
from pathlib import Path
import pickle

if len(sys.argv) < 2:
    print("Usage: python3 quick_auth.py <AUTH_CODE>")
    sys.exit(1)

code = sys.argv[1]

flow = Flow.from_client_secrets_file(
    '/home/ubuntu/.openclaw/credentials/calendar-credentials.json',
    scopes=['https://www.googleapis.com/auth/calendar.readonly'],
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

try:
    flow.fetch_token(code=code)
    
    # Save token
    TOKEN_FILE = Path.home() / '.openclaw' / 'credentials' / 'calendar-token.pickle'
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(flow.credentials, f)
    
    print('✅ Token saved successfully!')
    print(f'Token location: {TOKEN_FILE}')
    
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
