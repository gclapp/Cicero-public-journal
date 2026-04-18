#!/usr/bin/env python3
"""
Resy Calendar Scanner
Scans Google Calendar for NYC trips and checks for missing reservations
"""

import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error
import random
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import monitoring
from monitoring import log_scan, log_booking, log_error, log_reservation_attempt
from circuit_breaker import (
    record_failure, record_success, is_circuit_open, 
    should_skip_venue, get_problematic_venues
)
from trips import extract_trip_from_flights as extract_trips_from_flights

# Google Calendar integration
CALENDAR_CREDENTIALS = Path.home() / ".openclaw" / "credentials" / "calendar-credentials.json"
CALENDAR_TOKEN = Path.home() / ".openclaw" / "credentials" / "calendar-token.pickle"

# Resy credentials
RESY_CREDENTIALS = Path.home() / ".openclaw" / "config" / "resy-credentials.json"

# Data files
DATA_DIR = Path(__file__).parent / "data"
RESERVATIONS_FILE = DATA_DIR / "reservations.json"
RESTAURANTS_FILE = DATA_DIR / "restaurants.json"
SCAN_STATE_FILE = DATA_DIR / "scan_state.json"

def load_resy_credentials():
    """Load Resy API credentials"""
    with open(RESY_CREDENTIALS) as f:
        return json.load(f)

def load_restaurants():
    """Load restaurant list"""
    with open(RESTAURANTS_FILE) as f:
        return json.load(f)

def load_reservations():
    """Load existing reservations"""
    if not RESERVATIONS_FILE.exists():
        return {"reservations": []}
    with open(RESERVATIONS_FILE) as f:
        return json.load(f)

def save_reservations(data):
    """Save reservation history"""
    with open(RESERVATIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_scan_state():
    """Load last scan state"""
    if not SCAN_STATE_FILE.exists():
        return {"last_scan": None, "last_bookings": []}
    with open(SCAN_STATE_FILE) as f:
        return json.load(f)

def save_scan_state(state):
    """Save scan state"""
    with open(SCAN_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def find_resy_reservations(venue_id, day, party_size, venue_name="", lat=None, long=None):
    """Find available reservations at a venue
    
    Returns:
        tuple: (result_dict, status)
            - result_dict: The API response data or None
            - status: 'success', 'api_error', 'no_availability', or 'circuit_open'
    """
    # Check circuit breaker first
    should_skip, skip_reason = should_skip_venue(venue_id)
    if should_skip:
        print(f"  ⚠️  Skipping venue {venue_id}: {skip_reason}")
        return None, 'circuit_open'
    
    creds = load_resy_credentials()

    # Use provided coordinates or default to Manhattan
    if lat is None:
        lat = "40.7128"
    if long is None:
        long = "-74.0060"

    url = f"https://api.resy.com/4/find?day={day}&party_size={party_size}&venue_id={venue_id}&lat={lat}&long={long}"

    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            # Record success to reset failure count
            record_success(venue_id)
            
            # Check if API returned empty venues (no availability vs error)
            venues = result.get('results', {}).get('venues', [])
            if not venues:
                return result, 'no_availability'
            
            return result, 'success'
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        print(f"  ❌ Error checking venue {venue_id}: {error_msg}")
        # Record failure for circuit breaker
        record_failure(venue_id, venue_name, error_msg)
        log_error('scanner', 'api_error', f"Failed to check availability for venue {venue_id}",
                  {'venue_id': venue_id, 'day': day, 'error': error_msg})
        return None, 'api_error'
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Error checking venue {venue_id}: {e}")
        # Record failure for circuit breaker
        record_failure(venue_id, venue_name, error_msg)
        log_error('scanner', 'api_error', f"Failed to check availability for venue {venue_id}",
                  {'venue_id': venue_id, 'day': day, 'error': error_msg})
        return None, 'api_error'

def book_reservation(config_id, payment_method_id=None):
    """Book a reservation"""
    creds = load_resy_credentials()

    url = "https://api.resy.com/3/book"

    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/x-www-form-urlencoded"
    }

    import urllib.parse
    data = {
        "config_id": config_id,
        "struct_payment_method": json.dumps({"id": payment_method_id}) if payment_method_id else "{}"
    }

    encoded_data = urllib.parse.urlencode(data).encode()

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if hasattr(e, 'read') else 'Unknown error'
        error_msg = f"HTTP {e.code}: {e.reason}"
        print(f"  ❌ Booking error: {error_msg}")
        log_error('scanner', 'booking_error', f"Failed to book reservation",
                  {'config_id': config_id, 'error': error_msg, 'details': error_body})
        return None
    except Exception as e:
        print(f"  ❌ Booking error: {e}")
        log_error('scanner', 'booking_error', f"Failed to book reservation",
                  {'config_id': config_id, 'error': str(e)})
        return None

def get_payment_method():
    """Get user's payment method"""
    creds = load_resy_credentials()
    
    url = "https://api.resy.com/2/user/payment-methods"
    
    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data and "payment_methods" in data and len(data["payment_methods"]) > 0:
                return data["payment_methods"][0].get("id")
    except:
        pass
    return None

def get_user_reservations():
    """Fetch user's existing reservations from Resy API"""
    creds = load_resy_credentials()
    
    url = "https://api.resy.com/3/user/reservations"
    
    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            reservations = []
            
            # Parse reservations from response
            for res in data.get("reservations", []):
                # Extract venue name from share message if venue object doesn't have it
                venue_name = res.get("venue", {}).get("name")
                if not venue_name:
                    # Try to extract from share message
                    share_msg = res.get("share", {}).get("generic_message", "")
                    if "for " in share_msg and " on " in share_msg:
                        # Parse "Please RSVP for [Venue Name] on [Date]"
                        parts = share_msg.split(" for ", 1)
                        if len(parts) > 1:
                            venue_part = parts[1].split(" on ", 1)[0]
                            venue_name = venue_part
                
                reservation = {
                    "resy_reservation_id": res.get("reservation_id"),
                    "venue_name": venue_name or "Unknown Restaurant",
                    "venue_id": str(res.get("venue", {}).get("id", "")),
                    "date": res.get("day"),
                    "time": res.get("time_slot") or res.get("time"),
                    "party_size": res.get("num_seats"),
                    "status": "confirmed",  # If it's in the list, it's confirmed
                    "source": "resy_api",
                    "synced_at": datetime.now().isoformat()
                }
                reservations.append(reservation)
            
            return reservations
            
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        print(f"  ❌ Error fetching Resy reservations: {error_msg}")
        log_error('scanner', 'api_error', "Failed to fetch user reservations from Resy",
                  {'error': error_msg})
        return []
    except Exception as e:
        print(f"  ❌ Error fetching Resy reservations: {e}")
        log_error('scanner', 'api_error', "Failed to fetch user reservations from Resy",
                  {'error': str(e)})
        return []

def parse_calendar_reservations(events):
    """Parse Google Calendar events to find restaurant reservations"""
    reservations = []
    
    for event in events:
        summary = event.get("summary", "")
        location = event.get("location", "")
        description = event.get("description", "")
        
        # Look for reservation patterns
        is_reservation = False
        restaurant_name = None
        
        # Pattern 1: "Reservation at [Restaurant Name]"
        if "reservation at" in summary.lower():
            is_reservation = True
            # Extract restaurant name
            match = re.search(r'Reservation at (.+?)(?:\s+at\s+|$)', summary, re.IGNORECASE)
            if match:
                restaurant_name = match.group(1).strip()
        
        # Pattern 2: "Dinner at [Restaurant]" or "[Restaurant] reservation"
        elif any(word in summary.lower() for word in ["dinner at", "lunch at", "brunch at"]):
            is_reservation = True
            parts = summary.lower().split(" at ", 1)
            if len(parts) > 1:
                restaurant_name = parts[1].strip()
        
        if is_reservation and restaurant_name:
            # Get date from event
            start = event.get("start", {})
            date = None
            time = None
            
            if "dateTime" in start:
                dt = datetime.fromisoformat(start["dateTime"].replace('Z', '+00:00'))
                date = dt.strftime("%Y-%m-%d")
                time = dt.strftime("%H:%M")
            elif "date" in start:
                date = start["date"]
                time = "19:00"  # Default to 7 PM if no time specified
            
            if date:
                # Try to find venue_id from our database
                venue_id = find_venue_id_by_name(restaurant_name)
                
                reservation = {
                    "venue_name": restaurant_name,
                    "venue_id": venue_id,
                    "date": date,
                    "time": time,
                    "party_size": 2,  # Default assumption
                    "source": "calendar",
                    "calendar_event_id": event.get("id"),
                    "location": location,
                    "notes": f"Found in Google Calendar: {summary}",
                    "synced_at": datetime.now().isoformat()
                }
                reservations.append(reservation)
    
    return reservations

def find_venue_id_by_name(name):
    """Try to find venue_id from our database by name"""
    # Load NYC restaurants database
    nyc_db_path = Path(__file__).parent / "data" / "nyc_restaurants.json"
    if nyc_db_path.exists():
        with open(nyc_db_path) as f:
            data = json.load(f)
        
        name_lower = name.lower()
        for restaurant in data.get("restaurants", []):
            db_name = restaurant.get("name", "").lower()
            # Check for exact match or substring match
            if name_lower in db_name or db_name in name_lower:
                return restaurant.get("venue_id")
    
    return None

def sync_calendar_reservations():
    """Sync reservations found in Google Calendar"""
    print("🔄 Checking Google Calendar for reservations...")
    
    # Get calendar events
    events = parse_calendar_events()
    calendar_reservations = parse_calendar_reservations(events)
    
    if not calendar_reservations:
        print("  ℹ️  No reservations found in calendar")
        return
    
    # Load existing reservations
    local_data = load_reservations()
    local_reservations = local_data.get("reservations", [])
    
    # Create a set of existing dates to avoid duplicates
    existing_dates = {(r.get("date"), r.get("venue_name").lower() if r.get("venue_name") else "") 
                      for r in local_reservations}
    
    added_count = 0
    
    for res in calendar_reservations:
        date = res.get("date")
        venue_name = res.get("venue_name", "").lower()
        
        # Check if we already have this reservation
        if (date, venue_name) in existing_dates:
            continue
        
        # Add new reservation
        local_reservations.append(res)
        existing_dates.add((date, venue_name))
        added_count += 1
        print(f"  ✅ Found reservation: {res['venue_name']} on {date}")
    
    # Save updated reservations
    local_data["reservations"] = local_reservations
    save_reservations(local_data)
    
    print(f"  ✅ Added {added_count} reservations from Google Calendar")

def sync_resy_reservations():
    """Sync reservations from Resy API to local database"""
    print("🔄 Syncing reservations from Resy...")
    
    resy_reservations = get_user_reservations()
    local_data = load_reservations()
    local_reservations = local_data.get("reservations", [])
    
    # Create a set of current Resy reservation IDs
    current_resy_ids = {r.get("resy_reservation_id") for r in resy_reservations if r.get("resy_reservation_id")}
    
    # Create a set of existing Resy reservation IDs in local file
    existing_resy_ids = {r.get("resy_reservation_id") for r in local_reservations if r.get("resy_reservation_id")}
    
    added_count = 0
    updated_count = 0
    removed_count = 0
    
    # Remove reservations that no longer exist in Resy (cancelled or past)
    local_reservations = [
        r for r in local_reservations 
        if r.get("resy_reservation_id") not in existing_resy_ids or  # Keep non-Resy reservations
           r.get("resy_reservation_id") in current_resy_ids  # Keep if still in Resy
    ]
    removed_count = len(existing_resy_ids - current_resy_ids)
    
    for res in resy_reservations:
        resy_id = res.get("resy_reservation_id")
        
        # Skip cancelled reservations
        if res.get("status") == "cancelled":
            continue
            
        # Check if this reservation already exists locally
        existing = next((r for r in local_reservations if r.get("resy_reservation_id") == resy_id), None)
        
        if existing:
            # Update existing reservation if status changed
            if existing.get("status") != res.get("status"):
                existing["status"] = res.get("status")
                updated_count += 1
        else:
            # Add new reservation
            local_reservations.append(res)
            added_count += 1
    
    # Save updated reservations
    local_data["reservations"] = local_reservations
    local_data["last_sync"] = datetime.now().isoformat()
    save_reservations(local_data)
    
    print(f"  ✅ Synced {len(resy_reservations)} reservations from Resy")
    print(f"     Added: {added_count}, Updated: {updated_count}, Removed: {removed_count}")
    
    return local_reservations

def parse_calendar_events():
    """
    Parse calendar events to find NYC trips.
    For now, this is a simplified version that checks for common NYC indicators.
    In production, this would integrate with Google Calendar API.
    """
    # Read cached calendar events if available
    calendar_cache = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
    
    if not calendar_cache.exists():
        print("📅 No calendar cache found. Run calendar_reader.py first.")
        return []
    
    with open(calendar_cache) as f:
        data = json.load(f)
    
    events = data.get("events", [])
    
    # Find NYC trips (events with NYC/New York in title/location)
    nyc_indicators = ['nyc', 'new york', 'manhattan', 'brooklyn', 'jfk', 'lga', 'newark']
    
    nyc_events = []
    for event in events:
        summary = event.get("summary", "").lower()
        location = event.get("location", "").lower()
        description = event.get("description", "").lower()
        
        text = f"{summary} {location} {description}"
        
        if any(indicator in text for indicator in nyc_indicators):
            nyc_events.append(event)
    
    return nyc_events

def extract_trip_dates(events):
    """Extract trip date ranges from NYC events"""
    if not events:
        return []
    
    # Group events by date
    dates = set()
    for event in events:
        # Try start_raw first (ISO format from calendar cache)
        start_raw = event.get("start_raw", "")
        if start_raw:
            # Extract just the date part (YYYY-MM-DD)
            date_part = start_raw[:10]
            if len(date_part) == 10 and date_part[4] == '-' and date_part[7] == '-':
                dates.add(date_part)
                continue
        
        # Fallback to start dict
        start = event.get("start", {})
        if "date" in start:
            dates.add(start["date"])
        elif "dateTime" in start:
            dt = datetime.fromisoformat(start["dateTime"].replace('Z', '+00:00'))
            dates.add(dt.strftime("%Y-%m-%d"))
    
    # Sort dates
    sorted_dates = sorted(dates)
    
    if not sorted_dates:
        return []
    
    # Group consecutive dates into trips
    trips = []
    trip_start = sorted_dates[0]
    trip_end = sorted_dates[0]
    
    for i in range(1, len(sorted_dates)):
        current = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        previous = datetime.strptime(sorted_dates[i-1], "%Y-%m-%d")
        
        if (current - previous).days <= 2:  # Within 2 days = same trip
            trip_end = sorted_dates[i]
        else:
            trips.append({
                "start": trip_start,
                "end": trip_end,
                "dates": get_date_range(trip_start, trip_end)
            })
            trip_start = sorted_dates[i]
            trip_end = sorted_dates[i]
    
    # Add last trip
    trips.append({
        "start": trip_start,
        "end": trip_end,
        "dates": get_date_range(trip_start, trip_end)
    })
    
    return trips

def get_date_range(start, end):
    """Get all dates in a range"""
    dates = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    
    while current <= end_dt:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates

def has_reservation(date, reservations_data):
    """Check if we already have a reservation for this date. Returns the reservation dict or None."""
    for res in reservations_data.get("reservations", []):
        if res.get("date") == date:
            return res
    return None

def find_best_slot(slots, min_hour=17, max_hour=22, preferred_hour=19, preferred_minute=45):
    """Find best slot after 5pm (17:00), preferring 7:45pm (19:45)
    
    Args:
        slots: List of available slots from Resy API
        min_hour: Minimum hour (default 17 = 5pm)
        max_hour: Maximum hour (default 22 = 10pm)
        preferred_hour: Preferred hour (default 19 = 7pm)
        preferred_minute: Preferred minute (default 45)
    """
    best_slot = None
    best_time = None
    best_distance = None
    
    for slot in slots:
        time_str = slot.get("date", {}).get("start", "")
        if not time_str:
            continue
        
        # Parse time (format: "2026-04-15 19:30:00")
        try:
            time_parts = time_str.split()[1].split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Skip if outside acceptable range (5pm - 10pm)
            if hour < min_hour or hour > max_hour:
                continue
            # Skip if exactly at 10pm or later
            if hour == max_hour and minute > 0:
                continue
                
            # Calculate distance from preferred time (7:45pm)
            slot_minutes = hour * 60 + minute
            preferred_minutes = preferred_hour * 60 + preferred_minute
            distance = abs(slot_minutes - preferred_minutes)
            
            # Prefer slots closest to 7:45pm
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_time = time_str
                best_slot = slot
        except:
            continue
    
    return best_slot

def mark_restaurant_booked(restaurant_id):
    """Mark restaurant as booked (move to bottom of list)"""
    restaurants_data = load_restaurants()
    restaurants = restaurants_data.get("restaurants", [])
    
    for r in restaurants:
        if r["id"] == restaurant_id:
            r["last_booked"] = datetime.now().isoformat()
            r["priority"] = len(restaurants) + 100
            break
    
    # Reorder
    restaurants.sort(key=lambda x: x["priority"])
    for i, r in enumerate(restaurants):
        r["priority"] = i + 1
    
    with open(RESTAURANTS_FILE, 'w') as f:
        json.dump(restaurants_data, f, indent=2)

def scan_and_book():
    """Main scanning and booking function"""
    print("🔍 Resy Calendar Scanner")
    print("=" * 60)
    print(f"⏰ Woke up at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📅 Checking calendar for NYC trips and reservation status...")
    print()
    
    # Log the wake-up event
    log_reservation_attempt(
        trip_date=datetime.now().strftime('%Y-%m-%d'),
        restaurant_name="SYSTEM",
        venue_id="",
        party_size=0,
        status="wake_up",
        details="Scanner woke up and started processing"
    )

    # Tracking variables for monitoring
    scan_stats = {
        "trip_dates": [],
        "restaurants_checked": 0,
        "reservations_found": 0,
        "reservations_attempted": 0,
        "reservations_made": 0
    }

    # Load scan state
    scan_state = load_scan_state()
    now = datetime.now()

    # Check if we already scanned recently (within 6 hours)
    if scan_state.get("last_scan"):
        last_scan = datetime.fromisoformat(scan_state["last_scan"])
        hours_since_scan = (now - last_scan).total_seconds() / 3600

        if hours_since_scan < 6:
            print(f"⚠️  Scanned {hours_since_scan:.1f} hours ago. Skipping to avoid duplicates.")
            print("   (Minimum interval: 6 hours)")
            log_scan([], 0, 0, 0, 0, f"Skipped - scanned {hours_since_scan:.1f}h ago")
            return

    # Update scan state
    scan_state["last_scan"] = now.isoformat()
    save_scan_state(scan_state)

    # Parse calendar for NYC trips using flight-aware detection
    print("📅 Scanning calendar for NYC trips...")
    nyc_events = parse_calendar_events()
    
    # Use flight-based trip detection for better accuracy
    trips = extract_trips_from_flights(nyc_events)
    
    # Filter out trips with no dates
    trips = [t for t in trips if t.get("dates")]

    if not trips:
        print("✅ No upcoming NYC trips found.")
        log_scan([], 0, 0, 0, 0, "No upcoming trips found")
        return

    print(f"✅ Found {len(trips)} NYC trip(s):")
    for trip in trips:
        print(f"   {trip['start']} to {trip['end']} ({len(trip.get('dates', []))} days)")
        scan_stats["trip_dates"].extend(trip.get('dates', []))
    print()

    # Sync reservations from both Resy API and Google Calendar
    print("🔄 Syncing reservations from Resy API...")
    sync_resy_reservations()
    print()
    
    print("🔄 Syncing reservations from Google Calendar...")
    sync_calendar_reservations()
    print()
    
    # Load restaurants and reservations (after sync)
    restaurants_data = load_restaurants()
    reservations_data = load_reservations()

    nyc_restaurants = [r for r in restaurants_data.get("restaurants", [])
                      if r.get("city", "NYC") == "NYC"]

    if not nyc_restaurants:
        print("⚠️  No NYC restaurants in your list. Add some via the web interface.")
        log_error('scanner', 'no_restaurants', 'No NYC restaurants in list',
                  {'trip_dates': scan_stats['trip_dates']})
        log_scan(scan_stats['trip_dates'], 0, 0, 0, 0, "No restaurants in list")
        return
        return
    
    print(f"🍽️  {len(nyc_restaurants)} restaurant(s) in your NYC list")
    print()
    
    # Get payment method
    payment_id = get_payment_method()
    if not payment_id:
        print("⚠️  No payment method found. Some restaurants may require it.")
    
    # Check each trip date
    bookings_made = []

    for trip in trips:
        for date in trip["dates"]:
            # Skip if already has reservation
            existing_res = has_reservation(date, reservations_data)
            if existing_res:
                res_name = existing_res.get("venue_name", existing_res.get("restaurant_name", "Unknown"))
                print(f"✅ {date}: Already have a reservation at {res_name}")
                log_reservation_attempt(
                    trip_date=date,
                    restaurant_name=res_name,
                    venue_id=existing_res.get("venue_id", ""),
                    party_size=existing_res.get("party_size", 2),
                    status="skipped",
                    details=f"Skipped - already have reservation at {res_name}"
                )
                continue

            print(f"🔍 {date}: Looking for reservations...")

            # Try restaurants in priority order
            booked = False
            restaurants_to_check = sorted(nyc_restaurants, key=lambda x: x["priority"])
            
            for i, restaurant in enumerate(restaurants_to_check):
                if booked:
                    break
                
                # Add random delay between attempts (except first one)
                if i > 0:
                    delay = random.randint(33, 105)
                    print(f"   ⏱️  Waiting {delay}s before next check...")
                    time.sleep(delay)

                venue_id = restaurant["venue_id"]
                restaurant_name = restaurant["name"]
                print(f"   Checking {restaurant_name}...", end=" ")
                scan_stats["restaurants_checked"] += 1

                # Log that we're checking this restaurant
                log_reservation_attempt(
                    trip_date=date,
                    restaurant_name=restaurant_name,
                    venue_id=venue_id,
                    party_size=2,
                    status="checked",
                    details=f"Checking availability for {date}"
                )

                # Find available slots
                results, api_status = find_resy_reservations(venue_id, date, 2, restaurant_name)  # Default party of 2

                # Handle API errors separately from no availability
                if api_status == 'api_error':
                    print("❌ API error")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="api_error",
                        details="Resy API returned an error (HTTP 400/500 or network issue)"
                    )
                    continue
                
                if api_status == 'circuit_open':
                    print("⚠️  Circuit open (temporarily skipped)")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="skipped",
                        details="Circuit breaker - venue temporarily disabled due to repeated errors"
                    )
                    continue

                if api_status == 'no_availability' or not results:
                    print("❌ No availability")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="no_availability",
                        details="Restaurant has no tables available for this date"
                    )
                    continue

                venues = results.get("results", {}).get("venues", [])
                if not venues:
                    print("❌ No venues returned")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="no_availability",
                        details="API returned empty venue list"
                    )
                    continue
                slots = venues[0].get("slots", [])

                if not slots:
                    print("❌ No slots")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="no_availability",
                        details="No slots available for this date"
                    )
                    continue

                scan_stats["reservations_found"] += len(slots)

                # Find best slot after 5pm
                best_slot = find_best_slot(slots, min_hour=17)

                if not best_slot:
                    print("❌ No slots after 5pm")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="no_availability",
                        details=f"Found {len(slots)} slots but none after 5pm",
                        slots_found=len(slots)
                    )
                    continue

                time_str = best_slot["date"]["start"]
                slot_time = time_str.split()[1]
                print(f"✅ Found slot at {slot_time}")
                scan_stats["reservations_attempted"] += 1

                # Log that we found slots
                log_reservation_attempt(
                    trip_date=date,
                    restaurant_name=restaurant_name,
                    venue_id=venue_id,
                    party_size=2,
                    status="attempted",
                    details=f"Found {len(slots)} slots, best is {slot_time}",
                    slots_found=len(slots)
                )

                # Book it
                config_id = best_slot["config"]["token"]
                booking_result = book_reservation(config_id, payment_id)

                if booking_result:
                    # Save reservation
                    new_reservation = {
                        "id": len(reservations_data["reservations"]) + 1,
                        "restaurant_name": restaurant_name,
                        "venue_id": venue_id,
                        "date": date,
                        "time": slot_time,
                        "party_size": 2,
                        "confirmation_code": booking_result.get("reservation_id", ""),
                        "created_at": datetime.now().isoformat()
                    }
                    reservations_data["reservations"].append(new_reservation)
                    save_reservations(reservations_data)

                    # Mark restaurant as booked
                    mark_restaurant_booked(restaurant["id"])

                    bookings_made.append(new_reservation)
                    booked = True
                    scan_stats["reservations_made"] += 1
                    print(f"   🎉 BOOKED: {restaurant_name} at {slot_time}")

                    # Log the successful booking
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="success",
                        details=f"Successfully booked at {slot_time}",
                        slots_found=len(slots)
                    )
                    log_booking(date, restaurant_name, venue_id, 2,
                               slot_time, booking_result.get("reservation_id", ""))
                else:
                    print("   ❌ Booking failed")
                    log_reservation_attempt(
                        trip_date=date,
                        restaurant_name=restaurant_name,
                        venue_id=venue_id,
                        party_size=2,
                        status="failed",
                        details=f"Found slot at {slot_time} but booking API failed",
                        slots_found=len(slots),
                        error_message="Booking API returned error or no confirmation"
                    )

            if not booked:
                print(f"   ⚠️  Could not book any restaurant for {date}")

        print()

    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    if bookings_made:
        print(f"✅ Made {len(bookings_made)} reservation(s):")
        for booking in bookings_made:
            print(f"   📍 {booking['restaurant_name']} - {booking['date']} at {booking['time']}")
    else:
        print("ℹ️  No new reservations needed or available.")

    print()
    print("💡 View all reservations at: http://localhost:5000")

    # Log the scan
    log_scan(
        trip_dates=scan_stats["trip_dates"],
        restaurants_checked=scan_stats["restaurants_checked"],
        reservations_found=scan_stats["reservations_found"],
        reservations_attempted=scan_stats["reservations_attempted"],
        reservations_made=scan_stats["reservations_made"],
        details=f"Scanned {len(trips)} trip(s), made {scan_stats['reservations_made']} booking(s)"
    )
    
    # Log completion
    log_reservation_attempt(
        trip_date=datetime.now().strftime('%Y-%m-%d'),
        restaurant_name="SYSTEM",
        venue_id="",
        party_size=0,
        status="complete",
        details=f"Scan complete. Checked {scan_stats['restaurants_checked']} restaurants, made {scan_stats['reservations_made']} bookings."
    )
    
    print(f"\n🏁 Scan complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    scan_and_book()
