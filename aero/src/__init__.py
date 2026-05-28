"""
Aero Flight Tracking System

A Python flight tracking system integrating FlightAware AeroAPI v4.

Features:
- Real-time flight tracking by flight number
- Airport arrivals/departures monitoring
- Flight status and position data
- Rate limiting and error handling

Example:
    from aero import AeroTracker
    
    with AeroTracker() as tracker:
        # Track a flight
        flight = tracker.track_flight("UA123")
        print(f"Status: {flight.status}")
        print(f"Position: {flight.position}")
        
        # Get airport arrivals
        arrivals = tracker.get_airport_arrivals("KJFK")
        for arr in arrivals:
            print(f"{arr.flight_number} from {arr.origin_code}")
"""

from .flightaware_client import (
    FlightAwareClient,
    FlightAwareError,
    FlightAwareAuthError,
    FlightAwareRateLimitError,
    FlightAwareNotFoundError,
    FlightAwareServerError,
    FlightPosition,
    FlightStatus
)

from .aero_tracker import (
    AeroTracker,
    TrackedFlight
)

__version__ = "1.0.0"
__all__ = [
    'AeroTracker',
    'TrackedFlight',
    'FlightAwareClient',
    'FlightAwareError',
    'FlightAwareAuthError',
    'FlightAwareRateLimitError',
    'FlightAwareNotFoundError',
    'FlightAwareServerError',
    'FlightPosition',
    'FlightStatus'
]
