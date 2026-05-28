#!/usr/bin/env python3
"""
Aero Flight Monitor - Core flight tracking via FlightAware AeroAPI
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Configuration
CONFIG_PATH = Path(__file__).parent / "config.json"
MEMORY_PATH = Path(__file__).parent / "memory"

@dataclass
class FlightStatus:
    flight_number: str
    airline: str
    origin: str
    destination: str
    scheduled_departure: datetime
    estimated_departure: datetime
    scheduled_arrival: datetime
    estimated_arrival: datetime
    departure_gate: Optional[str]
    arrival_gate: Optional[str]
    status: str  # scheduled, active, landed, cancelled, delayed
    aircraft_type: Optional[str]
    delay_minutes: int
    progress_percent: Optional[int]
    altitude: Optional[int]
    groundspeed: Optional[int]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class FlightAwareClient:
    """Client for FlightAware AeroAPI v4"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.config = self._load_config()
        self.api_key = api_key or self.config.get("flightaware", {}).get("api_key")
        self.base_url = self.config.get("flightaware", {}).get("base_url", 
                                                                  "https://aeroapi.flightaware.com/aeroapi")
        
        if not self.api_key:
            raise ValueError("FlightAware API key not configured. Run setup first.")
    
    def _load_config(self) -> Dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {}
    
    def _headers(self) -> Dict[str, str]:
        return {
            "x-apikey": self.api_key,
            "Accept": "application/json"
        }
    
    def get_flight_status(self, flight_number: str, 
                          date: Optional[str] = None) -> Optional[FlightStatus]:
        """
        Get current status of a flight.
        
        Args:
            flight_number: e.g., "DL123" or "DAL123"
            date: Optional date in YYYY-MM-DD format
        """
        try:
            # Try to find the flight
            url = f"{self.base_url}/flights/{flight_number}"
            if date:
                url += f"?start={date}T00:00:00Z&end={date}T23:59:59Z"
            
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()
            data = response.json()
            
            if not data.get("flights"):
                return None
            
            # Get the first (most relevant) flight
            flight = data["flights"][0]
            return self._parse_flight_data(flight)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching flight status: {e}")
            return None
    
    def search_flights(self, origin: str, destination: str, 
                       date: str) -> List[FlightStatus]:
        """
        Search for flights between airports on a specific date.
        
        Args:
            origin: Origin airport code (e.g., "LAX")
            destination: Destination airport code (e.g., "JFK")
            date: Date in YYYY-MM-DD format
        """
        try:
            url = f"{self.base_url}/schedules/{date}"
            params = {
                "origin": origin,
                "destination": destination
            }
            
            response = requests.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            data = response.json()
            
            flights = []
            for flight in data.get("scheduled", []):
                flights.append(self._parse_schedule_data(flight))
            
            return flights
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching flights: {e}")
            return []
    
    def get_airport_delays(self, airport_code: str) -> Dict:
        """Get current delays and status for an airport."""
        try:
            url = f"{self.base_url}/airports/{airport_code}/delays"
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching airport delays: {e}")
            return {}
    
    def _parse_flight_data(self, flight: Dict) -> FlightStatus:
        """Parse FlightAware flight data into FlightStatus."""
        return FlightStatus(
            flight_number=flight.get("ident", "Unknown"),
            airline=flight.get("operator", "Unknown"),
            origin=flight.get("origin", {}).get("code", "Unknown"),
            destination=flight.get("destination", {}).get("code", "Unknown"),
            scheduled_departure=self._parse_datetime(flight.get("scheduled_out")),
            estimated_departure=self._parse_datetime(flight.get("estimated_out")),
            scheduled_arrival=self._parse_datetime(flight.get("scheduled_in")),
            estimated_arrival=self._parse_datetime(flight.get("estimated_in")),
            departure_gate=flight.get("gate_origin"),
            arrival_gate=flight.get("gate_destination"),
            status=self._map_status(flight.get("status", "unknown")),
            aircraft_type=flight.get("aircraft_type"),
            delay_minutes=self._calculate_delay(flight),
            progress_percent=flight.get("progress_percent"),
            altitude=flight.get("altitude"),
            groundspeed=flight.get("groundspeed")
        )
    
    def _parse_schedule_data(self, flight: Dict) -> FlightStatus:
        """Parse scheduled flight data."""
        return FlightStatus(
            flight_number=flight.get("ident", "Unknown"),
            airline=flight.get("operator", "Unknown"),
            origin=flight.get("origin", "Unknown"),
            destination=flight.get("destination", "Unknown"),
            scheduled_departure=self._parse_datetime(flight.get("scheduled_out")),
            estimated_departure=self._parse_datetime(flight.get("scheduled_out")),
            scheduled_arrival=self._parse_datetime(flight.get("scheduled_in")),
            estimated_arrival=self._parse_datetime(flight.get("scheduled_in")),
            departure_gate=None,
            arrival_gate=None,
            status="scheduled",
            aircraft_type=flight.get("aircraft_type"),
            delay_minutes=0,
            progress_percent=None,
            altitude=None,
            groundspeed=None
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> datetime:
        """Parse ISO datetime string."""
        if not dt_str:
            return datetime.now()
        try:
            # Remove Z and parse
            dt_str = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(dt_str)
        except:
            return datetime.now()
    
    def _map_status(self, fa_status: str) -> str:
        """Map FlightAware status to our status."""
        status_map = {
            "Scheduled": "scheduled",
            "Active": "active",
            "Landed": "landed",
            "Cancelled": "cancelled",
            "Delayed": "delayed",
            "Diverted": "diverted"
        }
        return status_map.get(fa_status, "unknown")
    
    def _calculate_delay(self, flight: Dict) -> int:
        """Calculate delay in minutes."""
        scheduled_out = flight.get("scheduled_out")
        estimated_out = flight.get("estimated_out")
        
        if scheduled_out and estimated_out:
            sched = self._parse_datetime(scheduled_out)
            est = self._parse_datetime(estimated_out)
            delay = (est - sched).total_seconds() / 60
            return max(0, int(delay))
        return 0


class FlightMonitor:
    """Main flight monitoring orchestrator."""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize FlightAware client if API key exists."""
        config = self._load_config()
        api_key = config.get("flightaware", {}).get("api_key")
        if api_key:
            self.client = FlightAwareClient(api_key)
    
    def _load_config(self) -> Dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {}
    
    def is_configured(self) -> bool:
        """Check if FlightAware is properly configured."""
        return self.client is not None
    
    def monitor_flight(self, flight_number: str, 
                       date: Optional[str] = None) -> Optional[FlightStatus]:
        """Monitor a specific flight."""
        if not self.client:
            raise RuntimeError("FlightAware not configured. Run setup first.")
        
        return self.client.get_flight_status(flight_number, date)
    
    def find_alternatives(self, origin: str, destination: str, 
                          date: str) -> List[FlightStatus]:
        """Find alternative flights."""
        if not self.client:
            raise RuntimeError("FlightAware not configured. Run setup first.")
        
        return self.client.search_flights(origin, destination, date)
    
    def check_airport_status(self, airport_code: str) -> Dict:
        """Check airport delays and status."""
        if not self.client:
            raise RuntimeError("FlightAware not configured. Run setup first.")
        
        return self.client.get_airport_delays(airport_code)


def setup_flightaware(api_key: str, api_secret: Optional[str] = None):
    """
    Setup FlightAware API credentials.
    
    Args:
        api_key: Your FlightAware AeroAPI key
        api_secret: Optional API secret (for some auth methods)
    """
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    
    if "flightaware" not in config:
        config["flightaware"] = {}
    
    config["flightaware"]["api_key"] = api_key
    if api_secret:
        config["flightaware"]["api_secret"] = api_secret
    
    # Ensure memory directory exists
    MEMORY_PATH.mkdir(parents=True, exist_ok=True)
    (MEMORY_PATH / "trips").mkdir(exist_ok=True)
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ FlightAware configuration saved!")
    print(f"   Config location: {CONFIG_PATH}")
    
    # Test the connection
    try:
        client = FlightAwareClient(api_key)
        # Try a simple request
        url = f"{client.base_url}/flights/DL123"
        response = requests.get(url, headers=client._headers())
        if response.status_code == 200:
            print("✅ Connection test successful!")
        elif response.status_code == 401:
            print("⚠️  Connection test failed: Invalid API key")
        else:
            print(f"⚠️  Connection test returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test connection: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python flight_monitor.py setup <api_key> [api_secret]")
        print("  python flight_monitor.py status <flight_number> [date]")
        print("  python flight_monitor.py search <origin> <destination> <date>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        if len(sys.argv) < 3:
            print("Error: API key required")
            sys.exit(1)
        api_key = sys.argv[2]
        api_secret = sys.argv[3] if len(sys.argv) > 3 else None
        setup_flightaware(api_key, api_secret)
    
    elif command == "status":
        if len(sys.argv) < 3:
            print("Error: Flight number required")
            sys.exit(1)
        flight_number = sys.argv[2]
        date = sys.argv[3] if len(sys.argv) > 3 else None
        
        monitor = FlightMonitor()
        if not monitor.is_configured():
            print("Error: FlightAware not configured. Run setup first.")
            sys.exit(1)
        
        status = monitor.monitor_flight(flight_number, date)
        if status:
            print(json.dumps(status.to_dict(), indent=2, default=str))
        else:
            print(f"Flight {flight_number} not found")
    
    elif command == "search":
        if len(sys.argv) < 5:
            print("Error: origin, destination, and date required")
            sys.exit(1)
        origin = sys.argv[2]
        destination = sys.argv[3]
        date = sys.argv[4]
        
        monitor = FlightMonitor()
        if not monitor.is_configured():
            print("Error: FlightAware not configured. Run setup first.")
            sys.exit(1)
        
        flights = monitor.find_alternatives(origin, destination, date)
        print(f"Found {len(flights)} flights from {origin} to {destination} on {date}")
        for flight in flights:
            print(f"  {flight.flight_number}: {flight.scheduled_departure.strftime('%H:%M')} → {flight.scheduled_arrival.strftime('%H:%M')}")
    
    else:
        print(f"Unknown command: {command}")