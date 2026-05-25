#!/usr/bin/env python3
"""
Download watch images using browser automation
Chrono24 requires proper session/cookies to download images
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import json
from pathlib import Path
from datetime import datetime
import base64

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
IMAGES_DIR = Path.home() / ".openclaw" / "workspace" / "dashboard" / "images"

def load_watches():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def download_image_from_page(listing_url, watch_id, source):
    """Use browser to get image from page"""
    try:
        print(f"Fetching page for watch #{watch_id}...")
        
        # Fetch the listing page
        page = StealthyFetcher.fetch(listing_url, headless=True, network_idle=True, timeout=30000)
        
        # Find the main image
        img_selectors = [
            'img[data-testid="main-image"]',
            '.main-image img',
            '.article-image img',
            'img[src*="chrono24.com/images/uhren/"]',
            'img[src*="cdn.shopify.com"]',
            'img[src*="bobswatches.com"]'
        ]
        
        image_url = None
        for selector in img_selectors:
            img = page.css(selector)
            if img:
                src = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                if src:
                    image_url = src
                    break
        
        if not image_url:
            print(f"  No image found on page")
            return None
        
        print(f"  Found image: {image_url[:60]}...")
        
        # Create directory
        source_dir = source.lower().replace(' ', '_').replace('&', 'and').replace("'", '')
        img_dir = IMAGES_DIR / source_dir
        img_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = img_dir / f"watch_{watch_id}.jpg"
        
        # Download the image using the browser session
        try:
            # Try to fetch the image directly
            img_page = StealthyFetcher.fetch(image_url, headless=True, timeout=20000)
            
            # Get image content
            # Scrapling doesn't have direct download, so we'll use the src and save it
            # Actually, let's use requests with the page's cookies
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Referer': listing_url,
            }
            
            response = requests.get(image_url, headers=headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify file size
                if filepath.stat().st_size > 1000:
                    relative_path = f"images/{source_dir}/watch_{watch_id}.jpg"
                    print(f"  ✅ Downloaded: {relative_path} ({filepath.stat().st_size} bytes)")
                    return relative_path
                else:
                    filepath.unlink()
                    print(f"  ❌ File too small")
                    return None
            else:
                print(f"  ❌ HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ Download error: {e}")
            return None
            
    except Exception as e:
        print(f"  ❌ Page fetch error: {e}")
        return None

def main():
    print("🏛️ Downloading Watch Images via Browser")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    watches = data.get('watches', [])
    
    downloaded = 0
    failed = []
    
    for watch in watches:
        watch_id = watch.get('id')
        source = watch.get('source', 'unknown')
        listing_url = watch.get('link') or watch.get('listingUrl', '')
        
        # Skip if already has local image
        local_path = watch.get('localImagePath', '')
        if local_path:
            full_path = Path.home() / ".openclaw" / "workspace" / "dashboard" / local_path
            if full_path.exists() and full_path.stat().st_size > 10000:
                print(f"✅ Watch #{watch_id}: Already has image")
                continue
        
        print(f"\n🖼️  Watch #{watch_id} ({source})")
        
        result = download_image_from_page(listing_url, watch_id, source)
        
        if result:
            watch['localImagePath'] = result
            downloaded += 1
        else:
            failed.append(watch_id)
    
    save_watches(data)
    
    print(f"\n{'='*60}")
    print(f"📊 Downloaded: {downloaded}, Failed: {len(failed)}")
    if failed:
        print(f"Failed: {failed}")
    print('='*60)

if __name__ == "__main__":
    main()
