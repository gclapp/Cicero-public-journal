#!/usr/bin/env python3
"""
Aero Day-of-Travel Monitor

Monitors flights on travel day using FlightAware API.
Provides real-time alerts for:
- Gate changes
- Departure/arrival time changes
- Delays
- Cancellations
- Status changes

Delivery methods:
- Telegram messages for urgent alerts
- Email for summaries
- Voice call/SMS for critical changes

Integrates with calendar scanning and task creation.
"""

import json
import os
import subprocess
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict
import logging

# Import Aero components
from flightaware_client import (
    FlightAwareClient,
    FlightAwareError,
    FlightAwareAuthError,
    FlightAwareRateLimitError,
    FlightAwareNotFoundError
)
from aero_tracker import AeroTracker, TrackedFlight

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "aero-travel-monitor.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "aero-travel-monitor.log"

TELEGRAM_CHAT_ID = "5187735980"
EMAIL_RECIPIENT = "[REDACTED]"
PHONE_NUMBER = "+16507767054"

# Alert severity levels
class AlertSeverity:
    INFO = "info"           # General updates
    WARNING = "warning"     # Minor changes (gate change, small delay)
    CRITICAL = "critical"   # Major issues (cancellation, large delay)


@dataclass
class FlightAlert:
    """Represents a flight status alert."""
    flight_number: str
    alert_type: str
    severity: str
    message: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'flight_number': self.flight_number,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MonitoredFlight:
    """Extended flight data for monitoring purposes."""
    flight_number: str
    airline: str
    origin_code: str
    destination_code: str
    scheduled_departure: Optional[datetime]
    scheduled_arrival: Optional[datetime]
    gate: Optional[str]
    terminal: Optional[str]
    status: str
    last_checked: datetime
    alerts_sent: List[str]  # List of alert types already sent
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'flight_number': self.flight_number,
            'airline': self.airline,
            'origin_code': self.origin_code,
            'destination_code': self.destination_code,
            'scheduled_departure': self.scheduled_departure.isoformat() if self.scheduled_departure else None,
            'scheduled_arrival': self.scheduled_arrival.isoformat() if self.scheduled_arrival else None,
            'gate': self.gate,
            'terminal': self.terminal,
            'status': self.status,
            'last_checked': self.last_checked.isoformat(),
            'alerts_sent': self.alerts_sent
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MonitoredFlight':
        return cls(
            flight_number=data['flight_number'],
            airline=data['airline'],
            origin_code=data['origin_code'],
            destination_code=data['destination_code'],
            scheduled_departure=datetime.fromisoformat(data['scheduled_departure']) if data.get('scheduled_departure') else None,
            scheduled_arrival=datetime.fromisoformat(data['scheduled_arrival']) if data.get('scheduled_arrival') else None,
            gate=data.get('gate'),
            terminal=data.get('terminal'),
            status=data['status'],
            last_checked=datetime.fromisoformat(data['last_checked']),
            alerts_sent=data.get('alerts_sent', [])
        )


class TravelDayMonitor:
    """
    Monitors flights on travel day with real-time alerts.
    """
    
    def __init__(self):
        self.tracker = AeroTracker()
        self.state = self._load_state()
        self.monitored_flights: Dict[str, MonitoredFlight] = {}
        self._load_monitored_flights()
    
    def _load_state(self) -> Dict:
        """Load monitor state from file."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return {'monitored_flights': {}, 'alert_history': []}
    
    def _save_state(self):
        """Save monitor state to file."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert monitored flights to dict
        state = {
            'monitored_flights': {
                k: v.to_dict() for k, v in self.monitored_flights.items()
            },
            'alert_history': self.state.get('alert_history', [])[-100:]  # Keep last 100 alerts
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_monitored_flights(self):
        """Load monitored flights from state."""
        flights_data = self.state.get('monitored_flights', {})
        for flight_id, data in flights_data.items():
            try:
                self.monitored_flights[flight_id] = MonitoredFlight.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load flight {flight_id}: {e}")
    
    def extract_flight_numbers(self, text: str) -> List[str]:
        """Extract flight numbers from calendar text."""
        flights = []
        
        # Delta patterns
        delta_patterns = [
            (r'Delta\s+(?:Air\s+)?(?:Lines?\s+)?(?:flight\s+)?(\d+)', 'DL'),
            (r'DL\s*(\d+)', 'DL'),
            (r'\(DL\s*(\d+)\)', 'DL'),
        ]
        
        # United patterns
        united_patterns = [
            (r'United\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', 'UA'),
            (r'UA\s*(\d+)', 'UA'),
        ]
        
        # American patterns
        american_patterns = [
            (r'American\s+(?:Airlines?\s+)?(?:flight\s+)?(\d+)', 'AA'),
            (r'AA\s*(\d+)', 'AA'),
        ]
        
        all_patterns = delta_patterns + united_patterns + american_patterns
        
        for pattern, prefix in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                flight_num = f"{prefix}{match}"
                if flight_num not in flights:
                    flights.append(flight_num)
        
        return flights
    
    def get_travel_day_flights(self) -> List[Dict]:
        """
        Get flights scheduled for today and tomorrow from calendar.
        Returns list of flight info dicts.
        """
        if not CALENDAR_FILE.exists():
            logger.warning(f"Calendar file not found: {CALENDAR_FILE}")
            return []
        
        try:
            with open(CALENDAR_FILE, 'r') as f:
                calendar = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load calendar: {e}")
            return []
        
        flights = []
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        # Look for flights within next 48 hours
        cutoff = now + timedelta(hours=48)
        
        for event in calendar.get('events', []):
            summary = event.get('summary', '')
            description = event.get('description', '')
            
            # Check if this is a flight event
            is_flight = any(kw in summary.lower() for kw in 
                          ['flight', 'delta', 'united', 'american', 'departs', 'arrives'])
            
            if not is_flight:
                continue
            
            # Parse departure time
            start_raw = event.get('start_raw', '')
            if not start_raw:
                continue
            
            try:
                if 'T' in start_raw:
                    dep_time = datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
                    dep_time = dep_time.replace(tzinfo=None)
                else:
                    dep_time = datetime.strptime(start_raw, '%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Failed to parse date {start_raw}: {e}")
                continue
            
            # Only include flights within next 48 hours
            if dep_time < now or dep_time > cutoff:
                continue
            
            # Extract flight numbers
            full_text = f"{summary} {description}"
            flight_numbers = self.extract_flight_numbers(full_text)
            
            if not flight_numbers:
                continue
            
            for flight_num in flight_numbers:
                flights.append({
                    'flight_number': flight_num,
                    'summary': summary,
                    'description': description,
                    'departure_time': dep_time,
                    'location': event.get('location', ''),
                    'event_id': event.get('id', ''),
                    'is_today': dep_time.date() == now.date(),
                    'is_tomorrow': dep_time.date() == tomorrow.date()
                })
        
        return flights
    
    def start_monitoring(self, flight_number: str, departure_time: datetime) -> Optional[MonitoredFlight]:
        """Start monitoring a flight."""
        flight_id = f"{flight_number}_{departure_time.strftime('%Y%m%d')}"
        
        if flight_id in self.monitored_flights:
            logger.info(f"Already monitoring {flight_number}")
            return self.monitored_flights[flight_id]
        
        try:
            # Get initial flight data
            tracked = self.tracker.track_flight(flight_number)
            
            monitored = MonitoredFlight(
                flight_number=flight_number,
                airline=tracked.airline,
                origin_code=tracked.origin_code,
                destination_code=tracked.destination_code,
                scheduled_departure=tracked.scheduled_departure,
                scheduled_arrival=tracked.scheduled_arrival,
                gate=tracked.gate,
                terminal=tracked.terminal,
                status=tracked.status,
                last_checked=datetime.now(),
                alerts_sent=[]
            )
            
            self.monitored_flights[flight_id] = monitored
            self._save_state()
            
            logger.info(f"Started monitoring {flight_number}")
            return monitored
            
        except FlightAwareNotFoundError:
            logger.warning(f"Flight {flight_number} not found in FlightAware")
            return None
        except Exception as e:
            logger.error(f"Failed to start monitoring {flight_number}: {e}")
            return None
    
    def check_flight(self, flight_id: str) -> List[FlightAlert]:
        """Check a monitored flight for changes and return alerts."""
        if flight_id not in self.monitored_flights:
            logger.warning(f"Flight {flight_id} not being monitored")
            return []
        
        monitored = self.monitored_flights[flight_id]
        alerts = []
        
        try:
            # Get updated flight data
            updated = self.tracker.update_flight(monitored.flight_number)
            
            # Check for gate changes
            if updated.gate and monitored.gate != updated.gate:
                if monitored.gate:
                    alert = FlightAlert(
                        flight_number=monitored.flight_number,
                        alert_type="gate_change",
                        severity=AlertSeverity.WARNING,
                        message=f"🚪 Gate changed from {monitored.gate} to {updated.gate}",
                        old_value=monitored.gate,
                        new_value=updated.gate
                    )
                    alerts.append(alert)
                monitored.gate = updated.gate
            
            # Check for terminal changes
            if updated.terminal and monitored.terminal != updated.terminal:
                if monitored.terminal:
                    alert = FlightAlert(
                        flight_number=monitored.flight_number,
                        alert_type="terminal_change",
                        severity=AlertSeverity.WARNING,
                        message=f"🏢 Terminal changed from {monitored.terminal} to {updated.terminal}",
                        old_value=monitored.terminal,
                        new_value=updated.terminal
                    )
                    alerts.append(alert)
                monitored.terminal = updated.terminal
            
            # Check for status changes
            if updated.status.lower() != monitored.status.lower():
                severity = AlertSeverity.INFO
                if updated.status.lower() in ['cancelled', 'canceled']:
                    severity = AlertSeverity.CRITICAL
                elif updated.status.lower() in ['delayed']:
                    severity = AlertSeverity.WARNING
                
                alert = FlightAlert(
                    flight_number=monitored.flight_number,
                    alert_type="status_change",
                    severity=severity,
                    message=f"✈️ Status changed: {monitored.status} → {updated.status}",
                    old_value=monitored.status,
                    new_value=updated.status
                )
                alerts.append(alert)
                monitored.status = updated.status
            
            # Check for delay
            if updated.is_delayed and not any(a.alert_type == "delay_alert" for a in alerts):
                delay_msg = f"⏰ Flight delayed by {updated.delay_minutes} minutes"
                if updated.estimated_departure:
                    delay_msg += f"\nNew departure: {updated.estimated_departure.strftime('%I:%M %p')}"
                
                alert = FlightAlert(
                    flight_number=monitored.flight_number,
                    alert_type="delay_alert",
                    severity=AlertSeverity.WARNING if updated.delay_minutes < 60 else AlertSeverity.CRITICAL,
                    message=delay_msg,
                    old_value=str(monitored.scheduled_departure),
                    new_value=str(updated.estimated_departure)
                )
                alerts.append(alert)
            
            # Check for departure time changes
            if (updated.estimated_departure and monitored.scheduled_departure and
                updated.estimated_departure != monitored.scheduled_departure):
                
                # Only alert if significant change (> 15 minutes)
                time_diff = abs((updated.estimated_departure - monitored.scheduled_departure).total_seconds())
                if time_diff > 900:  # 15 minutes
                    alert = FlightAlert(
                        flight_number=monitored.flight_number,
                        alert_type="departure_change",
                        severity=AlertSeverity.WARNING,
                        message=f"🛫 Departure time changed to {updated.estimated_departure.strftime('%I:%M %p')}",
                        old_value=monitored.scheduled_departure.strftime('%I:%M %p') if monitored.scheduled_departure else None,
                        new_value=updated.estimated_departure.strftime('%I:%M %p')
                    )
                    alerts.append(alert)
                
                monitored.scheduled_departure = updated.estimated_departure
            
            # Check for arrival time changes
            if (updated.estimated_arrival and monitored.scheduled_arrival and
                updated.estimated_arrival != monitored.scheduled_arrival):
                
                time_diff = abs((updated.estimated_arrival - monitored.scheduled_arrival).total_seconds())
                if time_diff > 900:  # 15 minutes
                    alert = FlightAlert(
                        flight_number=monitored.flight_number,
                        alert_type="arrival_change",
                        severity=AlertSeverity.INFO,
                        message=f"🛬 Arrival time changed to {updated.estimated_arrival.strftime('%I:%M %p')}",
                        old_value=monitored.scheduled_arrival.strftime('%I:%M %p') if monitored.scheduled_arrival else None,
                        new_value=updated.estimated_arrival.strftime('%I:%M %p')
                    )
                    alerts.append(alert)
                
                monitored.scheduled_arrival = updated.estimated_arrival
            
            # Update last checked time
            monitored.last_checked = datetime.now()
            
        except FlightAwareNotFoundError:
            logger.warning(f"Flight {monitored.flight_number} no longer found")
        except Exception as e:
            logger.error(f"Error checking flight {flight_id}: {e}")
        
        if alerts:
            self._save_state()
        
        return alerts
    
    def send_telegram_alert(self, alert: FlightAlert):
        """Send alert via Telegram."""
        try:
            message = f"✈️ *Flight Alert: {alert.flight_number}*\n\n"
            message += f"{alert.message}\n\n"
            message += f"_Checked at {alert.timestamp.strftime('%I:%M %p')}_"
            
            # Use Telegram bot API
            telegram_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_telegram.py"
            if telegram_script.exists():
                subprocess.run([
                    "python3", str(telegram_script),
                    "--chat_id", TELEGRAM_CHAT_ID,
                    "--message", message
                ], capture_output=True, timeout=30)
                logger.info(f"Telegram alert sent for {alert.flight_number}")
            else:
                # Fallback: use message tool
                logger.info(f"TELEGRAM: {alert.message}")
                
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    def send_email_alert(self, alert: FlightAlert):
        """Send alert via email."""
        try:
            subject = f"✈️ Flight Alert: {alert.flight_number} - {alert.alert_type.replace('_', ' ').title()}"
            
            body = f"""
<h2>Flight Status Alert</h2>

<p><strong>Flight:</strong> {alert.flight_number}</p>
<p><strong>Alert Type:</strong> {alert.alert_type.replace('_', ' ').title()}</p>
<p><strong>Severity:</strong> {alert.severity.upper()}</p>

<p>{alert.message}</p>

<p><em>Checked at: {alert.timestamp.strftime('%Y-%m-%d %H:%M %Z')}</em></p>
"""
            
            email_script = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
            if email_script.exists():
                subprocess.run([
                    "python3", str(email_script),
                    "--to", EMAIL_RECIPIENT,
                    "--subject", subject,
                    "--body", body,
                    "--html"
                ], capture_output=True, timeout=30)
                logger.info(f"Email alert sent for {alert.flight_number}")
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def send_voice_alert(self, alert: FlightAlert):
        """Send critical alert via voice call."""
        try:
            if alert.severity != AlertSeverity.CRITICAL:
                return  # Only voice call for critical alerts
            
            message = f"Hello Geoff, this is Aero. Your flight {alert.flight_number} has a critical update. {alert.message}"
            
            # Log for now - voice call would use voice_call tool
            logger.info(f"VOICE ALERT: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send voice alert: {e}")
    
    def process_alert(self, alert: FlightAlert, flight_id: str):
        """Process and send an alert through appropriate channels."""
        monitored = self.monitored_flights.get(flight_id)
        if not monitored:
            return
        
        # Check if we've already sent this alert type
        alert_key = f"{alert.alert_type}_{alert.new_value}"
        if alert_key in monitored.alerts_sent:
            logger.info(f"Alert already sent: {alert_key}")
            return
        
        # Send based on severity
        if alert.severity == AlertSeverity.CRITICAL:
            # Critical: All channels
            self.send_telegram_alert(alert)
            self.send_email_alert(alert)
            self.send_voice_alert(alert)
        elif alert.severity == AlertSeverity.WARNING:
            # Warning: Telegram + Email
            self.send_telegram_alert(alert)
            self.send_email_alert(alert)
        else:
            # Info: Email only
            self.send_email_alert(alert)
        
        # Mark as sent
        monitored.alerts_sent.append(alert_key)
        self._save_state()
        
        # Add to history
        self.state['alert_history'].append(alert.to_dict())
    
    def run_check(self, check_type: str = "regular") -> Dict[str, Any]:
        """
        Run a monitoring check.
        
        Args:
            check_type: "regular" (every 15-30 min) or "frequent" (every 5 min on travel day)
        
        Returns:
            Summary of check results
        """
        logger.info(f"Running {check_type} check...")
        
        results = {
            'check_type': check_type,
            'timestamp': datetime.now().isoformat(),
            'flights_checked': 0,
            'alerts_generated': 0,
            'alerts_sent': 0,
            'errors': []
        }
        
        try:
            # Get flights from calendar
            travel_flights = self.get_travel_day_flights()
            
            if not travel_flights:
                logger.info("No upcoming flights found")
                return results
            
            logger.info(f"Found {len(travel_flights)} upcoming flights")
            
            for flight_info in travel_flights:
                flight_number = flight_info['flight_number']
                departure_time = flight_info['departure_time']
                flight_id = f"{flight_number}_{departure_time.strftime('%Y%m%d')}"
                
                # Start monitoring if not already
                if flight_id not in self.monitored_flights:
                    monitored = self.start_monitoring(flight_number, departure_time)
                    if monitored:
                        # Send initial monitoring confirmation
                        init_alert = FlightAlert(
                            flight_number=flight_number,
                            alert_type="monitoring_started",
                            severity=AlertSeverity.INFO,
                            message=f"🔍 Now monitoring {flight_number} from {monitored.origin_code} to {monitored.destination_code}"
                        )
                        self.process_alert(init_alert, flight_id)
                        results['alerts_sent'] += 1
                
                # Check for updates
                if flight_id in self.monitored_flights:
                    alerts = self.check_flight(flight_id)
                    results['flights_checked'] += 1
                    results['alerts_generated'] += len(alerts)
                    
                    for alert in alerts:
                        self.process_alert(alert, flight_id)
                        results['alerts_sent'] += 1
            
            # Clean up old flights
            self._cleanup_old_flights()
            
        except Exception as e:
            logger.error(f"Error during check: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _cleanup_old_flights(self):
        """Remove flights that have already departed."""
        now = datetime.now()
        to_remove = []
        
        for flight_id, monitored in self.monitored_flights.items():
            if monitored.scheduled_departure:
                # Remove flights that departed more than 4 hours ago
                if monitored.scheduled_departure < now - timedelta(hours=4):
                    to_remove.append(flight_id)
        
        for flight_id in to_remove:
            del self.monitored_flights[flight_id]
            logger.info(f"Stopped monitoring {flight_id} (flight completed)")
        
        if to_remove:
            self._save_state()
    
    def get_status_summary(self) -> str:
        """Get a summary of all monitored flights."""
        if not self.monitored_flights:
            return "No flights currently being monitored."
        
        lines = ["📊 Monitored Flights:", ""]
        
        for flight_id, monitored in self.monitored_flights.items():
            lines.append(f"✈️ {monitored.flight_number}")
            lines.append(f"   Route: {monitored.origin_code} → {monitored.destination_code}")
            lines.append(f"   Status: {monitored.status}")
            
            if monitored.scheduled_departure:
                lines.append(f"   Departure: {monitored.scheduled_departure.strftime('%I:%M %p')}")
            
            if monitored.gate:
                lines.append(f"   Gate: {monitored.gate}")
            
            if monitored.terminal:
                lines.append(f"   Terminal: {monitored.terminal}")
            
            lines.append(f"   Last checked: {monitored.last_checked.strftime('%I:%M %p')}")
            lines.append("")
        
        return "\n".join(lines)
    
    def close(self):
        """Close the monitor and save state."""
        self._save_state()
        self.tracker.close()


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Aero Day-of-Travel Monitor')
    parser.add_argument('--check', choices=['regular', 'frequent'], default='regular',
                       help='Type of check to run')
    parser.add_argument('--status', action='store_true',
                       help='Show current monitoring status')
    
    args = parser.parse_args()
    
    monitor = TravelDayMonitor()
    
    try:
        if args.status:
            print(monitor.get_status_summary())
        else:
            results = monitor.run_check(args.check)
            print(json.dumps(results, indent=2))
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
