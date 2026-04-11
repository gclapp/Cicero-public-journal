#!/usr/bin/env python3
"""
Travel Automation v2 - Comprehensive travel task creation
Creates Todoist tasks for flights, hotels, Rover, Uber, and dinner reservations
"""

import json
import os
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"

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

def generate_flight_tasks(flight, existing_tasks):
    """Generate comprehensive tasks for a flight"""
    summary = flight.get('summary', 'Flight')
    date_str = flight.get('start', 'TBD')
    location = flight.get('location', '')
    
    # Parse flight date
    flight_date = parse_date(flight.get('start_raw', ''))
    if not flight_date:
        print(f"   ⚠️  Could not parse date for: {summary}")
        return 0, 0
    
    # Extract confirmation code
    confirmation = extract_confirmation_code(summary + ' ' + location)
    
    print(f"\n✈️  {summary}")
    print(f"   📆 {date_str}")
    if confirmation:
        print(f"   🎫 Confirmation: {confirmation}")
    
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
    
    return created, skipped

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
        return 0, 0
    
    # Get existing tasks to avoid duplicates
    print("📋 Fetching existing tasks...")
    existing_tasks = get_existing_tasks("Travel")
    print(f"   Found {len(existing_tasks)} existing tasks")
    print()
    
    print(f"🧳 Found {len(travel_events)} travel events")
    print("=" * 70)
    
    total_created = 0
    total_skipped = 0
    
    for trip in travel_events:
        summary = trip.get('summary', '').lower()
        
        # Determine trip type
        if 'flight' in summary or 'delta' in summary or 'united' in summary or 'american' in summary:
            created, skipped = generate_flight_tasks(trip, existing_tasks)
            total_created += created
            total_skipped += skipped
        
        elif 'hotel' in summary or 'stay at' in summary or 'marriott' in summary or 'hilton' in summary or 'ritz' in summary:
            created, skipped = generate_hotel_tasks(trip, existing_tasks)
            total_created += created
            total_skipped += skipped
    
    return total_created, total_skipped

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
    
    created, skipped = generate_travel_tasks()
    
    print()
    print("=" * 70)
    print(f"✅ Travel task generation complete")
    print(f"   Created: {created} new tasks")
    print(f"   Skipped: {skipped} existing tasks")

if __name__ == "__main__":
    main()
