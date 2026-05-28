# Aero Flight Tracking System

A Python flight tracking system integrating FlightAware AeroAPI v4 for real-time flight data, airport operations, and flight status monitoring.

## Features

- ✈️ **Real-time Flight Tracking** - Track flights by flight number
- 🛬 **Airport Operations** - Monitor arrivals and departures
- 📍 **Flight Position Data** - Get current location, altitude, speed, heading
- 🕐 **Flight Status** - Scheduled, active, delayed, landed status
- 🔄 **Automatic Updates** - Update tracking data with callbacks
- ⚡ **Rate Limiting** - Built-in rate limiting and retry logic
- 🛡️ **Error Handling** - Comprehensive error handling with specific exceptions
- 📊 **Rich Data** - Aircraft type, gates, terminals, baggage claim info

## Installation

### Prerequisites

- Python 3.8+
- FlightAware AeroAPI key ([Get one here](https://www.flightaware.com/commercial/aeroapi))

### Setup

1. Clone or copy the Aero project to your workspace:
```bash
cd /home/ubuntu/.openclaw/workspace/aero
```

2. Install dependencies:
```bash
pip install requests
```

3. Configure your API key (choose one method):

**Option A: Environment Variable**
```bash
export AEROAPI_KEY="your_api_key_here"
```

**Option B: Config File**
```bash
mkdir -p ~/.aero
echo '{"api_key": "your_api_key_here"}' > ~/.aero/config.json
chmod 600 ~/.aero/config.json
```

See `docs/API_SETUP.md` for detailed setup instructions.

## Quick Start

```python
from aero import AeroTracker

# Track a flight
with AeroTracker() as tracker:
    flight = tracker.track_flight("UA123")
    
    print(f"Flight: {flight.flight_number}")
    print(f"Status: {flight.status}")
    print(f"From: {flight.origin_name}")
    print(f"To: {flight.destination_name}")
    
    if flight.is_delayed:
        print(f"⚠️ Delayed by {flight.delay_minutes} minutes")
    
    if flight.is_active:
        position = tracker.get_flight_position("UA123")
        print(f"📍 Current position: {position['latitude']}, {position['longitude']}")
```

## Usage Examples

### Track a Flight

```python
from aero import AeroTracker

tracker = AeroTracker()

try:
    flight = tracker.track_flight("SWR123")
    print(f"{flight.flight_number}: {flight.status}")
    print(f"Route: {flight.origin_code} → {flight.destination_code}")
    print(f"Aircraft: {flight.aircraft_type}")
finally:
    tracker.close()
```

### Monitor Airport Arrivals

```python
with AeroTracker() as tracker:
    arrivals = tracker.get_airport_arrivals("KJFK", hours_ahead=2)
    
    for flight in arrivals:
        print(f"{flight.flight_number} from {flight.origin_code}")
        print(f"  Scheduled: {flight.scheduled_arrival}")
        print(f"  Gate: {flight.gate}")
```

### Search Flights

```python
with AeroTracker() as tracker:
    flights = tracker.search_flights(
        origin="KJFK",
        destination="KLAX",
        date="2024-06-15"
    )
    
    for flight in flights:
        print(f"{flight.flight_number}: {flight.scheduled_departure}")
```

## Project Structure

```
aero/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── flightaware_client.py    # FlightAware API client
│   └── aero_tracker.py          # Main tracking system
├── tests/
│   ├── test_flightaware_client.py
│   └── test_aero_tracker.py
├── docs/
│   ├── API_SETUP.md             # API key setup guide
│   └── USAGE.md                 # Detailed usage guide
├── config/
│   └── example_config.json      # Example configuration
└── README.md                    # This file
```

## API Reference

### AeroTracker

Main class for flight tracking operations.

```python
AeroTracker(api_key=None, config_path=None)
```

**Methods:**

- `track_flight(flight_number, date=None)` - Start tracking a flight
- `update_flight(flight_number)` - Update tracked flight data
- `get_airport_arrivals(airport_code, hours_ahead=2, hours_behind=1)` - Get airport arrivals
- `get_airport_departures(airport_code, hours_ahead=2, hours_behind=1)` - Get airport departures
- `search_flights(origin=None, destination=None, flight_number=None, date=None)` - Search flights
- `get_flight_position(flight_number)` - Get current position
- `on_update(callback)` - Register update callback
- `stop_tracking(flight_number)` - Stop tracking a flight

### TrackedFlight

Data class representing a tracked flight.

**Properties:**

- `flight_number` - Flight identifier
- `airline` - Airline name
- `origin_code` - Origin airport code
- `destination_code` - Destination airport code
- `status` - Current status (scheduled, active, delayed, landed)
- `is_delayed` - Boolean indicating delay status
- `is_active` - Boolean indicating if in flight
- `is_completed` - Boolean indicating if landed
- `delay_minutes` - Delay in minutes (if delayed)
- `position` - Current position dict (if available)

## Error Handling

```python
from aero import (
    AeroTracker,
    FlightAwareError,
    FlightAwareAuthError,
    FlightAwareRateLimitError,
    FlightAwareNotFoundError
)

try:
    tracker = AeroTracker()
    flight = tracker.track_flight("UA123")
except FlightAwareAuthError:
    print("Invalid API key")
except FlightAwareRateLimitError:
    print("Rate limit exceeded")
except FlightAwareNotFoundError:
    print("Flight not found")
except FlightAwareError as e:
    print(f"API error: {e}")
```

## Testing

Run the test suite:

```bash
cd /home/ubuntu/.openclaw/workspace/aero
python -m pytest tests/ -v
```

Or run individual test files:

```bash
python -m unittest tests.test_flightaware_client -v
python -m unittest tests.test_aero_tracker -v
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AEROAPI_KEY` | Your FlightAware API key |

### Config File Format

```json
{
  "api_key": "your_api_key_here"
}
```

## Rate Limiting

The client includes built-in rate limiting to help stay within FlightAware's limits:

- Minimum 100ms between requests
- Automatic retry with exponential backoff
- Maximum 3 retries for server errors

## Supported FlightAware Endpoints

- `GET /flights` - Search flights
- `GET /flights/{id}` - Flight details
- `GET /flights/{id}/position` - Flight position
- `GET /airports/{code}` - Airport info
- `GET /airports/{code}/flights/arrivals` - Airport arrivals
- `GET /airports/{code}/flights/departures` - Airport departures
- `GET /airports/{code}/delays` - Airport delays

## Documentation

- `docs/API_SETUP.md` - How to obtain and configure your FlightAware API key
- `docs/USAGE.md` - Detailed usage examples and guides

## Requirements

- Python 3.8+
- `requests` library

## License

This project is for personal use with FlightAware AeroAPI.

## Support

- [FlightAware AeroAPI Documentation](https://www.flightaware.com/aeroapi/portal/documentation)
- [FlightAware Support](https://www.flightaware.com/commercial/support/)

## Changelog

### v1.0.0
- Initial release
- FlightAware AeroAPI v4 integration
- Real-time flight tracking
- Airport arrivals/departures
- Flight position data
- Rate limiting and error handling
