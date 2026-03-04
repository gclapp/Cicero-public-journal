#!/usr/bin/env python3
"""
Calendar Reader - Device Auth Flow (No Browser Required)
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate():
    """Authenticate using device flow (no browser)"""
    from google_auth_oauthlib.flow import Flow
    
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    print("\n" + "="*70)
    print("🔐 Google Calendar Authorization Required")
    print("="*70)
    print("\n1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print("\n2. Sign in with your Google account")
    print("3. Grant permission to read your calendar")
    print("4. Copy the authorization code")
    print("\n5. Paste the code here and press Enter:")
    
    code = input("> ").strip()
    
    flow.fetch_token(code=code)
    
    # Save credentials
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(flow.credentials, f)
    
    print("\n✅ Calendar access granted!")
    return flow.credentials

def get_calendar_service():
    """Get authenticated calendar service"""
    creds = None
    
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as f:
                pickle.dump(creds, f)
        else:
            creds = authenticate()
    
    return build('calendar', 'v3', credentials=creds)

def get_upcoming_events(days=14, max_results=20):
    """Get upcoming calendar events"""
    service = get_calendar_service()
    if not service:
        return []
    
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'
    
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
                'is_travel': any(word in event.get('summary', '').lower() 
                               for word in ['flight', 'travel', 'trip', 'hotel', 'nyc', 'new york', 'portland', 'scottsdale', 'delta', 'united', 'american'])
            })
        
        return formatted
        
    except Exception as e:
        print(f"❌ Error fetching calendar: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main function to fetch and display calendar"""
    print("📅 Fetching upcoming events...")
    
    events = get_upcoming_events(days=14, max_results=20)
    
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
    
    # Save to file
    output_file = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
    with open(output_file, 'w') as f:
        json.dump({
            'last_updated': datetime.now().isoformat(),
            'total_events': len(events),
            'travel_events': len(travel),
            'events': events
        }, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")

if __name__ == "__main__":
    main()
