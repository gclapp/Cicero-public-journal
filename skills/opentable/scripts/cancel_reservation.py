#!/usr/bin/env python3
"""
Cancel an OpenTable reservation
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def main():
    parser = argparse.ArgumentParser(description="Cancel OpenTable reservation")
    parser.add_argument("--confirmation-number", required=True, help="Reservation confirmation number")
    parser.add_argument("--email", required=True, help="Email used for the reservation")
    parser.add_argument("--reason", help="Cancellation reason (optional)")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        result = client.cancel_reservation(
            confirmation_number=args.confirmation_number,
            email=args.email,
            reason=args.reason
        )
        
        output = {
            "success": True,
            "message": result.get("message", "Reservation cancelled successfully"),
            "confirmation_number": args.confirmation_number,
            "refund_info": result.get("refund_info"),
            "cancellation_policy": result.get("cancellation_policy")
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
