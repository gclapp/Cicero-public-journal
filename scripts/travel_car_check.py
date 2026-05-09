#!/usr/bin/env python3
"""
Travel Car Check - Verify car reservations exist 5 hours before flights
Sends alerts if no Uber/Lyft/car service is booked
"""

import json
import os
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
CAR_CHECK_LOG = Path.home() / ".openclaw" / "workspace" / "data" / "car-check-log.json"

# Keywords that indicate a car reservation
CAR_KEYWORDS = [
    'uber', 'lyft', 'taxi', 'cab', 'car service', 'car reservation',
    'reserved car', 'driver', 'pickup', 'dropoff', 'drop off', 'pick up',
    'black car', 'limo', 'limousine', 'shuttle', 'transportation',
    'ramtin', 'driver picking up'
]


def load_calendar():
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)


def load_check_log():
    """Load car check log"""
    if not CAR_CHECK_LOG.exists():
        return {'checks': [], 'alerts_sent': []}
    with open(CAR_CHECK_LOG, 'r') as f:
        return json.load(f)


def save_check_log(log):
    """Save car check log"""
    CAR_CHECK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CAR_CHECK_LOG, 'w') as f:
        json.dump(log, f, indent=2)


def parse_datetime(date_str):
    """Parse datetime from calendar"""
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None


def extract_flight_info(event):
    """Extract flight information from event"""
    summary = event.get('summary', '')
    description = event.get('description', '')
    full_text = (summary + ' ' + description).lower()
    
    # Check if this is a flight
    is_flight = any(word in full_text for word in 
                   ['flight', 'delta', 'united', 'american', 'departs', 'arrives', 'airport'])
    
    if not is_flight:
        return None
    
    # Extract flight number
    flight_patterns = [
        r'(?:delta|united|american|flight)\s+(?:air\s+lines?\s+)?(?:flight\s+)?(\d+)',
        r'(?:dl|ua|aa|b6|wn)\s+(\d+)',
    ]
    
    flight_number = None
    for pattern in flight_patterns:
        match = re.search(pattern, full_text)
        if match:
            flight_number = match.group(1)
            break
    
    # Parse departure time
    start_raw = event.get('start_raw', '')
    departure_time = parse_datetime(start_raw)
    
    if not departure_time:
        return None
    
    return {
        'summary': summary,
        'flight_number': flight_number,
        'departure_time': departure_time,
        'departure_time_str': departure_time.strftime('%A, %B %d at %I:%M %p'),
        'location': event.get('location', ''),
        'event_id': event.get('id', ''),
        'description': description
    }


def has_car_reservation(flight_event, all_events):
    """
    Check if there's a car reservation within 6 hours before the flight
    Returns True if car is booked, False otherwise
    """
    flight_time = parse_datetime(flight_event.get('start_raw', ''))
    if not flight_time:
        return False
    
    # Check window: 6 hours before to 1 hour after flight
    check_start = flight_time - timedelta(hours=6)
    check_end = flight_time + timedelta(hours=1)
    
    flight_summary = flight_event.get('summary', '').lower()
    flight_location = flight_event.get('location', '').lower()
    
    for event in all_events:
        event_time = parse_datetime(event.get('start_raw', ''))
        if not event_time:
            continue
        
        # Check if event is within our window
        if not (check_start <= event_time <= check_end):
            continue
        
        # Check event for car keywords
        event_summary = event.get('summary', '').lower()
        event_description = event.get('description', '').lower()
        event_location = event.get('location', '').lower()
        full_text = event_summary + ' ' + event_description + ' ' + event_location
        
        # Check for car keywords
        for keyword in CAR_KEYWORDS:
            if keyword in full_text:
                # Additional check: make sure it's related to this flight
                # (same day, airport-related, or explicitly mentions the flight)
                if any(word in full_text for word in ['airport', 'lax', 'jfk', 'flight']):
                    return True
                # If it's within 2 hours of flight, likely related
                if abs((event_time - flight_time).total_seconds()) < 7200:
                    return True
                # If it mentions pickup/dropoff and is on the same day
                if any(word in full_text for word in ['pickup', 'pick up', 'dropoff', 'drop off']):
                    return True
    
    return False


def create_todoist_task(task_text, project="Travel", priority="1", due_date=None):
    """Create an urgent Todoist task"""
    try:
        cmd = ["todoist", "add", task_text, "-p", project, "-P", priority]
        if due_date:
            cmd.extend(["-d", due_date])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✅ Todoist task created")
            return True
        else:
            print(f"   ⚠️  Todoist error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ⚠️  Failed to create Todoist task: {e}")
        return False


def send_car_alert(flight_info):
    """Send alert that car needs to be booked"""
    flight_summary = flight_info.get('summary', 'Unknown Flight')
    departure = flight_info.get('departure_time_str', 'Unknown')
    
    subject = f"🚗 URGENT: Book Car for Flight - {flight_summary}"
    
    body = f"""
<h2>Car Reservation Needed</h2>

<p><strong>Flight:</strong> {flight_summary}</p>
<p><strong>Departure:</strong> {departure}</p>
<p><strong>Location:</strong> {flight_info.get('location', 'N/A')}</p>

<h3>⚠️ No car reservation found within 5 hours of departure!</h3>

<p>Please book:</p>
<ul>
    <li><strong>Uber/Lyft</strong> - Schedule ride to airport</li>
    <li><strong>Car service</strong> - Book black car if preferred</li>
    <li><strong>Taxi</strong> - Arrange pickup time</li>
</ul>

<p><em>Alert sent at: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}</em></p>

<p><small>This is an automated reminder. A Todoist task has also been created.</small></p>
"""
    
    # Send email
    try:
        email_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
        if email_script.exists():
            result = subprocess.run([
                "python3", str(email_script),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", body,
                "--html"
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0:
                print(f"   📧 Alert email sent")
                return True
            else:
                print(f"   ⚠️  Email error: {result.stderr}")
    except Exception as e:
        print(f"   ⚠️  Failed to send email: {e}")
    
    return False


def check_car_reservations():
    """Main function to check car reservations for upcoming flights"""
    print("🚗 Travel Car Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Load calendar
    calendar = load_calendar()
    if not calendar:
        print("❌ No calendar data found")
        return
    
    log = load_check_log()
    all_events = calendar.get('events', [])
    
    # Find flights in the next 24 hours that need car check
    now = datetime.now()
    check_window_start = now
    check_window_end = now + timedelta(hours=24)
    
    flights_to_check = []
    
    for event in all_events:
        flight_info = extract_flight_info(event)
        if not flight_info:
            continue
        
        departure = flight_info['departure_time']
        
        # Only check flights between 5-24 hours from now
        hours_until = (departure - now).total_seconds() / 3600
        
        if 0 <= hours_until <= 24:
            flights_to_check.append((event, flight_info, hours_until))
    
    if not flights_to_check:
        print("✅ No flights in the next 24 hours requiring car check")
        return
    
    print(f"🔍 Found {len(flights_to_check)} flight(s) to check:")
    print()
    
    alerts_sent = 0
    
    for event, flight_info, hours_until in flights_to_check:
        flight_id = f"{flight_info['summary']}_{flight_info['departure_time'].strftime('%Y%m%d')}"
        
        print(f"✈️  {flight_info['summary']}")
        print(f"   📆 {flight_info['departure_time_str']}")
        print(f"   ⏰ {hours_until:.1f} hours from now")
        
        # Check if we already sent an alert for this flight
        if flight_id in log.get('alerts_sent', []):
            print(f"   ⏭️  Alert already sent for this flight")
            continue
        
        # Check for car reservation
        has_car = has_car_reservation(event, all_events)
        
        if has_car:
            print(f"   ✅ Car reservation found")
        else:
            print(f"   ❌ NO car reservation found!")
            print(f"   🚨 Sending alert...")
            
            # Send email alert
            if send_car_alert(flight_info):
                alerts_sent += 1
                log['alerts_sent'].append(flight_id)
            
            # Create urgent Todoist task
            due_date = flight_info['departure_time'].strftime('%Y-%m-%d')
            task_text = f"🚗 BOOK CAR: {flight_info['summary']} departing {flight_info['departure_time_str']}"
            create_todoist_task(task_text, "Travel", "1", due_date)
        
        # Log this check
        log['checks'].append({
            'flight_id': flight_id,
            'checked_at': now.isoformat(),
            'has_car': has_car,
            'hours_until_departure': hours_until
        })
        
        print()
    
    # Clean up old log entries (keep last 30 days)
    cutoff = now - timedelta(days=30)
    log['checks'] = [
        c for c in log.get('checks', [])
        if datetime.fromisoformat(c['checked_at']) > cutoff
    ]
    
    # Clean up old alerts (flights that have passed)
    current_ids = {f"{fi['summary']}_{fi['departure_time'].strftime('%Y%m%d')}" 
                   for _, fi, _ in flights_to_check}
    log['alerts_sent'] = [
        a for a in log.get('alerts_sent', [])
        if any(a.startswith(c['flight_id'].split('_')[0]) for c in log['checks'][-50:])
    ]
    
    save_check_log(log)
    
    print(f"{'='*70}")
    print(f"✅ Car check complete")
    print(f"   Flights checked: {len(flights_to_check)}")
    print(f"   Alerts sent: {alerts_sent}")


def main():
    check_car_reservations()


if __name__ == "__main__":
    main()
