#!/usr/bin/env python3
"""
OpenTable API Client
Handles authentication and API requests for OpenTable Partner API
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import urllib.request
import urllib.error
import urllib.parse


class OpenTableClient:
    """Client for OpenTable Partner API"""
    
    BASE_URL = "https://api.opentable.com/v2"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize with credentials from args, config file, or environment"""
        self.api_key = api_key or self._get_credential("api_key")
        self.api_secret = api_secret or self._get_credential("api_secret")
        
        if not self.api_key:
            raise ValueError("OpenTable API key required. Set OPENTABLE_API_KEY or configure ~/.openclaw/config/opentable.json")
    
    def _get_credential(self, key: str) -> Optional[str]:
        """Get credential from config file or environment"""
        # Check environment first
        env_var = f"OPENTABLE_{key.upper()}"
        if os.getenv(env_var):
            return os.getenv(env_var)
        
        # Check config file
        config_path = Path.home() / ".openclaw" / "config" / "opentable.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return config.get(key)
            except (json.JSONDecodeError, IOError):
                pass
        
        return None
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                raise Exception(f"API Error: {error_data.get('message', error_body)}")
            except json.JSONDecodeError:
                raise Exception(f"API Error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"Connection error: {e.reason}")
    
    def search_restaurants(self, city: Optional[str] = None,
                          cuisine: Optional[str] = None,
                          name: Optional[str] = None,
                          lat: Optional[float] = None,
                          lng: Optional[float] = None,
                          radius: int = 5000,
                          price: Optional[int] = None,
                          date: Optional[str] = None,
                          time: Optional[str] = None,
                          party_size: Optional[int] = None,
                          available_only: bool = False,
                          limit: int = 25,
                          offset: int = 0) -> Dict[str, Any]:
        """Search for restaurants"""
        params = {"limit": limit, "offset": offset}

        if city:
            params["city"] = city
        if cuisine:
            params["cuisine"] = cuisine
        if name:
            params["name"] = name
        if price:
            params["price"] = price
        if lat and lng:
            params["lat"] = lat
            params["lng"] = lng
            params["radius"] = radius
        if date:
            params["date"] = date
        if time:
            params["time"] = time
        if party_size:
            params["party_size"] = party_size
        if available_only:
            params["available_only"] = "true"

        return self._request("/restaurants", params)
    
    def get_restaurant(self, restaurant_id: int) -> Dict[str, Any]:
        """Get detailed restaurant information"""
        return self._request(f"/restaurants/{restaurant_id}")
    
    def check_availability(self, restaurant_id: int, date: str, 
                          time: str, party_size: int) -> Dict[str, Any]:
        """Check table availability"""
        params = {
            "date": date,
            "time": time,
            "party_size": party_size
        }
        return self._request(f"/restaurants/{restaurant_id}/availability", params)
    
    def make_reservation(self, restaurant_id: int, date: str, time: str,
                        party_size: int, first_name: str, last_name: str,
                        email: str, phone: str, **kwargs) -> Dict[str, Any]:
        """Make a reservation"""
        data = {
            "restaurant_id": restaurant_id,
            "date": date,
            "time": time,
            "party_size": party_size,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone
        }
        data.update(kwargs)
        
        url = f"{self.BASE_URL}/reservations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                raise Exception(f"API Error: {error_data.get('message', error_body)}")
            except json.JSONDecodeError:
                raise Exception(f"API Error {e.code}: {error_body}")
    
    def list_reservations(self, email: Optional[str] = None,
                         confirmation_number: Optional[str] = None,
                         upcoming_only: bool = True) -> Dict[str, Any]:
        """List reservations for a diner"""
        params = {}
        if email:
            params["email"] = email
        if confirmation_number:
            params["confirmation_number"] = confirmation_number
        if upcoming_only:
            params["upcoming_only"] = "true"

        return self._request("/reservations", params)

    def cancel_reservation(self, confirmation_number: str, email: str,
                          reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an existing reservation"""
        data = {
            "confirmation_number": confirmation_number,
            "email": email
        }
        if reason:
            data["reason"] = reason

        url = f"{self.BASE_URL}/reservations/{confirmation_number}/cancel"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Reservation {confirmation_number} not found")
            elif e.code == 403:
                raise Exception("Not authorized to cancel this reservation")
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                raise Exception(f"API Error: {error_data.get('message', error_body)}")
            except json.JSONDecodeError:
                raise Exception(f"API Error {e.code}: {error_body}")

    def get_reservation(self, confirmation_number: str) -> Dict[str, Any]:
        """Get details of a specific reservation"""
        return self._request(f"/reservations/{confirmation_number}")


if __name__ == "__main__":
    # Simple test
    try:
        client = OpenTableClient()
        print(json.dumps({"success": True, "message": "Client initialized successfully"}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)
