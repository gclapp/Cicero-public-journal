#!/usr/bin/env python3
"""
Resy Calendar Scanner
Scans Google Calendar for NYC trips and checks for missing reservations
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import monitoring
from monitoring import log_scan, log_booking, log_error

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

def find_resy_reservations(venue_id, day, party_size):
    """Find available reservations at a venue"""
    creds = load_resy_credentials()

    url = f"https://api.resy.com/4/find?day={day}&party_size={party_size}&venue_id={venue_id}"

    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        print(f"  ❌ Error checking venue {venue_id}: {error_msg}")
        log_error('scanner', 'api_error', f"Failed to check availability for venue {venue_id}",
                  {'venue_id': venue_id, 'day': day, 'error': error_msg})
        return None
    except Exception as e:
        print(f"  ❌ Error checking venue {venue_id}: {e}")
        log_error('scanner', 'api_error', f"Failed to check availability for venue {venue_id}",
                  {'venue_id': venue_id, 'day': day, 'error': str(e)})
        return None

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
    """Check if we already have a reservation for this date"""
    for res in reservations_data.get("reservations", []):
        if res.get("date") == date:
            return True
    return False

def find_best_slot(slots, min_hour=17):
    """Find best slot after 5pm (17:00)"""
    best_slot = None
    best_time = None
    
    for slot in slots:
        time_str = slot.get("date", {}).get("start", "")
        if not time_str:
            continue
        
        # Parse time (format: "2026-04-15 19:30:00")
        try:
            hour = int(time_str.split()[1].split(":")[0])
            if hour >= min_hour:
                if best_time is None or time_str < best_time:
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
    print(f"⏰ Scan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📅 Checking every 12 hours for new trips without reservations")
    print()

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

    # Parse calendar for NYC trips
    print("📅 Scanning calendar for NYC trips...")
    nyc_events = parse_calendar_events()
    trips = extract_trip_dates(nyc_events)

    if not trips:
        print("✅ No upcoming NYC trips found.")
        log_scan([], 0, 0, 0, 0, "No upcoming trips found")
        return

    print(f"✅ Found {len(trips)} NYC trip(s):")
    for trip in trips:
        print(f"   {trip['start']} to {trip['end']} ({len(trip['dates'])} days)")
        scan_stats["trip_dates"].extend(trip['dates'])
    print()

    # Load restaurants and reservations
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
            if has_reservation(date, reservations_data):
                print(f"✅ {date}: Already have a reservation")
                continue

            print(f"🔍 {date}: Looking for reservations...")

            # Try restaurants in priority order
            booked = False
            for restaurant in sorted(nyc_restaurants, key=lambda x: x["priority"]):
                if booked:
                    break

                venue_id = restaurant["venue_id"]
                print(f"   Checking {restaurant['name']}...", end=" ")
                scan_stats["restaurants_checked"] += 1

                # Find available slots
                results = find_resy_reservations(venue_id, date, 2)  # Default party of 2

                if not results or "results" not in results:
                    print("❌ No availability")
                    continue

                slots = results["results"].get("venues", [{}])[0].get("slots", [])

                if not slots:
                    print("❌ No slots")
                    continue

                scan_stats["reservations_found"] += len(slots)

                # Find best slot after 5pm
                best_slot = find_best_slot(slots, min_hour=17)

                if not best_slot:
                    print("❌ No slots after 5pm")
                    continue

                time_str = best_slot["date"]["start"]
                print(f"✅ Found slot at {time_str.split()[1]}")
                scan_stats["reservations_attempted"] += 1

                # Book it
                config_id = best_slot["config"]["token"]
                booking_result = book_reservation(config_id, payment_id)

                if booking_result:
                    # Save reservation
                    new_reservation = {
                        "id": len(reservations_data["reservations"]) + 1,
                        "restaurant_name": restaurant["name"],
                        "venue_id": venue_id,
                        "date": date,
                        "time": time_str.split()[1],
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
                    print(f"   🎉 BOOKED: {restaurant['name']} at {time_str.split()[1]}")

                    # Log the booking
                    log_booking(date, restaurant["name"], venue_id, 2,
                               time_str.split()[1], booking_result.get("reservation_id", ""))
                else:
                    print("   ❌ Booking failed")

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

if __name__ == "__main__":
    scan_and_book()
