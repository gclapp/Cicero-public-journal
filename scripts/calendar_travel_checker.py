#!/usr/bin/env python3
"""
Calendar Travel Checker - 3x/week automated travel task creation
Runs Mon/Wed/Fri at 9 AM PT to check for upcoming travel and create Todoist tasks

Features:
- Reads calendar-events.json for travel events
- Checks for new travel in next 30 days
- Creates Todoist tasks for travel prep
- Logs what was checked and what tasks were created
- Reports changes since last check
- Prevents duplicate task creation
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set

# Configuration
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "calendar-travel-checker.log"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "travel-checker-state.json"

# Travel keywords to identify travel events
TRAVEL_KEYWORDS = ['flight', 'delta', 'hotel', 'stay at', 'airbnb', 'resort', 'trip to', 'travel to']

# Restaurant reservation keywords
RESTAURANT_KEYWORDS = ['reservation at', 'dinner at', 'reservation:', 'dinner reservation']


def log_message(message: str, print_to_console: bool = True):
    """Log message to file and optionally print to console"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    
    if print_to_console:
        print(message)
    
    # Ensure log directory exists
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')


def load_state() -> Dict:
    """Load the checker state (last run info, known trips, etc.)"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            log_message(f"⚠️  Could not load state file: {e}")
    
    return {
        "last_run": None,
        "known_trips": [],
        "created_tasks": [],
        "run_count": 0
    }


def save_state(state: Dict):
    """Save the checker state"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def load_calendar() -> Optional[Dict]:
    """Load calendar events from JSON file"""
    if not CALENDAR_FILE.exists():
        log_message(f"❌ Calendar file not found: {CALENDAR_FILE}")
        return None
    
    try:
        with open(CALENDAR_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_message(f"❌ Error loading calendar: {e}")
        return None


def parse_event_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats from calendar events - returns naive datetime (no timezone)"""
    if not date_str:
        return None
    
    try:
        # ISO format with timezone: 2026-05-16T21:14:00-07:00
        if 'T' in date_str:
            # Parse with timezone then convert to naive
            date_str_clean = date_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(date_str_clean)
            # Convert to naive datetime by removing timezone info
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        
        # Simple date: 2026-05-16
        return datetime.strptime(date_str, '%Y-%m-%d')
    except Exception as e:
        log_message(f"⚠️  Could not parse date '{date_str}': {e}", print_to_console=False)
        return None


def is_travel_event(event: Dict) -> bool:
    """Determine if an event is travel-related"""
    summary = event.get('summary', '').lower()
    description = event.get('description', '').lower()
    location = event.get('location', '').lower()
    
    # Check if already marked as travel
    if event.get('is_travel'):
        return True
    
    # Check keywords in summary, description, or location
    text_to_check = f"{summary} {description} {location}"
    return any(keyword in text_to_check for keyword in TRAVEL_KEYWORDS)


def is_restaurant_reservation(event: Dict) -> bool:
    """Determine if an event is a restaurant reservation"""
    summary = event.get('summary', '').lower()
    return any(keyword in summary for keyword in RESTAURANT_KEYWORDS)


def get_upcoming_travel(calendar_data: Dict, days: int = 30) -> List[Dict]:
    """Get travel events within the next N days"""
    travel_events = []
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    
    for event in calendar_data.get('events', []):
        # Check if it's a travel event
        if not is_travel_event(event):
            continue
        
        # Parse the date
        date_str = event.get('start_raw', '')
        event_date = parse_event_date(date_str)
        
        if not event_date:
            continue
        
        # Check if within our window
        if now <= event_date <= cutoff:
            travel_events.append({
                **event,
                'parsed_date': event_date
            })
    
    # Sort by date
    travel_events.sort(key=lambda x: x['parsed_date'])
    return travel_events


def get_restaurant_reservations(calendar_data: Dict, days: int = 30) -> List[Dict]:
    """Get restaurant reservations within the next N days"""
    reservations = []
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    
    for event in calendar_data.get('events', []):
        if not is_restaurant_reservation(event):
            continue
        
        date_str = event.get('start_raw', '')
        event_date = parse_event_date(date_str)
        
        if not event_date:
            continue
        
        if now <= event_date <= cutoff:
            reservations.append({
                **event,
                'parsed_date': event_date
            })
    
    reservations.sort(key=lambda x: x['parsed_date'])
    return reservations


def get_existing_todoist_tasks() -> Set[str]:
    """Get set of existing task names from Todoist"""
    try:
        result = subprocess.run(
            ["todoist", "list"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return set()
        
        existing = set()
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Format: ID  Task name
                parts = line.split('  ', 1)
                if len(parts) > 1:
                    existing.add(parts[1].strip().lower())
        return existing
    except Exception as e:
        log_message(f"⚠️  Could not fetch existing tasks: {e}")
        return set()


def create_todoist_task(task_text: str, project: str = "Travel", 
                        priority: str = "2", due_date: Optional[str] = None,
                        existing_tasks: Optional[Set[str]] = None) -> Tuple[bool, str]:
    """
    Create a task in Todoist
    Returns: (success, message)
    """
    # Check if task already exists (case-insensitive)
    if existing_tasks and task_text.lower() in existing_tasks:
        return False, "already_exists"
    
    try:
        cmd = ["todoist", "add", task_text, "-p", project, "-P", priority]
        if due_date:
            cmd.extend(["-d", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            error = result.stderr.strip()
            if "already exists" in error.lower():
                return False, "already_exists"
            return False, f"error: {error}"
        
        return True, "created"
    except Exception as e:
        return False, f"exception: {e}"


def extract_flight_info(event: Dict) -> Dict:
    """Extract flight details from event summary/description"""
    summary = event.get('summary', '')
    description = event.get('description', '')
    location = event.get('location', '')
    
    info = {
        'flight_number': None,
        'confirmation': None,
        'origin': None,
        'destination': None,
        'departure_time': None
    }
    
    # Extract flight number (e.g., "Delta 960", "DL 960")
    import re
    flight_match = re.search(r'(?:Delta|DL)\s+(\d+)', summary, re.IGNORECASE)
    if flight_match:
        info['flight_number'] = f"DL {flight_match.group(1)}"
    
    # Extract confirmation code (e.g., "GAO7LP", "Confirmation code: XYZ123")
    conf_match = re.search(r'[A-Z0-9]{6}', description)
    if conf_match:
        info['confirmation'] = conf_match.group(0)
    
    # Determine origin/destination from location
    location_lower = location.lower()
    summary_lower = summary.lower()
    
    if 'lax' in location_lower or 'los angeles' in location_lower:
        if 'jfk' in location_lower or 'new york' in location_lower:
            # This is a return flight (JFK to LAX)
            info['origin'] = 'JFK'
            info['destination'] = 'LAX'
        else:
            # LAX departure
            info['origin'] = 'LAX'
            info['destination'] = 'JFK' if 'jfk' in summary_lower or 'new york' in summary_lower else 'Unknown'
    elif 'jfk' in location_lower or 'new york' in location_lower:
        info['origin'] = 'JFK'
        info['destination'] = 'LAX'
    elif 'rno' in location_lower or 'reno' in location_lower:
        info['origin'] = 'LAX'  # Assuming from LAX
        info['destination'] = 'RNO'
    
    return info


def extract_hotel_info(event: Dict) -> Dict:
    """Extract hotel details from event"""
    summary = event.get('summary', '')
    location = event.get('location', '')
    
    # Extract hotel name
    hotel_name = summary
    if 'stay at' in summary.lower():
        hotel_name = summary.replace('Stay at ', '').replace('stay at ', '')
    
    return {
        'name': hotel_name,
        'location': location
    }


def extract_restaurant_info(event: Dict) -> Dict:
    """Extract restaurant details from event"""
    summary = event.get('summary', '')
    location = event.get('location', '')
    
    # Extract restaurant name
    restaurant_name = summary
    for keyword in ['Reservation at ', 'reservation at ', 'Dinner at ', 'dinner at ']:
        if keyword in summary:
            restaurant_name = summary.replace(keyword, '')
            break
    
    return {
        'name': restaurant_name.strip(),
        'location': location
    }


def generate_flight_tasks(event: Dict, flight_info: Dict) -> List[Dict]:
    """Generate tasks for a flight"""
    tasks = []
    event_date = event.get('parsed_date', datetime.now())
    summary = event.get('summary', '')
    location = event.get('location', '').lower()
    
    # Determine if this is an LAX departure (needs Greta care)
    is_lax_departure = 'lax' in location and not ('jfk' in location and 'lax' in location)
    
    # Calculate due dates
    checkin_due = (event_date - timedelta(days=1)).strftime('%Y-%m-%d')
    pack_due = (event_date - timedelta(days=2)).strftime('%Y-%m-%d')
    uber_due = (event_date - timedelta(days=1)).strftime('%Y-%m-%d')
    rover_due = (event_date - timedelta(days=10)).strftime('%Y-%m-%d')
    
    flight_num = flight_info.get('flight_number', 'Flight')
    conf_code = flight_info.get('confirmation', '')
    conf_str = f" ({conf_code})" if conf_code else ""
    
    # Build task list
    if is_lax_departure:
        tasks.append({
            'text': f"🐕 Book Rover sitter for Greta - {flight_num}{conf_str}",
            'due': rover_due,
            'priority': '2'
        })
    
    tasks.append({
        'text': f"✈️ Check in for {flight_num}{conf_str}",
        'due': checkin_due,
        'priority': '2'
    })
    
    tasks.append({
        'text': f"🎒 Pack for trip - {flight_num}",
        'due': pack_due,
        'priority': '3'
    })
    
    if is_lax_departure:
        tasks.append({
            'text': f"🚗 Schedule Uber to airport - {flight_num}",
            'due': uber_due,
            'priority': '3'
        })
    
    return tasks


def generate_hotel_tasks(event: Dict, hotel_info: Dict) -> List[Dict]:
    """Generate tasks for a hotel stay"""
    tasks = []
    event_date = event.get('parsed_date', datetime.now())
    hotel_name = hotel_info.get('name', 'Hotel')
    
    confirm_due = (event_date - timedelta(days=7)).strftime('%Y-%m-%d')
    research_due = (event_date - timedelta(days=5)).strftime('%Y-%m-%d')
    
    tasks.append({
        'text': f"🏨 Confirm reservation - {hotel_name}",
        'due': confirm_due,
        'priority': '3'
    })
    
    tasks.append({
        'text': f"📋 Research hotel amenities - {hotel_name}",
        'due': research_due,
        'priority': '3'
    })
    
    return tasks


def generate_restaurant_tasks(event: Dict, restaurant_info: Dict) -> List[Dict]:
    """Generate tasks for restaurant reservations that need confirmation"""
    tasks = []
    event_date = event.get('parsed_date', datetime.now())
    restaurant_name = restaurant_info.get('name', 'Restaurant')
    
    # Only create confirmation task if it's more than 3 days out
    days_until = (event_date - datetime.now()).days
    if days_until > 3:
        confirm_due = (event_date - timedelta(days=3)).strftime('%Y-%m-%d')
        tasks.append({
            'text': f"🍽️ Confirm reservation - {restaurant_name}",
            'due': confirm_due,
            'priority': '3'
        })
    
    return tasks


def group_trips_by_date(travel_events: List[Dict]) -> Dict[str, List[Dict]]:
    """Group travel events by date to identify multi-day trips"""
    trips = {}
    
    for event in travel_events:
        date_key = event.get('parsed_date', datetime.now()).strftime('%Y-%m-%d')
        if date_key not in trips:
            trips[date_key] = []
        trips[date_key].append(event)
    
    return trips


def run_travel_check() -> Dict:
    """Main function to check calendar and create travel tasks"""
    log_message("=" * 70)
    log_message("🧳 Calendar Travel Checker - Starting Run")
    log_message(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message("")
    
    # Load state
    state = load_state()
    state['run_count'] = state.get('run_count', 0) + 1
    
    # Load calendar
    calendar_data = load_calendar()
    if not calendar_data:
        log_message("❌ Failed to load calendar data")
        return {'success': False, 'error': 'calendar_load_failed'}
    
    log_message(f"📅 Calendar loaded: {calendar_data.get('total_events', 0)} total events")
    log_message(f"📅 Last updated: {calendar_data.get('last_updated', 'unknown')}")
    log_message("")
    
    # Get upcoming travel
    travel_events = get_upcoming_travel(calendar_data, days=30)
    log_message(f"✈️  Found {len(travel_events)} travel events in next 30 days")
    
    # Get restaurant reservations
    restaurant_events = get_restaurant_reservations(calendar_data, days=30)
    log_message(f"🍽️  Found {len(restaurant_events)} restaurant reservations in next 30 days")
    log_message("")
    
    # Get existing tasks to avoid duplicates
    existing_tasks = get_existing_todoist_tasks()
    log_message(f"📋 Found {len(existing_tasks)} existing Todoist tasks")
    log_message("")
    
    # Track what we create
    created_tasks = []
    skipped_tasks = []
    failed_tasks = []
    
    # Process travel events
    for event in travel_events:
        summary = event.get('summary', 'Travel')
        event_date = event.get('parsed_date', datetime.now())
        date_str = event_date.strftime('%Y-%m-%d')
        
        log_message(f"✈️  Processing: {summary}")
        log_message(f"   📆 {date_str}", print_to_console=False)
        
        # Determine event type and generate tasks
        if 'flight' in summary.lower() or 'delta' in summary.lower():
            flight_info = extract_flight_info(event)
            tasks = generate_flight_tasks(event, flight_info)
        elif 'hotel' in summary.lower() or 'stay at' in summary.lower():
            hotel_info = extract_hotel_info(event)
            tasks = generate_hotel_tasks(event, hotel_info)
        else:
            # Generic travel
            tasks = [{
                'text': f"🧳 Prepare for: {summary}",
                'due': date_str,
                'priority': '3'
            }]
        
        # Create tasks
        for task in tasks:
            success, message = create_todoist_task(
                task['text'], 
                due_date=task['due'],
                priority=task['priority'],
                existing_tasks=existing_tasks
            )
            
            if success:
                log_message(f"   ✅ Created: {task['text'][:60]}")
                created_tasks.append(task['text'])
                existing_tasks.add(task['text'].lower())  # Add to existing set
            elif message == "already_exists":
                log_message(f"   ⏭️  Skipped (exists): {task['text'][:50]}...", print_to_console=False)
                skipped_tasks.append(task['text'])
            else:
                log_message(f"   ❌ Failed: {task['text'][:50]}... - {message}")
                failed_tasks.append({'task': task['text'], 'error': message})
    
    # Process restaurant reservations
    log_message("")
    for event in restaurant_events:
        summary = event.get('summary', 'Reservation')
        event_date = event.get('parsed_date', datetime.now())
        date_str = event_date.strftime('%Y-%m-%d')
        
        restaurant_info = extract_restaurant_info(event)
        tasks = generate_restaurant_tasks(event, restaurant_info)
        
        for task in tasks:
            success, message = create_todoist_task(
                task['text'],
                due_date=task['due'],
                priority=task['priority'],
                existing_tasks=existing_tasks
            )
            
            if success:
                log_message(f"   ✅ Created: {task['text'][:60]}")
                created_tasks.append(task['text'])
                existing_tasks.add(task['text'].lower())
            elif message == "already_exists":
                skipped_tasks.append(task['text'])
            else:
                log_message(f"   ❌ Failed: {task['text'][:50]}... - {message}")
    
    # Update state
    state['last_run'] = datetime.now().isoformat()
    state['known_trips'] = [e.get('summary') for e in travel_events]
    state['created_tasks'] = state.get('created_tasks', []) + created_tasks
    save_state(state)
    
    # Summary
    log_message("")
    log_message("=" * 70)
    log_message("📊 SUMMARY")
    log_message(f"   ✅ Created: {len(created_tasks)} new tasks")
    log_message(f"   ⏭️  Skipped: {len(skipped_tasks)} existing tasks")
    log_message(f"   ❌ Failed: {len(failed_tasks)} tasks")
    log_message(f"   📈 Total runs: {state['run_count']}")
    log_message("=" * 70)
    log_message("")
    
    return {
        'success': True,
        'created': created_tasks,
        'skipped': skipped_tasks,
        'failed': failed_tasks,
        'travel_events_found': len(travel_events),
        'restaurant_events_found': len(restaurant_events)
    }


def main():
    """Entry point"""
    # Check if todoist CLI is available
    try:
        result = subprocess.run(["todoist", "--version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            log_message("❌ Todoist CLI not configured. Run: todoist auth <token>")
            sys.exit(1)
    except Exception as e:
        log_message(f"❌ Todoist CLI not found: {e}")
        log_message("   Install: npm install -g todoist-ts-cli")
        sys.exit(1)
    
    # Run the check
    result = run_travel_check()
    
    if not result['success']:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
