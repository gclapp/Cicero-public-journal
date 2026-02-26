#!/usr/bin/env python3
"""
Make a reservation on OpenTable
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def main():
    parser = argparse.ArgumentParser(description="Make OpenTable reservation")
    parser.add_argument("--restaurant-id", type=int, required=True, help="Restaurant ID")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--time", required=True, help="Time (HH:MM, 24-hour format)")
    parser.add_argument("--party-size", type=int, required=True, help="Number of guests")
    parser.add_argument("--first-name", required=True, help="First name")
    parser.add_argument("--last-name", required=True, help="Last name")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--phone", required=True, help="Phone number")
    parser.add_argument("--special-requests", help="Special requests for the restaurant")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        
        reservation_kwargs = {}
        if args.special_requests:
            reservation_kwargs["special_requests"] = args.special_requests
        
        reservation = client.make_reservation(
            restaurant_id=args.restaurant_id,
            date=args.date,
            time=args.time,
            party_size=args.party_size,
            first_name=args.first_name,
            last_name=args.last_name,
            email=args.email,
            phone=args.phone,
            **reservation_kwargs
        )
        
        output = {
            "success": True,
            "reservation": {
                "confirmation_number": reservation.get("confirmation_number"),
                "restaurant_name": reservation.get("restaurant_name"),
                "date": reservation.get("date"),
                "time": reservation.get("time"),
                "party_size": reservation.get("party_size"),
                "status": reservation.get("status"),
                "cancellation_url": reservation.get("cancellation_url")
            }
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
