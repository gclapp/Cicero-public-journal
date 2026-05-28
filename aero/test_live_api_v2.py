#!/usr/bin/env python3
"""
Live API Test for FlightAware Integration
Tests the Aero system with the actual FlightAware API.
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from aero_tracker import AeroTracker
from flightaware_client import FlightAwareError, FlightAwareNotFoundError, FlightAwareAuthError


def test_api_connection():
    """Test basic API connectivity."""
    print("=" * 60)
    print("Testing FlightAware API Connection")
    print("=" * 60)
    print()
    
    try:
        with AeroTracker() as tracker:
            print("✓ Successfully authenticated with FlightAware API")
            print(f"  Using credentials from: ~/.openclaw/credentials/flightaware.json")
            print()
            
            # Test 1: Get airport info
            print("Test 1: Get Airport Info (KJFK)")
            print("-" * 40)
            try:
                airport_info = tracker.client.get_airport_info("KJFK")
                print(f"✓ Airport: {airport_info.get('name')}")
                print(f"  City: {airport_info.get('city')}")
                print(f"  Timezone: {airport_info.get('timezone')}")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
            print()
            
            # Test 2: Search for flights
            print("Test 2: Search Flights (KJFK → KLAX)")
            print("-" * 40)
            try:
                flights = tracker.search_flights(origin="KJFK", destination="KLAX")
                print(f"✓ Found {len(flights)} flights")
                if flights:
                    for i, flight in enumerate(flights[:3], 1):
                        print(f"  {i}. {flight.flight_number} - {flight.status}")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
            print()
            
            # Test 3: Try to track a common flight
            print("Test 3: Track Flight (AA100)")
            print("-" * 40)
            try:
                flight = tracker.track_flight("AA100")
                print(f"✓ Found flight: {flight.flight_number}")
                print(f"  Airline: {flight.airline}")
                print(f"  Status: {flight.status}")
                print(f"  Route: {flight.origin_code} → {flight.destination_code}")
                if flight.aircraft_type:
                    print(f"  Aircraft: {flight.aircraft_type}")
            except FlightAwareNotFoundError:
                print("ℹ Flight not found (may not be active currently)")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
            print()
            
            # Test 4: Try airport delays
            print("Test 4: Get Airport Delays")
            print("-" * 40)
            try:
                delays = tracker.client.get_airport_delays("KJFK")
                print(f"✓ Retrieved delay info")
                print(f"  Data: {delays}")
            except FlightAwareError as e:
                print(f"ℹ Could not retrieve delays: {e}")
            print()
    
    except FlightAwareAuthError:
        print("✗ Authentication failed - check API key")
        return 1
    except FlightAwareError as e:
        print(f"✗ API Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("=" * 60)
    print("API Integration Test Complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(test_api_connection())
