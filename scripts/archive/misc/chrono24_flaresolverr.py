#!/usr/bin/env python3
"""
Chrono24 Watch Search with FlareSolverr
Uses FlareSolverr to bypass Cloudflare and search Chrono24 for watches
"""

import requests
import json
import sys
from typing import List, Dict, Optional

FLARESOLVERR_URL = "http://localhost:8191/v1"

def flaresolverr_get(url: str) -> Optional[Dict]:
    """Use FlareSolverr to fetch a URL bypassing Cloudflare"""
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    
    try:
        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=65)
        data = response.json()
        
        if data.get("status") == "ok":
            return data.get("solution", {})
        else:
            print(f"FlareSolverr error: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error calling FlareSolverr: {e}")
        return None

def search_chrono24_raw(query: str, filters: List[str] = None, min_year: int = None, max_year: int = None) -> List[Dict]:
    """
    Search Chrono24 using FlareSolverr to bypass Cloudflare
    Returns raw HTML that can be parsed
    """
    # Build search URL
    base_url = "https://www.chrono24.com/search/index.htm"
    params = {
        "query": query,
        "dosearch": "true"
    }
    
    if filters:
        if isinstance(filters, str):
            filters = [filters]
        for f in filters:
            params[f] = "1"
    
    if min_year:
        params["minYear"] = min_year
    if max_year:
        params["maxYear"] = max_year
    
    # Build URL with params
    url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    print(f"Searching: {url}")
    
    result = flaresolverr_get(url)
    if result:
        return result.get("response", "")
    return ""

def test_flaresolverr():
    """Test if FlareSolverr is working"""
    print("Testing FlareSolverr...")
    result = flaresolverr_get("https://www.chrono24.com")
    if result:
        print("✅ FlareSolverr is working!")
        print(f"Response length: {len(result.get('response', ''))} chars")
        return True
    else:
        print("❌ FlareSolverr test failed")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_flaresolverr()
    else:
        # Test search
        print("Testing Chrono24 search with FlareSolverr...")
        if test_flaresolverr():
            html = search_chrono24_raw("Rolex DateJust 1973", min_year=1973, max_year=1973)
            if html:
                print(f"\n✅ Search successful! Got {len(html)} chars of HTML")
                # Save to file for inspection
                with open("/tmp/chrono24_search.html", "w") as f:
                    f.write(html)
                print("Saved to /tmp/chrono24_search.html")
            else:
                print("\n❌ Search failed")
