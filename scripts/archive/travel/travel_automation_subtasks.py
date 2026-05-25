#!/usr/bin/env python3
"""
Travel Automation - Subtask Mode
Creates parent tasks for each trip with subtasks underneath
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

def get_upcoming_travel(days=60):
    """Get travel events in next N days"""
    data = load_calendar()
    if not data:
        return []
    
    travel = []
    for event in data.get('events', []):
        if event.get('is_travel'):
            travel.append(event)
    
    return travel

def get_existing_tasks():
    """Get list of existing task names"""
    try:
        result = subprocess.run(["todoist", "list"], 
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

def create_parent_task(task_text, project="Travel", priority="2", due_date=None, existing_tasks=None):
    """Create a parent task and return its ID"""
    if existing_tasks and task_text in existing_tasks:
        print(f"   ⏭️  Parent exists: {task_text[:50]}...")
        # Try to find the task ID
        try:
            result = subprocess.run(["todoist", "list"], capture_output=True, text=True, timeout=30)
            for line in result.stdout.strip().split('\n'):
                if task_text in line:
                    parts = line.split()
                    if parts:
                        return parts[0]  # Return task ID
        except:
            pass
        return None
    
    try:
        cmd = ["todoist", "add", task_text, "-p", project, "-P", priority]
        if due_date:
            cmd.extend(["-d", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            error = result.stderr.strip()
            if "already exists" in error.lower():
                print(f"   ⏭️  Parent exists: {task_text[:50]}...")
                return None
            print(f"   ❌ Error creating parent: {error}")
            return None
        
        # Extract task ID from output
        output = result.stdout.strip()
        if output:
            # Output format: "Task added: <id>"
            parts = output.split()
            if len(parts) >= 3:
                return parts[2]  # Return the ID
        return None
    except Exception as e:
        print(f"❌ Error creating parent task: {e}")
        return None

def create_subtask(task_text, parent_id, project="Travel", priority="3", due_date=None, existing_tasks=None):
    """Create a subtask under a parent task"""
    full_text = f"    {task_text}"  # Indent to show as subtask in list view
    
    if existing_tasks and full_text in existing_tasks:
        print(f"   ⏭️  Subtask exists: {task_text[:50]}...")
        return True
    
    try:
        cmd = ["todoist", "add", full_text, "-p", project, "-P", priority]
        if due_date:
            cmd.extend(["-d", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            error = result.stderr.strip()
            if "already exists" in error.lower():
                print(f"   ⏭️  Subtask exists: {task_text[:50]}...")
                return True
            print(f"   ❌ Error creating subtask: {error}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error creating subtask: {e}")
        return False

def generate_travel_subtasks():
    """Generate and create travel tasks as subtasks"""
    travel_events = get_upcoming_travel(days=60)
    
    if not travel_events:
        print("✅ No upcoming travel found")
        return 0, 0
    
    print("📋 Fetching existing tasks...")
    existing_tasks = get_existing_tasks()
    print(f"   Found {len(existing_tasks)} existing tasks")
    print()
    
    print(f"🧳 Found {len(travel_events)} travel events")
    print("=" * 60)
    
    created_count = 0
    skipped_count = 0
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Group by trip (flights and hotels that belong together)
    trips = []
    current_trip = None
    
    for trip in travel_events:
        summary = trip.get('summary', 'Travel')
        date = trip.get('start', 'TBD')
        location = trip.get('location', '')
        
        print(f"\n✈️  {summary}")
        print(f"   📆 {date}")
        if location:
            print(f"   📍 {location}")
        
        # Create parent task name
        if 'flight' in summary.lower() or 'delta' in summary.lower():
            parent_name = f"✈️ TRIP: {summary[:50]}"
        elif 'hotel' in summary.lower() or 'stay at' in summary.lower():
            parent_name = f"🏨 STAY: {summary[:50]}"
        else:
            parent_name = f"🧳 TRAVEL: {summary[:50]}"
        
        # Create parent task
        parent_id = create_parent_task(parent_name, project="Travel", priority="2", 
                                       due_date=today_str, existing_tasks=existing_tasks)
        
        if parent_name in existing_tasks:
            skipped_count += 1
        else:
            created_count += 1
        
        # Create subtasks based on type
        if 'flight' in summary.lower() or 'delta' in summary.lower():
            # This is a flight
            location_lower = location.lower()
            summary_lower = summary.lower()
            
            # LAX departure = LAX is mentioned AND (flight TO somewhere OR departing from LAX)
            # JFK return = flight FROM JFK TO LAX
            is_jfk_to_lax = 'jfk' in location_lower and 'lax' in location_lower and ('new york' in location_lower or 'jfk' in summary_lower)
            is_lax_departure = 'lax' in location_lower and not is_jfk_to_lax
            
            subtasks = [
                ("🎒 PACK: Prepare luggage", "3"),
                ("🚗 UBER: Schedule ride to airport", "3"),
            ]
            
            # Only add ROVER for LAX departures (when Greta needs care)
            if is_lax_departure:
                subtasks.insert(0, ("🐕 ROVER: Schedule sitter for Greta", "2"))
                subtasks.append(("Check LAX traffic/security wait times", "3"))
            
            for subtask, priority in subtasks:
                if create_subtask(subtask, parent_id, project="Travel", priority=priority, 
                                 due_date=today_str, existing_tasks=existing_tasks):
                    if f"    {subtask}" not in existing_tasks:
                        created_count += 1
                    else:
                        skipped_count += 1
        
        elif 'hotel' in summary.lower() or 'stay at' in summary.lower():
            # This is a hotel
            subtasks = [
                ("🏨 CONFIRM: Hotel reservation", "3"),
                ("📋 RESEARCH: Hotel amenities & nearby restaurants", "3"),
                ("🍽️ DINNER: Make reservations near hotel", "3"),
            ]
            
            for subtask, priority in subtasks:
                if create_subtask(subtask, parent_id, project="Travel", priority=priority, 
                                 due_date=today_str, existing_tasks=existing_tasks):
                    if f"    {subtask}" not in existing_tasks:
                        created_count += 1
                    else:
                        skipped_count += 1
    
    return created_count, skipped_count

def main():
    """Main function"""
    print("🚨 Travel Automation - SUBTASK MODE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("   Parent tasks with indented subtasks")
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
    
    created, skipped = generate_travel_subtasks()
    
    if created is not None:
        print()
        print("=" * 60)
        print(f"✅ Subtask generation complete")
        print(f"   Created: {created} new tasks/subtasks")
        print(f"   Skipped: {skipped} existing")
        print()
        print("🚨 Check your Todoist - all travel organized as parent + subtasks!")

if __name__ == "__main__":
    main()
