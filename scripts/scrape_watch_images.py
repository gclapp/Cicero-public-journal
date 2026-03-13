#!/usr/bin/env python3
"""
Watch Image Scraper - Gets actual image URLs from listing pages
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import json
from pathlib import Path
from datetime import datetime
import time

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"

def load_watches():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def scrape_chrono24_image(listing_url):
    """Scrape image from Chrono24 listing"""
    try:
        print(f"   Fetching: {listing_url[:60]}...")
        page = StealthyFetcher.fetch(listing_url, headless=True, network_idle=True, timeout=30000)
        
        # Try multiple selectors for the main image
        selectors = [
            'img[data-testid="main-image"]',
            '.main-image img',
            '.article-image img',
            'img[src*="chrono24.com/images/uhren/"]'
        ]
        
        for selector in selectors:
            img = page.css(selector)
            if img:
                src = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                if src and 'chrono24' in src:
                    # Get high-res version
                    src = src.replace('-Square140.jpg', '-Square480.jpg')
                    src = src.replace('-Square280.jpg', '-Square480.jpg')
                    return src
        
        # Try to find any image with uhren in URL
        all_imgs = page.css('img')
        for img in all_imgs:
            src = img.attrib.get('src') or img.attrib.get('data-src', '')
            if 'chrono24.com/images/uhren/' in src:
                src = src.replace('-Square140.jpg', '-Square480.jpg')
                src = src.replace('-Square280.jpg', '-Square480.jpg')
                return src
        
        return None
    except Exception as e:
        print(f"   Error: {e}")
        return None

def scrape_bobs_watches_image(listing_url):
    """Scrape image from Bob's Watches"""
    try:
        print(f"   Fetching: {listing_url[:60]}...")
        page = StealthyFetcher.fetch(listing_url, headless=True, network_idle=True, timeout=30000)
        
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
        print(f"   Error: {e}")
        return None

def scrape_bulang_image(listing_url):
    """Scrape image from Bulang & Sons"""
    try:
        print(f"   Fetching: {listing_url[:60]}...")
        page = StealthyFetcher.fetch(listing_url, headless=True, network_idle=True, timeout=30000)
        
        selectors = [
            '.product-single__media img',
            '.product-image img',
            'img[src*="cdn.shopify.com"]'
        ]
        
        for selector in selectors:
            img = page.css(selector)
            if img:
                src = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                if src:
                    return src
        
        return None
    except Exception as e:
        print(f"   Error: {e}")
        return None

def main():
    print("🏛️ Scraping Watch Images from Listing Pages")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    watches = data.get('watches', [])
    
    updated = 0
    failed = 0
    
    # Only process watches that need images (SVG placeholders or missing)
    for watch in watches:
        watch_id = watch.get('id')
        source = watch.get('source', '')
        listing_url = watch.get('link') or watch.get('listingUrl', '')
        current_image = watch.get('imageUrl', '')
        
        # Skip if already has a good HTTP image URL
        if current_image and current_image.startswith('http') and not current_image.endswith('.svg'):
            print(f"✅ Watch #{watch_id}: Already has image")
            continue
        
        print(f"🖼️  Watch #{watch_id} ({source}):")
        
        image_url = None
        if 'chrono24' in source.lower():
            image_url = scrape_chrono24_image(listing_url)
        elif "Bob's Watches" in source:
            image_url = scrape_bobs_watches_image(listing_url)
        elif 'Bulang' in source:
            image_url = scrape_bulang_image(listing_url)
        
        if image_url:
            watch['imageUrl'] = image_url
            updated += 1
            print(f"   ✅ Found: {image_url[:60]}...")
        else:
            failed += 1
            print(f"   ❌ No image found")
        
        time.sleep(1)  # Be polite
    
    save_watches(data)
    
    print()
    print("="*60)
    print(f"📊 Updated {updated} watches, {failed} failed")
    print("="*60)

if __name__ == "__main__":
    main()
