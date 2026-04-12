#!/usr/bin/env python3
"""
Circuit Breaker for Resy API
Tracks venue failures and temporarily disables problematic venues
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent / "data"
CIRCUIT_BREAKER_FILE = DATA_DIR / "circuit_breaker.json"

# Configuration
FAILURE_THRESHOLD = 3  # Number of failures before circuit opens
CIRCUIT_OPEN_MINUTES = 60  # How long to keep circuit open
MAX_FAILURES_DISPLAY = 5  # Show last N failure messages

def load_circuit_data() -> Dict:
    """Load circuit breaker data"""
    if CIRCUIT_BREAKER_FILE.exists():
        with open(CIRCUIT_BREAKER_FILE, 'r') as f:
            return json.load(f)
    return {
        "venues": {},  # venue_id -> {failures, last_failure, circuit_open, failure_messages}
        "last_updated": datetime.now().isoformat()
    }

def save_circuit_data(data: Dict):
    """Save circuit breaker data"""
    DATA_DIR.mkdir(exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(CIRCUIT_BREAKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def record_failure(venue_id: str, venue_name: str, error_message: str):
    """Record a failure for a venue"""
    data = load_circuit_data()
    
    if venue_id not in data["venues"]:
        data["venues"][venue_id] = {
            "venue_name": venue_name,
            "failures": 0,
            "last_failure": None,
            "circuit_open": False,
            "circuit_opened_at": None,
            "failure_messages": [],
            "first_failure": datetime.now().isoformat()
        }
    
    venue_data = data["venues"][venue_id]
    venue_data["failures"] += 1
    venue_data["last_failure"] = datetime.now().isoformat()
    venue_data["failure_messages"].append({
        "timestamp": datetime.now().isoformat(),
        "message": error_message
    })
    # Keep only last N messages
    venue_data["failure_messages"] = venue_data["failure_messages"][-MAX_FAILURES_DISPLAY:]
    
    # Check if we should open the circuit
    if venue_data["failures"] >= FAILURE_THRESHOLD and not venue_data["circuit_open"]:
        venue_data["circuit_open"] = True
        venue_data["circuit_opened_at"] = datetime.now().isoformat()
    
    save_circuit_data(data)

def record_success(venue_id: str):
    """Record a successful call - resets failure count"""
    data = load_circuit_data()
    
    if venue_id in data["venues"]:
        venue_data = data["venues"][venue_id]
        # Only reset if circuit is closed
        if not venue_data.get("circuit_open", False):
            venue_data["failures"] = 0
            venue_data["failure_messages"] = []
            save_circuit_data(data)

def is_circuit_open(venue_id: str) -> bool:
    """Check if circuit is open for a venue"""
    data = load_circuit_data()
    
    if venue_id not in data["venues"]:
        return False
    
    venue_data = data["venues"][venue_id]
    
    # If circuit is open, check if we should close it (timeout)
    if venue_data.get("circuit_open", False):
        opened_at = venue_data.get("circuit_opened_at")
        if opened_at:
            opened_time = datetime.fromisoformat(opened_at)
            if datetime.now() - opened_time > timedelta(minutes=CIRCUIT_OPEN_MINUTES):
                # Close the circuit and reset
                venue_data["circuit_open"] = False
                venue_data["circuit_opened_at"] = None
                venue_data["failures"] = 0
                venue_data["failure_messages"] = []
                save_circuit_data(data)
                return False
        return True
    
    return False

def get_venue_status(venue_id: str) -> Optional[Dict]:
    """Get circuit breaker status for a venue"""
    data = load_circuit_data()
    return data["venues"].get(venue_id)

def get_all_venue_statuses() -> Dict[str, Dict]:
    """Get all venue statuses"""
    data = load_circuit_data()
    return data.get("venues", {})

def get_problematic_venues() -> List[Dict]:
    """Get list of venues with circuit open or high failure counts"""
    data = load_circuit_data()
    problematic = []
    
    for venue_id, venue_data in data.get("venues", {}).items():
        if venue_data.get("circuit_open", False) or venue_data.get("failures", 0) >= FAILURE_THRESHOLD:
            problematic.append({
                "venue_id": venue_id,
                **venue_data
            })
    
    # Sort by failures descending
    problematic.sort(key=lambda x: x.get("failures", 0), reverse=True)
    return problematic

def reset_circuit(venue_id: str):
    """Manually reset a circuit"""
    data = load_circuit_data()
    
    if venue_id in data["venues"]:
        data["venues"][venue_id]["circuit_open"] = False
        data["venues"][venue_id]["circuit_opened_at"] = None
        data["venues"][venue_id]["failures"] = 0
        data["venues"][venue_id]["failure_messages"] = []
        save_circuit_data(data)
        return True
    return False

def should_skip_venue(venue_id: str) -> tuple[bool, str]:
    """Check if we should skip a venue and return reason"""
    if is_circuit_open(venue_id):
        status = get_venue_status(venue_id)
        if status:
            return True, f"Circuit open ({status['failures']} failures)"
    return False, ""
