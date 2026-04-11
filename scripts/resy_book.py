#!/usr/bin/env python3
"""
Resy Reservation Booker
Book reservations at Resy restaurants
"""

import json
import os
import sys
import argparse
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

def get_payment_method():
    """Get user's payment method ID"""
    creds = load_credentials()
    
    url = "https://api.resy.com/2/user/payment-methods"
    
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
        print(f"❌ API Error: {e.code} - {e.read().decode()}")
        return None

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
        print(f"❌ API Error: {e.code} - {e.read().decode()}")
        return None

def book_reservation(config_id, payment_method_id=None):
    """Book a reservation"""
    creds = load_credentials()
    
    url = "https://api.resy.com/3/book"
    
    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "config_id": config_id,
        "struct_payment_method": json.dumps({"id": payment_method_id}) if payment_method_id else "{}"
    }
    
    encoded_data = urllib.parse.urlencode(data).encode()
    
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result
    except urllib.error.HTTPError as e:
        print(f"❌ Booking Error: {e.code} - {e.read().decode()}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Book Resy reservations")
    parser.add_argument("--venue-id", required=True, help="Venue ID to book")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--party", type=int, default=2, help="Party size")
    parser.add_argument("--time", help="Preferred time (HH:MM, 24hr)")
    parser.add_argument("--book", action="store_true", help="Actually book (dry-run by default)")
    
    args = parser.parse_args()
    
    print(f"🔍 Finding reservations at venue {args.venue_id}")
    print(f"   Date: {args.date} | Party: {args.party}")
    print("-" * 60)
    
    # Find available slots
    results = find_reservations(args.venue_id, args.date, args.party)
    
    if not results or "results" not in results:
        print("❌ No reservations found")
        return
    
    slots = results["results"].get("venues", [{}])[0].get("slots", [])
    
    if not slots:
        print("❌ No available slots found")
        return
    
    print(f"✅ Found {len(slots)} available slots:\n")
    
    for i, slot in enumerate(slots[:10]):  # Show top 10
        time_str = slot.get("date", {}).get("start", "Unknown")
        config_id = slot.get("config", {}).get("token", "")
        type_name = slot.get("config", {}).get("type", "")
        
        print(f"{i+1}. {time_str} - {type_name}")
        print(f"   Config ID: {config_id}")
        print()
    
    if args.book and slots:
        # Get payment method
        payment_methods = get_payment_method()
        payment_id = None
        if payment_methods and "payment_methods" in payment_methods:
            payment_id = payment_methods["payment_methods"][0].get("id")
        
        # Book first available slot
        config_id = slots[0]["config"]["token"]
        print(f"📝 Booking slot: {slots[0]['date']['start']}")
        
        result = book_reservation(config_id, payment_id)
        if result:
            print("✅ Reservation booked successfully!")
            print(json.dumps(result, indent=2))
        else:
            print("❌ Booking failed")
    elif not args.book:
        print("💡 Use --book to actually make a reservation")

if __name__ == "__main__":
    main()
