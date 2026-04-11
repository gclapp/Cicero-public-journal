#!/usr/bin/env python3
"""
Trip detection and management for Resy automation
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# Data files
DATA_DIR = Path(__file__).parent / "data"
RESERVATIONS_FILE = DATA_DIR / "reservations.json"
TRIPS_CACHE_FILE = DATA_DIR / "trips_cache.json"
SKIPPED_DATES_FILE = DATA_DIR / "skipped_dates.json"

def load_reservations():
    """Load existing reservations"""
    if not RESERVATIONS_FILE.exists():
        return {"reservations": []}
    with open(RESERVATIONS_FILE) as f:
        return json.load(f)

def load_trips_cache():
    """Load cached trips"""
    if not TRIPS_CACHE_FILE.exists():
        return {"trips": [], "last_updated": None}
    with open(TRIPS_CACHE_FILE) as f:
        return json.load(f)

def save_trips_cache(data):
    """Save trips cache"""
    with open(TRIPS_CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_skipped_dates():
    """Load list of dates to skip"""
    if not SKIPPED_DATES_FILE.exists():
        return {"skipped": []}
    with open(SKIPPED_DATES_FILE) as f:
        return json.load(f)

def save_skipped_dates(data):
    """Save skipped dates"""
    with open(SKIPPED_DATES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def skip_date(date_str, reason=""):
    """Add a date to the skip list"""
    data = load_skipped_dates()
    if date_str not in [s["date"] for s in data["skipped"]]:
        data["skipped"].append({
            "date": date_str,
            "reason": reason,
            "skipped_at": datetime.now().isoformat()
        })
        save_skipped_dates(data)
        return True
    return False

def unskip_date(date_str):
    """Remove a date from the skip list"""
    data = load_skipped_dates()
    data["skipped"] = [s for s in data["skipped"] if s["date"] != date_str]
    save_skipped_dates(data)

def is_date_skipped(date_str):
    """Check if a date is in the skip list"""
    data = load_skipped_dates()
    return any(s["date"] == date_str for s in data["skipped"])

def parse_calendar_events():
    """Parse calendar events to find NYC trips"""
    calendar_cache = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
    
    if not calendar_cache.exists():
        return []
    
    with open(calendar_cache) as f:
        data = json.load(f)
    
    events = data.get("events", [])
    
    # Find NYC trips
    nyc_indicators = ['nyc', 'new york', 'manhattan', 'brooklyn', 'jfk', 'lga', 'newark', 'progyny hq', 'nike hq']
    
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
        # Use start_raw if available (ISO format), otherwise parse start
        start_raw = event.get("start_raw", "")
        if start_raw:
            # Extract just the date part
            date_str = start_raw[:10]
            dates.add(date_str)
        else:
            start = event.get("start", {})
            if isinstance(start, dict):
                if "date" in start:
                    dates.add(start["date"])
                elif "dateTime" in start:
                    dt = datetime.fromisoformat(start["dateTime"].replace('Z', '+00:00'))
                    dates.add(dt.strftime("%Y-%m-%d"))
    
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
        
        if (current - previous).days <= 2:
            trip_end = sorted_dates[i]
        else:
            trips.append({
                "start": trip_start,
                "end": trip_end,
                "dates": get_date_range(trip_start, trip_end)
            })
            trip_start = sorted_dates[i]
            trip_end = sorted_dates[i]
    
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

def has_reservation_for_date(date, reservations_data):
    """Check if there's a reservation for a specific date"""
    for res in reservations_data.get("reservations", []):
        if res.get("date") == date:
            return res
    return None

def get_upcoming_trips(days_ahead=60):
    """Get upcoming trips with reservation status"""
    # Parse calendar for trips
    events = parse_calendar_events()
    trips = extract_trip_dates(events)
    
    # Load reservations and skipped dates
    reservations_data = load_reservations()
    skipped_data = load_skipped_dates()
    skipped_dates = {s["date"] for s in skipped_data["skipped"]}
    
    # Filter to upcoming trips
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = []
    
    for trip in trips:
        # Skip past trips
        if trip["end"] < today:
            continue
        
        # Check reservation status for each night
        nights = []
        for date in trip["dates"]:
            # Skip the departure day (usually don't need dinner)
            if date == trip["end"] and len(trip["dates"]) > 1:
                continue
            
            # Check if this date is skipped
            is_skipped = date in skipped_dates
            skip_info = next((s for s in skipped_data["skipped"] if s["date"] == date), None)
            
            reservation = has_reservation_for_date(date, reservations_data)
            nights.append({
                "date": date,
                "has_reservation": reservation is not None,
                "reservation": reservation,
                "is_skipped": is_skipped,
                "skip_reason": skip_info["reason"] if skip_info else "",
                "needs_booking": reservation is None and date >= today and not is_skipped
            })
        
        # Count nights that actually need booking (not skipped)
        nights_needing_booking = [n for n in nights if not n["is_skipped"]]
        
        trip_info = {
            "id": f"{trip['start']}_{trip['end']}",
            "start": trip["start"],
            "end": trip["end"],
            "nights": nights,
            "total_nights": len(nights),
            "booked_nights": sum(1 for n in nights if n["has_reservation"]),
            "skipped_nights": sum(1 for n in nights if n["is_skipped"]),
            "pending_nights": sum(1 for n in nights if n["needs_booking"]),
            "status": "complete" if all(n["has_reservation"] or n["is_skipped"] for n in nights) else "pending"
        }
        
        upcoming.append(trip_info)
    
    # Sort by start date
    upcoming.sort(key=lambda x: x["start"])
    
    # Cache the results
    cache_data = {
        "trips": upcoming,
        "last_updated": datetime.now().isoformat()
    }
    save_trips_cache(cache_data)
    
    return upcoming

def get_trips_from_cache():
    """Get trips from cache (for web UI)"""
    cache = load_trips_cache()
    return cache.get("trips", [])

def get_skipped_dates_list():
    """Get list of skipped dates with details"""
    return load_skipped_dates().get("skipped", [])

if __name__ == "__main__":
    trips = get_upcoming_trips()
    print(f"Found {len(trips)} upcoming trip(s):")
    for trip in trips:
        print(f"\n📅 {trip['start']} to {trip['end']}")
        print(f"   Status: {trip['status']}")
        print(f"   Nights: {trip['booked_nights']}/{trip['total_nights']} booked")
        for night in trip["nights"]:
            status = "✅" if night["has_reservation"] else "⏳"
            print(f"   {status} {night['date']}")
