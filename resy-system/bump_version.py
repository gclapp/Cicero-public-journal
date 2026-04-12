#!/usr/bin/env python3
"""
Version bumping script for NYCeats
Updates the version.json file with new deployment info
Format: vYYYY-MM-DD_N HH:MM:SS (Pacific Time)
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

VERSION_FILE = Path(__file__).parent / "version.json"

def bump_version():
    """Bump the version counter for today"""
    
    # Load current version
    if VERSION_FILE.exists():
        with open(VERSION_FILE) as f:
            data = json.load(f)
    else:
        data = {}
    
    # Get current time in Pacific Time
    pt = ZoneInfo("America/Los_Angeles")
    now = datetime.now(pt)
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    # Check if it's a new day
    last_date = data.get("date", "")
    
    if last_date == today:
        # Same day - increment counter
        counter = data.get("counter", 0) + 1
    else:
        # New day - reset counter
        counter = 1
    
    # Build version string
    version = f"v{today}_{counter}"
    
    # Update data
    data.update({
        "version": version,
        "date": today,
        "counter": counter,
        "time": current_time,
        "last_deployment": now.isoformat()
    })
    
    # Save version file
    with open(VERSION_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Version bumped to: {version} {current_time}")
    return data

if __name__ == "__main__":
    bump_version()