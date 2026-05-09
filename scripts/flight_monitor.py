#!/usr/bin/env python3
"""
Flight Monitor - Track flights and alert on changes
Runs daily to check flight status using flight-tracker skill
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "flight-monitor.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def extract_flight_number(summary):
    """Extract flight number from event summary"""
    import re
    # Look for patterns like "Delta 960", "DL 4099", "flight 960"
    patterns = [
        r'(?:Delta|DL)\s*(\d+)',
        r'flight\s*(\d+)',
        r'DL\s*(\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, summary, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def get_upcoming_flights(days=30):
    """Get flights in the next N days"""
    if not CALENDAR_FILE.exists():
        log("❌ Calendar file not found")
        return []
    
    with open(CALENDAR_FILE) as f:
        data = json.load(f)
    
    flights = []
    now = datetime.now().astimezone()
    cutoff = now + timedelta(days=days)
    
    for event in data.get("events", []):
        summary = event.get("summary", "").lower()
        if any(x in summary for x in ["flight", "delta", "dl "]):
            start = event.get("start", {})
            start_time = start.get("dateTime") or start.get("date")
            if start_time:
                try:
                    event_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    event_time = event_time.astimezone()
                    if now <= event_time <= cutoff:
                        flight_num = extract_flight_number(event.get("summary", ""))
                        flights.append({
                            "summary": event.get("summary"),
                            "flight_number": flight_num,
                            "departure": event_time,
                            "confirmation": event.get("description", "")
                        })
                except:
                    pass
    
    return flights

def check_flight_status(flight_number):
    """Check flight status using flight-tracker"""
    try:
        result = subprocess.run(
            ["python3", "skills/flight-tracker/track.py", flight_number],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout if result.returncode == 0 else None
    except Exception as e:
        log(f"❌ Error checking flight {flight_number}: {e}")
        return None

def main():
    log("=" * 60)
    log("🛫 Flight Monitor Starting")
    log("=" * 60)
    
    flights = get_upcoming_flights(days=14)
    log(f"📊 Found {len(flights)} upcoming flights")
    
    for flight in flights:
        log(f"\n✈️  {flight['summary']}")
        log(f"   Flight #: {flight['flight_number'] or 'Unknown'}")
        log(f"   Departure: {flight['departure']}")
        
        if flight['flight_number']:
            status = check_flight_status(flight['flight_number'])
            if status:
                log(f"   Status: {status[:200]}...")
            else:
                log(f"   Status: Could not fetch")
    
    log("\n✅ Flight check complete")

if __name__ == "__main__":
    main()
