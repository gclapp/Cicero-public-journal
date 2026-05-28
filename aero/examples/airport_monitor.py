#!/usr/bin/env python3
"""
Airport Monitor Example

Monitor arrivals and departures at a specific airport.
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from aero import AeroTracker, FlightAwareError


def format_time(dt):
    """Format datetime for display."""
    if not dt:
        return "N/A"
    return dt.strftime("%H:%M")


def format_delay(flight):
    """Format delay information."""
    if flight.is_delayed:
        return f" (+{flight.delay_minutes}m)"
    return ""


def display_flight(flight, is_arrival=True):
    """Display a flight in a formatted way."""
    direction = "From" if is_arrival else "To"
    other_airport = flight.origin_code if is_arrival else flight.destination_code
    other_name = flight.origin_name if is_arrival else flight.destination_name
    
    scheduled = flight.scheduled_arrival if is_arrival else flight.scheduled_departure
    estimated = flight.estimated_arrival if is_arrival else flight.estimated_departure
    actual = flight.actual_arrival if is_arrival else flight.actual_departure
    
    status_icon = {
        'scheduled': '📅',
        'active': '✈️',
        'landed': '✅',
        'arrived': '✅',
        'delayed': '⏰',
        'cancelled': '❌',
        'diverted': '↪️'
    }.get(flight.status.lower(), '❓')
    
    print(f"  {status_icon} {flight.flight_number:8} {direction}: {other_airport:4} ({other_name[:20]})")
    
    time_str = format_time(scheduled)
    if estimated and estimated != scheduled:
        time_str += f" → {format_time(estimated)}"
    if actual:
        time_str = format_time(actual)
    
    delay_str = format_delay(flight)
    
    print(f"     Time: {time_str}{delay_str} | Status: {flight.status.upper()}")
    
    if flight.gate:
        print(f"     Gate: {flight.gate}", end="")
        if flight.terminal:
            print(f" | Terminal: {flight.terminal}", end="")
        print()
    
    if flight.aircraft_type:
        print(f"     Aircraft: {flight.aircraft_type}")
    
    print()


def monitor_airport(airport_code: str, hours: int = 2):
    """
    Monitor an airport's arrivals and departures.
    
    Args:
        airport_code: ICAO airport code (e.g., KJFK, KLAX)
        hours: Hours to look ahead
    """
    print("=" * 70)
    print(f"Airport Monitor: {airport_code}")
    print("=" * 70)
    print()
    
    try:
        with AeroTracker() as tracker:
            # Get airport info
            try:
                airport_info = tracker.client.get_airport_info(airport_code)
                print(f"📍 {airport_info.get('name', 'Unknown Airport')}")
                print(f"   Code: {airport_code}")
                if airport_info.get('city'):
                    print(f"   Location: {airport_info.get('city')}, {airport_info.get('state') or airport_info.get('country')}")
                print()
            except FlightAwareError:
                print(f"📍 Airport: {airport_code}")
                print()
            
            # Get arrivals
            print("-" * 70)
            print(f"🛬 ARRIVALS (Next {hours} hours)")
            print("-" * 70)
            print()
            
            try:
                arrivals = tracker.get_airport_arrivals(
                    airport_code,
                    hours_ahead=hours,
                    hours_behind=0
                )
                
                if arrivals:
                    # Sort by scheduled arrival time
                    arrivals.sort(key=lambda f: f.scheduled_arrival or f.estimated_arrival)
                    
                    for flight in arrivals[:20]:  # Limit to 20
                        display_flight(flight, is_arrival=True)
                    
                    if len(arrivals) > 20:
                        print(f"  ... and {len(arrivals) - 20} more arrivals")
                else:
                    print("  No arrivals found in this time window.")
                    print()
                    
            except FlightAwareError as e:
                print(f"  Could not retrieve arrivals: {e}")
                print()
            
            # Get departures
            print("-" * 70)
            print(f"🛫 DEPARTURES (Next {hours} hours)")
            print("-" * 70)
            print()
            
            try:
                departures = tracker.get_airport_departures(
                    airport_code,
                    hours_ahead=hours,
                    hours_behind=0
                )
                
                if departures:
                    # Sort by scheduled departure time
                    departures.sort(key=lambda f: f.scheduled_departure or f.estimated_departure)
                    
                    for flight in departures[:20]:  # Limit to 20
                        display_flight(flight, is_arrival=False)
                    
                    if len(departures) > 20:
                        print(f"  ... and {len(departures) - 20} more departures")
                else:
                    print("  No departures found in this time window.")
                    print()
                    
            except FlightAwareError as e:
                print(f"  Could not retrieve departures: {e}")
                print()
    
    except FlightAwareError as e:
        print(f"❌ API Error: {e}")
        print()
        print("Make sure your AEROAPI_KEY is configured correctly.")
        return 1
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("=" * 70)
    print("Monitor completed!")
    print("=" * 70)
    return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor airport arrivals and departures'
    )
    parser.add_argument(
        'airport',
        help='Airport ICAO code (e.g., KJFK, KLAX, EGLL)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=2,
        help='Hours to look ahead (default: 2)'
    )
    
    args = parser.parse_args()
    
    return monitor_airport(args.airport.upper(), args.hours)


if __name__ == "__main__":
    sys.exit(main())
