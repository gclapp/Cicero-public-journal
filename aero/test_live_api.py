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
            print()
            
            # Test 1: Get airport info
            print("Test 1: Get Airport Info (KJFK)")
            print("-" * 40)
            try:
                airport_info = tracker.client.get_airport_info("KJFK")
                print(f"✓ Airport: {airport_info.get('name')}")
                print(f"  Code: {airport_info.get('code')}")
                print(f"  City: {airport_info.get('city')}")
                print(f"  Country: {airport_info.get('country')}")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
            print()
            
            # Test 2: Track a flight (may not find active flight)
            print("Test 2: Track Flight (UA1)")
            print("-" * 40)
            try:
                flight = tracker.track_flight("UA1")
                print(f"✓ Found flight: {flight.flight_number}")
                print(f"  Airline: {flight.airline}")
                print(f"  Status: {flight.status}")
                print(f"  Route: {flight.origin_code} → {flight.destination_code}")
            except FlightAwareNotFoundError:
                print("ℹ Flight not found (may not be in system currently)")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
            print()
            
            # Test 3: Get airport arrivals
            print("Test 3: Get Airport Arrivals (KJFK)")
            print("-" * 40)
            try:
                arrivals = tracker.get_airport_arrivals("KJFK", hours_ahead=1)
                print(f"✓ Found {len(arrivals)} arrivals")
                if arrivals:
                    for i, flight in enumerate(arrivals[:3], 1):
                        print(f"  {i}. {flight.flight_number} from {flight.origin_code} - {flight.status}")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
            print()
            
            # Test 4: Get airport departures
            print("Test 4: Get Airport Departures (KLAX)")
            print("-" * 40)
            try:
                departures = tracker.get_airport_departures("KLAX", hours_ahead=1)
                print(f"✓ Found {len(departures)} departures")
                if departures:
                    for i, flight in enumerate(departures[:3], 1):
                        print(f"  {i}. {flight.flight_number} to {flight.destination_code} - {flight.status}")
            except FlightAwareError as e:
                print(f"✗ Error: {e}")
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
