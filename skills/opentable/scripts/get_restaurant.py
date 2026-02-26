#!/usr/bin/env python3
"""
Get detailed restaurant information from OpenTable
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def main():
    parser = argparse.ArgumentParser(description="Get OpenTable restaurant details")
    parser.add_argument("--id", type=int, required=True, help="Restaurant ID")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        restaurant = client.get_restaurant(args.id)
        
        # Format output with key details
        output = {
            "success": True,
            "restaurant": {
                "id": restaurant.get("id"),
                "name": restaurant.get("name"),
                "description": restaurant.get("description"),
                "address": restaurant.get("address"),
                "city": restaurant.get("city"),
                "state": restaurant.get("state"),
                "postal_code": restaurant.get("postal_code"),
                "country": restaurant.get("country"),
                "phone": restaurant.get("phone"),
                "website": restaurant.get("website"),
                "cuisine": restaurant.get("cuisine"),
                "price": restaurant.get("price"),
                "rating": restaurant.get("rating"),
                "review_count": restaurant.get("review_count"),
                "hours": restaurant.get("hours"),
                "dress_code": restaurant.get("dress_code"),
                "parking": restaurant.get("parking"),
                "payment_options": restaurant.get("payment_options"),
                "reserve_url": restaurant.get("reserve_url"),
                "image_url": restaurant.get("image_url"),
                "latitude": restaurant.get("lat"),
                "longitude": restaurant.get("lng")
            }
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
