#!/usr/bin/env python3
"""
Travel Automation - Creates Todoist tasks for upcoming trips
Runs daily to check calendar and create travel prep tasks
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"

def load_calendar():
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)

def get_upcoming_travel(days=7):
    """Get travel events in next N days"""
    data = load_calendar()
    if not data:
        return []
    
    travel = []
    for event in data.get('events', []):
        if event.get('is_travel'):
            travel.append(event)
    
    return travel

def get_existing_tasks(project="Travel"):
    """Get list of existing task names in the Travel project"""
    try:
        result = subprocess.run(["todoist", "tasks", "-p", project], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return set()
        
        # Parse task names from output
        existing = set()
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Format: ID  Task name
                parts = line.split('  ', 1)
                if len(parts) > 1:
                    existing.add(parts[1].strip())
        return existing
    except Exception as e:
        print(f"⚠️  Could not fetch existing tasks: {e}")
        return set()

def create_todoist_task(task_text, project="Travel", priority="2", due_date=None, existing_tasks=None):
    """Create a task in Todoist if it doesn't already exist"""
    # Check if task already exists
    if existing_tasks and task_text in existing_tasks:
        print(f"   ⏭️  Skipped (already exists): {task_text[:50]}...")
        return True
    
    try:
        cmd = ["todoist", "add", task_text, "-p", project, "-P", priority]
        if due_date:
            cmd.extend(["-d", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            error = result.stderr.strip()
            if "already exists" in error.lower():
                print(f"   ⏭️  Skipped (already exists): {task_text[:50]}...")
                return True
            print(f"   ❌ Error: {error}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False

def generate_travel_tasks():
    """Generate and create travel tasks"""
    travel_events = get_upcoming_travel(days=14)
    
    if not travel_events:
        print("✅ No upcoming travel in next 14 days")
        return 0, 0
    
    # Get existing tasks to avoid duplicates
    print("📋 Fetching existing tasks...")
    existing_tasks = get_existing_tasks("Travel")
    print(f"   Found {len(existing_tasks)} existing tasks")
    print()
    
    print(f"🧳 Found {len(travel_events)} travel events")
    print("=" * 60)
    
    created_count = 0
    skipped_count = 0
    
    for trip in travel_events:
        summary = trip.get('summary', 'Travel')
        date = trip.get('start', 'TBD')
        location = trip.get('location', '')
        
        print(f"\n✈️  {summary}")
        print(f"   📆 {date}")
        if location:
            print(f"   📍 {location}")
        
        # Determine trip type and create relevant tasks
        if 'flight' in summary.lower() or 'delta' in summary.lower():
            # This is a flight - extract date for due date calculation
            trip_date_str = trip.get('start_raw', '')
            try:
                if 'T' in trip_date_str:
                    trip_date = datetime.fromisoformat(trip_date_str.replace('Z', '+00:00').replace('+00:00', ''))
                else:
                    trip_date = datetime.strptime(trip_date_str, '%Y-%m-%d')
                
                # Calculate due dates
                rover_due = (trip_date - timedelta(days=10)).strftime('%Y-%m-%d')
                pack_due = (trip_date - timedelta(days=2)).strftime('%Y-%m-%d')
                uber_due = (trip_date - timedelta(days=1)).strftime('%Y-%m-%d')
            except:
                rover_due = pack_due = uber_due = None
            
            # This is a flight
            # Only create ROVER task if departing FROM LAX (not returning TO LAX)
            # Check if LAX/Los Angeles is in the location AND it's a departure (not arrival)
            location_lower = location.lower()
            summary_lower = summary.lower()
            
            # Check for LAX or Los Angeles in location
            is_lax_location = 'lax' in location_lower or 'los angeles' in location_lower
            is_jfk_location = 'jfk' in location_lower or 'new york' in location_lower
            
            # JFK return = flight FROM JFK TO LAX (both airports mentioned, departing from JFK)
            is_jfk_to_lax = is_jfk_location and is_lax_location and ('jfk' in location_lower or 'new york' in location_lower)
            # LAX departure = LAX location and NOT a JFK->LAX return
            is_lax_departure = is_lax_location and not is_jfk_to_lax
            
            tasks = [
                (f"🎒 PACK: Prepare luggage - {summary}", pack_due, "2"),
                (f"🚗 UBER: Schedule ride to airport - {summary}", uber_due, "2"),
            ]
            
            # Only add ROVER for LAX departures (when Greta needs care)
            if is_lax_departure:
                tasks.insert(0, (f"🐕 ROVER: Schedule sitter for Greta - {summary}", rover_due, "2"))
                tasks.append((f"Check LAX traffic/security wait times", uber_due, "3"))
            
            for task, due, priority in tasks:
                if create_todoist_task(task, project="Travel", priority=priority, due_date=due, existing_tasks=existing_tasks):
                    if task not in existing_tasks:
                        print(f"   ✅ Created: {task}")
                        created_count += 1
                    else:
                        skipped_count += 1
                else:
                    print(f"   ⚠️  Failed: {task}")
        
        elif 'hotel' in summary.lower() or 'stay at' in summary.lower():
            # This is a hotel - extract date for due date calculation
            trip_date_str = trip.get('start_raw', '')
            try:
                if 'T' in trip_date_str:
                    trip_date = datetime.fromisoformat(trip_date_str.replace('Z', '+00:00').replace('+00:00', ''))
                else:
                    trip_date = datetime.strptime(trip_date_str, '%Y-%m-%d')
                
                # Calculate due dates
                confirm_due = (trip_date - timedelta(days=7)).strftime('%Y-%m-%d')
                research_due = (trip_date - timedelta(days=5)).strftime('%Y-%m-%d')
                dinner_due = (trip_date - timedelta(days=3)).strftime('%Y-%m-%d')
            except:
                confirm_due = research_due = dinner_due = None
            
            tasks = [
                (f"🏨 CONFIRM: Hotel reservation - {summary}", confirm_due, "3"),
                (f"📋 RESEARCH: Hotel amenities & nearby restaurants - {location}", research_due, "3"),
                (f"🍽️ DINNER: Make reservations near hotel - {location}", dinner_due, "3"),
            ]
            
            for task, due, priority in tasks:
                if create_todoist_task(task, project="Travel", priority=priority, due_date=due, existing_tasks=existing_tasks):
                    if task not in existing_tasks:
                        print(f"   ✅ Created: {task}")
                        created_count += 1
                    else:
                        skipped_count += 1
    
    return created_count, skipped_count

def main():
    """Main function"""
    print("🧳 Travel Automation - Generating Todoist Tasks")
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
    
    if created is not None:
        print()
        print("=" * 60)
        print(f"✅ Travel task generation complete")
        print(f"   Created: {created} new tasks")
        print(f"   Skipped: {skipped} existing tasks")

if __name__ == "__main__":
    main()
