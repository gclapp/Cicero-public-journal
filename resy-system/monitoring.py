#!/usr/bin/env python3
"""
Monitoring and logging system for Resy Automation
Tracks scans, bookings, errors, and system health
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Paths
DATA_DIR = Path(__file__).parent / "data"
LOGS_DIR = Path(__file__).parent / "logs"
MONITORING_FILE = DATA_DIR / "monitoring.json"

def ensure_dirs():
    """Ensure data and logs directories exist"""
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

def load_monitoring_data() -> Dict:
    """Load monitoring data from file"""
    if MONITORING_FILE.exists():
        with open(MONITORING_FILE, 'r') as f:
            return json.load(f)
    return {
        "scans": [],
        "bookings": [],
        "errors": [],
        "system_health": {
            "last_scan_time": None,
            "last_booking_time": None,
            "last_error_time": None,
            "total_scans": 0,
            "total_bookings": 0,
            "total_errors": 0,
            "status": "unknown"
        }
    }

def save_monitoring_data(data: Dict):
    """Save monitoring data to file"""
    ensure_dirs()
    with open(MONITORING_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def log_scan(trip_dates: List[str], restaurants_checked: int, 
             reservations_found: int, reservations_attempted: int,
             reservations_made: int, details: str = ""):
    """Log a scan event"""
    data = load_monitoring_data()
    
    scan_record = {
        "timestamp": datetime.now().isoformat(),
        "trip_dates": trip_dates,
        "restaurants_checked": restaurants_checked,
        "reservations_found": reservations_found,
        "reservations_attempted": reservations_attempted,
        "reservations_made": reservations_made,
        "details": details,
        "status": "success" if reservations_made > 0 else "no_bookings"
    }
    
    data["scans"].append(scan_record)
    data["system_health"]["last_scan_time"] = datetime.now().isoformat()
    data["system_health"]["total_scans"] = len(data["scans"])
    data["system_health"]["status"] = "healthy"
    
    # Keep only last 100 scans
    data["scans"] = data["scans"][-100:]
    
    save_monitoring_data(data)

def log_booking(trip_date: str, restaurant_name: str, venue_id: str,
                party_size: int, time: str, confirmation_code: str = ""):
    """Log a successful booking"""
    data = load_monitoring_data()
    
    booking_record = {
        "timestamp": datetime.now().isoformat(),
        "trip_date": trip_date,
        "restaurant_name": restaurant_name,
        "venue_id": venue_id,
        "party_size": party_size,
        "time": time,
        "confirmation_code": confirmation_code,
        "status": "confirmed"
    }
    
    data["bookings"].append(booking_record)
    data["system_health"]["last_booking_time"] = datetime.now().isoformat()
    data["system_health"]["total_bookings"] = len(data["bookings"])
    
    # Keep only last 100 bookings
    data["bookings"] = data["bookings"][-100:]
    
    save_monitoring_data(data)

def log_error(source: str, error_type: str, message: str, 
              details: Dict = None, user_email: str = None):
    """Log an error event"""
    data = load_monitoring_data()
    
    error_record = {
        "timestamp": datetime.now().isoformat(),
        "source": source,  # 'scanner', 'web_ui', 'api', 'system'
        "error_type": error_type,
        "message": message,
        "details": details or {},
        "user_email": user_email,
        "resolved": False
    }
    
    data["errors"].append(error_record)
    data["system_health"]["last_error_time"] = datetime.now().isoformat()
    data["system_health"]["total_errors"] = len(data["errors"])
    
    # Update status if too many recent errors
    recent_errors = [e for e in data["errors"][-10:] if not e.get("resolved")]
    if len(recent_errors) >= 5:
        data["system_health"]["status"] = "degraded"
    if len(recent_errors) >= 10:
        data["system_health"]["status"] = "critical"
    
    # Keep only last 200 errors
    data["errors"] = data["errors"][-200:]
    
    save_monitoring_data(data)

def resolve_error(error_index: int) -> bool:
    """Mark an error as resolved"""
    data = load_monitoring_data()
    
    if 0 <= error_index < len(data["errors"]):
        data["errors"][error_index]["resolved"] = True
        data["errors"][error_index]["resolved_at"] = datetime.now().isoformat()
        
        # Recalculate status
        recent_unresolved = [e for e in data["errors"][-10:] if not e.get("resolved")]
        if len(recent_unresolved) < 5:
            data["system_health"]["status"] = "healthy"
        elif len(recent_unresolved) < 10:
            data["system_health"]["status"] = "degraded"
        
        save_monitoring_data(data)
        return True
    return False

def get_system_health() -> Dict:
    """Get current system health summary"""
    data = load_monitoring_data()
    health = data["system_health"].copy()
    
    # Calculate time since last activities
    now = datetime.now()
    
    if health["last_scan_time"]:
        last_scan = datetime.fromisoformat(health["last_scan_time"])
        health["time_since_scan"] = format_duration(now - last_scan)
        health["scan_overdue"] = (now - last_scan) > timedelta(hours=14)
    else:
        health["time_since_scan"] = "Never"
        health["scan_overdue"] = True
    
    if health["last_booking_time"]:
        last_booking = datetime.fromisoformat(health["last_booking_time"])
        health["time_since_booking"] = format_duration(now - last_booking)
    else:
        health["time_since_booking"] = "Never"
    
    if health["last_error_time"]:
        last_error = datetime.fromisoformat(health["last_error_time"])
        health["time_since_error"] = format_duration(now - last_error)
    else:
        health["time_since_error"] = "None"
    
    # Get recent activity
    health["recent_scans"] = data["scans"][-5:][::-1]
    health["recent_bookings"] = data["bookings"][-5:][::-1]
    health["recent_errors"] = [e for e in data["errors"][-10:][::-1] if not e.get("resolved")]
    
    return health

def get_scan_history(days: int = 7) -> List[Dict]:
    """Get scan history for the last N days"""
    data = load_monitoring_data()
    cutoff = datetime.now() - timedelta(days=days)
    
    scans = []
    for scan in data["scans"]:
        scan_time = datetime.fromisoformat(scan["timestamp"])
        if scan_time >= cutoff:
            scans.append(scan)
    
    return scans[::-1]  # Most recent first

def get_error_summary() -> Dict:
    """Get error summary by source and type"""
    data = load_monitoring_data()
    
    summary = {
        "total": len(data["errors"]),
        "unresolved": len([e for e in data["errors"] if not e.get("resolved")]),
        "by_source": {},
        "by_type": {},
        "recent_critical": []
    }
    
    for error in data["errors"]:
        source = error["source"]
        error_type = error["error_type"]
        
        summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
        summary["by_type"][error_type] = summary["by_type"].get(error_type, 0) + 1
        
        if not error.get("resolved"):
            error_time = datetime.fromisoformat(error["timestamp"])
            if datetime.now() - error_time < timedelta(hours=24):
                summary["recent_critical"].append(error)
    
    return summary

def format_duration(td: timedelta) -> str:
    """Format a timedelta into a human-readable string"""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}m ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}h ago"
    else:
        days = total_seconds // 86400
        return f"{days}d ago"

def get_log_files() -> List[Dict]:
    """Get list of log files with metadata"""
    logs = []
    
    if LOGS_DIR.exists():
        for log_file in sorted(LOGS_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True):
            stat = log_file.stat()
            logs.append({
                "name": log_file.name,
                "size": format_file_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(log_file)
            })
    
    return logs

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"

def read_log_file(log_name: str, lines: int = 50) -> str:
    """Read the last N lines from a log file"""
    log_path = LOGS_DIR / log_name
    
    if not log_path.exists():
        return "Log file not found"
    
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception as e:
        return f"Error reading log: {str(e)}"

# Initialize on module load
ensure_dirs()
