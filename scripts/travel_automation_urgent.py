#!/usr/bin/env python3
"""
Travel Automation - URGENT MODE
Creates Todoist tasks for ALL upcoming trips with due date = TODAY
For immediate action on travel prep
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

def create_todoist_task(task_text, project="Travel", priority="2", due_date=None, existing_tasks=None):
    """Create a task in Todoist if it doesn't already exist"""
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

def generate_urgent_travel_tasks():
    """Generate and create travel tasks with TODAY as due date"""
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
            # This is a flight
            # Only create ROVER task if departing FROM LAX (not returning TO LAX)
            # Check if LAX is in the location AND it's a departure (not arrival)
            location_lower = location.lower()
            summary_lower = summary.lower()
            
            # LAX departure = LAX is mentioned AND (flight TO somewhere OR departing from LAX)
            # JFK return = flight FROM JFK TO LAX
            is_jfk_to_lax = 'jfk' in location_lower and 'lax' in location_lower and ('new york' in location_lower or 'jfk' in summary_lower)
            is_lax_departure = 'lax' in location_lower and not is_jfk_to_lax
            
            tasks = [
                (f"🎒 PACK: Prepare luggage - {summary}", today_str, "2"),
                (f"🚗 UBER: Schedule ride to airport - {summary}", today_str, "2"),
            ]
            
            # Only add ROVER for LAX departures (when Greta needs care)
            if is_lax_departure:
                tasks.insert(0, (f"🐕 ROVER: Schedule sitter for Greta - {summary}", today_str, "2"))
                tasks.append((f"Check LAX traffic/security wait times", today_str, "3"))
            
            for task, due, priority in tasks:
                if create_todoist_task(task, project="Travel", priority=priority, due_date=due, existing_tasks=existing_tasks):
                    if task not in existing_tasks:
                        print(f"   ✅ Created (DUE TODAY): {task}")
                        created_count += 1
                    else:
                        skipped_count += 1
                else:
                    print(f"   ⚠️  Failed: {task}")
        
        elif 'hotel' in summary.lower() or 'stay at' in summary.lower():
            # This is a hotel
            tasks = [
                (f"🏨 CONFIRM: Hotel reservation - {summary}", today_str, "3"),
                (f"📋 RESEARCH: Hotel amenities & nearby restaurants - {location}", today_str, "3"),
                (f"🍽️ DINNER: Make reservations near hotel - {location}", today_str, "3"),
            ]
            
            for task, due, priority in tasks:
                if create_todoist_task(task, project="Travel", priority=priority, due_date=due, existing_tasks=existing_tasks):
                    if task not in existing_tasks:
                        print(f"   ✅ Created (DUE TODAY): {task}")
                        created_count += 1
                    else:
                        skipped_count += 1
    
    return created_count, skipped_count

def main():
    """Main function"""
    print("🚨 URGENT Travel Automation - All Tasks Due TODAY")
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
    
    created, skipped = generate_urgent_travel_tasks()
    
    if created is not None:
        print()
        print("=" * 60)
        print(f"✅ URGENT task generation complete")
        print(f"   Created: {created} new tasks (ALL DUE TODAY)")
        print(f"   Skipped: {skipped} existing tasks")
        print()
        print("🚨 Check your Todoist - all travel tasks are due TODAY!")

if __name__ == "__main__":
    main()
