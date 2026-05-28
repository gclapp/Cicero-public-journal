"""
Tests for FlightAware API Client
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/aero/src')

from flightaware_client import (
    FlightAwareClient,
    FlightAwareError,
    FlightAwareAuthError,
    FlightAwareRateLimitError,
    FlightAwareNotFoundError,
    FlightPosition
)


class TestFlightAwareClient(unittest.TestCase):
    """Test cases for FlightAwareClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = FlightAwareClient(self.api_key)
    
    def tearDown(self):
        """Clean up after tests."""
        self.client.close()
    
    @patch('flightaware_client.requests.Session.request')
    def test_get_flight_by_number_success(self, mock_request):
        """Test successful flight lookup."""
        # Mock response
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
        
        # Call method
        flights = self.client.get_flight_by_number('UA123')
        
        # Assertions
        self.assertEqual(len(flights), 1)
        self.assertEqual(flights[0]['ident'], 'UA123')
        self.assertEqual(flights[0]['operator'], 'United Airlines')
    
    @patch('flightaware_client.requests.Session.request')
    def test_get_flight_by_number_with_date(self, mock_request):
        """Test flight lookup with specific date."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'flights': []}
        mock_request.return_value = mock_response
        
        self.client.get_flight_by_number('UA123', date='2024-01-15')
        
        # Verify the call was made with date parameter
        call_args = mock_request.call_args
        self.assertIn('params', call_args.kwargs)
        self.assertEqual(call_args.kwargs['params']['date'], '2024-01-15')
    
    @patch('flightaware_client.requests.Session.request')
    def test_get_flight_position(self, mock_request):
        """Test getting flight position."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'position': {
                'latitude': 40.7128,
                'longitude': -74.0060,
                'altitude': 35000,
                'ground_speed': 450,
                'heading': 270,
                'timestamp': '2024-01-15T12:00:00Z'
            }
        }
        mock_request.return_value = mock_response
        
        position = self.client.get_flight_position('UA123-1234567890')
        
        self.assertIsNotNone(position)
        self.assertEqual(position.latitude, 40.7128)
        self.assertEqual(position.longitude, -74.0060)
        self.assertEqual(position.altitude, 35000)
        self.assertEqual(position.ground_speed, 450)
        self.assertEqual(position.heading, 270)
    
    @patch('flightaware_client.requests.Session.request')
    def test_get_airport_arrivals(self, mock_request):
        """Test getting airport arrivals."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'arrivals': [
                {
                    'ident': 'AA456',
                    'operator': 'American Airlines',
                    'origin': {'code': 'KMIA', 'name': 'Miami International'},
                    'status': 'scheduled'
                },
                {
                    'ident': 'DL789',
                    'operator': 'Delta Air Lines',
                    'origin': {'code': 'KATL', 'name': 'Atlanta International'},
                    'status': 'active'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        arrivals = self.client.get_airport_arrivals('KJFK')
        
        self.assertEqual(len(arrivals), 2)
        self.assertEqual(arrivals[0]['ident'], 'AA456')
        self.assertEqual(arrivals[1]['ident'], 'DL789')
    
    @patch('flightaware_client.requests.Session.request')
    def test_get_airport_departures(self, mock_request):
        """Test getting airport departures."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'departures': [
                {
                    'ident': 'SWA123',
                    'operator': 'Southwest Airlines',
                    'destination': {'code': 'KDAL', 'name': 'Dallas Love Field'},
                    'status': 'active'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        departures = self.client.get_airport_departures('KLAX')
        
        self.assertEqual(len(departures), 1)
        self.assertEqual(departures[0]['ident'], 'SWA123')
    
    @patch('flightaware_client.requests.Session.request')
    def test_auth_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        with self.assertRaises(FlightAwareAuthError):
            self.client.get_flight_by_number('UA123')
    
    @patch('flightaware_client.requests.Session.request')
    def test_not_found_error(self, mock_request):
        """Test not found error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        with self.assertRaises(FlightAwareNotFoundError):
            self.client.get_flight_status('INVALID-FLIGHT-ID')
    
    @patch('flightaware_client.requests.Session.request')
    def test_rate_limit_error(self, mock_request):
        """Test rate limit error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_request.return_value = mock_response
        
        with self.assertRaises(FlightAwareRateLimitError):
            self.client.get_flight_by_number('UA123')
    
    @patch('flightaware_client.requests.Session.request')
    def test_server_error_with_retry(self, mock_request):
        """Test server error with retry logic."""
        mock_response_error = MagicMock()
        mock_response_error.status_code = 503
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'flights': []}
        
        mock_request.side_effect = [
            mock_response_error,
            mock_response_success
        ]
        
        flights = self.client.get_flight_by_number('UA123')
        self.assertEqual(flights, [])
        self.assertEqual(mock_request.call_count, 2)
    
    @patch('flightaware_client.requests.Session.request')
    def test_timeout_with_retry(self, mock_request):
        """Test timeout with retry logic."""
        import requests
        mock_request.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            MagicMock(status_code=200, json=lambda: {'flights': []})
        ]
        
        flights = self.client.get_flight_by_number('UA123')
        self.assertEqual(flights, [])
        self.assertEqual(mock_request.call_count, 3)
    
    def test_context_manager(self):
        """Test context manager usage."""
        with FlightAwareClient(self.api_key) as client:
            self.assertIsNotNone(client.session)
        # After exiting context, session should be closed


class TestFlightPosition(unittest.TestCase):
    """Test cases for FlightPosition dataclass."""
    
    def test_position_creation(self):
        """Test creating a FlightPosition."""
        position = FlightPosition(
            latitude=40.7128,
            longitude=-74.0060,
            altitude=35000,
            ground_speed=450,
            heading=270,
            timestamp=datetime.now()
        )
        
        self.assertEqual(position.latitude, 40.7128)
        self.assertEqual(position.longitude, -74.0060)
        self.assertEqual(position.altitude, 35000)


if __name__ == '__main__':
    unittest.main()
