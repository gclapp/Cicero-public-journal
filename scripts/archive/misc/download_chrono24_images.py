#!/usr/bin/env python3
"""
Download real watch images from Chrono24 using FlareSolverr
"""

import requests
import json
import os
import re
from datetime import datetime

FLARESOLVERR_URL = "http://localhost:8191/v1"
IMAGES_DIR = os.path.expanduser("~/.openclaw/workspace/dashboard/images/real")

def flaresolverr_get(url: str) -> dict:
    """Use FlareSolverr to fetch a URL"""
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
        print(f"Error: {e}")
        return None

def extract_image_urls(html: str, watch_id: str) -> list:
    """Extract image URLs from Chrono24 listing page"""
    # Look for image URLs in the HTML
    # Pattern: cdn.chrono24.com/images/uhren/{watch_id}
    pattern = rf'cdn\.chrono24\.com/images/uhren/{watch_id}-[^"\'\s<>]*\.(?:jpg|jpeg|png)'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    # Add https:// prefix and deduplicate
    urls = []
    for match in set(matches):
        if match.startswith('//'):
            url = 'https:' + match
        elif match.startswith('http'):
            url = match
        else:
            url = 'https://' + match
        urls.append(url)
    
    return urls

def download_image(url: str, filename: str) -> bool:
    """Download an image using FlareSolverr"""
    result = flaresolverr_get(url)
    if result and result.get("response"):
        # For images, we need to use the cookies/session to download
        # Try direct download with requests using the same session
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"Download error: {e}")
    return False

def get_watch_images(watch_id: str, watch_ref: str) -> list:
    """Get images for a specific watch"""
    url = f"https://www.chrono24.com/rolex/--id{watch_id}.htm"
    print(f"Fetching: {url}")
    
    result = flaresolverr_get(url)
    if not result:
        return []
    
    html = result.get("response", "")
    image_urls = extract_image_urls(html, watch_id)
    
    print(f"Found {len(image_urls)} images")
    
    # Download first image
    downloaded = []
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    for i, img_url in enumerate(image_urls[:2]):  # Download up to 2 images
        ext = img_url.split('.')[-1].split('?')[0]
        filename = os.path.join(IMAGES_DIR, f"{watch_ref}_{watch_id}_{i+1}.{ext}")
        
        print(f"Downloading: {img_url}")
        if download_image(img_url, filename):
            print(f"✅ Saved: {filename}")
            downloaded.append(filename)
        else:
            print(f"❌ Failed to download")
    
    return downloaded

if __name__ == "__main__":
    # Test with one of our watches
    # Watch ID 3: 43520266
    # Watch ID 4: 43563233
    
    print("🏛️ Downloading real watch images from Chrono24")
    print("=" * 80)
    
    # Try to get images for watch ID 3 (1973 Datejust Blue Sigma)
    images = get_watch_images("43520266", "1601")
    
    if images:
        print(f"\n✅ Downloaded {len(images)} images")
        for img in images:
            print(f"  - {img}")
    else:
        print("\n❌ No images downloaded")
