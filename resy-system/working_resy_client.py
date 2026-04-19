#!/usr/bin/env python3
"""
Working Resy API Client

A complete, working implementation for checking availability and booking
reservations using the current Resy API endpoints.

Key Changes from /3/find:
- Uses /4/find endpoint instead of /3/find
- Response structure: results.venues[].slots instead of results[]
- Requires both X-Resy-Auth-Token and X-Resy-Universal-Auth headers
- lat/long parameters required (can be 0)

Usage:
    # Check availability
    python working_resy_client.py check --venue-id 58528 --date 2026-05-17 --party-size 2
    
    # Search restaurants
    python working_resy_client.py search --query "carbone"
"""

import requests
import json
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Any

# Resy API Configuration
RESY_API_KEY = "AIcdK2rLXG6TYwJseSbmrBAy3RP81ocd"  # Public API key
BASE_URL = "https://api.resy.com"


class ResyClient:
    """Client for interacting with the Resy API."""
    
    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the Resy client.
        
        Args:
            auth_token: Your Resy auth token (JWT from browser)
                       Get from X-Resy-Auth-Token header in browser DevTools
        """
        self.auth_token = auth_token
        self.api_key = RESY_API_KEY
        self.base_url = BASE_URL
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Authorization": f'ResyAPI api_key="{self.api_key}"',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://resy.com",
            "Referer": "https://resy.com/",
        }
        
        if self.auth_token:
            headers["X-Resy-Auth-Token"] = self.auth_token
            headers["X-Resy-Universal-Auth"] = self.auth_token
        
        return headers
    
    def search_restaurants(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for restaurants by name.
        
        Args:
            query: Restaurant name or keyword
            
        Returns:
            List of venue dictionaries
        """
        url = f"{self.base_url}/3/venuesearch/search"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        
        payload = {"query": query}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("search", {}).get("hits", [])
        
        return hits
    
    def check_availability(
        self, 
        venue_id: int, 
        day: str, 
        party_size: int,
        lat: float = 0,
        long: float = 0
    ) -> List[Dict[str, Any]]:
        """
        Check availability for a restaurant using /4/find endpoint.
        
        This is the CURRENT working endpoint. The old /3/find returns empty results.
        
        Args:
            venue_id: Restaurant venue ID
            day: Date in YYYY-MM-DD format
            party_size: Number of guests
            lat: Latitude (default 0)
            long: Longitude (default 0)
            
        Returns:
            List of available slot dictionaries
        """
        url = f"{self.base_url}/4/find"
        
        params = {
            "venue_id": venue_id,
            "day": day,
            "party_size": party_size,
            "lat": lat,
            "long": long
        }
        
        headers = self._get_headers()
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse the nested response structure
        slots = []
        venues = data.get("results", {}).get("venues", [])
        
        for venue in venues:
            venue_info = venue.get("venue", {})
            for slot in venue.get("slots", []):
                slots.append({
                    "venue_id": venue_info.get("id", {}).get("resy"),
                    "venue_name": venue_info.get("name"),
                    "date": slot.get("date", {}).get("start"),
                    "end_date": slot.get("date", {}).get("end"),
                    "config_id": slot.get("config", {}).get("id"),
                    "table_type": slot.get("config", {}).get("type"),
                    "token": slot.get("config", {}).get("token")
                })
        
        return slots
    
    def get_booking_details(
        self, 
        config_token: str, 
        day: str, 
        party_size: int
    ) -> Dict[str, Any]:
        """
        Get booking details for a specific slot.
        
        CRITICAL STEP: This converts the config token (from /4/find) into
        the actual encrypted book token needed for booking.
        
        Args:
            config_token: The rgs:// token from availability check
            day: Date in YYYY-MM-DD format
            party_size: Number of guests
            
        Returns:
            Dictionary with book_token and payment methods
        """
        url = f"{self.base_url}/3/details"
        
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        
        payload = {
            "config_id": config_token,
            "day": day,
            "party_size": party_size
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def book_reservation(
        self, 
        book_token: str, 
        payment_method_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Book a reservation.
        
        Args:
            book_token: Encrypted book token from /3/details
            payment_method_id: Payment method ID (required for some restaurants)
            
        Returns:
            Booking confirmation details
        """
        url = f"{self.base_url}/3/book"
        
        headers = self._get_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        payload = {
            "book_token": book_token,
            "source_id": "resy.com-venue-details",
            "venue_marketing_opt_in": 0
        }
        
        if payment_method_id:
            payload["struct_payment_method"] = json.dumps({"id": payment_method_id})
        
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def get_venue_calendar(
        self, 
        venue_id: int, 
        start_date: str, 
        end_date: str,
        party_size: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get multi-day availability calendar for a venue.
        
        Args:
            venue_id: Restaurant venue ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            party_size: Number of guests
            
        Returns:
            List of daily availability status
        """
        url = f"{self.base_url}/4/venue/calendar"
        
        params = {
            "venue_id": venue_id,
            "num_seats": party_size,
            "start_date": start_date,
            "end_date": end_date
        }
        
        headers = self._get_headers()
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("scheduled", [])


def format_time_slot(slot: Dict[str, Any]) -> str:
    """Format a time slot for display."""
    time_str = slot.get("date", "N/A")
    table_type = slot.get("table_type", "N/A")
    
    # Parse time
    if time_str != "N/A":
        try:
            dt = datetime.fromisoformat(time_str.replace(" ", "T"))
            time_formatted = dt.strftime("%I:%M %p")
        except:
            time_formatted = time_str
    else:
        time_formatted = time_str
    
    return f"  {time_formatted} - {table_type}"


def main():
    parser = argparse.ArgumentParser(description="Resy API Client")
    parser.add_argument("--auth-token", help="Your Resy auth token (JWT)")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search restaurants")
    search_parser.add_argument("--query", required=True, help="Search query")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check availability")
    check_parser.add_argument("--venue-id", type=int, required=True, help="Venue ID")
    check_parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    check_parser.add_argument("--party-size", type=int, default=2, help="Party size")
    check_parser.add_argument("--lat", type=float, default=0, help="Latitude")
    check_parser.add_argument("--long", type=float, default=0, help="Longitude")
    
    # Calendar command
    calendar_parser = subparsers.add_parser("calendar", help="Get venue calendar")
    calendar_parser.add_argument("--venue-id", type=int, required=True, help="Venue ID")
    calendar_parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    calendar_parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    calendar_parser.add_argument("--party-size", type=int, default=2, help="Party size")
    
    args = parser.parse_args()
    
    # Get auth token from args or prompt
    auth_token = args.auth_token
    if not auth_token:
        auth_token = input("Enter your Resy auth token (or press Enter for limited access): ").strip()
    
    # Initialize client
    client = ResyClient(auth_token=auth_token if auth_token else None)
    
    if args.command == "search":
        print(f"\nSearching for: {args.query}\n")
        venues = client.search_restaurants(args.query)
        
        if not venues:
            print("No restaurants found.")
            return
        
        print(f"Found {len(venues)} restaurant(s):\n")
        for venue in venues:
            venue_id = venue.get("id", {}).get("resy")
            name = venue.get("name", "Unknown")
            locality = venue.get("locality", "")
            region = venue.get("region", "")
            cuisine = ", ".join(venue.get("cuisine", []))
            
            print(f"  {name}")
            print(f"    ID: {venue_id}")
            print(f"    Location: {locality}, {region}")
            print(f"    Cuisine: {cuisine}")
            print()
    
    elif args.command == "check":
        print(f"\nChecking availability:")
        print(f"  Venue ID: {args.venue_id}")
        print(f"  Date: {args.date}")
        print(f"  Party Size: {args.party_size}\n")
        
        slots = client.check_availability(
            venue_id=args.venue_id,
            day=args.date,
            party_size=args.party_size,
            lat=args.lat,
            long=args.long
        )
        
        if not slots:
            print("No available slots found.")
            return
        
        print(f"Found {len(slots)} available slot(s):\n")
        for slot in slots:
            print(format_time_slot(slot))
    
    elif args.command == "calendar":
        print(f"\nGetting calendar for venue {args.venue_id}:")
        print(f"  From: {args.start_date}")
        print(f"  To: {args.end_date}\n")
        
        days = client.get_venue_calendar(
            venue_id=args.venue_id,
            start_date=args.start_date,
            end_date=args.end_date,
            party_size=args.party_size
        )
        
        if not days:
            print("No calendar data found.")
            return
        
        for day in days:
            date = day.get("date", "N/A")
            inventory = day.get("inventory", {})
            status = inventory.get("reservation", "unknown")
            
            status_emoji = {
                "available": "✅",
                "sold_out": "❌",
                "unknown": "❓"
            }.get(status, "❓")
            
            print(f"  {date}: {status_emoji} {status}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
