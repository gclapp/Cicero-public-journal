#!/usr/bin/env python3
"""Test scan for May trip"""

import sys
sys.path.insert(0, '.')

from calendar_scanner import (
    parse_calendar_events, extract_trips_from_flights,
    sync_resy_reservations, load_restaurants, load_reservations,
    has_reservation, find_resy_reservations, get_payment_method,
    log_reservation_attempt
)
from datetime import datetime
import random
import time

print("=" * 60)
print("Manual Scan Test - May 2026 Trip")
print("=" * 60)

# Parse calendar
events = parse_calendar_events()
print(f"Found {len(events)} NYC events")

# Extract trips
trips = extract_trips_from_flights(events)
print(f"Found {len(trips)} trips")

# Find May trip
may_trip = None
for trip in trips:
    if trip['start'].startswith('2026-05'):
        may_trip = trip
        break

if not may_trip:
    print("No May trip found!")
    sys.exit(1)

print(f"\nMay Trip: {may_trip['start']} to {may_trip['end']}")
print(f"Dates: {may_trip.get('dates', [])}")

# Sync reservations
print("\nSyncing Resy reservations...")
sync_resy_reservations()

# Load data
restaurants_data = load_restaurants()
restaurants = restaurants_data.get("restaurants", [])
print(f"\nLoaded {len(restaurants)} restaurants")

reservations_data = load_reservations()
print(f"Loaded {len(reservations_data.get('reservations', []))} reservations")

# Filter to NYC
nyc_restaurants = [r for r in restaurants if r.get("city", "NYC") == "NYC"]
print(f"NYC restaurants: {len(nyc_restaurants)}")

# Sort by priority
nyc_restaurants.sort(key=lambda x: x.get("priority", 999))

# Check each date
for date in may_trip.get('dates', []):
    print(f"\n{'='*60}")
    print(f"Date: {date}")
    print(f"{'='*60}")
    
    # Check if already has reservation
    existing = has_reservation(date, reservations_data)
    if existing:
        print(f"  Already have reservation at {existing.get('venue_name', 'Unknown')}")
        continue
    
    print(f"  Looking for reservations...")
    
    # Try each restaurant
    for i, restaurant in enumerate(nyc_restaurants[:5]):  # Top 5 only for test
        name = restaurant['name']
        venue_id = restaurant['venue_id']
        
        print(f"  Checking {name}...", end=" ", flush=True)
        
        # Log attempt
        log_reservation_attempt(
            trip_date=date,
            restaurant_name=name,
            venue_id=venue_id,
            party_size=2,
            status="checked",
            details=f"Checking availability for {date}"
        )
        
        # Check availability
        results, status = find_resy_reservations(venue_id, date, 2, name)
        
        if status == 'api_error':
            print("API error")
            continue
        elif status == 'circuit_open':
            print("Circuit open")
            continue
        elif not results or status == 'no_availability':
            print("No availability")
            continue
        
        # Handle both v3 (list) and v4 (dict) response formats
        results_data = results.get("results", [])
        if isinstance(results_data, dict):
            venues = results_data.get("venues", [])
        else:
            venues = results_data  # v3 returns list directly
        if not venues:
            print("No venues")
            continue
            
        slots = venues[0].get("slots", [])
        if not slots:
            print("No slots")
            continue
        
        print(f"Found {len(slots)} slots!")
        
        # Show first few slots
        for slot in slots[:3]:
            time_str = slot.get("date", {}).get("start", "")
            print(f"    - {time_str}")
        
        # Add delay between checks
        if i < len(nyc_restaurants[:5]) - 1:
            delay = random.randint(5, 15)
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

print("\n" + "=" * 60)
print("Scan complete!")
