#!/usr/bin/env python3
"""
Travel Automation v2 - Comprehensive travel task creation
Creates Todoist tasks for flights, hotels, Rover, Uber, and dinner reservations
Includes flight tracking and car reservation monitoring
"""

import json
import os
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
FLIGHT_TRACKING_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "tracked-flights.json"

def load_calendar():
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)

def parse_date(date_str):
    """Parse various date formats"""
    try:
        # Try ISO format first
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Make offset-naive for comparison
            return dt.replace(tzinfo=None)
        else:
            # Date only format
            return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None

def get_existing_tasks(project="Travel"):
    """Get list of existing task names in the Travel project"""
    try:
        result = subprocess.run(["todoist", "tasks", "-p", project], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return set()
        
        existing = set()
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('  ', 1)
                if len(parts) > 1:
                    existing.add(parts[1].strip())
        return existing
    except Exception as e:
        print(f"⚠️  Could not fetch existing tasks: {e}")
        return set()

def create_todoist_task(task_text, project="Travel", priority="2", due_date=None, existing_tasks=None):
    """Create a task in Todoist if it doesn't already exist"""
    if existing_tasks and task_text in existing_tasks:
        print(f"   ⏭️  Already exists: {task_text[:60]}...")
        return True
    
    try:
        cmd = ["todoist", "add", task_text, "-p", project, "-P", priority]
        if due_date:
            cmd.extend(["-d", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            error = result.stderr.strip()
            if "already exists" in error.lower():
                print(f"   ⏭️  Already exists: {task_text[:60]}...")
                return True
            print(f"   ❌ Error: {error}")
            return False
        print(f"   ✅ Created: {task_text[:60]}...")
        return True
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False

def get_upcoming_travel(days=60):
    """Get travel events in next N days"""
    data = load_calendar()
    if not data:
        return []
    
    travel = []
    cutoff = datetime.now() + timedelta(days=days)
    
    for event in data.get('events', []):
        if event.get('is_travel'):
            # Parse date and filter
            date_str = event.get('start_raw', '')
            event_date = parse_date(date_str)
            if event_date and event_date <= cutoff:
                travel.append(event)
    
    return travel

def extract_confirmation_code(text):
    """Extract confirmation code from flight text"""
    patterns = [
        r'[Cc]onfirmation[:\s]+([A-Z0-9]{6})',
        r'[Cc]ode[:\s]+([A-Z0-9]{6})',
        r'\(([A-Z0-9]{6})\)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def extract_flight_numbers(text):
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

def save_flight_tracking(flight_data):
    """Save flight to tracking database"""
    FLIGHT_TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    tracked = {}
    if FLIGHT_TRACKING_FILE.exists():
        with open(FLIGHT_TRACKING_FILE, 'r') as f:
            tracked = json.load(f)
    
    flight_id = flight_data['id']
    tracked[flight_id] = flight_data
    
    with open(FLIGHT_TRACKING_FILE, 'w') as f:
        json.dump(tracked, f, indent=2)

def generate_flight_tasks(flight, existing_tasks):
    """Generate comprehensive tasks for a flight"""
    summary = flight.get('summary', 'Flight')
    date_str = flight.get('start', 'TBD')
    location = flight.get('location', '')
    description = flight.get('description', '')
    
    # Parse flight date
    flight_date = parse_date(flight.get('start_raw', ''))
    if not flight_date:
        print(f"   ⚠️  Could not parse date for: {summary}")
        return 0, 0, None
    
    # Extract confirmation code
    full_text = summary + ' ' + location + ' ' + description
    confirmation = extract_confirmation_code(full_text)
    
    # Extract flight numbers for tracking
    flight_numbers = extract_flight_numbers(full_text)
    
    print(f"\n✈️  {summary}")
    print(f"   📆 {date_str}")
    if confirmation:
        print(f"   🎫 Confirmation: {confirmation}")
    if flight_numbers:
        for airline, num in flight_numbers:
            print(f"   ✈️  Flight: {airline} {num}")
    
    created = 0
    skipped = 0
    
    # Calculate due dates
    rover_due = (flight_date - timedelta(days=10)).strftime('%Y-%m-%d')  # 10 days before for Rover
    check_due = (flight_date - timedelta(days=2)).strftime('%Y-%m-%d')
    uber_due = (flight_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Main flight task
    main_task = f"✈️ FLIGHT: {summary}"
    if create_todoist_task(main_task, "Travel", "1", rover_due, existing_tasks):
        if main_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Rover task (10 days before)
    rover_task = f"🐕 ROVER: Schedule sitter for Greta (10 days before) - {summary}"
    if create_todoist_task(rover_task, "Travel", "2", rover_due, existing_tasks):
        if rover_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Hotel check task (2 days before)
    hotel_task = f"🏨 HOTEL: Confirm reservation for trip - {summary}"
    if create_todoist_task(hotel_task, "Travel", "2", check_due, existing_tasks):
        if hotel_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Uber task (1 day before)
    uber_task = f"🚗 UBER: Schedule ride to airport - {summary}"
    if create_todoist_task(uber_task, "Travel", "2", uber_due, existing_tasks):
        if uber_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Pack task (2 days before)
    pack_task = f"🎒 PACK: Prepare luggage for {summary}"
    if create_todoist_task(pack_task, "Travel", "2", check_due, existing_tasks):
        if pack_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Create flight tracking data
    flight_data = None
    if flight_numbers:
        for airline, num in flight_numbers:
            flight_id = f"{airline}{num}_{flight_date.strftime('%Y%m%d')}"
            flight_data = {
                'id': flight_id,
                'airline': airline,
                'flight_number': num,
                'summary': summary,
                'departure_time': flight_date.isoformat(),
                'location': location,
                'confirmation': confirmation,
                'added_at': datetime.now().isoformat(),
                'status': 'pending'
            }
            save_flight_tracking(flight_data)
            print(f"   📊 Added to flight tracking: {airline} {num}")
    
    return created, skipped, flight_data

def generate_hotel_tasks(hotel, existing_tasks):
    """Generate tasks for hotel stays"""
    summary = hotel.get('summary', 'Hotel')
    location = hotel.get('location', '')
    
    # Parse check-in date
    checkin_date = parse_date(hotel.get('start_raw', ''))
    if not checkin_date:
        return 0, 0
    
    print(f"\n🏨 {summary}")
    print(f"   📆 Check-in: {hotel.get('start', 'TBD')}")
    print(f"   📍 {location[:60]}...")
    
    created = 0
    skipped = 0
    
    # Calculate due dates
    confirm_due = (checkin_date - timedelta(days=3)).strftime('%Y-%m-%d')
    dinner_due = (checkin_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Confirm reservation (3 days before)
    confirm_task = f"🏨 CONFIRM: Hotel reservation - {summary}"
    if create_todoist_task(confirm_task, "Travel", "2", confirm_due, existing_tasks):
        if confirm_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Dinner reservations (1 day before check-in)
    dinner_task = f"🍽️  DINNER: Make reservations near {summary}"
    if create_todoist_task(dinner_task, "Travel", "3", dinner_due, existing_tasks):
        if dinner_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    # Check amenities
    amenities_task = f"📋 RESEARCH: Hotel amenities & nearby restaurants - {summary}"
    if create_todoist_task(amenities_task, "Travel", "3", confirm_due, existing_tasks):
        if amenities_task not in existing_tasks:
            created += 1
        else:
            skipped += 1
    
    return created, skipped

def generate_travel_tasks():
    """Generate and create travel tasks"""
    travel_events = get_upcoming_travel(days=60)
    
    if not travel_events:
        print("✅ No upcoming travel in next 60 days")
        return 0, 0, []
    
    # Get existing tasks to avoid duplicates
    print("📋 Fetching existing tasks...")
    existing_tasks = get_existing_tasks("Travel")
    print(f"   Found {len(existing_tasks)} existing tasks")
    print()
    
    print(f"🧳 Found {len(travel_events)} travel events")
    print("=" * 70)
    
    total_created = 0
    total_skipped = 0
    tracked_flights = []
    
    for trip in travel_events:
        summary = trip.get('summary', '').lower()
        
        # Determine trip type
        if 'flight' in summary or 'delta' in summary or 'united' in summary or 'american' in summary:
            created, skipped, flight_data = generate_flight_tasks(trip, existing_tasks)
            total_created += created
            total_skipped += skipped
            if flight_data:
                tracked_flights.append(flight_data)
        
        elif 'hotel' in summary or 'stay at' in summary or 'marriott' in summary or 'hilton' in summary or 'ritz' in summary:
            created, skipped = generate_hotel_tasks(trip, existing_tasks)
            total_created += created
            total_skipped += skipped
    
    return total_created, total_skipped, tracked_flights

def run_flight_monitor():
    """Run the flight monitor to check flight status"""
    print("\n" + "=" * 70)
    print("📊 Running Flight Monitor...")
    try:
        monitor_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "travel_flight_monitor.py"
        if monitor_script.exists():
            result = subprocess.run(
                ["python3", str(monitor_script)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print("✅ Flight monitor completed")
            else:
                print(f"⚠️  Flight monitor error: {result.stderr}")
        else:
            print(f"⚠️  Flight monitor script not found")
    except Exception as e:
        print(f"⚠️  Could not run flight monitor: {e}")

def run_car_check():
    """Run the car check for upcoming flights"""
    print("\n" + "=" * 70)
    print("🚗 Running Car Reservation Check...")
    try:
        car_check_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "travel_car_check.py"
        if car_check_script.exists():
            result = subprocess.run(
                ["python3", str(car_check_script)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print("✅ Car check completed")
            else:
                print(f"⚠️  Car check error: {result.stderr}")
        else:
            print(f"⚠️  Car check script not found")
    except Exception as e:
        print(f"⚠️  Could not run car check: {e}")

def main():
    """Main function"""
    print("🧳 Travel Automation v2 - Comprehensive Travel Tasks")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Check if todoist CLI is available
    try:
        result = subprocess.run(["todoist", "--version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("❌ Todoist CLI not configured. Run: todoist auth <token>")
            return
    except:
        print("❌ Todoist CLI not found. Install: npm install -g todoist-ts-cli")
        return
    
    # Generate travel tasks
    created, skipped, tracked_flights = generate_travel_tasks()
    
    print()
    print("=" * 70)
    print(f"✅ Travel task generation complete")
    print(f"   Created: {created} new tasks")
    print(f"   Skipped: {skipped} existing tasks")
    
    if tracked_flights:
        print(f"   Flights tracked: {len(tracked_flights)}")
    
    # Run flight monitor (if --monitor flag or if new flights were found)
    import sys
    if '--monitor' in sys.argv or tracked_flights:
        run_flight_monitor()
    
    # Run car check (if --car-check flag)
    if '--car-check' in sys.argv:
        run_car_check()

if __name__ == "__main__":
    main()
