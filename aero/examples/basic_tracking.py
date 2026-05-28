#!/usr/bin/env python3
"""
Basic Flight Tracking Example

Demonstrates basic usage of the Aero flight tracking system.
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from aero import AeroTracker, FlightAwareError, FlightAwareNotFoundError


def main():
    """Run basic tracking example."""
    print("=" * 60)
    print("Aero Flight Tracking - Basic Example")
    print("=" * 60)
    print()
    
    try:
        with AeroTracker() as tracker:
            # Example: Track a flight (using a sample flight number)
            # In production, use a real flight number
            flight_number = "UA123"  # Example flight
            
            print(f"🔍 Looking up flight {flight_number}...")
            print()
            
            try:
                flight = tracker.track_flight(flight_number)
                
                # Display flight information
                print(f"✈️  Flight Information")
                print(f"   Flight Number: {flight.flight_number}")
                print(f"   Airline: {flight.airline}")
                print(f"   Status: {flight.status.upper()}")
                print()
                
                print(f"🛫 Departure")
                print(f"   Airport: {flight.origin_name} ({flight.origin_code})")
                if flight.scheduled_departure:
                    print(f"   Scheduled: {flight.scheduled_departure}")
                if flight.estimated_departure:
                    print(f"   Estimated: {flight.estimated_departure}")
                if flight.actual_departure:
                    print(f"   Actual: {flight.actual_departure}")
                print()
                
                print(f"🛬 Arrival")
                print(f"   Airport: {flight.destination_name} ({flight.destination_code})")
                if flight.scheduled_arrival:
                    print(f"   Scheduled: {flight.scheduled_arrival}")
                if flight.estimated_arrival:
                    print(f"   Estimated: {flight.estimated_arrival}")
                if flight.actual_arrival:
                    print(f"   Actual: {flight.actual_arrival}")
                print()
                
                # Additional details
                if flight.aircraft_type:
                    print(f"🛩️  Aircraft: {flight.aircraft_type}")
                if flight.gate:
                    print(f"   Gate: {flight.gate}")
                if flight.terminal:
                    print(f"   Terminal: {flight.terminal}")
                if flight.baggage_claim:
                    print(f"   Baggage Claim: {flight.baggage_claim}")
                print()
                
                # Status indicators
                if flight.is_delayed:
                    print(f"⚠️  DELAYED by {flight.delay_minutes} minutes")
                elif flight.is_active:
                    print(f"✈️  IN FLIGHT")
                    if flight.progress_percent:
                        print(f"   Route Progress: {flight.progress_percent}%")
                elif flight.is_completed:
                    print(f"✅ ARRIVED")
                print()
                
                # Try to get position if flight is active
                if flight.is_active and flight.fa_flight_id:
                    print(f"📍 Current Position")
                    position = tracker.get_flight_position(flight_number)
                    if position:
                        print(f"   Latitude: {position['latitude']:.4f}")
                        print(f"   Longitude: {position['longitude']:.4f}")
                        print(f"   Altitude: {position['altitude']:,} ft")
                        print(f"   Ground Speed: {position['ground_speed']} kts")
                        print(f"   Heading: {position['heading']}°")
                    else:
                        print(f"   Position data not available")
                    print()
                
            except FlightAwareNotFoundError:
                print(f"❌ Flight {flight_number} not found.")
                print("   This could mean:")
                print("   - The flight number is incorrect")
                print("   - The flight is not in the FlightAware database")
                print("   - The flight is too far in the future or past")
                return 1
            
            # Example: Get airport arrivals
            print("=" * 60)
            print("Example: Airport Arrivals (JFK)")
            print("=" * 60)
            print()
            
            try:
                arrivals = tracker.get_airport_arrivals("KJFK", hours_ahead=1)
                print(f"Found {len(arrivals)} arrivals in the next hour:")
                print()
                
                for i, flight in enumerate(arrivals[:5], 1):  # Show first 5
                    print(f"{i}. {flight.flight_number}")
                    print(f"   From: {flight.origin_name} ({flight.origin_code})")
                    print(f"   Status: {flight.status}")
                    if flight.scheduled_arrival:
                        print(f"   Arrival: {flight.scheduled_arrival.strftime('%H:%M')}")
                    print()
                    
            except FlightAwareError as e:
                print(f"Could not retrieve arrivals: {e}")
    
    except FlightAwareError as e:
        print(f"❌ API Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check that your AEROAPI_KEY is set correctly")
        print("2. Verify your API key is active in FlightAware portal")
        print("3. Check your internet connection")
        return 1
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
