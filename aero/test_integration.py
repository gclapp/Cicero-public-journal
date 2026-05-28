#!/usr/bin/env python3
"""
Integration test for Aero Flight Tracking System
Tests the basic functionality without making actual API calls.
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from flightaware_client import (
            FlightAwareClient,
            FlightAwareError,
            FlightAwareAuthError,
            FlightAwareRateLimitError,
            FlightAwareNotFoundError,
            FlightAwareServerError,
            FlightPosition,
            FlightStatus
        )
        from aero_tracker import AeroTracker, TrackedFlight
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_flight_aware_client_creation():
    """Test FlightAwareClient creation."""
    print("\nTesting FlightAwareClient creation...")
    try:
        from flightaware_client import FlightAwareClient
        client = FlightAwareClient("test_api_key")
        assert client.api_key == "test_api_key"
        client.close()
        print("✓ FlightAwareClient created successfully")
        return True
    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        return False


def test_aero_tracker_creation():
    """Test AeroTracker creation with mock."""
    print("\nTesting AeroTracker creation...")
    try:
        from aero_tracker import AeroTracker
        with patch('aero_tracker.FlightAwareClient') as mock_client:
            tracker = AeroTracker(api_key="test_key")
            assert tracker.api_key == "test_key"
            tracker.close()
        print("✓ AeroTracker created successfully")
        return True
    except Exception as e:
        print(f"✗ Tracker creation failed: {e}")
        return False


def test_tracked_flight_creation():
    """Test TrackedFlight dataclass."""
    print("\nTesting TrackedFlight creation...")
    try:
        from aero_tracker import TrackedFlight
        from datetime import datetime
        
        flight = TrackedFlight(
            flight_number="UA123",
            airline="United Airlines",
            origin_code="KJFK",
            origin_name="John F Kennedy International",
            destination_code="KLAX",
            destination_name="Los Angeles International",
            scheduled_departure=datetime.now(),
            estimated_departure=datetime.now(),
            actual_departure=None,
            scheduled_arrival=None,
            estimated_arrival=None,
            actual_arrival=None,
            status="scheduled",
            aircraft_type="B739",
            gate="A12",
            terminal="1",
            baggage_claim=None,
            position=None,
            progress_percent=0,
            fa_flight_id="UA123-1234567890",
            last_updated=datetime.now()
        )
        
        assert flight.flight_number == "UA123"
        assert flight.airline == "United Airlines"
        assert not flight.is_delayed
        assert not flight.is_active
        
        # Test to_dict
        d = flight.to_dict()
        assert d['flight_number'] == "UA123"
        assert isinstance(d['scheduled_departure'], str)
        
        print("✓ TrackedFlight created and serialized successfully")
        return True
    except Exception as e:
        print(f"✗ TrackedFlight creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flight_position_creation():
    """Test FlightPosition dataclass."""
    print("\nTesting FlightPosition creation...")
    try:
        from flightaware_client import FlightPosition
        from datetime import datetime
        
        position = FlightPosition(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            ground_speed=450,
            heading=270,
            timestamp=datetime.now()
        )
        
        assert position.latitude == 40.7128
        assert position.longitude == -74.0060
        assert position.altitude == 35000
        
        print("✓ FlightPosition created successfully")
        return True
    except Exception as e:
        print(f"✗ FlightPosition creation failed: {e}")
        return False


def test_mock_api_calls():
    """Test API calls with mocked responses."""
    print("\nTesting mock API calls...")
    try:
        from flightaware_client import FlightAwareClient
        
        with patch('flightaware_client.requests.Session.request') as mock_request:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'flights': [
                    {
                        'ident': 'UA123',
                        'fa_flight_id': 'UA123-1234567890',
                        'operator': 'United Airlines',
                        'status': 'scheduled',
                        'origin': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                        'destination': {'code': 'KLAX', 'name': 'Los Angeles International'}
                    }
                ]
            }
            mock_request.return_value = mock_response
            
            client = FlightAwareClient("test_key")
            flights = client.get_flight_by_number("UA123")
            
            assert len(flights) == 1
            assert flights[0]['ident'] == 'UA123'
            
            client.close()
        
        print("✓ Mock API calls successful")
        return True
    except Exception as e:
        print(f"✗ Mock API calls failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    try:
        from flightaware_client import (
            FlightAwareClient,
            FlightAwareAuthError,
            FlightAwareNotFoundError
        )
        
        with patch('flightaware_client.requests.Session.request') as mock_request:
            # Test 401 error
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_request.return_value = mock_response
            
            client = FlightAwareClient("test_key")
            
            try:
                client.get_flight_by_number("UA123")
                print("✗ Should have raised FlightAwareAuthError")
                return False
            except FlightAwareAuthError:
                pass  # Expected
            
            # Test 404 error
            mock_response.status_code = 404
            try:
                client.get_flight_status("invalid-id")
                print("✗ Should have raised FlightAwareNotFoundError")
                return False
            except FlightAwareNotFoundError:
                pass  # Expected
            
            client.close()
        
        print("✓ Error handling works correctly")
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Aero Flight Tracking System - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_flight_aware_client_creation,
        test_aero_tracker_creation,
        test_tracked_flight_creation,
        test_flight_position_creation,
        test_mock_api_calls,
        test_error_handling,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
