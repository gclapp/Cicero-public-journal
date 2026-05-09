#!/usr/bin/env python3
"""
Travel Flight Monitor - Track flights and check for delays/gate changes
Monitors flights daily until departure and alerts on status changes
"""

import json
import os
import subprocess
import re
import requests
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
FLIGHT_DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "tracked-flights.json"

# OpenSky Network API for live flight tracking
OPENSKY_API = "https://opensky-network.org/api"

# AviationStack API for flight schedules (optional, for detailed info)
AVIATIONSTACK_API_KEY = os.environ.get('AVIATIONSTACK_API_KEY', '')


def load_calendar():
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)


def load_tracked_flights():
    """Load currently tracked flights"""
    if not FLIGHT_DATA_FILE.exists():
        return {}
    with open(FLIGHT_DATA_FILE, 'r') as f:
        return json.load(f)


def save_tracked_flights(flights):
    """Save tracked flights to file"""
    FLIGHT_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FLIGHT_DATA_FILE, 'w') as f:
        json.dump(flights, f, indent=2)


def extract_flight_number(text):
    """
    Extract flight numbers from text
    Returns list of (airline_code, flight_number) tuples
    """
    patterns = [
        # Delta patterns
        (r'Delta\s+(?:Air\s+Lines?\s+)?(?:flight\s+)?(\d+)', 'DL'),
        (r'DL\s+(\d+)', 'DL'),
        # United patterns
        (r'United\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', 'UA'),
        (r'UA\s+(\d+)', 'UA'),
        # American patterns
        (r'American\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', 'AA'),
        (r'AA\s+(\d+)', 'AA'),
        # JetBlue patterns
        (r'JetBlue\s+(?:Airways?\s+)?(?:flight\s+)?(\d+)', 'B6'),
        (r'B6\s+(\d+)', 'B6'),
        # Southwest patterns
        (r'Southwest\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', 'WN'),
        (r'WN\s+(\d+)', 'WN'),
        # Alaska patterns
        (r'Alaska\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', 'AS'),
        (r'AS\s+(\d+)', 'AS'),
    ]
    
    found_flights = []
    text_upper = text.upper()
    
    for pattern, default_code in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            flight_num = match if isinstance(match, str) else match[0]
            found_flights.append((default_code, flight_num))
    
    # Also try generic pattern for IATA codes followed by numbers
    generic_pattern = r'\b([A-Z]{2})\s*(\d{1,4})\b'
    generic_matches = re.findall(generic_pattern, text_upper)
    for code, num in generic_matches:
        if code in ['DL', 'UA', 'AA', 'B6', 'WN', 'AS', 'F9', 'NK', 'HA']:
            found_flights.append((code, num))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_flights = []
    for flight in found_flights:
        if flight not in seen:
            seen.add(flight)
            unique_flights.append(flight)
    
    return unique_flights


def parse_flight_datetime(date_str):
    """Parse flight date/time from calendar"""
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None


def get_flight_status_from_opensky(airline_code, flight_number):
    """
    Check flight status using OpenSky Network
    Returns dict with status info or None if not found
    """
    try:
        # Construct callsign (e.g., "DAL960" for Delta 960)
        airline_map = {
            'DL': 'DAL', 'UA': 'UAL', 'AA': 'AAL', 'B6': 'JBU',
            'WN': 'SWA', 'AS': 'ASA', 'F9': 'FFT', 'NK': 'NKS', 'HA': 'HAL'
        }
        callsign_prefix = airline_map.get(airline_code, airline_code)
        callsign = f"{callsign_prefix}{flight_number}"
        
        # Query OpenSky for flights with this callsign
        url = f"{OPENSKY_API}/states/all"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        states = data.get('states', [])
        
        for state in states:
            if state[1] and state[1].strip().upper() == callsign.upper():
                return {
                    'callsign': state[1].strip(),
                    'origin_country': state[2],
                    'longitude': state[5],
                    'latitude': state[6],
                    'altitude': state[7],  # meters
                    'velocity': state[9],  # m/s
                    'heading': state[10],
                    'vertical_rate': state[11],
                    'icao24': state[0]
                }
        
        return None
    except Exception as e:
        print(f"   ⚠️  OpenSky API error: {e}")
        return None


def get_flight_schedule_info(airline_code, flight_number, date_str=None):
    """
    Get flight schedule information
    Returns dict with departure/arrival info
    """
    # Without API key, return basic info with search links
    if not AVIATIONSTACK_API_KEY:
        return {
            'airline': airline_code,
            'flight_number': flight_number,
            'status': 'unknown',
            'search_links': [
                f"https://www.google.com/travel/flights?q={airline_code}{flight_number}",
                f"https://www.flightradar24.com/data/flights/{airline_code}{flight_number}",
                f"https://www.flightaware.com/live/flight/{airline_code}{flight_number}"
            ]
        }
    
    # With API key, fetch detailed info
    try:
        url = f"http://api.aviationstack.com/v1/flights"
        params = {
            'access_key': AVIATIONSTACK_API_KEY,
            'flight_iata': f"{airline_code}{flight_number}"
        }
        if date_str:
            params['flight_date'] = date_str
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('data'):
            flight = data['data'][0]
            return {
                'airline': airline_code,
                'flight_number': flight_number,
                'status': flight.get('flight_status', 'unknown'),
                'departure': {
                    'airport': flight.get('departure', {}).get('airport'),
                    'iata': flight.get('departure', {}).get('iata'),
                    'scheduled': flight.get('departure', {}).get('scheduled'),
                    'estimated': flight.get('departure', {}).get('estimated'),
                    'actual': flight.get('departure', {}).get('actual'),
                    'gate': flight.get('departure', {}).get('gate'),
                    'terminal': flight.get('departure', {}).get('terminal')
                },
                'arrival': {
                    'airport': flight.get('arrival', {}).get('airport'),
                    'iata': flight.get('arrival', {}).get('iata'),
                    'scheduled': flight.get('arrival', {}).get('scheduled'),
                    'estimated': flight.get('arrival', {}).get('estimated'),
                    'actual': flight.get('arrival', {}).get('actual'),
                    'gate': flight.get('arrival', {}).get('gate'),
                    'terminal': flight.get('arrival', {}).get('terminal')
                }
            }
    except Exception as e:
        print(f"   ⚠️  AviationStack API error: {e}")
    
    return None


def send_flight_alert(flight_info, alert_type, details):
    """Send alert about flight status changes"""
    airline_code = flight_info.get('airline', 'Unknown')
    flight_number = flight_info.get('flight_number', 'Unknown')
    
    subject = f"✈️ Flight Alert: {airline_code} {flight_number} - {alert_type}"
    
    body = f"""
<h2>Flight Status Alert</h2>

<p><strong>Flight:</strong> {airline_code} {flight_number}</p>
<p><strong>Alert Type:</strong> {alert_type}</p>

<p>{details}</p>

<p><em>Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}</em></p>
"""
    
    # Send email
    try:
        email_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
        if email_script.exists():
            subprocess.run([
                "python3", str(email_script),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", body,
                "--html"
            ], capture_output=True, timeout=30)
            print(f"   📧 Alert email sent: {alert_type}")
    except Exception as e:
        print(f"   ⚠️  Failed to send email: {e}")


def check_flights():
    """Main function to check all upcoming flights"""
    print("✈️  Travel Flight Monitor")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Load calendar and tracked flights
    calendar = load_calendar()
    if not calendar:
        print("❌ No calendar data found")
        return
    
    tracked = load_tracked_flights()
    
    # Find all flight events in the next 30 days
    cutoff = datetime.now() + timedelta(days=30)
    flights_found = []
    
    for event in calendar.get('events', []):
        summary = event.get('summary', '')
        description = event.get('description', '')
        
        # Check if this is a flight event
        is_flight = any(word in summary.lower() for word in 
                       ['flight', 'delta', 'united', 'american', 'departs', 'arrives'])
        
        if not is_flight:
            continue
        
        # Extract flight numbers
        full_text = summary + ' ' + description
        flight_numbers = extract_flight_number(full_text)
        
        if not flight_numbers:
            continue
        
        # Parse departure time
        start_raw = event.get('start_raw', '')
        departure_time = parse_flight_datetime(start_raw)
        
        if not departure_time or departure_time > cutoff:
            continue
        
        for airline_code, flight_num in flight_numbers:
            flight_id = f"{airline_code}{flight_num}_{departure_time.strftime('%Y%m%d')}"
            
            flight_data = {
                'id': flight_id,
                'airline': airline_code,
                'flight_number': flight_num,
                'summary': summary,
                'departure_time': departure_time.isoformat(),
                'location': event.get('location', ''),
                'last_checked': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            flights_found.append(flight_data)
            
            # Check if this is a new flight or needs update
            existing = tracked.get(flight_id, {})
            
            print(f"\n✈️  {airline_code} {flight_num}")
            print(f"   📆 {departure_time.strftime('%A, %B %d at %I:%M %p')}")
            print(f"   📝 {summary[:60]}...")
            
            # Check flight status
            live_status = get_flight_status_from_opensky(airline_code, flight_num)
            schedule_info = get_flight_schedule_info(
                airline_code, flight_num, 
                departure_time.strftime('%Y-%m-%d')
            )
            
            if live_status:
                print(f"   🛫 Live tracking: Active")
                print(f"   📍 Altitude: {live_status.get('altitude', 'N/A')}m")
                print(f"   💨 Speed: {live_status.get('velocity', 'N/A')} m/s")
                flight_data['status'] = 'in_air'
                flight_data['live_data'] = live_status
            else:
                print(f"   ⏳ Not yet airborne or not tracked")
                flight_data['status'] = 'scheduled'
            
            # Check for status changes
            if existing:
                old_status = existing.get('status', 'unknown')
                if old_status != flight_data['status']:
                    print(f"   ⚠️  Status changed: {old_status} → {flight_data['status']}")
                    send_flight_alert(
                        flight_data,
                        "Status Change",
                        f"Flight status changed from {old_status} to {flight_data['status']}"
                    )
            
            # Update tracked flights
            tracked[flight_id] = flight_data
    
    # Save updated tracking data
    save_tracked_flights(tracked)
    
    # Clean up old flights (older than 1 day)
    cutoff_past = datetime.now() - timedelta(days=1)
    to_remove = []
    for flight_id, flight in tracked.items():
        dep_time = parse_flight_datetime(flight.get('departure_time', ''))
        if dep_time and dep_time < cutoff_past:
            to_remove.append(flight_id)
    
    for flight_id in to_remove:
        del tracked[flight_id]
    
    save_tracked_flights(tracked)
    
    print(f"\n{'='*70}")
    print(f"✅ Flight check complete")
    print(f"   Flights tracked: {len(flights_found)}")
    print(f"   Total in database: {len(tracked)}")


def main():
    check_flights()


if __name__ == "__main__":
    main()
