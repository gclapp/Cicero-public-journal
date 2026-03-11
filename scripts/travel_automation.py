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

def create_todoist_task(task_text, project="Travel", priority="2", due_date=None):
    """Create a task in Todoist"""
    try:
        cmd = ["todoist", "add", task_text, "-p", project, "--priority", priority]
        if due_date:
            cmd.extend(["--due", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False

def generate_travel_tasks():
    """Generate and create travel tasks"""
    travel_events = get_upcoming_travel(days=14)
    
    if not travel_events:
        print("✅ No upcoming travel in next 14 days")
        return
    
    print(f"🧳 Found {len(travel_events)} travel events")
    print("=" * 60)
    
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
            tasks = [
                f"Check in for flight: {summary}",
                f"Download boarding pass: {summary}",
                f"Pack for trip: {summary} (location: {location})",
            ]
            
            if 'lax' in location.lower():
                tasks.append(f"Check LAX traffic/security wait times")
            
            for task in tasks:
                if create_todoist_task(task, project="Travel", priority="2"):
                    print(f"   ✅ Created: {task}")
                else:
                    print(f"   ⚠️  Failed: {task}")
        
        elif 'hotel' in summary.lower() or 'stay at' in summary.lower():
            # This is a hotel
            tasks = [
                f"Confirm hotel reservation: {summary}",
                f"Check hotel amenities/location: {location}",
            ]
            
            for task in tasks:
                if create_todoist_task(task, project="Travel", priority="3"):
                    print(f"   ✅ Created: {task}")

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
    
    generate_travel_tasks()
    
    print()
    print("=" * 60)
    print("✅ Travel task generation complete")

if __name__ == "__main__":
    main()
