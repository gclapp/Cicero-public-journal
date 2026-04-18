#!/usr/bin/env python3
"""
Trip detection and management for Resy automation
"""

import json
import re
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
    
    return data.get("events", [])

def is_outbound_flight_to_nyc(event):
    """Check if this is an outbound flight TO NYC"""
    summary = event.get("summary", "").lower()
    description = event.get("description", "").lower()
    location = event.get("location", "").lower()
    
    text = f"{summary} {description} {location}"
    
    # Must be a flight (check various indicators)
    flight_indicators = ["flight", "air lines", "airlines", "delta", "american airlines", "united", "jetblue"]
    is_flight = any(ind in text for ind in flight_indicators)
    if not is_flight:
        return False
    
    # NYC destination indicators
    nyc_destinations = ["jfk", "lga", "newark", "kennedy", "laguardia", 
                       "to new york", "to nyc", "new york (", "nyc (", "to kennedy"]
    
    # Check if destination is NYC
    for indicator in nyc_destinations:
        if indicator in text:
            return True
    
    # Check if departing from LAX/Los Angeles and going to NYC area
    if any(x in location for x in ["lax", "los angeles", "lax ("]):
        if any(x in text for x in ["new york", "nyc", "jfk", "lga", "kennedy"]):
            return True
    
    return False

def is_return_flight_from_nyc(event):
    """Check if this is a return flight FROM NYC"""
    summary = event.get("summary", "").lower()
    description = event.get("description", "").lower()
    location = event.get("location", "").lower()
    
    text = f"{summary} {description} {location}"
    
    # Must be a flight (check various indicators)
    flight_indicators = ["flight", "air lines", "airlines", "delta", "american airlines", "united", "jetblue"]
    is_flight = any(ind in text for ind in flight_indicators)
    if not is_flight:
        return False
    
    # NYC origin indicators
    nyc_origins = ["jfk", "lga", "newark", "kennedy", "laguardia",
                  "new york(jfk)", "new york (jfk)", "from new york", "from nyc",
                  "new york(jfk)", "new york (jfk) -"]
    
    # Check if origin is NYC
    for indicator in nyc_origins:
        if indicator in text:
            return True
    
    # Check if going TO LAX/Los Angeles FROM NYC area
    lax_patterns = ["to lax", "to los angeles", "- los angeles", "to los angeles(lax)", "(lax)"]
    going_to_la = any(x in text for x in lax_patterns)
    coming_from_nyc = any(x in text for x in ["jfk", "lga", "newark", "new york", "nyc"])
    
    if going_to_la and coming_from_nyc:
        return True
    
    return False

def is_hotel_reservation(event):
    """Check if this is a hotel reservation"""
    summary = event.get("summary", "").lower()
    
    hotel_indicators = ["stay at", "hotel", "resort", "inn", "marriott", 
                       "hilton", "hyatt", "four seasons", "ritz-carlton",
                       "algonquin", "ace hotel", "nomad", "standard"]
    
    for indicator in hotel_indicators:
        if indicator in summary:
            return True
    
    return False

def get_event_date(event):
    """Extract date from event"""
    start_raw = event.get("start_raw", "")
    if start_raw:
        return start_raw[:10]
    
    start = event.get("start", {})
    if isinstance(start, dict):
        if "date" in start:
            return start["date"]
        elif "dateTime" in start:
            dt = datetime.fromisoformat(start["dateTime"].replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
    
    return None

def get_event_datetime(event):
    """Extract datetime from event"""
    start_raw = event.get("start_raw", "")
    if start_raw:
        try:
            dt = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            # Make offset-naive for consistent comparison
            return dt.replace(tzinfo=None)
        except:
            pass
    
    start = event.get("start", {})
    if isinstance(start, dict) and "dateTime" in start:
        try:
            dt = datetime.fromisoformat(start["dateTime"].replace('Z', '+00:00'))
            # Make offset-naive for consistent comparison
            return dt.replace(tzinfo=None)
        except:
            pass
    
    return None

def extract_trip_from_flights(events):
    """Extract complete trips by matching outbound and return flights"""
    
    # First, classify all flights - a flight can only be one type
    outbound_flights = []
    return_flights = []
    seen_flight_dates = set()
    
    for event in events:
        dt = get_event_datetime(event)
        date = get_event_date(event)
        if not dt or not date:
            continue
            
        is_outbound = is_outbound_flight_to_nyc(event)
        is_return = is_return_flight_from_nyc(event)
        
        # Skip if not a flight
        if not is_outbound and not is_return:
            continue
        
        # Deduplicate: only keep one flight per date
        if date in seen_flight_dates:
            continue
        seen_flight_dates.add(date)
        
        # If flight matches both, determine by direction
        # Priority: if it has "New York(JFK) - Los Angeles" pattern, it's return
        # If it has "Los Angeles - New York" pattern, it's outbound
        if is_outbound and is_return:
            summary = event.get("summary", "").lower()
            description = event.get("description", "").lower()
            location = event.get("location", "").lower()
            text = f"{summary} {description} {location}"
            
            # Check for explicit patterns
            if "new york" in text and ("- los angeles" in text or "to los angeles" in text):
                is_outbound = False  # It's actually a return
            elif "los angeles" in text and ("- new york" in text or "to new york" in text or "to kennedy" in text or "to jfk" in text):
                is_return = False  # It's actually outbound
            elif "lax" in text and ("- jfk" in text or "- new york" in text):
                is_return = False  # It's outbound
            elif "jfk" in text and ("- lax" in text or "- los angeles" in text):
                is_outbound = False  # It's return
        
        if is_return:
            return_flights.append({
                "event": event,
                "datetime": dt,
                "date": date,
                "summary": event.get("summary", "")
            })
        elif is_outbound:
            outbound_flights.append({
                "event": event,
                "datetime": dt,
                "date": date,
                "summary": event.get("summary", "")
            })
    
    # Find all hotel reservations in NYC
    hotels = []
    nyc_indicators = ['nyc', 'new york', 'manhattan', 'brooklyn', 'jfk', 'lga']
    for event in events:
        if is_hotel_reservation(event):
            location = event.get("location", "").lower()
            summary = event.get("summary", "").lower()
            text = f"{summary} {location}"
            
            # Only include NYC hotels
            if any(ind in text for ind in nyc_indicators):
                dt = get_event_datetime(event)
                hotels.append({
                    "event": event,
                    "datetime": dt,
                    "date": get_event_date(event),
                    "name": event.get("summary", "").replace("Stay at ", ""),
                    "location": location
                })
    
    # Match outbound flights with return flights
    trips = []
    
    for outbound in outbound_flights:
        outbound_date = outbound["date"]
        outbound_dt = outbound["datetime"]
        
        # Find the best matching return flight (after outbound, within 14 days)
        best_return = None
        min_return_date = None
        
        for ret in return_flights:
            ret_date = ret["date"]
            ret_dt = ret["datetime"]
            
            # Return must be after outbound
            if ret_dt <= outbound_dt:
                continue
            
            # Return should be within 14 days (typical business trip)
            days_diff = (ret_dt - outbound_dt).days
            if days_diff > 14:
                continue
            
            # Use the earliest return that matches
            if min_return_date is None or ret_date < min_return_date:
                min_return_date = ret_date
                best_return = ret
        
        # Calculate trip dates
        if best_return:
            # Trip starts the day after arrival (next day after outbound flight)
            arrival_date = (outbound_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            # Trip ends the day before departure (or day of if morning flight)
            return_dt = best_return["datetime"]
            return_hour = return_dt.hour + (return_dt.minute / 60)
            
            # Return day is always excluded - you're flying back to LA
            # Last night for dinner is always the day before departure
            last_night = (return_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            
            trip_dates = get_date_range(arrival_date, last_night)
            
            # Find associated hotel
            associated_hotel = None
            for hotel in hotels:
                hotel_date = hotel["date"]
                # Hotel check-in should be during trip
                if arrival_date <= hotel_date <= last_night:
                    associated_hotel = hotel
                    break
            
            trips.append({
                "start": arrival_date,
                "end": last_night,
                "dates": trip_dates,
                "outbound_flight": outbound["summary"],
                "outbound_date": outbound_date,
                "return_flight": best_return["summary"],
                "return_date": best_return["date"],
                "hotel": associated_hotel["name"] if associated_hotel else None,
                "hotel_location": associated_hotel["location"] if associated_hotel else None,
                "source": "flight_matched"
            })
        else:
            # No return flight found - use fallback logic
            # Check for hotel to determine length
            trip_end = None
            for hotel in hotels:
                hotel_date = hotel["date"]
                # Hotel must be after outbound
                if hotel_date > outbound_date:
                    # Assume 2-3 night trip if hotel found
                    trip_end = (datetime.strptime(hotel_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
                    break
            
            if not trip_end:
                # Default to 2-night trip if no return flight or hotel
                trip_end = (outbound_dt + timedelta(days=3)).strftime("%Y-%m-%d")
            
            arrival_date = (outbound_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            trip_dates = get_date_range(arrival_date, trip_end)
            
            trips.append({
                "start": arrival_date,
                "end": trip_end,
                "dates": trip_dates,
                "outbound_flight": outbound["summary"],
                "outbound_date": outbound_date,
                "return_flight": None,
                "return_date": None,
                "hotel": None,
                "hotel_location": None,
                "source": "outbound_only"
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

def sync_resy_reservations():
    """Sync reservations from Resy API to local database"""
    try:
        # Import here to avoid circular dependency
        from calendar_scanner import sync_resy_reservations as do_sync
        do_sync()
    except Exception as e:
        print(f"Warning: Could not sync Resy reservations: {e}")

def get_upcoming_trips(days_ahead=60):
    """Get upcoming trips with reservation status"""
    # Sync reservations from Resy first
    sync_resy_reservations()
    
    # Parse calendar for trips
    events = parse_calendar_events()
    trips = extract_trip_from_flights(events)
    
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
        
        trip_info = {
            "id": f"{trip['start']}_{trip['end']}",
            "start": trip["start"],
            "end": trip["end"],
            "nights": nights,
            "total_nights": len(nights),
            "booked_nights": sum(1 for n in nights if n["has_reservation"]),
            "skipped_nights": sum(1 for n in nights if n["is_skipped"]),
            "pending_nights": sum(1 for n in nights if n["needs_booking"]),
            "status": "complete" if all(n["has_reservation"] or n["is_skipped"] for n in nights) else "pending",
            "outbound_flight": trip.get("outbound_flight"),
            "return_flight": trip.get("return_flight"),
            "hotel": trip.get("hotel"),
            "source": trip.get("source", "unknown")
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
        print(f"\n📅 {trip['start']} to {trip['end']} ({trip['total_nights']} nights)")
        print(f"   Status: {trip['status']} ({trip['booked_nights']}/{trip['total_nights']} booked)")
        if trip.get('outbound_flight'):
            print(f"   ✈️  Outbound: {trip['outbound_flight']}")
        if trip.get('return_flight'):
            print(f"   ✈️  Return: {trip['return_flight']}")
        if trip.get('hotel'):
            print(f"   🏨 Hotel: {trip['hotel']}")
        for night in trip["nights"]:
            status = "✅" if night["has_reservation"] else ("⏭️" if night["is_skipped"] else "⏳")
            print(f"   {status} {night['date']}")
