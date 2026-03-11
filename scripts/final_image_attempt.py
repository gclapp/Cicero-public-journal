#!/usr/bin/env python3
"""
Download Chrono24 images using Selenium through FlareSolverr proxy
"""

import requests
import os
import base64

FLARESOLVERR_URL = "http://localhost:8191/v1"
IMAGES_DIR = os.path.expanduser("~/.openclaw/workspace/dashboard/images/real")

def get_page_with_cookies(url: str) -> dict:
    """Get page through FlareSolverr and extract cookies/session"""
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    
    try:
        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=65)
        data = response.json()
        
        if data.get("status") == "ok":
            solution = data.get("solution", {})
            return {
                "cookies": solution.get("cookies", []),
                "user_agent": solution.get("userAgent", ""),
                "html": solution.get("response", "")
            }
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def try_download_image(img_url: str, session_data: dict) -> bytes:
    """Try multiple methods to download image"""
    
    # Method 1: Direct with session cookies
    session = requests.Session()
    for cookie in session_data.get("cookies", []):
        session.cookies.set(
            cookie.get("name"),
            cookie.get("value"),
            domain=cookie.get("domain", ".chrono24.com")
        )
    
    headers = {
        "User-Agent": session_data.get("user_agent", ""),
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.chrono24.com/rolex/rolex-datejust-36--id43520266.htm",
        "Origin": "https://www.chrono24.com",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site"
    }
    
    try:
        response = session.get(img_url, headers=headers, timeout=30)
        if response.status_code == 200 and len(response.content) > 1000:
            return response.content
    except:
        pass
    
    # Method 2: Through FlareSolverr directly
    payload = {
        "cmd": "request.get",
        "url": img_url,
        "maxTimeout": 60000
    }
    
    try:
        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=65)
        data = response.json()
        if data.get("status") == "ok":
            # Response might be base64
            resp_text = data.get("solution", {}).get("response", "")
            if len(resp_text) > 10000:
                try:
                    return base64.b64decode(resp_text)
                except:
                    return resp_text.encode()
    except:
        pass
    
    return None

if __name__ == "__main__":
    print("🏛️ Chrono24 Image Download - Final Attempt")
    print("=" * 80)
    
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    # Get session from main Chrono24 page
    print("\n1. Getting session...")
    session_data = get_page_with_cookies("https://www.chrono24.com")
    
    if not session_data:
        print("❌ Failed to get session")
        exit(1)
    
    print(f"✅ Got session with {len(session_data['cookies'])} cookies")
    
    # Try to download images
    images_to_try = [
        ("https://cdn.chrono24.com/images/uhren/43520266-6j9c61z8de77z6mwl2q1r9e6-Original.jpg", "watch_3_real.jpg"),
    ]
    
    for img_url, filename in images_to_try:
        print(f"\n2. Downloading: {img_url}")
        
        image_data = try_download_image(img_url, session_data)
        
        if image_data:
            output_path = os.path.join(IMAGES_DIR, filename)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"✅ SUCCESS! Saved {len(image_data)} bytes to {filename}")
        else:
            print("❌ All methods failed")
            
    print("\n" + "=" * 80)
    print("Done. Check ~/.openclaw/workspace/dashboard/images/real/")
