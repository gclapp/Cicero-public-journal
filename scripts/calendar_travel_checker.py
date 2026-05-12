#!/usr/bin/env python3
"""
Calendar Travel Checker - Creates travel tasks with subtasks
One main task per trip with subtasks for pack, uber, and rover
"""

import json
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "calendar-travel-checker.log"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "travel-checker-state.json"
TODOIST_PATH = "/home/ubuntu/.npm-global/bin/todoist"

TRAVEL_KEYWORDS = ['flight', 'delta', 'hotel', 'stay at', 'trip to', 'travel to']

def log(msg: str):
    """Log to console and file"""
    print(msg, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def load_calendar() -> Optional[Dict]:
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from calendar"""
    if not date_str:
        return None
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None

def is_travel_event(event: Dict) -> bool:
    """Check if event is travel-related"""
    summary = event.get('summary', '').lower()
    return any(kw in summary for kw in TRAVEL_KEYWORDS) or event.get('is_travel')

def extract_flight_info(event: Dict) -> Dict:
    """Extract flight number and confirmation from event"""
    summary = event.get('summary', '')
    description = event.get('description', '')
    
    # Extract flight number - try multiple patterns
    flight_num = None
    
    # Pattern 1: "DL 4099" or "(DL 4099)" in summary
    match = re.search(r'\(?DL\s*(\d+)\)?', summary, re.IGNORECASE)
    if match:
        flight_num = f"DL{match.group(1)}"
    
    # Pattern 2: "Delta Air Lines flight 960" or "Delta Air Lines 1430" in summary
    if not flight_num:
        match = re.search(r'Delta\s+(?:Air\s+)?(?:Lines?\s+)?(?:flight\s+)?(\d+)', summary, re.IGNORECASE)
        if match:
            flight_num = f"DL{match.group(1)}"
    
    # Pattern 3: "Delta 1559" in summary
    if not flight_num:
        match = re.search(r'Delta\s+(\d+)', summary, re.IGNORECASE)
        if match:
            flight_num = f"DL{match.group(1)}"
    
    # Extract confirmation code (6 char alphanumeric, typically in description or summary)
    confirmation = None
    text = f"{summary} {description}"
    match = re.search(r'[A-Z0-9]{6}', text)
    if match:
        confirmation = match.group(0)
    
    return {'flight': flight_num, 'confirmation': confirmation}

def extract_destination(event: Dict) -> str:
    """Extract destination city from event - looks for arrival airport/city"""
    location = event.get('location', '')
    summary = event.get('summary', '')
    description = event.get('description', '')
    
    # First check summary for "Flight to [Destination]" pattern
    # e.g., "Flight to RNO (DL 4099)" or "Flight to San Francisco"
    flight_to_match = re.search(r'Flight\s+to\s+([A-Za-z\s]+?)(?:\s+\(|\s*-|\s*$)', summary, re.IGNORECASE)
    if flight_to_match:
        dest = flight_to_match.group(1).strip()
        # Map airport codes to cities
        airport_map = {
            'RNO': 'Reno',
            'LAX': 'Los Angeles',
            'SFO': 'San Francisco',
            'SJC': 'San Jose',
            'JFK': 'NYC',
            'LGA': 'NYC',
            'EWR': 'NYC',
            'PDX': 'Portland',
            'SEA': 'Seattle',
            'LAS': 'Las Vegas',
            'PHX': 'Phoenix',
            'DEN': 'Denver',
            'ORD': 'Chicago',
            'DFW': 'Dallas',
            'MIA': 'Miami',
            'BOS': 'Boston',
            'DCA': 'DC',
            'IAD': 'DC',
        }
        # Check if it's an airport code
        dest_upper = dest.upper()
        if dest_upper in airport_map:
            return airport_map[dest_upper]
        # Otherwise return the city name as-is
        return dest
    
    # Check if location has "Departure - Arrival" format
    # e.g., "Los Angeles(LAX) - San Jose(SJC)"
    if '-' in location:
        parts = location.split('-')
        if len(parts) >= 2:
            # Take the second part (arrival)
            arrival = parts[1].strip()
            # Extract city name before parentheses if present
            city_match = arrival.split('(')[0].strip()
            if city_match:
                return city_match
    
    # Check description for "to [City]" pattern
    to_match = re.search(r'to\s+([A-Za-z\s]+?)(?:\s+\(|\s*,|\s*$)', description, re.IGNORECASE)
    if to_match:
        city = to_match.group(1).strip()
        if city and 'detailed information' not in city.lower():
            return city
    
    # Check for common destinations in text
    text = f"{location} {summary} {description}".lower()
    
    # Check for arrival patterns in description
    if 'arrive' in description.lower() or 'arrival' in description.lower():
        # Try to find city after arrival
        arr_match = re.search(r'arriv(?:e|al)(?:\s+in)?\s+([A-Za-z\s]+?)(?:\s+\(|\s*,|\s*$)', description, re.IGNORECASE)
        if arr_match:
            city = arr_match.group(1).strip()
            if city and 'detailed information' not in city.lower():
                return city
    
    if 'new york' in text or 'jfk' in text or 'lga' in text or 'ewr' in text:
        return 'NYC'
    if 'reno' in text or 'rno' in text or 'tahoe' in text:
        return 'Tahoe'
    if 'san jose' in text or 'sjc' in text:
        return 'San Jose'
    if 'palo alto' in text:
        return 'Palo Alto'
    if 'portland' in text or 'pdx' in text:
        return 'Portland'
    if 'san francisco' in text or 'sfo' in text:
        return 'San Francisco'
    if 'los angeles' in text or 'lax' in text:
        # Only return LA if it's clearly the destination, not departure
        if 'from' in text and ('lax' in text.split('from')[1] or 'los angeles' in text.split('from')[1]):
            return 'Los Angeles'
    
    # Extract from location as fallback
    if location:
        parts = location.split(',')
        if parts:
            loc = parts[0].strip()
            if 'detailed information' not in loc.lower():
                return loc
    
    return 'Trip'


def is_return_flight(event: Dict) -> bool:
    """Check if this is a return flight to LAX (end of trip)"""
    location = event.get('location', '')
    description = event.get('description', '')
    summary = event.get('summary', '')
    
    # Check if destination is LAX/Los Angeles
    text = f"{location} {description}".lower()
    
    # Check for "- Los Angeles" or "to LAX" patterns
    if '-' in location:
        parts = location.split('-')
        if len(parts) >= 2:
            arrival = parts[1].strip().lower()
            if 'lax' in arrival or 'los angeles' in arrival:
                return True
    
    # Check summary for "to Los Angeles" or "to LAX"
    if re.search(r'to\s+(Los Angeles|LAX)', summary, re.IGNORECASE):
        return True
    
    return False

def get_all_tasks(project: str = "Travel") -> List[Dict]:
    """Get all tasks from Todoist including completed ones"""
    try:
        # Get active tasks
        result = subprocess.run(
            [TODOIST_PATH, "tasks", "-p", project, "--all", "--json"],
            capture_output=True, text=True, timeout=30
        )
        tasks = []
        if result.returncode == 0:
            tasks = json.loads(result.stdout)
        return tasks
    except Exception as e:
        log(f"Could not fetch tasks: {e}")
        return []

def get_existing_task_names(project: str = "Travel") -> Set[str]:
    """Get set of existing task names (both active and completed)"""
    tasks = get_all_tasks(project)
    return {task.get('content', '').lower() for task in tasks}

def create_task(text: str, project: str = "Travel", due: Optional[str] = None, 
                parent_id: Optional[str] = None) -> Optional[str]:
    """Create a task and return its ID"""
    try:
        cmd = [TODOIST_PATH, "add", text, "-p", project, "-P", "2"]
        if due:
            cmd.extend(["-d", due])
        if parent_id:
            cmd.extend(["--parent", parent_id])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            if "already exists" in result.stderr.lower():
                return None
            log(f"  Failed to create: {text[:50]} - {result.stderr}")
            return None
        
        # Extract task ID from output like "✓ Added: Task name\n  ID: 6gcjgQ44Q3wFVvJx"
        match = re.search(r'ID:\s+(\w+)', result.stdout)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        log(f"  Error creating task: {e}")
        return None

def get_task_id_by_name(task_name: str, project: str = "Travel") -> Optional[str]:
    """Find task ID by name"""
    try:
        result = subprocess.run(
            [TODOIST_PATH, "tasks", "-p", project, "--all", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        
        tasks = json.loads(result.stdout)
        for task in tasks:
            if task.get('content', '').lower() == task_name.lower():
                return task.get('id')
        return None
    except:
        return None

def get_hotel_stays(calendar_data: Dict) -> List[Dict]:
    """Extract hotel stay events from calendar"""
    hotels = []
    hotel_keywords = ['stay at', 'hotel', 'westin', 'ritz', 'marriott', 'hilton']
    
    for event in calendar_data.get('events', []):
        summary = event.get('summary', '').lower()
        if any(kw in summary for kw in hotel_keywords):
            event_date = parse_date(event.get('start_raw', ''))
            if event_date:
                location = extract_destination(event)
                # Clean up location names
                if 'palo alto' in summary.lower():
                    location = 'Palo Alto'
                elif 'new york' in summary.lower():
                    location = 'NYC'
                elif 'tahoe' in summary.lower() or 'truckee' in summary.lower():
                    location = 'Tahoe'
                hotels.append({
                    'event': event,
                    'date': event_date,
                    'location': location
                })
    
    return sorted(hotels, key=lambda x: x['date'])

def group_events_by_trip(events: List[Dict], calendar_data: Dict) -> List[Dict]:
    """Group flight events into trips using hotel stays as anchors"""
    if not events:
        return []
    
    # Get hotel stays for trip detection
    hotel_stays = get_hotel_stays(calendar_data)
    
    # Sort flights by date
    flights = sorted([e for e in events if extract_flight_info(e).get('flight')], 
                     key=lambda x: parse_date(x.get('start_raw', '')) or datetime.now())
    
    trips = []
    used_flights = set()
    
    # Group flights into trips
    # A trip starts with an outbound flight and ends with a return to LAX
    current_trip_flights = []
    current_trip_destination = None
    
    for flight in flights:
        flight_date = parse_date(flight.get('start_raw', ''))
        if not flight_date:
            continue
        
        flight_id = flight.get('summary', '') + flight.get('start_raw', '')
        if flight_id in used_flights:
            continue
        
        flight_dest = extract_destination(flight)
        is_return = is_return_flight(flight)
        
        # Check if there's a hotel stay near this flight to determine destination
        # Find the CLOSEST hotel within 4 days
        closest_hotel = None
        closest_days = 5
        for hotel in hotel_stays:
            days_from_hotel = abs((flight_date - hotel['date']).days)
            if days_from_hotel <= 4 and hotel['location'] != 'Trip':
                if days_from_hotel < closest_days:
                    closest_days = days_from_hotel
                    closest_hotel = hotel
        
        if closest_hotel:
            flight_dest = closest_hotel['location']
        
        if not current_trip_flights:
            # Start new trip
            current_trip_flights = [flight]
            current_trip_destination = flight_dest if flight_dest != 'Trip' else 'Trip'
        elif is_return:
            # This is a return flight - add to current trip and end it
            current_trip_flights.append(flight)
            trips.append({
                'events': current_trip_flights,
                'start_date': parse_date(current_trip_flights[0].get('start_raw', '')),
                'end_date': flight_date,
                'destination': current_trip_destination
            })
            for f in current_trip_flights:
                used_flights.add(f.get('summary', '') + f.get('start_raw', ''))
            current_trip_flights = []
            current_trip_destination = None
        else:
            # Continue current trip
            current_trip_flights.append(flight)
            if flight_dest != 'Trip' and current_trip_destination == 'Trip':
                current_trip_destination = flight_dest
    
    # Handle any remaining flights in current trip
    if current_trip_flights:
        trips.append({
            'events': current_trip_flights,
            'start_date': parse_date(current_trip_flights[0].get('start_raw', '')),
            'end_date': parse_date(current_trip_flights[-1].get('start_raw', '')),
            'destination': current_trip_destination
        })
        for f in current_trip_flights:
            used_flights.add(f.get('summary', '') + f.get('start_raw', ''))
    
    # Handle any remaining flights not associated with hotels
    remaining_flights = [f for f in flights 
                        if (f.get('summary', '') + f.get('start_raw', '')) not in used_flights]
    
    if remaining_flights:
        # Group remaining flights by proximity
        remaining_flights.sort(key=lambda x: parse_date(x.get('start_raw', '')) or datetime.now())
        
        current_trip = None
        for flight in remaining_flights:
            flight_date = parse_date(flight.get('start_raw', ''))
            if not flight_date:
                continue
            
            flight_dest = extract_destination(flight)
            
            if current_trip is None or (flight_date - current_trip['end_date']).days > 2:
                # New trip
                if current_trip:
                    trips.append(current_trip)
                current_trip = {
                    'events': [flight],
                    'start_date': flight_date,
                    'end_date': flight_date,
                    'destination': flight_dest if flight_dest != 'Trip' else 'Trip'
                }
            else:
                # Add to current trip
                current_trip['events'].append(flight)
                current_trip['end_date'] = flight_date
                if flight_dest != 'Trip':
                    current_trip['destination'] = flight_dest
        
        if current_trip:
            trips.append(current_trip)
    
    # Sort trips by start date
    trips.sort(key=lambda x: x['start_date'])
    
    return trips

def process_trip(trip: Dict, existing_tasks: Set[str]) -> int:
    """Process a single trip and create tasks"""
    created_count = 0
    
    # Get first flight for main task naming
    first_event = trip['events'][0]
    first_date = trip['start_date']
    flight_info = extract_flight_info(first_event)
    
    # Use the trip destination from the grouping (which is hotel-based)
    # This is more accurate than the first flight's destination
    destination = trip['destination']
    date_str = first_date.strftime('%b %d')
    flight_str = flight_info.get('flight', 'Flight')
    conf_str = flight_info.get('confirmation', '')
    
    # Main task name
    main_task_name = f"Tasks for {destination} Trip on {date_str}"
    if flight_str and flight_str != 'Flight':
        main_task_name += f" - {flight_str}"
    if conf_str:
        main_task_name += f" {conf_str}"
    
    # Check if main task already exists
    if main_task_name.lower() in existing_tasks:
        log(f"  Task already exists: {main_task_name[:60]}")
        return 0
    
    # Create main task
    log(f"Creating: {main_task_name}")
    parent_id = create_task(main_task_name, due=first_date.strftime('%Y-%m-%d'))
    if not parent_id:
        log(f"  Could not create main task")
        return 0
    
    created_count += 1
    existing_tasks.add(main_task_name.lower())
    
    # Create subtasks
    
    # 1. Pack task - due day before
    pack_due = (first_date - timedelta(days=1)).strftime('%Y-%m-%d')
    pack_task = create_task("└── 🧳 Pack", due=pack_due, parent_id=parent_id)
    if pack_task:
        created_count += 1
        log(f"  Created: └── 🧳 Pack (due {pack_due})")
    
    # 2. Contact Marriott Ambassador - due 7 days before
    marriott_due = (first_date - timedelta(days=7)).strftime('%Y-%m-%d')
    marriott_task = create_task("└── 🏢 Contact Marriott Ambassador about hotel", due=marriott_due, parent_id=parent_id)
    if marriott_task:
        created_count += 1
        log(f"  Created: └── 🏢 Contact Marriott Ambassador (due {marriott_due})")
    
    # 3. Schedule Rover - due immediately (today)
    today = datetime.now().strftime('%Y-%m-%d')
    rover_task = create_task("└── 🐕 Schedule Rover for Greta", due=today, parent_id=parent_id)
    if rover_task:
        created_count += 1
        log(f"  Created: └── 🐕 Schedule Rover (due today)")
    
    # 4. Schedule Uber for each flight leg - due 3 days before each
    # Only create for events that have actual flight numbers
    for event in trip['events']:
        event_date = parse_date(event.get('start_raw', ''))
        if not event_date:
            continue
        
        # Only create Uber tasks for actual flights (with flight numbers)
        flight_info = extract_flight_info(event)
        flight_str = flight_info.get('flight')
        
        if not flight_str:
            continue  # Skip non-flight events
        
        # Get destination for this specific flight
        flight_dest = extract_destination(event)
        
        uber_due = (event_date - timedelta(days=3)).strftime('%Y-%m-%d')
        uber_text = f"└── 🚗 Schedule Uber to airport for {flight_str} to {flight_dest}"
        
        uber_task = create_task(uber_text, due=uber_due, parent_id=parent_id)
        if uber_task:
            created_count += 1
            log(f"  Created: {uber_text[:60]} (due {uber_due})")
    
    return created_count

def main():
    log("=" * 70)
    log("Calendar Travel Checker - Starting")
    log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("")
    
    # Load calendar
    calendar_data = load_calendar()
    if not calendar_data:
        log("Could not load calendar")
        return 1
    
    log(f"Calendar loaded: {calendar_data.get('total_events', 0)} events")
    
    # Get travel events
    travel_events = []
    for event in calendar_data.get('events', []):
        if is_travel_event(event):
            event_date = parse_date(event.get('start_raw', ''))
            if event_date and event_date <= datetime.now() + timedelta(days=60):
                travel_events.append(event)
    
    log(f"Found {len(travel_events)} travel events in next 60 days")
    
    # Group into trips
    trips = group_events_by_trip(travel_events, calendar_data)
    log(f"Grouped into {len(trips)} trips")
    log("")
    
    # Get existing tasks (including completed)
    existing_tasks = get_existing_task_names()
    log(f"Found {len(existing_tasks)} existing tasks (including completed)")
    log("")
    
    # Process each trip
    total_created = 0
    for trip in trips:
        created = process_trip(trip, existing_tasks)
        total_created += created
        if created > 0:
            log("")
    
    log("=" * 70)
    log(f"SUMMARY: Created {total_created} tasks")
    log("=" * 70)
    
    return 0

if __name__ == "__main__":
    exit(main())
