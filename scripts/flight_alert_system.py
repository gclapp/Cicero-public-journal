#!/usr/bin/env python3
"""
Flight Alert System - Monitors flights and calls/texts on important changes
Only alerts for: delays, cancellations, gate changes, significant schedule changes
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
ALERT_LOG = Path.home() / ".openclaw" / "workspace" / "logs" / "flight-alerts.log"
PHONE_NUMBER = "+16507767054"  # Geoff's number

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(ALERT_LOG, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def get_upcoming_flights(days=3):
    """Get flights in next N days from calendar"""
    if not CALENDAR_FILE.exists():
        return []
    
    with open(CALENDAR_FILE) as f:
        data = json.load(f)
    
    flights = []
    now = datetime.now()
    cutoff = now + timedelta(days=days)
    
    for event in data.get("events", []):
        summary = event.get("summary", "").lower()
        if any(x in summary for x in ["flight", "delta", "dl "]):
            start_time = event.get("start_raw", "")
            if start_time:
                try:
                    event_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    event_time = event_time.replace(tzinfo=None)
                    if now <= event_time <= cutoff:
                        flights.append({
                            "summary": event.get("summary"),
                            "date": event_time.strftime("%Y-%m-%d"),
                            "time": event_time.strftime("%I:%M %p"),
                            "description": event.get("description", "")
                        })
                except:
                    pass
    
    return flights

def send_voice_alert(message):
    """Send voice call alert"""
    try:
        # Use voice_call tool
        voice_message = f"Hello Geoff, this is Cicero. {message} Thanks for listening. Talk to you soon Geoff."
        
        # For now, log it - actual call would use voice_call tool
        log(f"VOICE ALERT: {message}")
        return True
    except Exception as e:
        log(f"Failed to send voice alert: {e}")
        return False

def send_telegram_alert(message):
    """Send Telegram alert"""
    log(f"TELEGRAM ALERT: {message}")
    return True

def check_flight_status(flight):
    """Check flight status - placeholder for actual API integration"""
    # This would integrate with FlightAware/aviationstack API
    # For now, just log that we're checking
    log(f"Checking status for: {flight['summary']} on {flight['date']}")
    return None  # No alerts for now until API is set up

def main():
    log("=" * 60)
    log("Flight Alert System - Starting")
    log("=" * 60)
    
    flights = get_upcoming_flights(days=3)
    log(f"Found {len(flights)} upcoming flights")
    
    for flight in flights:
        log(f"  - {flight['summary']} on {flight['date']} at {flight['time']}")
        
        # Check for status changes
        alert = check_flight_status(flight)
        if alert:
            send_voice_alert(alert)
            send_telegram_alert(alert)
    
    log("Check complete")

if __name__ == "__main__":
    main()
