#!/usr/bin/env python3
"""
Car Reservation Check - Alert if no Uber/car booked 5 hours before flight
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "car-check.log"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def has_car_reservation(flight_time, hours_before=5):
    """Check if there's a car/Uber reservation within 5 hours of flight"""
    if not CALENDAR_FILE.exists():
        return False
    
    with open(CALENDAR_FILE) as f:
        data = json.load(f)
    
    check_window_start = flight_time - timedelta(hours=hours_before)
    check_window_end = flight_time - timedelta(hours=1)  # At least 1 hour before
    
    car_keywords = ["uber", "lyft", "taxi", "car service", "reserved car", "black car", "ground transport"]
    
    for event in data.get("events", []):
        summary = event.get("summary", "").lower()
        
        # Check if it's a car-related event
        if any(keyword in summary for keyword in car_keywords):
            start = event.get("start", {})
            start_time = start.get("dateTime") or start.get("date")
            
            if start_time:
                try:
                    event_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    # Check if car reservation is within the window
                    if check_window_start <= event_time <= check_window_end:
                        return True
                except:
                    pass
    
    return False

def send_alert(flight_summary, flight_time):
    """Send email alert about missing car reservation"""
    subject = f"🚗 URGENT: Book car for flight - {flight_summary}"
    body = f"""
<h2>Car Reservation Needed</h2>

<p><strong>Flight:</strong> {flight_summary}</p>
<p><strong>Departure:</strong> {flight_time.strftime('%Y-%m-%d %H:%M')}</p>
<p><strong>Time until departure:</strong> {(flight_time - datetime.now()).total_seconds() / 3600:.1f} hours</p>

<p>No Uber, Lyft, or car service reservation found within 5 hours of departure.</p>

<h3>Action Required:</h3>
<ul>
<li>Book Uber/Lyft to airport</li>
<li>Or arrange car service</li>
<li>Or confirm alternative transportation</li>
</ul>

<p><em>This is an automated alert from Cicero's travel monitoring system.</em></p>
"""
    
    try:
        subprocess.run([
            "python3", str(EMAIL_SCRIPT),
            "--to", "[REDACTED]",
            "--subject", subject,
            "--body", body,
            "--html"
        ], check=True, timeout=60)
        log(f"   ✅ Alert email sent")
        return True
    except Exception as e:
        log(f"   ❌ Failed to send email: {e}")
        return False

def create_todoist_task(flight_summary, flight_time):
    """Create urgent Todoist task"""
    try:
        import os
        os.environ["PATH"] += ":/home/ubuntu/.npm-global/bin:/home/ubuntu/.local/bin"
        
        task = f"🚗 BOOK CAR: {flight_summary} departing {flight_time.strftime('%H:%M')}"
        subprocess.run([
            "todoist", "add", task,
            "-p", "Travel",
            "-P", "1"
        ], check=True, timeout=30)
        log(f"   ✅ Todoist task created")
        return True
    except Exception as e:
        log(f"   ❌ Failed to create Todoist task: {e}")
        return False

def get_flights_needing_car_check():
    """Get flights departing in the next 6 hours"""
    if not CALENDAR_FILE.exists():
        return []
    
    with open(CALENDAR_FILE) as f:
        data = json.load(f)
    
    flights = []
    now = datetime.now()
    check_window = now + timedelta(hours=6)
    
    for event in data.get("events", []):
        summary = event.get("summary", "").lower()
        if any(x in summary for x in ["flight", "delta", "dl "]):
            start = event.get("start", {})
            start_time = start.get("dateTime") or start.get("date")
            
            if start_time:
                try:
                    event_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    # Check if flight is between 5-6 hours away (alert window)
                    if now + timedelta(hours=5) <= event_time <= check_window:
                        flights.append({
                            "summary": event.get("summary"),
                            "departure": event_time
                        })
                except:
                    pass
    
    return flights

def main():
    log("=" * 60)
    log("🚗 Car Reservation Check Starting")
    log("=" * 60)
    
    flights = get_flights_needing_car_check()
    log(f"📊 Found {len(flights)} flights in 5-6 hour window")
    
    alerts_sent = 0
    for flight in flights:
        log(f"\n✈️  Checking: {flight['summary']}")
        log(f"   Departure: {flight['departure']}")
        
        if has_car_reservation(flight['departure']):
            log(f"   ✅ Car reservation found")
        else:
            log(f"   ⚠️  NO CAR RESERVATION FOUND")
            if send_alert(flight['summary'], flight['departure']):
                alerts_sent += 1
            create_todoist_task(flight['summary'], flight['departure'])
    
    log(f"\n✅ Check complete. Alerts sent: {alerts_sent}")

if __name__ == "__main__":
    main()
