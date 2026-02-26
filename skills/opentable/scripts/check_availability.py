#!/usr/bin/env python3
"""
Check table availability at a restaurant
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def main():
    parser = argparse.ArgumentParser(description="Check OpenTable availability")
    parser.add_argument("--restaurant-id", type=int, required=True, help="Restaurant ID")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--time", required=True, help="Time (HH:MM, 24-hour format)")
    parser.add_argument("--party-size", type=int, required=True, help="Number of guests")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        availability = client.check_availability(
            restaurant_id=args.restaurant_id,
            date=args.date,
            time=args.time,
            party_size=args.party_size
        )
        
        output = {
            "success": True,
            "restaurant_id": args.restaurant_id,
            "date": args.date,
            "time": args.time,
            "party_size": args.party_size,
            "available": availability.get("available", False),
            "times": availability.get("times", []),
            "message": availability.get("message", "")
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
