"""
Tests for Aero Tracker
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os
import tempfile

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from aero_tracker import AeroTracker, TrackedFlight
from flightaware_client import FlightAwareNotFoundError, FlightAwareAuthError


class TestAeroTracker(unittest.TestCase):
    """Test cases for AeroTracker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        
    @patch('aero_tracker.FlightAwareClient')
    def test_init_with_api_key(self, mock_client_class):
        """Test initialization with API key."""
        tracker = AeroTracker(api_key=self.api_key)
        self.assertEqual(tracker.api_key, self.api_key)
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_init_with_env_var(self, mock_client_class):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {'AEROAPI_KEY': 'env_api_key'}):
            tracker = AeroTracker()
            self.assertEqual(tracker.api_key, 'env_api_key')
            tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_init_with_config_file(self, mock_client_class):
        """Test initialization with config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'api_key': 'config_api_key'}, f)
            config_path = f.name
        
        try:
            tracker = AeroTracker(config_path=config_path)
            self.assertEqual(tracker.api_key, 'config_api_key')
            tracker.close()
        finally:
            os.unlink(config_path)
    
    @patch('aero_tracker.FlightAwareClient')
    def test_init_without_api_key_raises_error(self, mock_client_class):
        """Test that initialization fails without API key."""
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(FlightAwareAuthError):
                AeroTracker()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_track_flight(self, mock_client_class):
        """Test tracking a flight."""
        # Mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_flight_by_number.return_value = [
            {
                'ident': 'UA123',
                'fa_flight_id': 'UA123-1234567890',
                'operator': 'United Airlines',
                'status': 'scheduled',
                'origin': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                'destination': {'code': 'KLAX', 'name': 'Los Angeles International'},
                'scheduled_out': '2024-01-15T10:00:00Z',
                'estimated_out': '2024-01-15T10:00:00Z',
                'aircraft_type': 'B739'
            }
        ]
        mock_client.get_flight_position.return_value = None
        
        tracker = AeroTracker(api_key=self.api_key)
        flight = tracker.track_flight('UA123')
        
        self.assertEqual(flight.flight_number, 'UA123')
        self.assertEqual(flight.airline, 'United Airlines')
        self.assertEqual(flight.origin_code, 'KJFK')
        self.assertEqual(flight.destination_code, 'KLAX')
        self.assertEqual(flight.aircraft_type, 'B739')
        
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_track_flight_not_found(self, mock_client_class):
        """Test tracking a non-existent flight."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_flight_by_number.return_value = []
        
        tracker = AeroTracker(api_key=self.api_key)
        
        with self.assertRaises(FlightAwareNotFoundError):
            tracker.track_flight('INVALID')
        
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_get_airport_arrivals(self, mock_client_class):
        """Test getting airport arrivals."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_airport_arrivals.return_value = [
            {
                'ident': 'AA456',
                'operator': 'American Airlines',
                'origin': {'code': 'KMIA', 'name': 'Miami International'},
                'destination': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                'status': 'scheduled',
                'scheduled_in': '2024-01-15T14:00:00Z'
            }
        ]
        
        tracker = AeroTracker(api_key=self.api_key)
        arrivals = tracker.get_airport_arrivals('KJFK')
        
        self.assertEqual(len(arrivals), 1)
        self.assertEqual(arrivals[0].flight_number, 'AA456')
        self.assertEqual(arrivals[0].origin_code, 'KMIA')
        
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_get_airport_departures(self, mock_client_class):
        """Test getting airport departures."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_airport_departures.return_value = [
            {
                'ident': 'DL789',
                'operator': 'Delta Air Lines',
                'origin': {'code': 'KATL', 'name': 'Atlanta International'},
                'destination': {'code': 'KLAX', 'name': 'Los Angeles International'},
                'status': 'active',
                'scheduled_out': '2024-01-15T12:00:00Z'
            }
        ]
        
        tracker = AeroTracker(api_key=self.api_key)
        departures = tracker.get_airport_departures('KATL')
        
        self.assertEqual(len(departures), 1)
        self.assertEqual(departures[0].flight_number, 'DL789')
        
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_search_flights(self, mock_client_class):
        """Test searching flights."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.search_flights.return_value = [
            {
                'ident': 'UA123',
                'operator': 'United Airlines',
                'origin': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                'destination': {'code': 'KLAX', 'name': 'Los Angeles International'},
                'status': 'scheduled'
            }
        ]
        
        tracker = AeroTracker(api_key=self.api_key)
        flights = tracker.search_flights(origin='KJFK', destination='KLAX')
        
        self.assertEqual(len(flights), 1)
        self.assertEqual(flights[0].flight_number, 'UA123')
        
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_get_flight_position(self, mock_client_class):
        """Test getting flight position."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # First call for track_flight
        mock_client.get_flight_by_number.return_value = [
            {
                'ident': 'UA123',
                'fa_flight_id': 'UA123-1234567890',
                'operator': 'United Airlines',
                'origin': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                'destination': {'code': 'KLAX', 'name': 'Los Angeles International'},
                'status': 'active'
            }
        ]
        
        # Position call
        from flightaware_client import FlightPosition
        mock_client.get_flight_position.return_value = FlightPosition(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            ground_speed=450,
            heading=270,
            timestamp=datetime.now()
        )
        
        tracker = AeroTracker(api_key=self.api_key)
        position = tracker.get_flight_position('UA123')
        
        self.assertIsNotNone(position)
        self.assertEqual(position['latitude'], 40.7128)
        self.assertEqual(position['longitude'], -74.0060)
        
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_update_callback(self, mock_client_class):
        """Test update callback functionality."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_flight_by_number.return_value = [
            {
                'ident': 'UA123',
                'fa_flight_id': 'UA123-1234567890',
                'operator': 'United Airlines',
                'origin': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                'destination': {'code': 'KLAX', 'name': 'Los Angeles International'},
                'status': 'scheduled'
            }
        ]
        mock_client.get_flight_position.return_value = None
        
        tracker = AeroTracker(api_key=self.api_key)
        
        callback_called = False
        def test_callback(flight):
            nonlocal callback_called
            callback_called = True
        
        tracker.on_update(test_callback)
        tracker.update_flight('UA123')
        
        self.assertTrue(callback_called)
        tracker.close()
    
    @patch('aero_tracker.FlightAwareClient')
    def test_stop_tracking(self, mock_client_class):
        """Test stopping flight tracking."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_flight_by_number.return_value = [
            {
                'ident': 'UA123',
                'fa_flight_id': 'UA123-1234567890',
                'operator': 'United Airlines',
                'origin': {'code': 'KJFK', 'name': 'John F Kennedy International'},
                'destination': {'code': 'KLAX', 'name': 'Los Angeles International'},
                'status': 'scheduled'
            }
        ]
        mock_client.get_flight_position.return_value = None
        
        tracker = AeroTracker(api_key=self.api_key)
        tracker.track_flight('UA123')
        
        self.assertIn('UA123', tracker.get_tracked_flights())
        
        tracker.stop_tracking('UA123')
        self.assertNotIn('UA123', tracker.get_tracked_flights())
        
        tracker.close()


class TestTrackedFlight(unittest.TestCase):
    """Test cases for TrackedFlight dataclass."""
    
    def test_tracked_flight_creation(self):
        """Test creating a TrackedFlight."""
        now = datetime.now()
        flight = TrackedFlight(
            flight_number='UA123',
            airline='United Airlines',
            origin_code='KJFK',
            origin_name='John F Kennedy International',
            destination_code='KLAX',
            destination_name='Los Angeles International',
            scheduled_departure=now,
            estimated_departure=now,
            actual_departure=None,
            scheduled_arrival=now + timedelta(hours=5),
            estimated_arrival=now + timedelta(hours=5),
            actual_arrival=None,
            status='scheduled',
            aircraft_type='B739',
            gate='A12',
            terminal='1',
            baggage_claim='3',
            position=None,
            progress_percent=0,
            fa_flight_id='UA123-1234567890',
            last_updated=now
        )
        
        self.assertEqual(flight.flight_number, 'UA123')
        self.assertEqual(flight.airline, 'United Airlines')
        self.assertEqual(flight.origin_code, 'KJFK')
        self.assertEqual(flight.destination_code, 'KLAX')
        self.assertFalse(flight.is_delayed)
        self.assertFalse(flight.is_active)
        self.assertFalse(flight.is_completed)
    
    def test_tracked_flight_delayed(self):
        """Test delayed flight detection."""
        now = datetime.now()
        flight = TrackedFlight(
            flight_number='UA123',
            airline='United Airlines',
            origin_code='KJFK',
            origin_name='John F Kennedy International',
            destination_code='KLAX',
            destination_name='Los Angeles International',
            scheduled_departure=now,
            estimated_departure=now + timedelta(minutes=30),
            actual_departure=None,
            scheduled_arrival=now + timedelta(hours=5),
            estimated_arrival=now + timedelta(hours=5, minutes=30),
            actual_arrival=None,
            status='delayed',
            aircraft_type='B739',
            gate='A12',
            terminal='1',
            baggage_claim=None,
            position=None,
            progress_percent=0,
            fa_flight_id='UA123-1234567890',
            last_updated=now
        )
        
        self.assertTrue(flight.is_delayed)
        self.assertEqual(flight.delay_minutes, 30)
    
    def test_tracked_flight_active(self):
        """Test active flight detection."""
        now = datetime.now()
        flight = TrackedFlight(
            flight_number='UA123',
            airline='United Airlines',
            origin_code='KJFK',
            origin_name='John F Kennedy International',
            destination_code='KLAX',
            destination_name='Los Angeles International',
            scheduled_departure=now - timedelta(hours=2),
            estimated_departure=now - timedelta(hours=2),
            actual_departure=now - timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=3),
            estimated_arrival=now + timedelta(hours=3),
            actual_arrival=None,
            status='active',
            aircraft_type='B739',
            gate=None,
            terminal=None,
            baggage_claim=None,
            position={'latitude': 40.0, 'longitude': -100.0},
            progress_percent=40,
            fa_flight_id='UA123-1234567890',
            last_updated=now
        )
        
        self.assertTrue(flight.is_active)
        self.assertFalse(flight.is_completed)
    
    def test_tracked_flight_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now()
        flight = TrackedFlight(
            flight_number='UA123',
            airline='United Airlines',
            origin_code='KJFK',
            origin_name='John F Kennedy International',
            destination_code='KLAX',
            destination_name='Los Angeles International',
            scheduled_departure=now,
            estimated_departure=now,
            actual_departure=None,
            scheduled_arrival=now + timedelta(hours=5),
            estimated_arrival=now + timedelta(hours=5),
            actual_arrival=None,
            status='scheduled',
            aircraft_type='B739',
            gate='A12',
            terminal='1',
            baggage_claim=None,
            position=None,
            progress_percent=0,
            fa_flight_id='UA123-1234567890',
            last_updated=now
        )
        
        d = flight.to_dict()
        self.assertEqual(d['flight_number'], 'UA123')
        self.assertIsInstance(d['scheduled_departure'], str)


if __name__ == '__main__':
    unittest.main()
