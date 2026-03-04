#!/usr/bin/env python3
"""
Calendar Intelligence Scanner
Analyzes next 30 days to build Geoff's profile
"""

import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from googleapiclient.discovery import build

TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"

def get_calendar_service():
    """Get authenticated calendar service"""
    with open(TOKEN_FILE, 'rb') as f:
        creds = pickle.load(f)
    return build('calendar', 'v3', credentials=creds)

def analyze_next_30_days():
    """Deep analysis of next 30 days"""
    service = get_calendar_service()
    
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=30)).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # Analysis buckets
    profile = {
        'restaurants': [],
        'flights': [],
        'hotels': [],
        'kid_events': [],
        'work_meetings': [],
        'personal_time': [],
        'patterns': {},
        'questions_to_ask': []
    }
    
    restaurant_keywords = ['reservation', 'l\'artusi', 'nowon', 'dinner', 'lunch', 'restaurant']
    flight_keywords = ['flight', 'delta', 'lax', 'airport', 'travel']
    hotel_keywords = ['hotel', 'courtyard', 'algonquin', 'marriott', 'stay at']
    kid_keywords = ['sophie', 'oliver', 'ollie', 'mackenzie', 'pick up', 'drop off', 'kids']
    
    for event in events:
        summary = event.get('summary', '').lower()
        location = event.get('location', '').lower()
        description = event.get('description', '').lower()
        full_text = f"{summary} {location} {description}"
        
        start = event['start'].get('dateTime', event['start'].get('date'))
        
        # Categorize
        if any(kw in full_text for kw in restaurant_keywords):
            profile['restaurants'].append({
                'name': event.get('summary'),
                'location': event.get('location'),
                'date': start,
                'type': 'dining'
            })
        
        if any(kw in full_text for kw in flight_keywords):
            profile['flights'].append({
                'summary': event.get('summary'),
                'date': start,
                'location': event.get('location')
            })
        
        if any(kw in full_text for kw in hotel_keywords):
            profile['hotels'].append({
                'name': event.get('summary'),
                'location': event.get('location'),
                'date': start
            })
        
        if any(kw in full_text for kw in kid_keywords):
            profile['kid_events'].append({
                'summary': event.get('summary'),
                'date': start
            })
        
        # Detect work meetings (Microsoft Teams, Zoom, no personal keywords)
        if 'teams' in full_text or 'zoom' in full_text or 'meeting' in full_text:
            if not any(kw in full_text for kw in kid_keywords + ['personal', 'family']):
                profile['work_meetings'].append({
                    'summary': event.get('summary'),
                    'date': start
                })
    
    # Generate questions based on patterns
    if profile['restaurants']:
        restaurants = [r['name'] for r in profile['restaurants']]
        profile['questions_to_ask'].append(f"I see you have reservations at {', '.join(restaurants[:3])}. Are these business dinners or personal?")
    
    if len(profile['flights']) >= 3:
        profile['questions_to_ask'].append(f"You have {len(profile['flights'])} flights in the next 30 days. Is this a heavy travel month or typical for you?")
    
    if profile['kid_events']:
        profile['questions_to_ask'].append("I see regular school pickups for Sophie and Oliver. Do you share custody or is this your regular schedule?")
    
    # Detect patterns
    locations = Counter([e.get('location', '').split(',')[0] for e in events if e.get('location')])
    profile['patterns']['top_locations'] = locations.most_common(5)
    
    return profile, events

def main():
    print("🔍 Scanning next 30 days of calendar...")
    print("=" * 70)
    
    profile, all_events = analyze_next_30_days()
    
    print(f"\n📊 FOUND {len(all_events)} EVENTS")
    print("=" * 70)
    
    # Restaurants
    if profile['restaurants']:
        print(f"\n🍽️  RESTAURANTS ({len(profile['restaurants'])}):")
        for r in profile['restaurants'][:5]:
            print(f"   • {r['name']}")
            if r['location']:
                print(f"     📍 {r['location']}")
    
    # Flights
    if profile['flights']:
        print(f"\n✈️  FLIGHTS ({len(profile['flights'])}):")
        for f in profile['flights']:
            print(f"   • {f['summary']}")
            if f['location']:
                print(f"     📍 {f['location']}")
    
    # Hotels
    if profile['hotels']:
        print(f"\n🏨 HOTELS ({len(profile['hotels'])}):")
        for h in profile['hotels']:
            print(f"   • {h['name']}")
    
    # Kid events
    if profile['kid_events']:
        print(f"\n👶 KID EVENTS ({len(profile['kid_events'])}):")
        for k in profile['kid_events'][:5]:
            print(f"   • {k['summary']}")
    
    # Questions
    print(f"\n❓ QUESTIONS TO ASK:")
    for q in profile['questions_to_ask']:
        print(f"   • {q}")
    
    # Save profile
    profile_file = Path.home() / ".openclaw" / "workspace" / "memory" / "geoff-profile-calendar.md"
    
    with open(profile_file, 'w') as f:
        f.write("# Geoff's Calendar Profile (Next 30 Days)\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Events:** {len(all_events)}\n")
        f.write(f"- **Restaurants:** {len(profile['restaurants'])}\n")
        f.write(f"- **Flights:** {len(profile['flights'])}\n")
        f.write(f"- **Hotels:** {len(profile['hotels'])}\n")
        f.write(f"- **Kid Events:** {len(profile['kid_events'])}\n\n")
        
        if profile['restaurants']:
            f.write("## Restaurant Reservations\n\n")
            for r in profile['restaurants']:
                f.write(f"- **{r['name']}**\n")
                f.write(f"  - Location: {r['location']}\n")
                f.write(f"  - Date: {r['date']}\n\n")
        
        if profile['flights']:
            f.write("## Travel\n\n")
            for fl in profile['flights']:
                f.write(f"- {fl['summary']} ({fl['date']})\n")
            f.write("\n")
        
        if profile['hotels']:
            f.write("## Hotels\n\n")
            for h in profile['hotels']:
                f.write(f"- {h['name']} ({h['date']})\n")
            f.write("\n")
        
        f.write("## Open Questions\n\n")
        for q in profile['questions_to_ask']:
            f.write(f"- [ ] {q}\n")
    
    print(f"\n💾 Profile saved to: {profile_file}")

if __name__ == "__main__":
    main()
