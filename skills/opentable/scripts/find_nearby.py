#!/usr/bin/env python3
"""
Find restaurants near current location
Uses IP-based geolocation or provided coordinates
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def get_location_from_ip():
    """Get approximate location from IP address"""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://ipapi.co/json/",
            headers={"User-Agent": "OpenTableSkill/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                "lat": data.get("latitude"),
                "lng": data.get("longitude"),
                "city": data.get("city"),
                "region": data.get("region")
            }
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Find restaurants near you")
    parser.add_argument("--lat", type=float, help="Your latitude")
    parser.add_argument("--lng", type=float, help="Your longitude")
    parser.add_argument("--radius", type=int, default=5000, help="Search radius in meters (default: 5000)")
    parser.add_argument("--cuisine", help="Filter by cuisine")
    parser.add_argument("--price", type=int, choices=[1, 2, 3, 4], help="Price level (1-4)")
    parser.add_argument("--date", help="Date for availability (YYYY-MM-DD)")
    parser.add_argument("--time", help="Time for availability (HH:MM)")
    parser.add_argument("--party-size", type=int, help="Party size")
    parser.add_argument("--available-only", action="store_true", help="Only show available restaurants")
    parser.add_argument("--limit", type=int, default=25, help="Max results (default: 25)")
    parser.add_argument("--use-ip-location", action="store_true", help="Auto-detect location from IP")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    # Get location
    lat, lng = args.lat, args.lng
    location_source = "provided"
    
    if not (lat and lng):
        if args.use_ip_location:
            location = get_location_from_ip()
            if location and location["lat"] and location["lng"]:
                lat, lng = location["lat"], location["lng"]
                location_source = f"detected ({location.get('city', 'Unknown')}, {location.get('region', '')})"
            else:
                print(json.dumps({
                    "success": False,
                    "error": "Could not detect location from IP. Please provide --lat and --lng"
                }))
                sys.exit(1)
        else:
            print(json.dumps({
                "success": False,
                "error": "Location required. Provide --lat and --lng, or use --use-ip-location"
            }))
            sys.exit(1)
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        results = client.search_restaurants(
            lat=lat,
            lng=lng,
            radius=args.radius,
            cuisine=args.cuisine,
            price=args.price,
            date=args.date,
            time=args.time,
            party_size=args.party_size,
            available_only=args.available_only,
            limit=args.limit
        )
        
        restaurants = results.get("restaurants", [])
        total = results.get("total", len(restaurants))
        
        output = {
            "success": True,
            "location": {
                "lat": lat,
                "lng": lng,
                "source": location_source
            },
            "total": total,
            "count": len(restaurants),
            "restaurants": []
        }
        
        for r in restaurants:
            output["restaurants"].append({
                "id": r.get("id"),
                "name": r.get("name"),
                "address": r.get("address"),
                "city": r.get("city"),
                "state": r.get("state"),
                "phone": r.get("phone"),
                "cuisine": r.get("cuisine"),
                "price": r.get("price"),
                "rating": r.get("rating"),
                "review_count": r.get("review_count"),
                "distance": r.get("distance"),  # Distance from search location
                "reserve_url": r.get("reserve_url"),
                "image_url": r.get("image_url")
            })
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
