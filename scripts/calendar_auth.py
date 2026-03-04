#!/usr/bin/env python3
"""
Calendar Authorization - Complete flow with PKCE
"""

import pickle
import base64
import hashlib
import secrets
from pathlib import Path
from google_auth_oauthlib.flow import Flow

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
VERIFIER_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-verifier.txt"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def generate_pkce():
    """Generate PKCE verifier and challenge"""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode('ascii')
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b'=').decode('ascii')
    return verifier, challenge

def step1_generate_url():
    """Generate authorization URL"""
    verifier, challenge = generate_pkce()
    
    # Save verifier for step 2
    with open(VERIFIER_FILE, 'w') as f:
        f.write(verifier)
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        code_challenge=challenge,
        code_challenge_method='S256'
    )
    
    print("="*70)
    print("🔗 Open this URL in your browser:")
    print("="*70)
    print(auth_url)
    print("="*70)
    print("\nAfter granting access, run:")
    print(f"python3 {Path(__file__)} STEP2 'YOUR_CODE_HERE'")

def step2_exchange_code(code):
    """Exchange authorization code for token"""
    # Load verifier
    if not VERIFIER_FILE.exists():
        print("❌ Verifier not found. Run STEP1 first.")
        return
    
    with open(VERIFIER_FILE, 'r') as f:
        verifier = f.read().strip()
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    print("Fetching token...")
    flow.fetch_token(code=code, code_verifier=verifier)
    
    # Save credentials
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(flow.credentials, f)
    
    # Clean up verifier
    VERIFIER_FILE.unlink()
    
    print("✅ Calendar access granted and saved!")
    print(f"Token saved to: {TOKEN_FILE}")
    print("\nTesting calendar access...")
    
    # Quick test
    from googleapiclient.discovery import build
    service = build('calendar', 'v3', credentials=flow.credentials)
    events_result = service.events().list(
        calendarId='primary',
        maxResults=5,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    print(f"✅ Successfully connected! Found {len(events)} upcoming events.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        step1_generate_url()
    elif len(sys.argv) >= 3 and sys.argv[1] == 'STEP2':
        step2_exchange_code(sys.argv[2])
    else:
        print("Usage:")
        print(f"  python3 {Path(__file__)}              # Generate auth URL")
        print(f"  python3 {Path(__file__)} STEP2 'CODE' # Exchange code for token")
