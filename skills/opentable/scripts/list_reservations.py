#!/usr/bin/env python3
"""
List reservations on OpenTable
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def main():
    parser = argparse.ArgumentParser(description="List OpenTable reservations")
    parser.add_argument("--email", help="Filter by diner email")
    parser.add_argument("--confirmation-number", help="Look up specific reservation")
    parser.add_argument("--all", action="store_true", help="Show all reservations (not just upcoming)")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        results = client.list_reservations(
            email=args.email,
            confirmation_number=args.confirmation_number,
            upcoming_only=not args.all
        )
        
        reservations = results.get("reservations", [])
        
        output = {
            "success": True,
            "count": len(reservations),
            "reservations": []
        }
        
        for r in reservations:
            output["reservations"].append({
                "confirmation_number": r.get("confirmation_number"),
                "restaurant_name": r.get("restaurant_name"),
                "restaurant_id": r.get("restaurant_id"),
                "date": r.get("date"),
                "time": r.get("time"),
                "party_size": r.get("party_size"),
                "status": r.get("status"),
                "created_at": r.get("created_at")
            })
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
