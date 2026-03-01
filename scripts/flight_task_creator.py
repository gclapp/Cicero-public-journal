#!/usr/bin/env python3
"""
Flight Detection & Task Creation
Scans Google Calendar for flights and creates Todoist tasks automatically
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    """Authenticate and return Google Calendar service"""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def find_flight_events(service, days_ahead=60):
    """Scan calendar for flight-related events"""
    
    # Calculate time range
    now = datetime.utcnow()
    future = now + timedelta(days=days_ahead)
    
    now_str = now.isoformat() + 'Z'
    future_str = future.isoformat() + 'Z'
    
    # Search for events
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now_str,
        timeMax=future_str,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # Filter for flight-related events
    flight_keywords = ['flight', 'depart', 'arrive', 'travel', 'trip', 'airport', 
                       'jfk', 'lax', 'sfo', 'delta', 'united', 'american', 'southwest']
    
    flights = []
    
    for event in events:
        summary = event.get('summary', '').lower()
        description = event.get('description', '').lower()
        location = event.get('location', '').lower()
        
        # Check if event matches flight keywords
        is_flight = any(keyword in summary or keyword in description or keyword in location 
                       for keyword in flight_keywords)
        
        if is_flight:
            start = event['start'].get('dateTime', event['start'].get('date'))
            flights.append({
                'summary': event.get('summary'),
                'start': start,
                'location': event.get('location', ''),
                'description': event.get('description', '')[:100]  # Truncate
            })
    
    return flights

def create_todoist_flight_task(flight):
    """Create Todoist task for flight"""
    import subprocess
    
    flight_date = datetime.fromisoformat(flight['start'].replace('Z', '+00:00'))
    flight_date_str = flight_date.strftime('%Y-%m-%d')
    task_name = f"✈️ FLIGHT: {flight['summary']} ({flight_date_str})"
    
    # Calculate due dates for subtasks
    rover_due = (flight_date - timedelta(days=4)).strftime('%Y-%m-%d')
    check_due = (flight_date - timedelta(days=2)).strftime('%Y-%m-%d')
    uber_due = (flight_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Create main flight task
    cmd = f'todoist add "{task_name}" --project "Personal" --due "{rover_due}" --priority 2'
    subprocess.run(cmd, shell=True, capture_output=True)
    
    # Create related tasks (subtasks via naming convention)
    subprocess.run(f'todoist add "  ├─ 🐕 Rover: Schedule for {flight[\'summary\']}" --project "Personal" --due "{rover_due}"', shell=True, capture_output=True)
    subprocess.run(f'todoist add "  ├─ 🏨 Check: Hotel & flight confirmations for {flight[\'summary\']}" --project "Personal" --due "{check_due}"', shell=True, capture_output=True)
    subprocess.run(f'todoist add "  └─ 🚗 Uber: Schedule ride for {flight[\'summary\']}" --project "Personal" --due "{uber_due}"', shell=True, capture_output=True)
    
    print(f"✅ Created tasks for: {flight['summary']} on {flight_date_str}")

def main():
    """Main function"""
    print("🔍 Scanning calendar for flights...")
    
    try:
        service = get_calendar_service()
        flights = find_flight_events(service)
        
        if not flights:
            print("No flights found in the next 60 days.")
            return
        
        print(f"\nFound {len(flights)} flight(s):\n")
        
        for flight in flights:
            print(f"✈️  {flight['summary']}")
            print(f"   Date: {flight['start']}")
            print(f"   Location: {flight['location']}")
            print()
            
            # Create Todoist tasks
            create_todoist_flight_task(flight)
        
        print(f"\n✅ Created Todoist tasks for {len(flights)} flight(s)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure credentials.json is set up with Google Calendar API")

if __name__ == '__main__':
    main()