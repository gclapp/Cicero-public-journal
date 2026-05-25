#!/usr/bin/env python3
"""
Download real watch images using FlareSolverr session
Uses the session cookies from FlareSolverr to download images
"""

import requests
import json
import os
import re
from urllib.parse import urljoin

FLARESOLVERR_URL = "http://localhost:8191/v1"
IMAGES_DIR = os.path.expanduser("~/.openclaw/workspace/dashboard/images/real")

def flaresolverr_get_session(url: str) -> dict:
    """Get page through FlareSolverr and return session data"""
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
                "headers": solution.get("headers", {})
            }
        else:
            print(f"FlareSolverr error: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def download_with_session(image_url: str, session_data: dict, output_path: str) -> bool:
    """Download image using FlareSolverr session"""
    headers = {
        "User-Agent": session_data.get("user_agent", "Mozilla/5.0"),
        "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.chrono24.com/",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site"
    }
    
    # Create session with cookies
    session = requests.Session()
    for cookie in session_data.get("cookies", []):
        session.cookies.set(
            cookie.get("name"), 
            cookie.get("value"),
            domain=cookie.get("domain", ".chrono24.com")
        )
    
    try:
        print(f"  Downloading: {image_url[:70]}...")
        response = session.get(image_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type or len(response.content) > 1000:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"  ✅ Saved: {output_path} ({len(response.content):,} bytes)")
                return True
            else:
                print(f"  ⚠️  Not an image: {content_type}")
        else:
            print(f"  ❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return False

def get_watch_page_and_images(watch_id: str) -> list:
    """Get watch page and extract image URLs using session"""
    listing_url = f"https://www.chrono24.com/rolex/--id{watch_id}.htm"
    print(f"\n🔍 Fetching: {listing_url}")
    
    # Get session from FlareSolverr
    session_data = flaresolverr_get_session(listing_url)
    if not session_data:
        return []
    
    print(f"  ✅ Got session with {len(session_data.get('cookies', []))} cookies")
    
    # Now use the same session to get the page content
    headers = {
        "User-Agent": session_data.get("user_agent", "Mozilla/5.0"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.chrono24.com/"
    }
    
    session = requests.Session()
    for cookie in session_data.get("cookies", []):
        session.cookies.set(
            cookie.get("name"), 
            cookie.get("value"),
            domain=cookie.get("domain", ".chrono24.com")
        )
    
    try:
        response = session.get(listing_url, headers=headers, timeout=30)
        html = response.text
        print(f"  📄 Got {len(html):,} chars")
        
        # Extract image URLs - look for the main product images
        # Pattern: cdn.chrono24.com/images/uhren/{watch_id}-{hash}-{size}.jpg
        patterns = [
            rf'https://cdn\.chrono24\.com/images/uhren/{watch_id}-[^"\'\s<>]+?\.jpg',
            rf'https://cdn2\.chrono24\.com/images/uhren/{watch_id}-[^"\'\s<>]+?\.jpg',
        ]
        
        image_urls = []
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            image_urls.extend(matches)
        
        # Deduplicate and convert to Original size
        unique_urls = []
        for url in set(image_urls):
            # Convert any size to Original
            url = re.sub(r'-(?:Square|Square140|ExtraLarge|Large|Medium)[^/]*\.jpg', '-Original.jpg', url, flags=re.IGNORECASE)
            if url not in unique_urls:
                unique_urls.append(url)
        
        print(f"  🖼️  Found {len(unique_urls)} unique images")
        return unique_urls[:3], session_data  # Return top 3
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return [], session_data

if __name__ == "__main__":
    print("🏛️ Downloading Real Watch Images")
    print("=" * 80)
    
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    # Watches to download
    watches = [
        ("43520266", "1601"),  # Blue Sigma
        ("43563233", "1601"),  # Deep Blue
    ]
    
    total_downloaded = 0
    
    for watch_id, watch_ref in watches:
        image_urls, session_data = get_watch_page_and_images(watch_id)
        
        if not image_urls or not session_data:
            print(f"  ⚠️  Skipping {watch_ref} - no images found")
            continue
        
        # Download each image
        for i, img_url in enumerate(image_urls):
            filename = f"{watch_ref}_{watch_id}_{i+1}.jpg"
            output_path = os.path.join(IMAGES_DIR, filename)
            
            if download_with_session(img_url, session_data, output_path):
                total_downloaded += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Complete: Downloaded {total_downloaded} images")
    
    # List files
    if os.path.exists(IMAGES_DIR):
        files = os.listdir(IMAGES_DIR)
        if files:
            print(f"\nFiles in {IMAGES_DIR}:")
            for f in sorted(files):
                path = os.path.join(IMAGES_DIR, f)
                size = os.path.getsize(path)
                print(f"  - {f} ({size:,} bytes)")
