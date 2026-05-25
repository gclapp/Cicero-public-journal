#!/usr/bin/env python3
"""
Watch Image Scraper using Browser Automation
Uses Playwright/Scrapling to capture actual images from watch listing pages
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import json
from pathlib import Path
from datetime import datetime
import time

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
IMAGES_DIR = Path.home() / ".openclaw" / "workspace" / "dashboard" / "images"

def load_watches():
    """Load existing watch data"""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    """Save watch data to JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def scrape_chrono24_image(listing_url):
    """Scrape image from Chrono24 listing page"""
    try:
        print(f"   Fetching page: {listing_url[:60]}...")
        page = StealthyFetcher.fetch(listing_url, headless=True, network_idle=True, timeout=30000)
        
        # Look for main image
        # Chrono24 uses various selectors for main image
        selectors = [
            'img[data-testid="main-image"]',
            '.main-image img',
            '.product-image img',
            'img[alt*="Rolex"]',
            'img[src*="chrono24"]', 
            'img[src*="uhren"]'
        ]
        
        for selector in selectors:
            img = page.css(selector)
            if img:
                src = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                if src and ('chrono24' in src or 'uhren' in src):
                    # Get high-res version
                    src = src.replace('-Square140.jpg', '-Square480.jpg')
                    src = src.replace('-Square280.jpg', '-Square480.jpg')
                    return src
        
        return None
    except Exception as e:
        print(f"   ⚠️  Error scraping: {e}")
        return None

def scrape_bobs_watches_image(listing_url):
    """Scrape image from Bob's Watches listing page"""
    try:
        print(f"   Fetching page: {listing_url[:60]}...")
        page = StealthyFetcher.fetch(listing_url, headless=True, network_idle=True, timeout=30000)
        
        # Look for main product image
        selectors = [
            '.product-image img',
            '.gallery-image img',
            'img[alt*="Rolex"]',
            '.fotorama__stage img'
        ]
        
        for selector in selectors:
            img = page.css(selector)
            if img:
                src = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                if src:
                    return src
        
        return None
    except Exception as e:
        print(f"   ⚠️  Error scraping: {e}")
        return None

def download_image(url, filepath):
    """Download image from URL"""
    import requests
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': 'https://www.chrono24.com/',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Verify it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return False
        
        # Check size - must be > 1KB to be valid
        content_length = int(response.headers.get('content-length', 0))
        if content_length > 0 and content_length < 1024:
            return False
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify file size
        if filepath.stat().st_size < 1024:
            filepath.unlink()
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return False

def update_images_from_listings():
    """Scrape images directly from listing pages"""
    print("🏛️ Watch Image Scraper (Browser Automation)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    watches = data.get('watches', [])
    
    print(f"📋 Checking {len(watches)} watches for images...")
    print()
    
    updated = 0
    failed = 0
    skipped = 0
    
    for watch in watches:
        watch_id = watch.get('id', 'unknown')
        source = watch.get('source', 'unknown')
        listing_url = watch.get('link') or watch.get('listingUrl')
        
        # Skip if already has a good local image
        local_path = watch.get('localImagePath')
        if local_path:
            full_path = Path.home() / ".openclaw" / "workspace" / "dashboard" / local_path
            if full_path.exists() and full_path.stat().st_size > 10000:  # > 10KB
                skipped += 1
                continue
        
        # Skip if no listing URL
        if not listing_url:
            continue
        
        print(f"🖼️  Watch #{watch_id} ({source}):")
        
        # Scrape based on source
        image_url = None
        if 'chrono24' in listing_url.lower():
            image_url = scrape_chrono24_image(listing_url)
        elif 'bobswatches' in listing_url.lower():
            image_url = scrape_bobs_watches_image(listing_url)
        
        if not image_url:
            print(f"   ⚠️  Could not find image on page")
            failed += 1
            continue
        
        print(f"   Found image: {image_url[:60]}...")
        
        # Create filepath
        source_dir = source.lower().replace(' ', '_').replace('&', 'and')
        source_path = IMAGES_DIR / source_dir
        source_path.mkdir(parents=True, exist_ok=True)
        
        filepath = source_path / f"watch_{watch_id}_{datetime.now().strftime('%Y%m%d')}.jpg"
        
        # Download image
        if download_image(image_url, filepath):
            relative_path = filepath.relative_to(Path.home() / ".openclaw" / "workspace" / "dashboard")
            watch['imageUrl'] = image_url  # Update remote URL too
            watch['localImagePath'] = str(relative_path)
            updated += 1
            print(f"   ✅ Downloaded: {relative_path}")
        else:
            failed += 1
            print(f"   ❌ Failed to download image")
        
        time.sleep(1)  # Be polite
    
    # Save updated data
    save_watches(data)
    
    print()
    print("="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"   Already had images: {skipped}")
    print(f"   New images scraped: {updated}")
    print(f"   Failed: {failed}")
    print("="*60)
    
    return updated

if __name__ == "__main__":
    try:
        count = update_images_from_listings()
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
