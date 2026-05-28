# Aero Flight Tracking System - Usage Guide

Complete guide for using the Aero flight tracking system with FlightAware API integration.

## Quick Start

```python
from aero import AeroTracker

# Initialize tracker (reads API key from environment or config)
with AeroTracker() as tracker:
    # Track a flight
    flight = tracker.track_flight("UA123")
    print(f"Status: {flight.status}")
    print(f"From: {flight.origin_name}")
    print(f"To: {flight.destination_name}")
```

## Basic Usage

### Tracking a Flight

```python
from aero import AeroTracker

tracker = AeroTracker()

# Track by flight number
try:
    flight = tracker.track_flight("SWR123")
    
    print(f"Flight: {flight.flight_number}")
    print(f"Airline: {flight.airline}")
    print(f"Status: {flight.status}")
    print(f"Aircraft: {flight.aircraft_type}")
    
    # Check if delayed
    if flight.is_delayed:
        print(f"⚠️ Delayed by {flight.delay_minutes} minutes")
    
    # Check if in the air
    if flight.is_active:
        print(f"✈️ Currently at {flight.progress_percent}% of route")
        
except FlightAwareNotFoundError:
    print("Flight not found")
except FlightAwareError as e:
    print(f"Error: {e}")

tracker.close()
```

### Tracking with Specific Date

```python
# Track a flight on a specific date
flight = tracker.track_flight("UA123", date="2024-06-15")
```

### Getting Flight Position

```python
# Get real-time position
position = tracker.get_flight_position("UA123")

if position:
    print(f"Location: {position['latitude']}, {position['longitude']}")
    print(f"Altitude: {position['altitude']} feet")
    print(f"Speed: {position['ground_speed']} knots")
    print(f"Heading: {position['heading']}°")
```

## Airport Operations

### Get Airport Arrivals

```python
from datetime import datetime

# Get arrivals at JFK for the next 2 hours
arrivals = tracker.get_airport_arrivals(
    airport_code="KJFK",
    hours_ahead=2,
    hours_behind=1
)

print(f"Found {len(arrivals)} arrivals")

for flight in arrivals:
    print(f"{flight.flight_number} from {flight.origin_code}")
    print(f"  Scheduled: {flight.scheduled_arrival}")
    print(f"  Estimated: {flight.estimated_arrival}")
    print(f"  Status: {flight.status}")
    print(f"  Gate: {flight.gate}")
    print()
```

### Get Airport Departures

```python
# Get departures from LAX
departures = tracker.get_airport_departures(
    airport_code="KLAX",
    hours_ahead=2
)

for flight in departures:
    print(f"{flight.flight_number} to {flight.destination_code}")
    print(f"  Departure: {flight.scheduled_departure}")
    print(f"  Terminal: {flight.terminal}, Gate: {flight.gate}")
```

## Advanced Usage

### Search Flights

```python
# Search flights between airports
flights = tracker.search_flights(
    origin="KJFK",
    destination="KLAX",
    date="2024-06-15"
)

for flight in flights:
    print(f"{flight.flight_number}: {flight.scheduled_departure} - {flight.status}")
```

### Update Tracking

```python
# Update a tracked flight with latest data
updated_flight = tracker.update_flight("UA123")

print(f"Last updated: {updated_flight.last_updated}")
print(f"Current status: {updated_flight.status}")
```

### Track Multiple Flights

```python
# Track multiple flights
flight_numbers = ["UA123", "AA456", "DL789"]
tracked = {}

for number in flight_numbers:
    try:
        tracked[number] = tracker.track_flight(number)
        print(f"✓ Tracking {number}")
    except FlightAwareNotFoundError:
        print(f"✗ {number} not found")

# Get all tracked flights
all_tracked = tracker.get_tracked_flights()
for number, flight in all_tracked.items():
    print(f"{number}: {flight.status}")

# Stop tracking
tracker.stop_tracking("UA123")
```

### Update Callbacks

```python
# Register a callback for flight updates
def on_flight_update(flight):
    print(f"🔄 {flight.flight_number} updated!")
    print(f"   Status: {flight.status}")
    
    if flight.is_delayed:
        print(f"   ⚠️ Now delayed by {flight.delay_minutes} min")

tracker.on_update(on_flight_update)

# When update_flight is called, the callback will fire
tracker.update_flight("UA123")
```

## Working with Flight Data

### Flight Status Properties

```python
flight = tracker.track_flight("UA123")

# Status checks
print(f"Is active: {flight.is_active}")       # Currently in the air
print(f"Is delayed: {flight.is_delayed}")     # Has a significant delay
print(f"Is completed: {flight.is_completed}") # Has landed

# Delay information
if flight.delay_minutes:
    print(f"Delay: {flight.delay_minutes} minutes")

# Progress
if flight.progress_percent:
    print(f"Route progress: {flight.progress_percent}%")
```

### Export Flight Data

```python
import json

flight = tracker.track_flight("UA123")

# Convert to dictionary
flight_dict = flight.to_dict()

# Save to file
with open('flight_data.json', 'w') as f:
    json.dump(flight_dict, f, indent=2)

# Or process programmatically
print(json.dumps(flight_dict, indent=2))
```

## Error Handling

```python
from aero import (
    AeroTracker,
    FlightAwareError,
    FlightAwareAuthError,
    FlightAwareRateLimitError,
    FlightAwareNotFoundError
)

tracker = AeroTracker()

try:
    flight = tracker.track_flight("UA123")
    
except FlightAwareAuthError:
    print("❌ Invalid API key. Check your configuration.")
    
except FlightAwareRateLimitError:
    print("⏳ Rate limit exceeded. Please wait before trying again.")
    
except FlightAwareNotFoundError:
    print("🔍 Flight not found. Check the flight number.")
    
except FlightAwareError as e:
    print(f"❌ API Error: {e}")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    
finally:
    tracker.close()
```

## Context Manager Usage

The recommended way to use the tracker is with a context manager:

```python
from aero import AeroTracker

with AeroTracker() as tracker:
    # Track flights
    flight1 = tracker.track_flight("UA123")
    flight2 = tracker.track_flight("AA456")
    
    # Get airport data
    arrivals = tracker.get_airport_arrivals("KJFK")
    
# Tracker is automatically closed when exiting the context
```

## Common Airport Codes

### Major US Airports
| Code | Airport | City |
|------|---------|------|
| KJFK | John F. Kennedy International | New York |
| KLAX | Los Angeles International | Los Angeles |
| KORD | Chicago O'Hare International | Chicago |
| KDFW | Dallas/Fort Worth International | Dallas |
| KDEN | Denver International | Denver |
| KSFO | San Francisco International | San Francisco |
| KSEA | Seattle-Tacoma International | Seattle |
| KMIA | Miami International | Miami |
| KATL | Hartsfield-Jackson Atlanta | Atlanta |
| KBOS | Boston Logan International | Boston |

### European Airports
| Code | Airport | City |
|------|---------|------|
| EGLL | London Heathrow | London |
| LFPG | Paris Charles de Gaulle | Paris |
| EDDF | Frankfurt Airport | Frankfurt |
| EHAM | Amsterdam Schiphol | Amsterdam |
| LEMD | Madrid-Barajas | Madrid |
| LSZH | Zurich Airport | Zurich |
| LSGG | Geneva Airport | Geneva |

### Asian Airports
| Code | Airport | City |
|------|---------|------|
| RJTT | Tokyo Haneda | Tokyo |
| VHHH | Hong Kong International | Hong Kong |
| WSSS | Singapore Changi | Singapore |
| OMDB | Dubai International | Dubai |
| VIDP | Indira Gandhi International | Delhi |

## Tips and Best Practices

1. **Use ICAO codes** (4 letters like KJFK) instead of IATA codes (3 letters like JFK) for best results

2. **Handle rate limits gracefully** - The client has built-in retry logic, but you should still handle rate limit errors

3. **Cache results** - Don't make the same API call repeatedly within a short time

4. **Use context managers** - Ensures proper cleanup of resources

5. **Check flight status before accessing position** - Not all flights have position data

6. **Handle timezone conversions** - API returns times in UTC

## Example: Complete Flight Monitor

```python
#!/usr/bin/env python3
"""
Example: Complete flight monitoring script
"""

from aero import AeroTracker, FlightAwareError
from datetime import datetime
import time

def monitor_flight(flight_number: str, interval: int = 300):
    """
    Monitor a flight until it lands.
    
    Args:
        flight_number: Flight number to monitor
        interval: Update interval in seconds (default: 5 minutes)
    """
    with AeroTracker() as tracker:
        print(f"🔍 Starting to monitor {flight_number}")
        print(f"⏱️  Updates every {interval} seconds")
        print("-" * 50)
        
        # Initial track
        flight = tracker.track_flight(flight_number)
        
        print(f"✈️  {flight.flight_number}")
        print(f"   {flight.origin_name} → {flight.destination_name}")
        print(f"   Scheduled departure: {flight.scheduled_departure}")
        print(f"   Scheduled arrival: {flight.scheduled_arrival}")
        print()
        
        while not flight.is_completed:
            try:
                # Update flight data
                flight = tracker.update_flight(flight_number)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if flight.is_active:
                    pos = tracker.get_flight_position(flight_number)
                    if pos:
                        print(f"[{timestamp}] ✈️ In flight")
                        print(f"           Position: {pos['latitude']:.2f}, {pos['longitude']:.2f}")
                        print(f"           Altitude: {pos['altitude']} ft")
                        print(f"           Speed: {pos['ground_speed']} kts")
                        print(f"           Progress: {flight.progress_percent}%")
                
                elif flight.is_delayed:
                    print(f"[{timestamp}] ⏰ Delayed by {flight.delay_minutes} minutes")
                
                else:
                    print(f"[{timestamp}] 📋 Status: {flight.status}")
                
                print()
                
                # Wait before next update
                if not flight.is_completed:
                    time.sleep(interval)
                    
            except FlightAwareError as e:
                print(f"[{timestamp}] Error: {e}")
                time.sleep(interval)
        
        print("-" * 50)
        print(f"✅ Flight {flight_number} has landed!")
        print(f"   Actual arrival: {flight.actual_arrival}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python monitor.py <flight_number>")
        print("Example: python monitor.py UA123")
        sys.exit(1)
    
    flight_number = sys.argv[1]
    monitor_flight(flight_number)
```

## See Also

- `API_SETUP.md` - How to get and configure your API key
- `README.md` - Project overview and installation
