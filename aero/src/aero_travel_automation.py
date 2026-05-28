#!/usr/bin/env python3
"""
Aero Travel Automation - Unified Travel Management

This is the main entry point for all travel-related automation.
It integrates:
1. Calendar scanning for flight detection
2. Todoist task creation (pack, uber, rover, marriott)
3. Day-of-travel flight monitoring with FlightAware API
4. Real-time alerts via Telegram, Email, and Voice

Migrates all travel functionality from Cicero to Aero.
"""

import json
import os
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import logging

# Aero imports
from travel_monitor import TravelDayMonitor, FlightAlert, AlertSeverity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "aero-travel-automation.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "aero-travel-automation.log"
TODOIST_PATH = "/home/ubuntu/.npm-global/bin/todoist"

TRAVEL_KEYWORDS = ['flight', 'delta', 'united', 'american', 'trip to', 'travel to', 'stay at', 'hotel']


class AeroTravelAutomation:
    """
    Unified travel automation system.
    
    Combines calendar scanning, task creation, and flight monitoring
    into a single expert agent for all travel needs.
    """
    
    def __init__(self):
        self.state = self._load_state()
        self.monitor = TravelDayMonitor()
    
    def _load_state(self) -> Dict:
        """Load automation state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return {
            'processed_trips': [],
            'created_tasks': [],
            'last_run': None
        }
    
    def _save_state(self):
        """Save automation state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.state['last_run'] = datetime.now().isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_calendar(self) -> Optional[Dict]:
        """Load calendar events."""
        if not CALENDAR_FILE.exists():
            logger.warning(f"Calendar file not found: {CALENDAR_FILE}")
            return None
        try:
            with open(CALENDAR_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load calendar: {e}")
            return None
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from calendar."""
        if not date_str:
            return None
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
    
    def is_travel_event(self, event: Dict) -> bool:
        """Check if event is travel-related."""
        summary = event.get('summary', '').lower()
        return any(kw in summary for kw in TRAVEL_KEYWORDS) or event.get('is_travel')
    
    def extract_flight_info(self, event: Dict) -> Dict:
        """Extract flight number and confirmation from event."""
        summary = event.get('summary', '')
        description = event.get('description', '')
        
        flight_num = None
        airline = None
        
        # Delta patterns
        match = re.search(r'(?:Delta|DL)\s*(\d+)', summary, re.IGNORECASE)
        if match:
            flight_num = f"DL{match.group(1)}"
            airline = "Delta"
        
        # United patterns
        if not flight_num:
            match = re.search(r'(?:United|UA)\s*(\d+)', summary, re.IGNORECASE)
            if match:
                flight_num = f"UA{match.group(1)}"
                airline = "United"
        
        # American patterns
        if not flight_num:
            match = re.search(r'(?:American|AA)\s*(\d+)', summary, re.IGNORECASE)
            if match:
                flight_num = f"AA{match.group(1)}"
                airline = "American"
        
        # Extract confirmation code
        confirmation = None
        text = f"{summary} {description}"
        match = re.search(r'\b[A-Z0-9]{6}\b', text)
        if match:
            confirmation = match.group(0)
        
        return {
            'flight': flight_num,
            'airline': airline,
            'confirmation': confirmation
        }
    
    def extract_destination(self, event: Dict) -> str:
        """Extract destination city from event."""
        location = event.get('location', '')
        summary = event.get('summary', '')
        description = event.get('description', '')
        
        # Check summary for "Flight to [Destination]" pattern
        flight_to_match = re.search(r'Flight\s+to\s+([A-Za-z\s]+?)(?:\s+\(|\s*-|\s*$)', summary, re.IGNORECASE)
        if flight_to_match:
            dest = flight_to_match.group(1).strip()
            airport_map = {
                'RNO': 'Reno',
                'LAX': 'Los Angeles',
                'SFO': 'San Francisco',
                'SJC': 'San Jose',
                'JFK': 'NYC',
                'LGA': 'NYC',
                'EWR': 'NYC',
                'PDX': 'Portland',
                'SEA': 'Seattle',
                'LAS': 'Las Vegas',
                'PHX': 'Phoenix',
                'DEN': 'Denver',
                'ORD': 'Chicago',
                'DFW': 'Dallas',
                'MIA': 'Miami',
                'BOS': 'Boston',
                'DCA': 'DC',
                'IAD': 'DC',
            }
            dest_upper = dest.upper()
            if dest_upper in airport_map:
                return airport_map[dest_upper]
            return dest
        
        # Check location for arrival city
        if '-' in location:
            parts = location.split('-')
            if len(parts) >= 2:
                arrival = parts[1].strip()
                city_match = arrival.split('(')[0].strip()
                if city_match:
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
            return 'Los Angeles'
        
        return 'Trip'
    
    def get_hotel_stays(self, calendar_data: Dict) -> List[Dict]:
        """Extract hotel stay events from calendar."""
        hotels = []
        hotel_keywords = ['stay at', 'hotel', 'westin', 'ritz', 'marriott', 'hilton']
        
        for event in calendar_data.get('events', []):
            summary = event.get('summary', '').lower()
            if any(kw in summary for kw in hotel_keywords):
                event_date = self.parse_date(event.get('start_raw', ''))
                if event_date:
                    location = self.extract_destination(event)
                    hotels.append({
                        'event': event,
                        'date': event_date,
                        'location': location
                    })
        
        return sorted(hotels, key=lambda x: x['date'])
    
    def group_events_by_trip(self, events: List[Dict], calendar_data: Dict) -> List[Dict]:
        """Group flight events into trips using hotel stays as anchors."""
        if not events:
            return []
        
        hotel_stays = self.get_hotel_stays(calendar_data)
        
        # Sort flights by date
        flights = sorted(
            [e for e in events if self.extract_flight_info(e).get('flight')],
            key=lambda x: self.parse_date(x.get('start_raw', '')) or datetime.now()
        )
        
        trips = []
        used_flights = set()
        
        # Group flights into trips
        current_trip_flights = []
        current_trip_destination = None
        
        for flight in flights:
            flight_date = self.parse_date(flight.get('start_raw', ''))
            if not flight_date:
                continue
            
            flight_id = flight.get('summary', '') + flight.get('start_raw', '')
            if flight_id in used_flights:
                continue
            
            flight_dest = self.extract_destination(flight)
            
            # Find closest hotel
            closest_hotel = None
            closest_days = 5
            for hotel in hotel_stays:
                days_from_hotel = abs((flight_date - hotel['date']).days)
                if days_from_hotel <= 4:
                    if days_from_hotel < closest_days:
                        closest_days = days_from_hotel
                        closest_hotel = hotel
            
            if closest_hotel:
                flight_dest = closest_hotel['location']
            
            if not current_trip_flights:
                current_trip_flights = [flight]
                current_trip_destination = flight_dest if flight_dest != 'Trip' else 'Trip'
            else:
                current_trip_flights.append(flight)
                if flight_dest != 'Trip' and current_trip_destination == 'Trip':
                    current_trip_destination = flight_dest
            
            # End trip if we see a return to LAX pattern
            if 'lax' in flight.get('location', '').lower() or 'los angeles' in flight.get('location', '').lower():
                if current_trip_flights:
                    trips.append({
                        'events': current_trip_flights,
                        'start_date': self.parse_date(current_trip_flights[0].get('start_raw', '')),
                        'end_date': flight_date,
                        'destination': current_trip_destination
                    })
                    for f in current_trip_flights:
                        used_flights.add(f.get('summary', '') + f.get('start_raw', ''))
                    current_trip_flights = []
                    current_trip_destination = None
        
        # Handle remaining flights
        if current_trip_flights:
            trips.append({
                'events': current_trip_flights,
                'start_date': self.parse_date(current_trip_flights[0].get('start_raw', '')),
                'end_date': self.parse_date(current_trip_flights[-1].get('start_raw', '')),
                'destination': current_trip_destination
            })
        
        trips.sort(key=lambda x: x['start_date'])
        return trips
    
    def get_existing_tasks(self, project: str = "Travel") -> Set[str]:
        """Get set of existing task names from Todoist."""
        try:
            result = subprocess.run(
                [TODOIST_PATH, "tasks", "-p", project, "--all", "--json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                tasks = json.loads(result.stdout)
                return {task.get('content', '').lower() for task in tasks}
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
        return set()
    
    def create_task(self, text: str, project: str = "Travel", due: Optional[str] = None,
                    parent_id: Optional[str] = None, existing_tasks: Optional[Set[str]] = None) -> Optional[str]:
        """Create a task in Todoist."""
        try:
            if existing_tasks and text.lower() in existing_tasks:
                logger.info(f"Task already exists: {text[:60]}")
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
                logger.error(f"Failed to create task: {result.stderr}")
                return None
            
            # Extract task ID
            match = re.search(r'ID:\s+(\w+)', result.stdout)
            if match:
                return match.group(1)
            return None
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None
    
    def process_trip(self, trip: Dict, existing_tasks: Set[str]) -> int:
        """Process a single trip and create tasks."""
        created_count = 0
        
        first_event = trip['events'][0]
        first_date = trip['start_date']
        flight_info = self.extract_flight_info(first_event)
        
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
        
        # Check if already processed
        trip_id = f"{main_task_name}_{first_date.strftime('%Y%m%d')}"
        if trip_id in self.state['processed_trips']:
            logger.info(f"Trip already processed: {main_task_name}")
            return 0
        
        if main_task_name.lower() in existing_tasks:
            logger.info(f"Task exists: {main_task_name}")
            self.state['processed_trips'].append(trip_id)
            return 0
        
        # Create main task
        logger.info(f"Creating: {main_task_name}")
        parent_id = self.create_task(main_task_name, due=first_date.strftime('%Y-%m-%d'), 
                                     existing_tasks=existing_tasks)
        if not parent_id:
            return 0
        
        created_count += 1
        existing_tasks.add(main_task_name.lower())
        
        # Create subtasks
        subtasks = [
            ("└── 🧳 Pack", (first_date - timedelta(days=1)).strftime('%Y-%m-%d')),
            ("└── 🏢 Contact Marriott Ambassador about hotel", (first_date - timedelta(days=7)).strftime('%Y-%m-%d')),
            ("└── 🐕 Schedule Rover for Greta", datetime.now().strftime('%Y-%m-%d')),
        ]
        
        for text, due in subtasks:
            task_id = self.create_task(text, due=due, parent_id=parent_id, existing_tasks=existing_tasks)
            if task_id:
                created_count += 1
                existing_tasks.add(text.lower())
        
        # Create Uber tasks for each flight
        for event in trip['events']:
            event_date = self.parse_date(event.get('start_raw', ''))
            if not event_date:
                continue
            
            flight_info = self.extract_flight_info(event)
            flight_str = flight_info.get('flight')
            if not flight_str:
                continue
            
            flight_dest = self.extract_destination(event)
            uber_due = (event_date - timedelta(days=3)).strftime('%Y-%m-%d')
            uber_text = f"└── 🚗 Schedule Uber to airport for {flight_str} to {flight_dest}"
            
            task_id = self.create_task(uber_text, due=uber_due, parent_id=parent_id, existing_tasks=existing_tasks)
            if task_id:
                created_count += 1
                existing_tasks.add(uber_text.lower())
        
        # Mark as processed
        self.state['processed_trips'].append(trip_id)
        self._save_state()
        
        return created_count
    
    def run_task_creation(self) -> Dict:
        """Run the task creation workflow."""
        logger.info("=" * 70)
        logger.info("Aero Travel Automation - Task Creation")
        logger.info("=" * 70)
        
        results = {
            'trips_found': 0,
            'tasks_created': 0,
            'errors': []
        }
        
        try:
            calendar_data = self.load_calendar()
            if not calendar_data:
                results['errors'].append("Could not load calendar")
                return results
            
            # Get travel events
            travel_events = []
            for event in calendar_data.get('events', []):
                if self.is_travel_event(event):
                    event_date = self.parse_date(event.get('start_raw', ''))
                    if event_date and event_date <= datetime.now() + timedelta(days=60):
                        travel_events.append(event)
            
            logger.info(f"Found {len(travel_events)} travel events")
            
            # Group into trips
            trips = self.group_events_by_trip(travel_events, calendar_data)
            results['trips_found'] = len(trips)
            logger.info(f"Grouped into {len(trips)} trips")
            
            # Get existing tasks
            existing_tasks = self.get_existing_tasks()
            logger.info(f"Found {len(existing_tasks)} existing tasks")
            
            # Process each trip
            for trip in trips:
                created = self.process_trip(trip, existing_tasks)
                results['tasks_created'] += created
            
        except Exception as e:
            logger.error(f"Error in task creation: {e}")
            results['errors'].append(str(e))
        
        logger.info(f"Created {results['tasks_created']} tasks")
        return results
    
    def run_flight_monitoring(self, check_type: str = "regular") -> Dict:
        """Run the flight monitoring workflow."""
        logger.info("=" * 70)
        logger.info(f"Aero Travel Automation - Flight Monitoring ({check_type})")
        logger.info("=" * 70)
        
        return self.monitor.run_check(check_type)
    
    def run_full_automation(self) -> Dict:
        """Run the complete travel automation workflow."""
        logger.info("=" * 70)
        logger.info("Aero Travel Automation - Full Run")
        logger.info("=" * 70)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'task_creation': {},
            'flight_monitoring': {},
            'errors': []
        }
        
        try:
            # Step 1: Task Creation (runs less frequently)
            last_run = self.state.get('last_run')
            should_create_tasks = True
            
            if last_run:
                last_run_time = datetime.fromisoformat(last_run)
                hours_since = (datetime.now() - last_run_time).total_seconds() / 3600
                if hours_since < 12:  # Only create tasks every 12 hours
                    should_create_tasks = False
                    logger.info("Skipping task creation (ran recently)")
            
            if should_create_tasks:
                results['task_creation'] = self.run_task_creation()
            
            # Step 2: Flight Monitoring (runs every time)
            results['flight_monitoring'] = self.run_flight_monitoring("regular")
            
        except Exception as e:
            logger.error(f"Error in full automation: {e}")
            results['errors'].append(str(e))
        
        self._save_state()
        return results
    
    def close(self):
        """Clean up resources."""
        self.monitor.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Aero Travel Automation')
    parser.add_argument('command', choices=['tasks', 'monitor', 'full', 'status'],
                       help='Command to run')
    parser.add_argument('--check-type', choices=['regular', 'frequent'], default='regular',
                       help='Monitoring check type')
    
    args = parser.parse_args()
    
    automation = AeroTravelAutomation()
    
    try:
        if args.command == 'tasks':
            results = automation.run_task_creation()
            print(json.dumps(results, indent=2))
        
        elif args.command == 'monitor':
            results = automation.run_flight_monitoring(args.check_type)
            print(json.dumps(results, indent=2))
        
        elif args.command == 'full':
            results = automation.run_full_automation()
            print(json.dumps(results, indent=2))
        
        elif args.command == 'status':
            print(automation.monitor.get_status_summary())
    
    finally:
        automation.close()


if __name__ == "__main__":
    main()
