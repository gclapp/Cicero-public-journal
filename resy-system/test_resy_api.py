#!/usr/bin/env python3
"""
Resy API Test Script

Tests both /3/find (deprecated) and /4/find (current) endpoints
to demonstrate the difference in response.

Usage:
    python test_resy_api.py

Requirements:
    - requests library: pip install requests
    - Valid Resy auth token (get from browser DevTools)
"""

import requests
import json
from urllib.parse import urlencode

# Resy API Configuration
RESY_API_KEY = "AIcdK2rLXG6TYwJseSbmrBAy3RP81ocd"  # Public API key from Resy website
BASE_URL = "https://api.resy.com"

# Test Parameters (from your example)
VENUE_ID = 58528  # Restaurant ID
DAY = "2026-05-17"  # Date to check
PARTY_SIZE = 2  # Number of guests
LAT = 40.7596  # Latitude (NYC area)
LONG = -73.9685  # Longitude (NYC area)

# IMPORTANT: Replace with your actual auth token
# Get this from browser DevTools:
# 1. Open resy.com and log in
# 2. Open DevTools (F12) → Network tab
# 3. Look for any api.resy.com request
# 4. Copy value from "X-Resy-Auth-Token" header
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"  # TODO: Replace this!


def get_headers(auth_token=None):
    """Build request headers for Resy API."""
    headers = {
        "Authorization": f'ResyAPI api_key="{RESY_API_KEY}"',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://resy.com",
        "Referer": "https://resy.com/",
    }
    
    if auth_token:
        headers["X-Resy-Auth-Token"] = auth_token
        headers["X-Resy-Universal-Auth"] = auth_token
    
    return headers


def test_v3_find(auth_token=None):
    """Test the deprecated /3/find endpoint."""
    print("=" * 60)
    print("TESTING /3/find (DEPRECATED)")
    print("=" * 60)
    
    url = f"{BASE_URL}/3/find"
    params = {
        "venue_id": VENUE_ID,
        "day": DAY,
        "party_size": PARTY_SIZE,
        "lat": LAT,
        "long": LONG
    }
    
    headers = get_headers(auth_token)
    
    print(f"\nURL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    print(f"Headers: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        data = response.json()
        if "results" in data and len(data["results"]) == 0:
            print("\n⚠️  WARNING: Empty results - this endpoint may be deprecated!")
        
        return data
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


def test_v4_find(auth_token=None):
    """Test the current /4/find endpoint."""
    print("\n" + "=" * 60)
    print("TESTING /4/find (CURRENT)")
    print("=" * 60)
    
    url = f"{BASE_URL}/4/find"
    params = {
        "venue_id": VENUE_ID,
        "day": DAY,
        "party_size": PARTY_SIZE,
        "lat": LAT,
        "long": LONG
    }
    
    headers = get_headers(auth_token)
    
    print(f"\nURL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    print(f"Headers: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        data = response.json()
        
        # Parse and display available slots
        if "results" in data and "venues" in data["results"]:
            venues = data["results"]["venues"]
            print(f"\n✅ Found {len(venues)} venue(s)")
            
            for venue in venues:
                venue_name = venue.get("venue", {}).get("name", "Unknown")
                slots = venue.get("slots", [])
                print(f"\n📍 {venue_name}")
                print(f"   Available slots: {len(slots)}")
                
                for slot in slots:
                    start_time = slot.get("date", {}).get("start", "N/A")
                    table_type = slot.get("config", {}).get("type", "N/A")
                    print(f"   - {start_time} ({table_type})")
        else:
            print("\n⚠️  No results found")
        
        return data
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


def parse_slots(data):
    """Parse available slots from /4/find response."""
    slots = []
    
    if not data or "results" not in data:
        return slots
    
    venues = data["results"].get("venues", [])
    for venue in venues:
        for slot in venue.get("slots", []):
            slots.append({
                "time": slot.get("date", {}).get("start"),
                "type": slot.get("config", {}).get("type"),
                "token": slot.get("config", {}).get("token")
            })
    
    return slots


def main():
    """Run the tests."""
    print("Resy API Endpoint Test")
    print("=" * 60)
    print(f"Venue ID: {VENUE_ID}")
    print(f"Date: {DAY}")
    print(f"Party Size: {PARTY_SIZE}")
    print(f"Location: {LAT}, {LONG}")
    
    if AUTH_TOKEN == "YOUR_AUTH_TOKEN_HERE":
        print("\n" + "!" * 60)
        print("WARNING: AUTH_TOKEN not set!")
        print("!" * 60)
        print("\nTo get your auth token:")
        print("1. Open resy.com in your browser and log in")
        print("2. Open DevTools (F12) → Network tab")
        print("3. Look for any request to api.resy.com")
        print("4. Copy the value from 'X-Resy-Auth-Token' header")
        print("5. Replace YOUR_AUTH_TOKEN_HERE in this script")
        print("\nTesting without auth token (may return limited results)...")
    
    # Test v3 endpoint
    v3_result = test_v3_find(AUTH_TOKEN if AUTH_TOKEN != "YOUR_AUTH_TOKEN_HERE" else None)
    
    # Test v4 endpoint
    v4_result = test_v4_find(AUTH_TOKEN if AUTH_TOKEN != "YOUR_AUTH_TOKEN_HERE" else None)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if v3_result:
        v3_count = len(v3_result.get("results", []))
        print(f"/3/find: {v3_count} results (likely empty/deprecated)")
    
    if v4_result:
        v4_slots = parse_slots(v4_result)
        print(f"/4/find: {len(v4_slots)} slot(s) available")
        
        if len(v4_slots) > 0:
            print("\n✅ SOLUTION: Use /4/find endpoint instead of /3/find")
            print("   See working_resy_client.py for full implementation")


if __name__ == "__main__":
    main()
