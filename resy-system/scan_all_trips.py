#!/usr/bin/env python3
"""Scan all trips (April and May) for reservations"""

import sys
sys.path.insert(0, '.')

from calendar_scanner import (
    parse_calendar_events, extract_trips_from_flights,
    sync_resy_reservations, load_restaurants, load_reservations,
    has_reservation, find_resy_reservations, get_payment_method,
    log_reservation_attempt, log_scan
)
from datetime import datetime
import random
import time

print("=" * 70)
print("NYCeats Scanner - All Trips")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Parse calendar
events = parse_calendar_events()
print(f"\nFound {len(events)} NYC events")

# Extract trips
trips = extract_trips_from_flights(events)
print(f"Found {len(trips)} trip(s):")
for trip in trips:
    print(f"  - {trip['start']} to {trip['end']} ({len(trip.get('dates', []))} nights)")

# Sync reservations
print("\nSyncing Resy reservations...")
sync_resy_reservations()

# Load data
restaurants_data = load_restaurants()
all_restaurants = restaurants_data.get("restaurants", [])
nyc_restaurants = [r for r in all_restaurants if r.get("city", "NYC") == "NYC"]
nyc_restaurants.sort(key=lambda x: x.get("priority", 999))

print(f"\nRestaurants: {len(nyc_restaurants)} in NYC list")
for r in nyc_restaurants:
    print(f"  {r['priority']}. {r['name']}")

reservations_data = load_reservations()
print(f"\nExisting reservations: {len(reservations_data.get('reservations', []))}")

payment_id = get_payment_method()
print(f"Payment method: {'✓' if payment_id else '✗'}")

# Track stats
scan_stats = {
    "trip_dates": [],
    "restaurants_checked": 0,
    "reservations_found": 0,
    "reservations_attempted": 0,
    "reservations_made": 0
}

# Check each trip
for trip in trips:
    print(f"\n{'='*70}")
    print(f"Trip: {trip['start']} to {trip['end']}")
    print(f"{'='*70}")
    
    for date in trip.get('dates', []):
        scan_stats["trip_dates"].append(date)
        
        print(f"\n📅 {date}")
        print("-" * 40)
        
        # Check if already has reservation
        existing = has_reservation(date, reservations_data)
        if existing:
            venue_name = existing.get('venue_name', existing.get('restaurant_name', 'Unknown'))
            print(f"  ✅ Already booked at {venue_name}")
            log_reservation_attempt(
                trip_date=date,
                restaurant_name=venue_name,
                venue_id=existing.get('venue_id', ''),
                party_size=existing.get('party_size', 2),
                status="skipped",
                details=f"Already have reservation at {venue_name}"
            )
            continue
        
        print(f"  🔍 Looking for reservations...")
        
        # Try each restaurant
        booked = False
        for i, restaurant in enumerate(nyc_restaurants):
            if booked:
                break
            
            name = restaurant['name']
            venue_id = restaurant['venue_id']
            
            scan_stats["restaurants_checked"] += 1
            
            # Log attempt
            log_reservation_attempt(
                trip_date=date,
                restaurant_name=name,
                venue_id=venue_id,
                party_size=2,
                status="checked",
                details=f"Checking availability"
            )
            
            # Check availability
            results, status = find_resy_reservations(venue_id, date, 2, name)
            
            if status == 'api_error':
                print(f"  ❌ {name}: API error")
                continue
            elif status == 'circuit_open':
                print(f"  ⚠️  {name}: Circuit open (too many failures)")
                continue
            elif not results or status == 'no_availability':
                print(f"  ❌ {name}: No availability")
                continue
            
            # Handle both v3 (list) and v4 (dict) response formats
            results_data = results.get("results", [])
            if isinstance(results_data, dict):
                venues = results_data.get("venues", [])
            else:
                venues = results_data  # v3 returns list directly
            if not venues:
                print(f"  ❌ {name}: No venues")
                continue
            
            slots = venues[0].get("slots", [])
            if not slots:
                print(f"  ❌ {name}: No slots")
                continue
            
            scan_stats["reservations_found"] += len(slots)
            print(f"  ✅ {name}: Found {len(slots)} slot(s)!")
            
            # Show slots (first 3)
            for slot in slots[:3]:
                time_str = slot.get("date", {}).get("start", "")
                print(f"      - {time_str}")
            
            # Note: Not actually booking - just checking
            print(f"      (Would attempt booking here)")
            
            # Delay between restaurants
            if i < len(nyc_restaurants) - 1:
                delay = random.randint(33, 105)
                print(f"  ⏱️  Waiting {delay}s...")
                time.sleep(delay)

# Log final scan
print(f"\n{'='*70}")
print("Scan Complete")
print(f"{'='*70}")
print(f"Dates checked: {len(scan_stats['trip_dates'])}")
print(f"Restaurants checked: {scan_stats['restaurants_checked']}")
print(f"Reservations found: {scan_stats['reservations_found']}")
print(f"Reservations made: {scan_stats['reservations_made']}")

log_scan(
    scan_stats["trip_dates"],
    scan_stats["restaurants_checked"],
    scan_stats["reservations_found"],
    scan_stats["reservations_attempted"],
    scan_stats["reservations_made"],
    f"Scanned {len(trips)} trip(s), made {scan_stats['reservations_made']} booking(s)"
)
