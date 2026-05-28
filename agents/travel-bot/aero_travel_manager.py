#!/usr/bin/env python3
"""
Aero Travel Manager - Complete travel automation with FlightAware integration
Handles: trip detection, smart task creation, day-of-travel monitoring, alerts
"""

import json
import subprocess
import re
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict

# Paths
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "aero-travel-manager.log"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "aero-travel-state.json"
FLIGHT_DATA_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "aero-tracked-flights.json"
CONFIG_PATH = Path(__file__).parent / "config.json"
TODOIST_PATH = "/home/ubuntu/.npm-global/bin/todoist"

# Constants
TRAVEL_KEYWORDS = ['flight', 'delta', 'united', 'american', 'alaska', 'jetblue', 
                   'southwest', 'hotel', 'stay at', 'trip to', 'travel to']
HOME_AIRPORTS = ['LAX', 'BUR', 'VNY', 'LGB', 'ONT']  # SoCal airports


@dataclass
class FlightStatus:
    """Flight status from FlightAware"""
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
    departure_terminal: Optional[str]
    arrival_terminal: Optional[str]
    status: str
    aircraft_type: Optional[str]
    delay_minutes: int
    progress_percent: Optional[int]
    altitude: Optional[int]
    groundspeed: Optional[int]
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert datetime objects to strings for JSON serialization
        for key in ['scheduled_departure', 'estimated_departure', 
                    'scheduled_arrival', 'estimated_arrival']:
            if isinstance(result[key], datetime):
                result[key] = result[key].isoformat()
        return result


class FlightAwareClient:
    """Client for FlightAware AeroAPI v4"""
    
    def __init__(self):
        self.config = self._load_config()
        self.api_key = self.config.get("flightaware", {}).get("api_key")
        self.base_url = "https://aeroapi.flightaware.com/aeroapi"
        
        if not self.api_key:
            raise ValueError("FlightAware API key not configured")
    
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
        """Get current status of a flight"""
        try:
            url = f"{self.base_url}/flights/{flight_number}"
            if date:
                url += f"?start={date}T00:00:00Z&end={date}T23:59:59Z"
            
            response = requests.get(url, headers=self._headers(), timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("flights"):
                return None
            
            flight = data["flights"][0]
            return self._parse_flight_data(flight)
            
        except requests.exceptions.RequestException as e:
            log(f"FlightAware API error: {e}")
            return None
    
    def get_airport_delays(self, airport_code: str) -> Dict:
        """Get current delays and status for an airport"""
        try:
            url = f"{self.base_url}/airports/{airport_code}/delays"
            response = requests.get(url, headers=self._headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log(f"Error fetching airport delays: {e}")
            return {}
    
    def _parse_flight_data(self, flight: Dict) -> FlightStatus:
        """Parse FlightAware flight data into FlightStatus"""
        origin = flight.get("origin", {})
        destination = flight.get("destination", {})
        
        return FlightStatus(
            flight_number=flight.get("ident", "Unknown"),
            airline=flight.get("operator", "Unknown"),
            origin=origin.get("code", "Unknown"),
            destination=destination.get("code", "Unknown"),
            scheduled_departure=self._parse_datetime(flight.get("scheduled_out")),
            estimated_departure=self._parse_datetime(flight.get("estimated_out")),
            scheduled_arrival=self._parse_datetime(flight.get("scheduled_in")),
            estimated_arrival=self._parse_datetime(flight.get("estimated_in")),
            departure_gate=flight.get("gate_origin"),
            arrival_gate=flight.get("gate_destination"),
            departure_terminal=origin.get("terminal"),
            arrival_terminal=destination.get("terminal"),
            status=self._map_status(flight.get("status", "unknown")),
            aircraft_type=flight.get("aircraft_type"),
            delay_minutes=self._calculate_delay(flight),
            progress_percent=flight.get("progress_percent"),
            altitude=flight.get("altitude"),
            groundspeed=flight.get("groundspeed")
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> datetime:
        """Parse ISO datetime string"""
        if not dt_str:
            return datetime.now()
        try:
            dt_str = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(dt_str)
        except:
            return datetime.now()
    
    def _map_status(self, fa_status: str) -> str:
        """Map FlightAware status to our status"""
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
        """Calculate delay in minutes"""
        scheduled_out = flight.get("scheduled_out")
        estimated_out = flight.get("estimated_out")
        
        if scheduled_out and estimated_out:
            sched = self._parse_datetime(scheduled_out)
            est = self._parse_datetime(estimated_out)
            delay = (est - sched).total_seconds() / 60
            return max(0, int(delay))
        return 0


def log(msg: str):
    """Log to console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}", flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")


def load_calendar() -> Optional[Dict]:
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)


def load_state() -> Dict:
    """Load processed trips state"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'processed_trips': [],
        'processed_tasks': [],  # Track individual tasks too
        'version': '2.0'
    }


def save_state(state: Dict):
    """Save processed trips state"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def load_tracked_flights() -> Dict:
    """Load currently tracked flights with their last known status"""
    if FLIGHT_DATA_FILE.exists():
        with open(FLIGHT_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_tracked_flights(flights: Dict):
    """Save tracked flights"""
    FLIGHT_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FLIGHT_DATA_FILE, 'w') as f:
        json.dump(flights, f, indent=2)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from calendar"""
    if not date_str:
        return None
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None


def is_travel_event(event: Dict) -> bool:
    """Check if event is travel-related"""
    summary = event.get('summary', '').lower()
    return any(kw in summary for kw in TRAVEL_KEYWORDS) or event.get('is_travel')


def extract_flight_info(event: Dict) -> Dict:
    """Extract flight number and confirmation from event"""
    summary = event.get('summary', '')
    description = event.get('description', '')
    
    flight_num = None
    airline_code = 'DL'  # Default to Delta
    
    # Pattern 1: "DL 4099" or "(DL 4099)"
    match = re.search(r'\(?(DL|UA|AA|AS|B6|WN)\s*(\d+)\)?', summary, re.IGNORECASE)
    if match:
        airline_code = match.group(1).upper()
        flight_num = f"{airline_code}{match.group(2)}"
    
    # Pattern 2: "Delta Air Lines flight 960"
    if not flight_num:
        match = re.search(r'Delta\s+(?:Air\s+)?(?:Lines?\s+)?(?:flight\s+)?(\d+)', summary, re.IGNORECASE)
        if match:
            flight_num = f"DL{match.group(1)}"
    
    # Pattern 3: "United flight 123"
    if not flight_num:
        match = re.search(r'United\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', summary, re.IGNORECASE)
        if match:
            airline_code = 'UA'
            flight_num = f"UA{match.group(1)}"
    
    # Pattern 4: "American flight 123"
    if not flight_num:
        match = re.search(r'American\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', summary, re.IGNORECASE)
        if match:
            airline_code = 'AA'
            flight_num = f"AA{match.group(1)}"
    
    # Extract confirmation code (6 char alphanumeric)
    confirmation = None
    text = f"{summary} {description}"
    match = re.search(r'\b([A-Z0-9]{6})\b', text)
    if match:
        potential = match.group(1)
        # Filter out common non-confirmation patterns
        if potential not in ['FLIGHT', 'DELTA', 'UNITED', 'TRAVEL']:
            confirmation = potential
    
    return {
        'flight': flight_num,
        'airline': airline_code,
        'confirmation': confirmation
    }


def extract_destination(event: Dict) -> str:
    """Extract destination city from event"""
    location = event.get('location', '')
    summary = event.get('summary', '')
    description = event.get('description', '')
    
    # Check summary for "Flight to [Destination]" pattern
    flight_to_match = re.search(r'Flight\s+to\s+([A-Za-z\s]+?)(?:\s+\(|\s*-|\s*$)', summary, re.IGNORECASE)
    if flight_to_match:
        dest = flight_to_match.group(1).strip()
        airport_map = {
            'RNO': 'Reno', 'LAX': 'Los Angeles', 'SFO': 'San Francisco',
            'SJC': 'San Jose', 'JFK': 'NYC', 'LGA': 'NYC', 'EWR': 'NYC',
            'PDX': 'Portland', 'SEA': 'Seattle', 'LAS': 'Las Vegas',
            'PHX': 'Phoenix', 'DEN': 'Denver', 'ORD': 'Chicago',
            'DFW': 'Dallas', 'MIA': 'Miami', 'BOS': 'Boston',
            'DCA': 'DC', 'IAD': 'DC', 'BUR': 'Burbank', 'VNY': 'Van Nuys',
            'LGB': 'Long Beach', 'ONT': 'Ontario'
        }
        dest_upper = dest.upper()
        if dest_upper in airport_map:
            return airport_map[dest_upper]
        return dest
    
    # Check location for "Departure - Arrival" format
    if '-' in location:
        parts = location.split('-')
        if len(parts) >= 2:
            arrival = parts[1].strip()
            city_match = arrival.split('(')[0].strip()
            if city_match and 'detailed information' not in city_match.lower():
                return city_match
    
    # Check for common destinations
    text = f"{location} {summary} {description}".lower()
    
    if 'new york' in text or 'jfk' in text or 'lga' in text or 'ewr' in text:
        return 'NYC'
    if 'reno' in text or 'rno' in text or 'tahoe' in text:
        return 'Tahoe'
    if 'san jose' in text or 'sjc' in text:
        return 'San Jose'
    if 'palo alto' in text:
        return 'Palo Alto'
    if 'portland' in text or 'pdx' in text:
        return 'Portland'
    if 'san francisco' in text or 'sfo' in text:
        return 'San Francisco'
    if 'los angeles' in text or 'lax' in text:
        if 'from' in text and ('lax' in text.split('from')[1] or 'los angeles' in text.split('from')[1]):
            return 'Los Angeles'
    
    if location:
        parts = location.split(',')
        if parts:
            loc = parts[0].strip()
            if 'detailed information' not in loc.lower():
                return loc
    
    return 'Trip'


def is_return_flight(event: Dict) -> bool:
    """Check if this is a return flight to LAX/Burbank (end of trip)"""
    location = event.get('location', '')
    summary = event.get('summary', '')
    
    text = f"{location} {summary}".lower()
    
    if '-' in location:
        parts = location.split('-')
        if len(parts) >= 2:
            arrival = parts[1].strip().lower()
            if any(ap in arrival for ap in ['lax', 'los angeles', 'burbank', 'bur']):
                return True
    
    if re.search(r'to\s+(Los Angeles|LAX|Burbank|BUR)', summary, re.IGNORECASE):
        return True
    
    return False


def is_outbound_from_home(event: Dict) -> bool:
    """Check if flight departs from home airport (LAX/BUR/etc)"""
    location = event.get('location', '')
    summary = event.get('summary', '')
    
    text = f"{location} {summary}".lower()
    
    # Check if departing from home airport
    for airport in ['lax', 'burbank', 'bur', 'van nuys', 'vny', 'long beach', 'lgb', 'ontario', 'ont']:
        if airport in text:
            return True
    
    return False


def get_all_tasks(project: str = "Travel") -> List[Dict]:
    """Get all tasks from Todoist including completed ones"""
    try:
        result = subprocess.run(
            [TODOIST_PATH, "tasks", "-p", project, "--all", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []
    except Exception as e:
        log(f"Could not fetch tasks from Todoist: {e}")
        return []


def get_existing_task_names(project: str = "Travel") -> Set[str]:
    """Get set of existing task names (both active and completed)"""
    tasks = get_all_tasks(project)
    return {task.get('content', '').lower() for task in tasks}


def task_exists(task_name: str, existing_tasks: Set[str]) -> bool:
    """Smart task existence check with fuzzy matching"""
    task_lower = task_name.lower()
    
    # Exact match
    if task_lower in existing_tasks:
        return True
    
    # For Uber tasks, check if similar task exists for same flight
    if "uber" in task_lower:
        flight_match = re.search(r'(DL|UA|AA|AS|B6|WN)\d+', task_lower)
        if flight_match:
            flight_num = flight_match.group(0)
            for existing in existing_tasks:
                if flight_num in existing and "uber" in existing:
                    return True
    
    # For pack tasks, check if any pack task exists for similar timeframe
    if "pack" in task_lower:
        for existing in existing_tasks:
            if "pack" in existing:
                return True
    
    return False


def create_task(text: str, project: str = "Travel", due: Optional[str] = None, 
                parent_id: Optional[str] = None, existing_tasks: Optional[Set[str]] = None) -> Optional[str]:
    """Create a task and return its ID"""
    try:
        # Check if task already exists
        if existing_tasks and task_exists(text, existing_tasks):
            log(f"  Already exists: {text[:60]}")
            return None
        
        cmd = [TODOIST_PATH, "add", text, "-p", project, "-P", "2"]
        if due:
            cmd.extend(["-d", due])
        if parent_id:
            cmd.extend(["--parent", parent_id])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            if "already exists" in result.stderr.lower():
                return None
            log(f"  Failed to create: {text[:50]} - {result.stderr}")
            return None
        
        # Extract task ID
        match = re.search(r'ID:\s+(\w+)', result.stdout)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        log(f"  Error creating task: {e}")
        return None


def get_hotel_stays(calendar_data: Dict) -> List[Dict]:
    """Extract hotel stay events from calendar"""
    hotels = []
    hotel_keywords = ['stay at', 'hotel', 'westin', 'ritz', 'marriott', 'hilton', 'four seasons']
    
    for event in calendar_data.get('events', []):
        summary = event.get('summary', '').lower()
        if any(kw in summary for kw in hotel_keywords):
            event_date = parse_date(event.get('start_raw', ''))
            if event_date:
                location = extract_destination(event)
                hotels.append({
                    'event': event,
                    'date': event_date,
                    'location': location
                })
    
    return sorted(hotels, key=lambda x: x['date'])


def group_events_by_trip(events: List[Dict], calendar_data: Dict) -> List[Dict]:
    """Group flight events into trips using hotel stays as anchors"""
    if not events:
        return []
    
    hotel_stays = get_hotel_stays(calendar_data)
    
    # Sort flights by date
    flights = sorted([e for e in events if extract_flight_info(e).get('flight')], 
                     key=lambda x: parse_date(x.get('start_raw', '')) or datetime.now())
    
    trips = []
    used_flights = set()
    current_trip_flights = []
    current_trip_destination = None
    
    for flight in flights:
        flight_date = parse_date(flight.get('start_raw', ''))
        if not flight_date:
            continue
        
        flight_id = flight.get('summary', '') + flight.get('start_raw', '')
        if flight_id in used_flights:
            continue
        
        flight_dest = extract_destination(flight)
        is_return = is_return_flight(flight)
        
        # Find closest hotel within 4 days
        closest_hotel = None
        closest_days = 5
        for hotel in hotel_stays:
            days_from_hotel = abs((flight_date - hotel['date']).days)
            if days_from_hotel <= 4 and hotel['location'] != 'Trip':
                if days_from_hotel < closest_days:
                    closest_days = days_from_hotel
                    closest_hotel = hotel
        
        if closest_hotel:
            flight_dest = closest_hotel['location']
        
        if not current_trip_flights:
            current_trip_flights = [flight]
            current_trip_destination = flight_dest if flight_dest != 'Trip' else 'Trip'
        elif is_return:
            current_trip_flights.append(flight)
            trips.append({
                'events': current_trip_flights,
                'start_date': parse_date(current_trip_flights[0].get('start_raw', '')),
                'end_date': flight_date,
                'destination': current_trip_destination
            })
            for f in current_trip_flights:
                used_flights.add(f.get('summary', '') + f.get('start_raw', ''))
            current_trip_flights = []
            current_trip_destination = None
        else:
            current_trip_flights.append(flight)
            if flight_dest != 'Trip' and current_trip_destination == 'Trip':
                current_trip_destination = flight_dest
    
    # Handle remaining flights
    if current_trip_flights:
        trips.append({
            'events': current_trip_flights,
            'start_date': parse_date(current_trip_flights[0].get('start_raw', '')),
            'end_date': parse_date(current_trip_flights[-1].get('start_raw', '')),
            'destination': current_trip_destination
        })
        for f in current_trip_flights:
            used_flights.add(f.get('summary', '') + f.get('start_raw', ''))
    
    # Handle remaining ungrouped flights
    remaining_flights = [f for f in flights 
                        if (f.get('summary', '') + f.get('start_raw', '')) not in used_flights]
    
    if remaining_flights:
        remaining_flights.sort(key=lambda x: parse_date(x.get('start_raw', '')) or datetime.now())
        current_trip = None
        
        for flight in remaining_flights:
            flight_date = parse_date(flight.get('start_raw', ''))
            if not flight_date:
                continue
            
            flight_dest = extract_destination(flight)
            
            if current_trip is None or (flight_date - current_trip['end_date']).days > 2:
                if current_trip:
                    trips.append(current_trip)
                current_trip = {
                    'events': [flight],
                    'start_date': flight_date,
                    'end_date': flight_date,
                    'destination': flight_dest if flight_dest != 'Trip' else 'Trip'
                }
            else:
                current_trip['events'].append(flight)
                current_trip['end_date'] = flight_date
                if flight_dest != 'Trip':
                    current_trip['destination'] = flight_dest
        
        if current_trip:
            trips.append(current_trip)
    
    trips.sort(key=lambda x: x['start_date'])
    return trips


def get_trip_id(trip: Dict) -> str:
    """Generate unique ID for a trip"""
    events = trip.get('events', [])
    if not events:
        return ""
    first = events[0]
    summary = first.get('summary', '')
    date = first.get('start_raw', '')
    return f"{summary}_{date}"


def process_trip(trip: Dict, existing_tasks: Set[str], state: Dict, 
                 fa_client: Optional[FlightAwareClient] = None) -> int:
    """Process a single trip and create tasks"""
    created_count = 0
    processed_trips = state.get('processed_trips', [])
    processed_tasks = state.get('processed_tasks', [])
    
    first_event = trip['events'][0]
    first_date = trip['start_date']
    flight_info = extract_flight_info(first_event)
    
    destination = trip['destination']
    date_str = first_date.strftime('%b %d')
    flight_str = flight_info.get('flight', 'Flight')
    conf_str = flight_info.get('confirmation', '')
    
    # Main task name
    main_task_name = f"Tasks for {destination} Trip on {date_str}"
    if flight_str and flight_str != 'Flight':
        main_task_name += f" - {flight_str}"
    if conf_str:
        main_task_name += f" {conf_str}"
    
    trip_id = get_trip_id(trip)
    
    # DUPLICATE DETECTION: Check state first
    if trip_id and trip_id in processed_trips:
        log(f"  ✓ Trip already processed (state): {main_task_name[:60]}")
        return 0
    
    # Check if main task exists
    if main_task_name.lower() in existing_tasks:
        log(f"  ✓ Task already exists (Todoist): {main_task_name[:60]}")
        if trip_id:
            processed_trips.append(trip_id)
        return 0
    
    # Fuzzy match
    trip_pattern = f"tasks for {destination.lower()} trip on {date_str.lower()}"
    for existing in existing_tasks:
        if trip_pattern in existing:
            log(f"  ✓ Similar trip found (fuzzy): {existing[:60]}")
            if trip_id:
                processed_trips.append(trip_id)
            return 0
    
    # Create main task
    log(f"Creating: {main_task_name}")
    parent_id = create_task(main_task_name, due=first_date.strftime('%Y-%m-%d'), 
                           existing_tasks=existing_tasks)
    if not parent_id:
        log(f"  Could not create main task")
        return 0
    
    created_count += 1
    existing_tasks.add(main_task_name.lower())
    if trip_id:
        processed_trips.append(trip_id)
    
    # Create subtasks
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Pack task - due day before
    pack_due = (first_date - timedelta(days=1)).strftime('%Y-%m-%d')
    pack_text = "└── 🧳 Pack"
    if pack_text.lower() not in processed_tasks:
        pack_task = create_task(pack_text, due=pack_due, parent_id=parent_id, 
                               existing_tasks=existing_tasks)
        if pack_task:
            created_count += 1
            processed_tasks.append(pack_text.lower())
            log(f"  Created: └── 🧳 Pack (due {pack_due})")
    
    # 2. Contact Marriott Ambassador - due 7 days before
    marriott_due = (first_date - timedelta(days=7)).strftime('%Y-%m-%d')
    marriott_text = "└── 🏢 Contact Marriott Ambassador about hotel"
    if marriott_text.lower() not in processed_tasks:
        marriott_task = create_task(marriott_text, due=marriott_due, parent_id=parent_id,
                                   existing_tasks=existing_tasks)
        if marriott_task:
            created_count += 1
            processed_tasks.append(marriott_text.lower())
            log(f"  Created: └── 🏢 Contact Marriott Ambassador (due {marriott_due})")
    
    # 3. Schedule Rover - only for outbound flights from home
    # Check if first flight is outbound from LAX/Burbank
    if is_outbound_from_home(first_event):
        rover_text = "└── 🐕 Schedule Rover for Greta"
        if rover_text.lower() not in processed_tasks:
            rover_task = create_task(rover_text, due=today, parent_id=parent_id,
                                   existing_tasks=existing_tasks)
            if rover_task:
                created_count += 1
                processed_tasks.append(rover_text.lower())
                log(f"  Created: └── 🐕 Schedule Rover (due today)")
    
    # 4. Schedule Uber for each flight leg
    for event in trip['events']:
        event_date = parse_date(event.get('start_raw', ''))
        if not event_date:
            continue
        
        flight_info = extract_flight_info(event)
        flight_str = flight_info.get('flight')
        
        if not flight_str:
            continue
        
        flight_dest = extract_destination(event)
        uber_due = (event_date - timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Determine if this is to airport or from airport
        if is_outbound_from_home(event):
            uber_text = f"└── 🚗 Schedule Uber TO airport for {flight_str} to {flight_dest}"
        else:
            uber_text = f"└── 🚗 Schedule Uber FROM airport for {flight_str} from {flight_dest}"
        
        if uber_text.lower() not in processed_tasks:
            uber_task = create_task(uber_text, due=uber_due, parent_id=parent_id,
                                   existing_tasks=existing_tasks)
            if uber_task:
                created_count += 1
                processed_tasks.append(uber_text.lower())
                log(f"  Created: {uber_text[:60]} (due {uber_due})")
    
    log(f"  Marked trip as processed: {trip_id}")
    return created_count


def check_flight_changes(flight_number: str, current_status: FlightStatus, 
                        tracked_flights: Dict) -> List[str]:
    """Check for changes in flight status and return alerts"""
    alerts = []
    flight_id = f"{flight_number}_{current_status.scheduled_departure.strftime('%Y%m%d')}"
    
    if flight_id not in tracked_flights:
        # New flight being tracked
        return []
    
    previous = tracked_flights[flight_id]
    
    # Check for gate changes
    prev_departure_gate = previous.get('departure_gate')
    curr_departure_gate = current_status.departure_gate
    if prev_departure_gate != curr_departure_gate and curr_departure_gate:
        if prev_departure_gate:
            alerts.append(f"🔄 GATE CHANGE: Departure gate changed from {prev_departure_gate} to {curr_departure_gate}")
        else:
            alerts.append(f"📍 GATE ASSIGNED: Departure gate is now {curr_departure_gate}")
    
    # Check for arrival gate changes
    prev_arrival_gate = previous.get('arrival_gate')
    curr_arrival_gate = current_status.arrival_gate
    if prev_arrival_gate != curr_arrival_gate and curr_arrival_gate:
        if prev_arrival_gate:
            alerts.append(f"🔄 ARRIVAL GATE CHANGE: Arrival gate changed from {prev_arrival_gate} to {curr_arrival_gate}")
        else:
            alerts.append(f"📍 ARRIVAL GATE ASSIGNED: Arrival gate is now {curr_arrival_gate}")
    
    # Check for terminal changes
    prev_terminal = previous.get('departure_terminal')
    curr_terminal = current_status.departure_terminal
    if prev_terminal != curr_terminal and curr_terminal:
        alerts.append(f"🔄 TERMINAL CHANGE: Now departing from Terminal {curr_terminal}")
    
    # Check for delays
    prev_delay = previous.get('delay_minutes', 0)
    curr_delay = current_status.delay_minutes
    if curr_delay > prev_delay and curr_delay >= 15:
        alerts.append(f"⏰ DELAY ALERT: Flight delayed by {curr_delay} minutes")
    
    # Check for status changes
    prev_status = previous.get('status', 'unknown')
    curr_status = current_status.status
    if prev_status != curr_status:
        if curr_status == 'cancelled':
            alerts.append(f"🚨 FLIGHT CANCELLED: {flight_number} has been cancelled")
        elif curr_status == 'delayed':
            alerts.append(f"⏰ STATUS: Flight now showing as DELAYED")
    
    return alerts


def monitor_day_of_travel(fa_client: FlightAwareClient) -> Dict:
    """Monitor flights departing today and send alerts for changes"""
    log("=" * 70)
    log("Aero: Day-of-Travel Monitoring")
    log("=" * 70)
    
    calendar = load_calendar()
    if not calendar:
        log("No calendar data found")
        return {'alerts_sent': 0, 'flights_checked': 0}
    
    tracked_flights = load_tracked_flights()
    today = datetime.now().date()
    alerts_sent = 0
    flights_checked = 0
    
    # Find flights departing today or tomorrow (for early morning flights)
    for event in calendar.get('events', []):
        if not is_travel_event(event):
            continue
        
        flight_info = extract_flight_info(event)
        flight_number = flight_info.get('flight')
        
        if not flight_number:
            continue
        
        event_date = parse_date(event.get('start_raw', ''))
        if not event_date:
            continue
        
        # Check flights departing today or tomorrow
        event_date_only = event_date.date()
        if event_date_only not in [today, today + timedelta(days=1)]:
            continue
        
        flights_checked += 1
        log(f"\n✈️ Checking {flight_number} on {event_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Get current status from FlightAware
        date_str = event_date.strftime('%Y-%m-%d')
        current_status = fa_client.get_flight_status(flight_number, date_str)
        
        if not current_status:
            log(f"  Could not fetch status from FlightAware")
            continue
        
        log(f"  Status: {current_status.status}")
        log(f"  Gate: {current_status.departure_gate or 'Not assigned'}")
        log(f"  Terminal: {current_status.departure_terminal or 'N/A'}")
        log(f"  Delay: {current_status.delay_minutes} minutes")
        
        # Check for changes
        alerts = check_flight_changes(flight_number, current_status, tracked_flights)
        
        if alerts:
            log(f"  🔔 {len(alerts)} alert(s) detected:")
            for alert in alerts:
                log(f"    - {alert}")
            
            # Send alerts
            send_flight_alerts(flight_number, current_status, alerts)
            alerts_sent += len(alerts)
        else:
            log(f"  ✓ No changes detected")
        
        # Update tracked flights
        flight_id = f"{flight_number}_{event_date.strftime('%Y%m%d')}"
        tracked_flights[flight_id] = current_status.to_dict()
    
    # Save updated tracking data
    save_tracked_flights(tracked_flights)
    
    log(f"\n{'=' * 70}")
    log(f"Summary: {flights_checked} flights checked, {alerts_sent} alerts sent")
    log("=" * 70)
    
    return {'alerts_sent': alerts_sent, 'flights_checked': flights_checked}


def send_flight_alerts(flight_number: str, status: FlightStatus, alerts: List[str]):
    """Send flight alerts via email and Telegram"""
    subject = f"✈️ Flight Alert: {flight_number}"
    
    # Build email body
    email_body = f"""<h2>✈️ Flight Alert: {flight_number}</h2>

<p><strong>Flight:</strong> {flight_number}<br>
<strong>Route:</strong> {status.origin} → {status.destination}<br>
<strong>Status:</strong> {status.status.upper()}<br>
<strong>Scheduled:</strong> {status.scheduled_departure.strftime('%I:%M %p')}<br>
<strong>Estimated:</strong> {status.estimated_departure.strftime('%I:%M %p')}</p>

<h3>🚨 Changes Detected:</h3>
<ul>
"""
    for alert in alerts:
        email_body += f"<li>{alert}</li>\n"
    
    email_body += f"""</ul>

<h3>📍 Current Information:</h3>
<p>
<strong>Departure Gate:</strong> {status.departure_gate or 'Not assigned'}<br>
<strong>Departure Terminal:</strong> {status.departure_terminal or 'N/A'}<br>
<strong>Arrival Gate:</strong> {status.arrival_gate or 'Not assigned'}<br>
<strong>Arrival Terminal:</strong> {status.arrival_terminal or 'N/A'}<br>
<strong>Aircraft:</strong> {status.aircraft_type or 'Unknown'}<br>
<strong>Delay:</strong> {status.delay_minutes} minutes
</p>

<p><em>Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}</em></p>
"""
    
    # Send email
    try:
        email_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
        if email_script.exists():
            subprocess.run([
                "python3", str(email_script),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", email_body,
                "--html"
            ], capture_output=True, timeout=30)
            log(f"  📧 Email alert sent")
    except Exception as e:
        log(f"  ⚠️ Failed to send email: {e}")
    
    # Send Telegram
    try:
        telegram_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "telegram_notify.py"
        if telegram_script.exists():
            telegram_text = f"✈️ *{flight_number} Alert*\n\n"
            telegram_text += f"*{status.origin} → {status.destination}*\n"
            telegram_text += f"Status: {status.status.upper()}\n\n"
            telegram_text += "*Changes:*\n"
            for alert in alerts:
                telegram_text += f"• {alert}\n"
            telegram_text += f"\nGate: {status.departure_gate or 'TBD'}"
            
            subprocess.run([
                "python3", str(telegram_script),
                telegram_text
            ], capture_output=True, timeout=30)
            log(f"  📱 Telegram alert sent")
    except Exception as e:
        log(f"  ⚠️ Failed to send Telegram: {e}")


def create_travel_tasks(fa_client: Optional[FlightAwareClient] = None) -> Dict:
    """Main function to create travel tasks with smart duplicate detection"""
    log("=" * 70)
    log("Aero Travel Manager: Creating Travel Tasks")
    log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)
    
    state = load_state()
    processed_trips = state.get('processed_trips', [])
    processed_tasks = state.get('processed_tasks', [])
    
    calendar_data = load_calendar()
    if not calendar_data:
        log("Could not load calendar")
        return {'created': 0, 'trips_processed': 0}
    
    log(f"Calendar loaded: {calendar_data.get('total_events', 0)} events")
    
    # Get travel events in next 60 days
    travel_events = []
    cutoff = datetime.now() + timedelta(days=60)
    for event in calendar_data.get('events', []):
        if is_travel_event(event):
            event_date = parse_date(event.get('start_raw', ''))
            if event_date and event_date <= cutoff:
                travel_events.append(event)
    
    log(f"Found {len(travel_events)} travel events in next 60 days")
    
    # Group into trips
    trips = group_events_by_trip(travel_events, calendar_data)
    log(f"Grouped into {len(trips)} trips")
    log("")
    
    # Get existing tasks
    existing_tasks = get_existing_task_names()
    log(f"Found {len(existing_tasks)} existing tasks")
    log("")
    
    # Process each trip
    total_created = 0
    for trip in trips:
        created = process_trip(trip, existing_tasks, state, fa_client)
        total_created += created
        if created > 0:
            log("")
    
    # Save state
    state['processed_trips'] = processed_trips
    state['processed_tasks'] = processed_tasks
    save_state(state)
    
    log("=" * 70)
    log(f"SUMMARY: Created {total_created} tasks for {len(trips)} trips")
    log("=" * 70)
    
    return {'created': total_created, 'trips_processed': len(trips)}


def validate_flight_info(flight_number: str, date_str: str) -> Dict:
    """
    Validate flight information by checking multiple sources.
    Returns validation results with confidence score.
    """
    log(f"\n🔍 Validating flight: {flight_number} on {date_str}")
    
    results = {
        'flight_number': flight_number,
        'date': date_str,
        'sources_checked': [],
        'confidence': 0,
        'validated': False,
        'details': {}
    }
    
    # Source 1: FlightAware API (primary)
    try:
        fa_client = FlightAwareClient()
        status = fa_client.get_flight_status(flight_number, date_str)
        if status:
            results['sources_checked'].append('flightaware')
            results['details']['flightaware'] = {
                'status': status.status,
                'origin': status.origin,
                'destination': status.destination,
                'scheduled_departure': status.scheduled_departure.isoformat(),
                'scheduled_arrival': status.scheduled_arrival.isoformat(),
                'aircraft_type': status.aircraft_type
            }
            results['confidence'] += 50
            log(f"  ✅ FlightAware: Found flight {status.origin} → {status.destination}")
        else:
            log(f"  ⚠️ FlightAware: Flight not found")
    except Exception as e:
        log(f"  ❌ FlightAware error: {e}")
    
    # Source 2: Calendar cross-reference
    calendar = load_calendar()
    if calendar:
        for event in calendar.get('events', []):
            flight_info = extract_flight_info(event)
            if flight_info.get('flight') == flight_number:
                event_date = parse_date(event.get('start_raw', ''))
                if event_date and event_date.strftime('%Y-%m-%d') == date_str:
                    results['sources_checked'].append('calendar')
                    results['details']['calendar'] = {
                        'summary': event.get('summary'),
                        'start': event.get('start_raw'),
                        'location': event.get('location')
                    }
                    results['confidence'] += 30
                    log(f"  ✅ Calendar: Found matching event")
                    break
    
    # Source 3: FlightAware schedule search (if we have origin/destination)
    if 'flightaware' in results['details']:
        details = results['details']['flightaware']
        try:
            fa_client = FlightAwareClient()
            # Search for scheduled flights on that route
            url = f"{fa_client.base_url}/schedules/{date_str}"
            params = {
                'origin': details['origin'],
                'destination': details['destination']
            }
            response = requests.get(url, headers=fa_client._headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                for flight in data.get('scheduled', []):
                    if flight.get('ident') == flight_number:
                        results['sources_checked'].append('flightaware_schedule')
                        results['confidence'] += 20
                        log(f"  ✅ FlightAware Schedule: Confirmed in schedule")
                        break
        except Exception as e:
            log(f"  ⚠️ Schedule search error: {e}")
    
    # Determine validation status
    if results['confidence'] >= 80:
        results['validated'] = True
        results['status'] = 'CONFIRMED'
    elif results['confidence'] >= 50:
        results['validated'] = True
        results['status'] = 'LIKELY'
    else:
        results['status'] = 'UNVERIFIED'
    
    log(f"  📊 Validation confidence: {results['confidence']}% - {results['status']}")
    
    return results


def test_flight_aware_connection() -> bool:
    """Test FlightAware API connection"""
    log("\n🧪 Testing FlightAware API Connection")
    log("=" * 50)
    
    try:
        fa_client = FlightAwareClient()
        
        # Test with a known Delta flight
        test_flight = "DL123"
        url = f"{fa_client.base_url}/flights/{test_flight}"
        
        log(f"Testing with flight: {test_flight}")
        response = requests.get(url, headers=fa_client._headers(), timeout=10)
        
        if response.status_code == 200:
            log("✅ FlightAware API connection successful")
            data = response.json()
            if data.get('flights'):
                log(f"✅ Found {len(data['flights'])} flight records")
            return True
        elif response.status_code == 401:
            log("❌ FlightAware API: Invalid credentials")
            return False
        else:
            log(f"⚠️ FlightAware API returned: {response.status_code}")
            return False
            
    except ValueError as e:
        log(f"❌ FlightAware not configured: {e}")
        return False
    except Exception as e:
        log(f"❌ FlightAware connection error: {e}")
        return False


def setup_flightaware(api_key: str):
    """Setup FlightAware API credentials"""
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    
    if "flightaware" not in config:
        config["flightaware"] = {}
    
    config["flightaware"]["api_key"] = api_key
    config["flightaware"]["base_url"] = "https://aeroapi.flightaware.com/aeroapi"
    
    # Ensure memory directory exists
    MEMORY_PATH = Path(__file__).parent / "memory"
    MEMORY_PATH.mkdir(parents=True, exist_ok=True)
    (MEMORY_PATH / "trips").mkdir(exist_ok=True)
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ FlightAware configuration saved!")
    print(f"   Config location: {CONFIG_PATH}")
    
    # Test the connection
    try:
        client = FlightAwareClient()
        url = f"{client.base_url}/flights/DL123"
        response = requests.get(url, headers=client._headers(), timeout=10)
        if response.status_code == 200:
            print("✅ Connection test successful!")
        elif response.status_code == 401:
            print("⚠️  Connection test failed: Invalid API key")
        else:
            print(f"⚠️  Connection test returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test connection: {e}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python aero_travel_manager.py setup <api_key>")
        print("  python aero_travel_manager.py tasks")
        print("  python aero_travel_manager.py monitor")
        print("  python aero_travel_manager.py full")
        print("  python aero_travel_manager.py validate <flight_number> <date>")
        print("  python aero_travel_manager.py test")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        if len(sys.argv) < 3:
            print("Error: API key required")
            print("Usage: python aero_travel_manager.py setup <api_key>")
            sys.exit(1)
        api_key = sys.argv[2]
        setup_flightaware(api_key)
        sys.exit(0)
    
    # Initialize FlightAware client if configured
    fa_client = None
    try:
        fa_client = FlightAwareClient()
        log("✅ FlightAware client initialized")
    except ValueError as e:
        log(f"⚠️ FlightAware not configured: {e}")
        log("   Day-of-travel monitoring will be limited")
    
    if command == "tasks":
        create_travel_tasks(fa_client)
    elif command == "monitor":
        if fa_client:
            monitor_day_of_travel(fa_client)
        else:
            log("❌ Cannot monitor: FlightAware not configured")
            sys.exit(1)
    elif command == "full":
        create_travel_tasks(fa_client)
        if fa_client:
            monitor_day_of_travel(fa_client)
    elif command == "validate":
        if len(sys.argv) < 4:
            print("Usage: python aero_travel_manager.py validate <flight_number> <YYYY-MM-DD>")
            sys.exit(1)
        flight_number = sys.argv[2]
        date_str = sys.argv[3]
        result = validate_flight_info(flight_number, date_str)
        print(json.dumps(result, indent=2))
    elif command == "test":
        test_flight_aware_connection()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
