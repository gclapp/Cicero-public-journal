"""
Aero Flight Tracking System

Main module integrating FlightAware API with the Aero flight tracking system.
Provides high-level flight tracking, airport monitoring, and flight status services.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

from flightaware_client import (
    FlightAwareClient,
    FlightAwareError,
    FlightAwareAuthError,
    FlightAwareRateLimitError,
    FlightAwareNotFoundError,
    FlightPosition,
    FlightStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TrackedFlight:
    """Represents a tracked flight with enhanced information."""
    flight_number: str
    airline: str
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    scheduled_departure: Optional[datetime]
    estimated_departure: Optional[datetime]
    actual_departure: Optional[datetime]
    scheduled_arrival: Optional[datetime]
    estimated_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    status: str
    aircraft_type: Optional[str]
    gate: Optional[str]
    terminal: Optional[str]
    baggage_claim: Optional[str]
    position: Optional[Dict[str, Any]]
    progress_percent: Optional[int]
    fa_flight_id: Optional[str]
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        for key in result:
            if isinstance(result[key], datetime):
                result[key] = result[key].isoformat()
        return result
    
    @property
    def is_delayed(self) -> bool:
        """Check if flight is delayed."""
        if self.scheduled_departure and self.estimated_departure:
            delay = self.estimated_departure - self.scheduled_departure
            return delay > timedelta(minutes=15)
        return False
    
    @property
    def delay_minutes(self) -> Optional[int]:
        """Get delay in minutes if delayed."""
        if self.scheduled_departure and self.estimated_departure:
            delay = self.estimated_departure - self.scheduled_departure
            return max(0, int(delay.total_seconds() / 60))
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if flight is currently in the air."""
        return self.status.lower() in ['active', 'enroute', 'in_air']
    
    @property
    def is_completed(self) -> bool:
        """Check if flight has landed."""
        return self.status.lower() in ['landed', 'arrived', 'completed']


class AeroTracker:
    """
    Main Aero Flight Tracking class.
    
    Integrates with FlightAware API to provide:
    - Real-time flight tracking
    - Airport arrivals/departures monitoring
    - Flight status updates
    - Historical flight data
    """
    
    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize the Aero Tracker.
        
        Args:
            api_key: FlightAware API key (or from AEROAPI_KEY env var)
            config_path: Path to config file with API key
        """
        self.api_key = self._load_api_key(api_key, config_path)
        self.client = FlightAwareClient(self.api_key)
        self._tracked_flights: Dict[str, TrackedFlight] = {}
        self._update_callbacks: List[Callable] = []
        
        logger.info("Aero Tracker initialized")
    
    def _load_api_key(
        self,
        api_key: Optional[str],
        config_path: Optional[str]
    ) -> str:
        """Load API key from various sources."""
        # 1. Direct parameter
        if api_key:
            return api_key
        
        # 2. Environment variable
        env_key = os.getenv('AEROAPI_KEY')
        if env_key:
            return env_key
        
        # 3. Config file
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
                    if 'api_key' in config:
                        return config['api_key']
        
        # 4. OpenClaw credentials directory
        openclaw_creds = Path.home() / '.openclaw' / 'credentials' / 'flightaware.json'
        if openclaw_creds.exists():
            with open(openclaw_creds) as f:
                config = json.load(f)
                if 'api_key' in config:
                    return config['api_key']
        
        # 5. Default config location
        default_config = Path.home() / '.aero' / 'config.json'
        if default_config.exists():
            with open(default_config) as f:
                config = json.load(f)
                if 'api_key' in config:
                    return config['api_key']
        
        raise FlightAwareAuthError(
            "API key not found. Provide it via: "
            "1) Constructor parameter, "
            "2) AEROAPI_KEY environment variable, "
            "3) OpenClaw credentials file (~/.openclaw/credentials/flightaware.json), "
            "4) Config file"
        )
    
    def track_flight(self, flight_number: str, date: Optional[str] = None) -> TrackedFlight:
        """
        Start tracking a flight by flight number.
        
        Args:
            flight_number: Airline flight number (e.g., "UA123")
            date: Optional date in YYYY-MM-DD format
            
        Returns:
            TrackedFlight object with current status
        """
        logger.info(f"Tracking flight {flight_number}")
        
        flights = self.client.get_flight_by_number(flight_number, date)
        
        if not flights:
            raise FlightAwareNotFoundError(f"Flight {flight_number} not found")
        
        # Get the most relevant flight (usually the first one)
        flight_data = flights[0]
        fa_flight_id = flight_data.get('fa_flight_id')
        
        # Get position if available
        position = None
        if fa_flight_id:
            position = self.client.get_flight_position(fa_flight_id)
        
        tracked = self._create_tracked_flight(flight_data, position)
        self._tracked_flights[flight_number] = tracked
        
        return tracked
    
    def update_flight(self, flight_number: str) -> TrackedFlight:
        """
        Update tracking information for a flight.
        
        Args:
            flight_number: Flight number to update
            
        Returns:
            Updated TrackedFlight object
        """
        logger.info(f"Updating flight {flight_number}")
        
        tracked = self.track_flight(flight_number)
        
        # Notify callbacks
        for callback in self._update_callbacks:
            try:
                callback(tracked)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        return tracked
    
    def get_airport_arrivals(
        self,
        airport_code: str,
        hours_ahead: int = 2,
        hours_behind: int = 1
    ) -> List[TrackedFlight]:
        """
        Get arrivals for an airport.
        
        Args:
            airport_code: ICAO or IATA airport code
            hours_ahead: Hours to look ahead
            hours_behind: Hours to look behind
            
        Returns:
            List of TrackedFlight objects
        """
        logger.info(f"Getting arrivals for {airport_code}")
        
        now = datetime.now()
        start_time = now - timedelta(hours=hours_behind)
        end_time = now + timedelta(hours=hours_ahead)
        
        arrivals = self.client.get_airport_arrivals(
            airport_code,
            start_time=start_time,
            end_time=end_time
        )
        
        return [self._create_tracked_flight(a) for a in arrivals]
    
    def get_airport_departures(
        self,
        airport_code: str,
        hours_ahead: int = 2,
        hours_behind: int = 1
    ) -> List[TrackedFlight]:
        """
        Get departures for an airport.
        
        Args:
            airport_code: ICAO or IATA airport code
            hours_ahead: Hours to look ahead
            hours_behind: Hours to look behind
            
        Returns:
            List of TrackedFlight objects
        """
        logger.info(f"Getting departures for {airport_code}")
        
        now = datetime.now()
        start_time = now - timedelta(hours=hours_behind)
        end_time = now + timedelta(hours=hours_ahead)
        
        departures = self.client.get_airport_departures(
            airport_code,
            start_time=start_time,
            end_time=end_time
        )
        
        return [self._create_tracked_flight(d) for d in departures]
    
    def search_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        flight_number: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[TrackedFlight]:
        """
        Search for flights with various criteria.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            flight_number: Flight number
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of matching TrackedFlight objects
        """
        logger.info(f"Searching flights: origin={origin}, dest={destination}, flight={flight_number}")
        
        flights = self.client.search_flights(
            origin=origin,
            destination=destination,
            flight_number=flight_number,
            date=date
        )
        
        return [self._create_tracked_flight(f) for f in flights]
    
    def get_flight_position(self, flight_number: str) -> Optional[Dict[str, Any]]:
        """
        Get current position of a tracked flight.
        
        Args:
            flight_number: Flight number
            
        Returns:
            Position dictionary or None
        """
        if flight_number not in self._tracked_flights:
            self.track_flight(flight_number)
        
        tracked = self._tracked_flights[flight_number]
        if tracked.fa_flight_id:
            position = self.client.get_flight_position(tracked.fa_flight_id)
            if position:
                return {
                    'latitude': position.latitude,
                    'longitude': position.longitude,
                    'altitude': position.altitude,
                    'ground_speed': position.ground_speed,
                    'heading': position.heading,
                    'timestamp': position.timestamp.isoformat() if position.timestamp else None
                }
        return None
    
    def on_update(self, callback: Callable):
        """
        Register a callback for flight updates.
        
        Args:
            callback: Function to call with updated TrackedFlight
        """
        self._update_callbacks.append(callback)
    
    def _create_tracked_flight(
        self,
        flight_data: Dict[str, Any],
        position: Optional[FlightPosition] = None
    ) -> TrackedFlight:
        """Create TrackedFlight from API response data."""
        origin = flight_data.get('origin', {})
        destination = flight_data.get('destination', {})
        
        # Parse scheduled/estimated/actual times
        scheduled_out = self._parse_time(flight_data.get('scheduled_out'))
        estimated_out = self._parse_time(flight_data.get('estimated_out'))
        actual_out = self._parse_time(flight_data.get('actual_out'))
        scheduled_in = self._parse_time(flight_data.get('scheduled_in'))
        estimated_in = self._parse_time(flight_data.get('estimated_in'))
        actual_in = self._parse_time(flight_data.get('actual_in'))
        
        # Determine status
        status = flight_data.get('status', 'unknown')
        if actual_in:
            status = 'landed'
        elif actual_out:
            status = 'active'
        elif estimated_out and estimated_out > scheduled_out:
            status = 'delayed'
        
        return TrackedFlight(
            flight_number=flight_data.get('ident', ''),
            airline=flight_data.get('operator', ''),
            origin_code=origin.get('code', ''),
            origin_name=origin.get('name', ''),
            destination_code=destination.get('code', ''),
            destination_name=destination.get('name', ''),
            scheduled_departure=scheduled_out,
            estimated_departure=estimated_out,
            actual_departure=actual_out,
            scheduled_arrival=scheduled_in,
            estimated_arrival=estimated_in,
            actual_arrival=actual_in,
            status=status,
            aircraft_type=flight_data.get('aircraft_type', ''),
            gate=flight_data.get('gate_origin') or flight_data.get('gate_destination'),
            terminal=flight_data.get('terminal_origin') or flight_data.get('terminal_destination'),
            baggage_claim=flight_data.get('baggage_claim'),
            position=asdict(position) if position else None,
            progress_percent=flight_data.get('progress_percent'),
            fa_flight_id=flight_data.get('fa_flight_id'),
            last_updated=datetime.now()
        )
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse time string to datetime."""
        if not time_str:
            return None
        try:
            time_str = time_str.replace('Z', '+00:00')
            return datetime.fromisoformat(time_str)
        except (ValueError, TypeError):
            return None
    
    def get_tracked_flights(self) -> Dict[str, TrackedFlight]:
        """Get all currently tracked flights."""
        return self._tracked_flights.copy()
    
    def stop_tracking(self, flight_number: str):
        """Stop tracking a flight."""
        if flight_number in self._tracked_flights:
            del self._tracked_flights[flight_number]
            logger.info(f"Stopped tracking {flight_number}")
    
    def close(self):
        """Close the tracker and release resources."""
        self.client.close()
        logger.info("Aero Tracker closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
