#!/usr/bin/env python3
"""
Download real watch images from Chrono24 using FlareSolverr
Fetches images through the proxy to bypass hotlink protection
"""

import requests
import json
import os
import re
import base64
from datetime import datetime

FLARESOLVERR_URL = "http://localhost:8191/v1"
IMAGES_DIR = os.path.expanduser("~/.openclaw/workspace/dashboard/images/real")

def flaresolverr_request(url: str, method: str = "GET", post_data: dict = None) -> dict:
    """Make request through FlareSolverr"""
    payload = {
        "cmd": f"request.{method.lower()}",
        "url": url,
        "maxTimeout": 60000
    }
    
    if post_data:
        payload["postData"] = json.dumps(post_data)
    
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

def extract_image_urls_from_page(html: str, watch_id: str) -> list:
    """Extract image URLs from Chrono24 listing page HTML"""
    # Look for image URLs in various formats
    patterns = [
        rf'cdn\.chrono24\.com/images/uhren/{watch_id}-[^"\'\s<>]+',
        rf'cdn2\.chrono24\.com/images/uhren/{watch_id}-[^"\'\s<>]+',
        rf'images/uhren/{watch_id}-[^"\'\s<>]+',
    ]
    
    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        all_matches.extend(matches)
    
    # Add https:// prefix and deduplicate
    urls = []
    for match in set(all_matches):
        if match.startswith('//'):
            url = 'https:' + match
        elif match.startswith('http'):
            url = match
        else:
            # Add full domain if missing
            url = 'https://cdn.chrono24.com/' + match
        # Replace size suffix with Original for full resolution
        url = re.sub(r'-Square_SIZE_\.(jpg|jpeg|png)', r'-Original.\1', url, flags=re.IGNORECASE)
        url = re.sub(r'-ExtraLarge\.(jpg|jpeg|png)', r'-Original.\1', url, flags=re.IGNORECASE)
        url = re.sub(r'-Square140\.(jpg|jpeg|png)', r'-Original.\1', url, flags=re.IGNORECASE)
        urls.append(url)
    
    return list(set(urls))

def download_image_via_flaresolverr(image_url: str, output_path: str) -> bool:
    """Download image through FlareSolverr"""
    print(f"  Downloading: {image_url[:80]}...")
    
    result = flaresolverr_request(image_url)
    if not result:
        return False
    
    # Check if we got a response
    response = result.get("response", "")
    
    # If response is base64 encoded image data
    if len(response) > 1000 and not response.startswith('<'):
        try:
            # Try to decode as base64
            image_data = base64.b64decode(response)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"  ✅ Saved (base64): {output_path}")
            return True
        except:
            pass
    
    # Otherwise try direct download with cookies from FlareSolverr
    cookies = result.get("cookies", [])
    headers = {
        "User-Agent": result.get("userAgent", "Mozilla/5.0"),
        "Referer": "https://www.chrono24.com/"
    }
    
    try:
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie.get("name"), cookie.get("value"))
        
        img_response = session.get(image_url, headers=headers, timeout=30)
        if img_response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            print(f"  ✅ Saved ({len(img_response.content)} bytes): {output_path}")
            return True
        else:
            print(f"  ❌ HTTP {img_response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return False

def get_watch_images(watch_id: str, watch_ref: str, max_images: int = 2) -> list:
    """Get images for a specific watch"""
    listing_url = f"https://www.chrono24.com/rolex/--id{watch_id}.htm"
    print(f"\n🔍 Fetching listing: {listing_url}")
    
    # Get listing page through FlareSolverr
    result = flaresolverr_request(listing_url)
    if not result:
        print("  ❌ Failed to fetch listing page")
        return []
    
    html = result.get("response", "")
    print(f"  📄 Got {len(html)} chars of HTML")
    
    # Extract image URLs
    image_urls = extract_image_urls_from_page(html, watch_id)
    print(f"  🖼️  Found {len(image_urls)} image URLs")
    
    if not image_urls:
        return []
    
    # Download images
    os.makedirs(IMAGES_DIR, exist_ok=True)
    downloaded = []
    
    for i, img_url in enumerate(image_urls[:max_images]):
        ext = img_url.split('.')[-1].split('?')[0] or 'jpg'
        filename = f"{watch_ref}_{watch_id}_{i+1}.{ext}"
        output_path = os.path.join(IMAGES_DIR, filename)
        
        if download_image_via_flaresolverr(img_url, output_path):
            downloaded.append(output_path)
    
    return downloaded

if __name__ == "__main__":
    print("🏛️ Downloading Real Watch Images from Chrono24")
    print("=" * 80)
    
    # Watches to download images for
    watches = [
        ("43520266", "1601"),  # Watch 3: 1973 Blue Sigma
        ("43563233", "1601"),  # Watch 4: 1973 Deep Blue
        ("45062642", "1601"),  # Watch 6: 1973 Blue Serviced
    ]
    
    all_downloaded = []
    
    for watch_id, watch_ref in watches:
        images = get_watch_images(watch_id, watch_ref)
        all_downloaded.extend(images)
    
    print("\n" + "=" * 80)
    print(f"✅ Download complete: {len(all_downloaded)} images")
    
    if all_downloaded:
        print("\nDownloaded files:")
        for img in all_downloaded:
            size = os.path.getsize(img)
            print(f"  - {os.path.basename(img)} ({size:,} bytes)")
    else:
        print("\n❌ No images downloaded")
