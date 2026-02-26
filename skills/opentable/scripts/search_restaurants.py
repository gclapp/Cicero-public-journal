#!/usr/bin/env python3
"""
Search for restaurants on OpenTable
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from opentable_client import OpenTableClient


def main():
    parser = argparse.ArgumentParser(description="Search OpenTable restaurants")
    parser.add_argument("--city", help="City name (e.g., 'Portland')")
    parser.add_argument("--cuisine", help="Cuisine type (e.g., 'Italian', 'Japanese')")
    parser.add_argument("--name", help="Restaurant name search")
    parser.add_argument("--lat", type=float, help="Latitude for location search")
    parser.add_argument("--lng", type=float, help="Longitude for location search")
    parser.add_argument("--radius", type=int, default=5000, help="Search radius in meters (default: 5000)")
    parser.add_argument("--price", type=int, choices=[1, 2, 3, 4], help="Price level (1-4)")
    parser.add_argument("--date", help="Date for availability check (YYYY-MM-DD)")
    parser.add_argument("--time", help="Time for availability check (HH:MM)")
    parser.add_argument("--party-size", type=int, help="Party size for availability check")
    parser.add_argument("--available-only", action="store_true", help="Only show restaurants with availability")
    parser.add_argument("--limit", type=int, default=25, help="Max results (default: 25)")
    parser.add_argument("--offset", type=int, default=0, help="Result offset for pagination")
    parser.add_argument("--api-key", help="OpenTable API key (or set OPENTABLE_API_KEY)")
    
    args = parser.parse_args()
    
    # Validate at least one search criteria
    if not any([args.city, args.cuisine, args.name, (args.lat and args.lng)]):
        print(json.dumps({
            "success": False,
            "error": "At least one search criteria required: --city, --cuisine, --name, or --lat/--lng"
        }))
        sys.exit(1)
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        results = client.search_restaurants(
            city=args.city,
            cuisine=args.cuisine,
            name=args.name,
            lat=args.lat,
            lng=args.lng,
            radius=args.radius,
            price=args.price,
            date=args.date,
            time=args.time,
            party_size=args.party_size,
            available_only=args.available_only,
            limit=args.limit,
            offset=args.offset
        )
        
        # Format output
        restaurants = results.get("restaurants", [])
        total = results.get("total", len(restaurants))
        
        output = {
            "success": True,
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
                "price": r.get("price"),  # 1-4 scale
                "rating": r.get("rating"),
                "review_count": r.get("review_count"),
                "reserve_url": r.get("reserve_url"),
                "image_url": r.get("image_url")
            })
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
