#!/usr/bin/env python3
"""
Flight Search Example

Search for flights between airports or by flight number.
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from aero import AeroTracker, FlightAwareError


def search_by_route(origin: str, destination: str, date: str = None):
    """Search flights by route."""
    print(f"\n🔍 Searching flights from {origin} to {destination}")
    if date:
        print(f"   Date: {date}")
    print()
    
    try:
        with AeroTracker() as tracker:
            flights = tracker.search_flights(
                origin=origin,
                destination=destination,
                date=date
            )
            
            if not flights:
                print("   No flights found.")
                return
            
            print(f"   Found {len(flights)} flight(s):\n")
            
            for i, flight in enumerate(flights, 1):
                print(f"   {i}. {flight.flight_number}")
                print(f"      Airline: {flight.airline}")
                print(f"      Status: {flight.status}")
                
                if flight.scheduled_departure:
                    print(f"      Departure: {flight.scheduled_departure}")
                if flight.scheduled_arrival:
                    print(f"      Arrival: {flight.scheduled_arrival}")
                if flight.aircraft_type:
                    print(f"      Aircraft: {flight.aircraft_type}")
                
                print()
                
    except FlightAwareError as e:
        print(f"   Error: {e}")


def search_by_number(flight_number: str, date: str = None):
    """Search flight by flight number."""
    print(f"\n🔍 Searching for flight {flight_number}")
    if date:
        print(f"   Date: {date}")
    print()
    
    try:
        with AeroTracker() as tracker:
            flight = tracker.track_flight(flight_number, date=date)
            
            print(f"   ✈️  {flight.flight_number}")
            print(f"      Airline: {flight.airline}")
            print(f"      Status: {flight.status.upper()}")
            print()
            
            print(f"      🛫 {flight.origin_name} ({flight.origin_code})")
            if flight.scheduled_departure:
                print(f"         Scheduled: {flight.scheduled_departure}")
            if flight.estimated_departure and flight.estimated_departure != flight.scheduled_departure:
                print(f"         Estimated: {flight.estimated_departure}")
            if flight.actual_departure:
                print(f"         Actual: {flight.actual_departure}")
            print()
            
            print(f"      🛬 {flight.destination_name} ({flight.destination_code})")
            if flight.scheduled_arrival:
                print(f"         Scheduled: {flight.scheduled_arrival}")
            if flight.estimated_arrival and flight.estimated_arrival != flight.scheduled_arrival:
                print(f"         Estimated: {flight.estimated_arrival}")
            if flight.actual_arrival:
                print(f"         Actual: {flight.actual_arrival}")
            print()
            
            if flight.is_delayed:
                print(f"      ⚠️  Delayed by {flight.delay_minutes} minutes")
            
            if flight.is_active:
                print(f"      ✈️  Currently in flight")
                if flight.progress_percent:
                    print(f"         Progress: {flight.progress_percent}%")
            
            if flight.is_completed:
                print(f"      ✅ Flight completed")
            
            print()
            
            if flight.aircraft_type:
                print(f"      Aircraft: {flight.aircraft_type}")
            if flight.gate:
                print(f"      Gate: {flight.gate}")
            if flight.terminal:
                print(f"      Terminal: {flight.terminal}")
            print()
            
    except FlightAwareError as e:
        print(f"   Error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Search for flights'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Search type')
    
    # Route search
    route_parser = subparsers.add_parser('route', help='Search by route')
    route_parser.add_argument('origin', help='Origin airport code (e.g., KJFK)')
    route_parser.add_argument('destination', help='Destination airport code (e.g., KLAX)')
    route_parser.add_argument('--date', help='Date in YYYY-MM-DD format')
    
    # Flight number search
    flight_parser = subparsers.add_parser('flight', help='Search by flight number')
    flight_parser.add_argument('number', help='Flight number (e.g., UA123)')
    flight_parser.add_argument('--date', help='Date in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    print("=" * 60)
    print("Aero Flight Search")
    print("=" * 60)
    
    try:
        if args.command == 'route':
            search_by_route(
                args.origin.upper(),
                args.destination.upper(),
                args.date
            )
        elif args.command == 'flight':
            search_by_number(args.number.upper(), args.date)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
