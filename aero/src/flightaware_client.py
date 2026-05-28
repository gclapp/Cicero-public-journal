"""
FlightAware AeroAPI v4 Client

A Python client for the FlightAware AeroAPI v4 REST API.
Provides real-time flight tracking, airport arrivals/departures, and flight status data.

API Documentation: https://www.flightaware.com/aeroapi/portal/documentation
Base URL: https://aeroapi.flightaware.com/aeroapi
"""

import requests
import time
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlightAwareError(Exception):
    """Base exception for FlightAware API errors."""
    pass


class FlightAwareAuthError(FlightAwareError):
    """Authentication error (401)."""
    pass


class FlightAwareRateLimitError(FlightAwareError):
    """Rate limit exceeded (429)."""
    pass


class FlightAwareNotFoundError(FlightAwareError):
    """Resource not found (404)."""
    pass


class FlightAwareServerError(FlightAwareError):
    """Server error (5xx)."""
    pass


@dataclass
class FlightPosition:
    """Represents a flight's current position."""
    latitude: float
    longitude: float
    altitude: Optional[int]  # feet
    ground_speed: Optional[int]  # knots
    heading: Optional[int]  # degrees
    timestamp: Optional[datetime]


@dataclass
class FlightStatus:
    """Represents flight status information."""
    flight_number: str
    airline_code: Optional[str]
    airline_name: Optional[str]
    origin: Dict[str, Any]  # airport info
    destination: Dict[str, Any]  # airport info
    departure_time: Optional[datetime]
    arrival_time: Optional[datetime]
    status: str  # scheduled, active, landed, cancelled, diverted
    position: Optional[FlightPosition]
    aircraft_type: Optional[str]
    progress_percent: Optional[int]


@dataclass
class AirportFlight:
    """Represents a flight at an airport (arrival or departure)."""
    flight_number: str
    airline: Optional[str]
    origin: Dict[str, Any]
    destination: Dict[str, Any]
    scheduled_time: Optional[datetime]
    estimated_time: Optional[datetime]
    actual_time: Optional[datetime]
    status: str
    gate: Optional[str]
    terminal: Optional[str]
    aircraft_type: Optional[str]


class FlightAwareClient:
    """
    Client for FlightAware AeroAPI v4.
    
    Features:
    - Real-time flight tracking by flight number
    - Airport arrivals/departures
    - Flight status and position data
    - Rate limiting and error handling
    - Automatic retries with exponential backoff
    """
    
    BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the FlightAware client.
        
        Args:
            api_key: Your FlightAware AeroAPI key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'x-apikey': api_key,
            'Accept': 'application/json'
        })
        
        # Rate limiting state
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        logger.info("FlightAware client initialized")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make an API request with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            retry_count: Current retry attempt
            
        Returns:
            JSON response as dictionary
            
        Raises:
            FlightAwareError: Various error types based on response
        """
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=self.timeout
            )
            self._last_request_time = time.time()
            
            # Handle different status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise FlightAwareAuthError("Invalid API key or unauthorized")
            elif response.status_code == 404:
                raise FlightAwareNotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code == 429:
                if retry_count < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (2 ** retry_count)
                    logger.warning(f"Rate limited. Retrying in {delay}s...")
                    time.sleep(delay)
                    return self._make_request(method, endpoint, params, data, retry_count + 1)
                raise FlightAwareRateLimitError("Rate limit exceeded. Max retries reached.")
            elif response.status_code >= 500:
                if retry_count < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (2 ** retry_count)
                    logger.warning(f"Server error {response.status_code}. Retrying in {delay}s...")
                    time.sleep(delay)
                    return self._make_request(method, endpoint, params, data, retry_count + 1)
                raise FlightAwareServerError(f"Server error: {response.status_code}")
            else:
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)
                logger.warning(f"Request timeout. Retrying in {delay}s...")
                time.sleep(delay)
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise FlightAwareError("Request timeout. Max retries reached.")
            
        except requests.exceptions.RequestException as e:
            raise FlightAwareError(f"Request failed: {str(e)}")
    
    def get_flight_by_number(
        self,
        flight_number: str,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get flight information by flight number.
        
        Args:
            flight_number: Airline flight number (e.g., "UA123", "SWR123")
            date: Optional date in YYYY-MM-DD format
            
        Returns:
            List of flight information dictionaries
        """
        params = {'ident': flight_number}
        if date:
            params['date'] = date
            
        response = self._make_request('GET', '/flights', params=params)
        return response.get('flights', [])
    
    def get_flight_position(self, fa_flight_id: str) -> Optional[FlightPosition]:
        """
        Get current position of a flight.
        
        Args:
            fa_flight_id: FlightAware flight ID (from get_flight_by_number)
            
        Returns:
            FlightPosition object or None if not available
        """
        try:
            response = self._make_request('GET', f'/flights/{fa_flight_id}/position')
            position_data = response.get('position')
            
            if not position_data:
                return None
                
            return FlightPosition(
                latitude=position_data.get('latitude'),
                longitude=position_data.get('longitude'),
                altitude=position_data.get('altitude'),
                ground_speed=position_data.get('ground_speed'),
                heading=position_data.get('heading'),
                timestamp=self._parse_timestamp(position_data.get('timestamp'))
            )
        except FlightAwareNotFoundError:
            return None
    
    def get_airport_arrivals(
        self,
        airport_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get arrivals for an airport.
        
        Args:
            airport_code: ICAO or IATA airport code (e.g., "KJFK", "JFK")
            start_time: Optional start time (defaults to now)
            end_time: Optional end time
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of arrival flight dictionaries
        """
        params = {}
        if start_time:
            # Ensure timezone-aware ISO format
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
            params['start'] = start_time.isoformat()
        if end_time:
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
            params['end'] = end_time.isoformat()
            
        all_arrivals = []
        endpoint = f'/airports/{airport_code}/flights/arrivals'
        
        for page in range(max_pages):
            response = self._make_request('GET', endpoint, params=params)
            arrivals = response.get('arrivals', [])
            all_arrivals.extend(arrivals)
            
            # Check for next page
            links = response.get('_links', {})
            if 'next' not in links:
                break
                
            # Extract cursor for next page
            next_url = links['next']
            if 'cursor' in next_url:
                import urllib.parse
                parsed = urllib.parse.urlparse(next_url)
                query = urllib.parse.parse_qs(parsed.query)
                params['cursor'] = query.get('cursor', [None])[0]
        
        return all_arrivals
    
    def get_airport_departures(
        self,
        airport_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get departures for an airport.
        
        Args:
            airport_code: ICAO or IATA airport code
            start_time: Optional start time
            end_time: Optional end time
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of departure flight dictionaries
        """
        params = {}
        if start_time:
            # Ensure timezone-aware ISO format
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
            params['start'] = start_time.isoformat()
        if end_time:
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
            params['end'] = end_time.isoformat()

        all_departures = []
        endpoint = f'/airports/{airport_code}/flights/departures'
        
        for page in range(max_pages):
            response = self._make_request('GET', endpoint, params=params)
            departures = response.get('departures', [])
            all_departures.extend(departures)
            
            links = response.get('_links', {})
            if 'next' not in links:
                break
                
            next_url = links['next']
            if 'cursor' in next_url:
                import urllib.parse
                parsed = urllib.parse.urlparse(next_url)
                query = urllib.parse.parse_qs(parsed.query)
                params['cursor'] = query.get('cursor', [None])[0]
        
        return all_departures
    
    def get_flight_status(self, fa_flight_id: str) -> Dict[str, Any]:
        """
        Get detailed status for a specific flight.
        
        Args:
            fa_flight_id: FlightAware flight ID
            
        Returns:
            Flight status dictionary
        """
        return self._make_request('GET', f'/flights/{fa_flight_id}')
    
    def search_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        flight_number: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for flights with various criteria.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            flight_number: Flight number
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of matching flights
        """
        params = {}
        if origin:
            params['origin'] = origin
        if destination:
            params['destination'] = destination
        if flight_number:
            params['ident'] = flight_number
        if date:
            params['date'] = date
            
        response = self._make_request('GET', '/flights/search', params=params)
        return response.get('flights', [])
    
    def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """
        Get information about an airport.
        
        Args:
            airport_code: ICAO or IATA airport code
            
        Returns:
            Airport information dictionary
        """
        return self._make_request('GET', f'/airports/{airport_code}')
    
    def get_airport_delays(self, airport_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get airport delay information.
        
        Args:
            airport_code: Optional specific airport, or None for all delays
            
        Returns:
            List of airport delay information
        """
        if airport_code:
            return self._make_request('GET', f'/airports/{airport_code}/delays')
        else:
            response = self._make_request('GET', '/airports/delays')
            return response.get('delays', [])
    
    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp string to datetime object."""
        if not timestamp:
            return None
        try:
            # Handle various ISO formats
            timestamp = timestamp.replace('Z', '+00:00')
            return datetime.fromisoformat(timestamp)
        except (ValueError, TypeError):
            return None
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.info("FlightAware client closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
