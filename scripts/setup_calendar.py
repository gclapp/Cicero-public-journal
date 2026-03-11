#!/usr/bin/env python3
"""
Google Calendar Integration Setup
Reads Geoff's shared calendar for travel events and morning updates
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
CONFIG_DIR = Path.home() / ".openclaw" / "config"
CALENDAR_CONFIG = CONFIG_DIR / "calendar-config.json"

def setup_calendar():
    """Guide through Google Calendar API setup"""
    print("=" * 60)
    print("🔧 Google Calendar Integration Setup")
    print("=" * 60)
    print()
    print("To read your shared calendar, I need to set up OAuth credentials.")
    print()
    print("Steps:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project (or use existing)")
    print("3. Enable Google Calendar API")
    print("4. Create OAuth 2.0 credentials (Desktop app)")
    print("5. Download credentials.json")
    print()
    
    # Check if credentials already exist
    creds_file = CREDENTIALS_DIR / "calendar-credentials.json"
    
    if creds_file.exists():
        print(f"✅ Credentials file found: {creds_file}")
        print("Setting up calendar access...")
        return True
    else:
        print("❌ No credentials file found.")
        print(f"\nPlease save your Google Calendar API credentials to:")
        print(f"  {creds_file}")
        print()
        print("Expected format (credentials.json from Google Cloud Console):")
        print(json.dumps({
            "installed": {
                "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
                "project_id": "your-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "YOUR_CLIENT_SECRET",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }, indent=2))
        return False

def create_calendar_reader():
    """Create the calendar reading script"""
    script_content = '''#!/usr/bin/env python3
"""
Calendar Reader - Fetches Geoff's events for morning updates
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

# Configuration
CREDENTIALS_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"

# If modifying these scopes, delete the token file
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    """Get authenticated calendar service"""
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print("❌ Calendar credentials not found. Run setup first.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for future runs
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def get_upcoming_events(days=7, max_results=10):
    """Get upcoming calendar events"""
    service = get_calendar_service()
    if not service:
        return []
    
    # Calculate time range
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
        
        # Format events
        formatted = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Parse datetime
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                start_str = start_dt.strftime('%A, %B %d at %I:%M %p')
            else:
                start_dt = datetime.fromisoformat(start)
                start_str = start_dt.strftime('%A, %B %d')
            
            formatted.append({
                'summary': event.get('summary', 'No title'),
                'start': start_str,
                'location': event.get('location', ''),
                'description': event.get('description', '')[:200],
                'is_travel': any(word in event.get('summary', '').lower() 
                               for word in ['flight', 'travel', 'trip', 'hotel', 'nyc', 'new york', 'portland', 'scottsdale'])
            })
        
        return formatted
        
    except Exception as e:
        print(f"❌ Error fetching calendar: {e}")
        return []

def get_travel_events(events):
    """Filter for travel-related events"""
    travel_keywords = ['flight', 'travel', 'trip', 'hotel', 'airport', 'delta', 'united', 'american airlines']
    
    travel_events = []
    for event in events:
        summary = event.get('summary', '').lower()
        if any(keyword in summary for keyword in travel_keywords):
            travel_events.append(event)
    
    return travel_events

def main():
    """Main function to fetch and display calendar"""
    print("📅 Fetching upcoming events...")
    
    events = get_upcoming_events(days=14, max_results=20)
    
    if not events:
        print("No upcoming events found.")
        return
    
    print(f"\\n📊 Found {len(events)} upcoming events:")
    print("=" * 60)
    
    for event in events:
        emoji = "✈️" if event['is_travel'] else "📅"
        print(f"\\n{emoji} {event['summary']}")
        print(f"   📆 {event['start']}")
        if event['location']:
            print(f"   📍 {event['location']}")
    
    # Show travel summary
    travel = get_travel_events(events)
    if travel:
        print(f"\\n✈️ TRAVEL SUMMARY: {len(travel)} trip(s) detected")
        for t in travel:
            print(f"   - {t['summary']} on {t['start']}")
    
    # Save to file for morning updates
    output_file = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
    with open(output_file, 'w') as f:
        json.dump({
            'last_updated': datetime.now().isoformat(),
            'total_events': len(events),
            'travel_events': len(travel),
            'events': events
        }, f, indent=2)
    
    print(f"\\n💾 Saved to: {output_file}")

if __name__ == "__main__":
    main()
'''
    
    script_path = Path.home() / ".openclaw" / "workspace" / "scripts" / "calendar_reader.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"✅ Created calendar reader script: {script_path}")
    return script_path

if __name__ == "__main__":
    if setup_calendar():
        script = create_calendar_reader()
        print(f"\\n🚀 Ready to use!")
        print(f"Run: python3 {script}")
    else:
        print("\\n⚠️  Setup incomplete - need Google Calendar API credentials")
