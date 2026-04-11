#!/usr/bin/env python3
"""
Resy Restaurant Search
Search for available reservations at Resy restaurants
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

def search_venues(lat, long, day, party_size, query=None):
    """Search for venues near a location"""
    creds = load_credentials()
    
    url = f"https://api.resy.com/3/venues?lat={lat}&long={long}&day={day}&party_size={party_size}"
    
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
    """Find available reservations at a specific venue"""
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

def format_venue(venue):
    """Format venue info for display"""
    name = venue.get("name", "Unknown")
    venue_type = venue.get("type", "Restaurant")
    rating = venue.get("rater", [{}])[0].get("score", "N/A")
    reviews = venue.get("rater", [{}])[0].get("total", 0)
    price = "$" * venue.get("price_range_id", 1)
    
    location = venue.get("location", {})
    neighborhood = location.get("neighborhood", "")
    address = location.get("address_1", "")
    
    return {
        "name": name,
        "type": venue_type,
        "rating": rating,
        "reviews": reviews,
        "price": price,
        "neighborhood": neighborhood,
        "address": address,
        "id": venue.get("id", {}).get("resy")
    }

def main():
    parser = argparse.ArgumentParser(description="Search Resy restaurants")
    parser.add_argument("--city", default="la", help="City code (la, nyc, sf, etc.)")
    parser.add_argument("--date", help="Date (YYYY-MM-DD, default: tomorrow)")
    parser.add_argument("--party", type=int, default=2, help="Party size")
    parser.add_argument("--venue-id", help="Search specific venue")
    parser.add_argument("--lat", default="34.0522", help="Latitude")
    parser.add_argument("--long", default="-118.2437", help="Longitude")
    
    args = parser.parse_args()
    
    # Default to tomorrow
    if not args.date:
        tomorrow = datetime.now() + timedelta(days=1)
        args.date = tomorrow.strftime("%Y-%m-%d")
    
    print(f"🔍 Searching Resy for {args.party} people on {args.date}")
    print("-" * 60)
    
    if args.venue_id:
        # Search specific venue
        results = find_reservations(args.venue_id, args.date, args.party)
        if results:
            print(json.dumps(results, indent=2))
    else:
        # Search all venues
        results = search_venues(args.lat, args.long, args.date, args.party)
        if results and "results" in results:
            venues = results["results"].get("venues", [])
            print(f"Found {len(venues)} venues:\n")
            
            for venue in venues[:20]:  # Show top 20
                info = format_venue(venue)
                print(f"📍 {info['name']}")
                print(f"   Type: {info['type']} | Rating: {info['rating']}/5 ({info['reviews']} reviews)")
                print(f"   Price: {info['price']} | Location: {info['neighborhood']}")
                print(f"   Venue ID: {info['id']}")
                print()

if __name__ == "__main__":
    main()
