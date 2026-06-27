#!/usr/bin/env python3
"""
Calendar Reader - Device Auth Flow (No Browser Required)
"""

import os
import json
import pickle
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
CODE_VERIFIER_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-code-verifier.txt"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_code_verifier():
    """Load or create the PKCE code verifier used for calendar auth."""
    import base64
    import secrets

    if CODE_VERIFIER_FILE.exists():
        return CODE_VERIFIER_FILE.read_text().strip()

    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')
    CODE_VERIFIER_FILE.write_text(code_verifier)
    return code_verifier

def get_auth_url():
    """Build the Google Calendar auth URL for manual reauthorization."""
    import base64
    import hashlib

    code_verifier = get_code_verifier()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').rstrip('=')

    return (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id=[REDACTED]"
        f"&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob"
        f"&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&prompt=consent"
        f"&access_type=offline"
    )

def authenticate(auth_code=None):
    """Authenticate using device flow (no browser)"""
    from google_auth_oauthlib.flow import Flow
    
    code_verifier = get_code_verifier()
    auth_url = get_auth_url()
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    if auth_code is None:
        print("\n" + "="*70)
        print("🔐 Google Calendar Authorization Required")
        print("="*70)
        print("\n1. Open this URL in your browser:")
        print(f"   {auth_url}")
        print("\n2. Sign in with your Google account")
        print("3. Grant permission to read your calendar")
        print("4. Copy the authorization code")
        print("\n5. Paste the code here and press Enter:")
        
        auth_code = input("> ").strip()
    
    # Fetch token with our code verifier
    flow.fetch_token(code=auth_code, code_verifier=code_verifier)
    
    # Save credentials
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(flow.credentials, f)
    
    print("\n✅ Calendar access granted!")
    return flow.credentials

def get_calendar_service():
    """Get authenticated calendar service"""
    creds = None
    
    # Load client credentials
    with open(CREDENTIALS_FILE) as f:
        client_creds = json.load(f)['installed']
    
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as f:
            data = pickle.load(f)
            # Handle both dict and Credentials object formats
            if isinstance(data, dict):
                creds = Credentials(
                    token=data.get('access_token'),
                    refresh_token=data.get('refresh_token'),
                    token_uri=client_creds['token_uri'],
                    client_id=client_creds['client_id'],
                    client_secret=client_creds['client_secret'],
                    scopes=data.get('scope', '').split() if isinstance(data.get('scope'), str) else SCOPES
                )
            else:
                creds = data
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                raise RuntimeError(
                    "Calendar authorization has expired or been revoked.\n"
                    "Open this URL, approve access, then rerun with --auth-code CODE:\n"
                    f"{get_auth_url()}"
                )
            with open(TOKEN_FILE, 'wb') as f:
                pickle.dump(creds, f)
        else:
            creds = authenticate()
    
    return build('calendar', 'v3', credentials=creds)

TRAVEL_KEYWORDS = [
    'flight', 'travel', 'trip', 'hotel', 'stay at',
    'delta', 'united', 'american', 'alaska', 'jetblue', 'southwest',
    'nyc', 'new york', 'jfk', 'lga', 'ewr',
    'san francisco', 'sfo',
    'san diego',
    'portland', 'pdx',
    'scottsdale', 'phoenix', 'phx',
    'truckee', 'tahoe', 'reno', 'rno',
    'providence', 'pvd'
]


def is_travel_event(event):
    """Classify travel using title, location, and description."""
    text = " ".join([
        event.get('summary', ''),
        event.get('location', ''),
        event.get('description', ''),
    ]).lower()
    return any(word in text for word in TRAVEL_KEYWORDS)


def get_upcoming_events(days=14, max_results=20):
    """Get upcoming calendar events"""
    service = get_calendar_service()
    if not service:
        return []
    
    now = datetime.now(timezone.utc)
    time_min = now.isoformat().replace('+00:00', 'Z')
    time_max = (now + timedelta(days=days)).isoformat().replace('+00:00', 'Z')
    
    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                start_str = start_dt.strftime('%A, %B %d at %I:%M %p')
            else:
                start_dt = datetime.fromisoformat(start)
                start_str = start_dt.strftime('%A, %B %d')
            
            formatted.append({
                'summary': event.get('summary', 'No title'),
                'start': start_str,
                'start_raw': start,
                'location': event.get('location', ''),
                'description': event.get('description', '')[:200],
                'is_travel': is_travel_event(event)
            })
        
        return formatted
        
    except Exception as e:
        print(f"❌ Error fetching calendar: {e}")
        return None

def main():
    """Main function to fetch and display calendar"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=90, help='Number of days to look ahead')
    parser.add_argument('--max', type=int, default=100, help='Maximum events to fetch')
    parser.add_argument('--auth-code', type=str, help='Authorization code from Google')
    parser.add_argument('--no-save', action='store_true', help='Fetch events without updating the shared calendar cache')
    args = parser.parse_args()
    
    # If auth code provided, authenticate immediately
    if args.auth_code:
        authenticate(args.auth_code)
        return
    
    print(f"📅 Fetching upcoming events ({args.days} days ahead)...")
    
    try:
        events = get_upcoming_events(days=args.days, max_results=args.max)
    except RuntimeError as e:
        print(f"🔴 {e}")
        sys.exit(2)
    if events is None:
        sys.exit(1)
    
    if not events:
        print("No upcoming events found.")
        return
    
    print(f"\n📊 Found {len(events)} upcoming events:")
    print("=" * 60)
    
    for event in events:
        emoji = "✈️" if event['is_travel'] else "📅"
        print(f"\n{emoji} {event['summary']}")
        print(f"   📆 {event['start']}")
        if event['location']:
            print(f"   📍 {event['location']}")
    
    travel = [e for e in events if e['is_travel']]
    if travel:
        print(f"\n✈️ TRAVEL SUMMARY: {len(travel)} trip(s) detected")
        for t in travel:
            print(f"   - {t['summary']} on {t['start']}")
    
    if not args.no_save:
        # Save to file
        output_file = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
        with open(output_file, 'w') as f:
            json.dump({
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_events': len(events),
                'travel_events': len(travel),
                'events': events
            }, f, indent=2)
        
        print(f"\n💾 Saved to: {output_file}")

if __name__ == "__main__":
    main()
