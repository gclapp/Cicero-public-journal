#!/usr/bin/env python3
"""
Resy Reservation Monitor
Monitor for new availability at hard-to-get restaurants
"""

import json
import os
import sys
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error

# Load credentials
CREDENTIALS_PATH = Path.home() / ".openclaw" / "config" / "resy-credentials.json"

def load_credentials():
    """Load Resy API credentials"""
    if not CREDENTIALS_PATH.exists():
        print("❌ Credentials not found. Run setup first.")
        sys.exit(1)
    
    with open(CREDENTIALS_PATH) as f:
        return json.load(f)

def find_reservations(venue_id, day, party_size):
    """Find available reservations"""
    creds = load_credentials()
    
    url = f"https://api.resy.com/4/find?day={day}&party_size={party_size}&venue_id={venue_id}"
    
    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data
    except urllib.error.HTTPError as e:
        print(f"❌ API Error: {e.code}")
        return None

def monitor_venue(venue_id, dates, party_size, interval=60, notify_script=None):
    """Monitor a venue for availability"""
    print(f"👁️  Monitoring venue {venue_id}")
    print(f"   Dates: {', '.join(dates)}")
    print(f"   Party size: {party_size}")
    print(f"   Check interval: {interval} seconds")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    known_slots = set()
    
    while True:
        for date in dates:
            results = find_reservations(venue_id, date, party_size)
            
            if results and "results" in results:
                slots = results["results"].get("venues", [{}])[0].get("slots", [])
                
                for slot in slots:
                    time_str = slot.get("date", {}).get("start", "")
                    slot_id = f"{venue_id}-{date}-{time_str}"
                    
                    if slot_id not in known_slots:
                        known_slots.add(slot_id)
                        
                        # New slot found!
                        print(f"\n🎉 NEW AVAILABILITY!")
                        print(f"   Date: {date}")
                        print(f"   Time: {time_str}")
                        print(f"   Type: {slot.get('config', {}).get('type', '')}")
                        print(f"   Config ID: {slot.get('config', {}).get('token', '')}")
                        print(f"   Found at: {datetime.now().strftime('%H:%M:%S')}")
                        print()
                        
                        # Run notification script if provided
                        if notify_script:
                            os.system(f"{notify_script} '{venue_id}' '{date}' '{time_str}'")
        
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Monitor Resy for availability")
    parser.add_argument("--venue-id", required=True, help="Venue ID to monitor")
    parser.add_argument("--dates", required=True, help="Comma-separated dates (YYYY-MM-DD)")
    parser.add_argument("--party", type=int, default=2, help="Party size")
    parser.add_argument("--interval", type=int, default=60, help="Check interval (seconds)")
    parser.add_argument("--notify", help="Script to run when availability found")
    
    args = parser.parse_args()
    
    dates = [d.strip() for d in args.dates.split(",")]
    
    try:
        monitor_venue(args.venue_id, dates, args.party, args.interval, args.notify)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    main()
