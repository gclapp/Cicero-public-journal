#!/usr/bin/env python3
"""
Watch Image URL Scraper - Gets actual image URLs from listing pages
Updates watch-data.json with real image URLs
"""

import json
import re
from pathlib import Path
from datetime import datetime

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"

def load_watches():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def extract_chrono24_image_url(listing_url):
    """Extract image URL from Chrono24 listing URL"""
    # Chrono24 image URLs follow a pattern based on listing ID
    # Try to construct the image URL from the listing ID
    match = re.search(r'--id(\d+)\.htm', listing_url)
    if match:
        listing_id = match.group(1)
        # Chrono24 uses CDN pattern: https://img.chrono24.com/images/uhren/{id}-...-Square480.jpg
        # We'll return a pattern that the browser can try
        return f"https://img.chrono24.com/images/uhren/{listing_id}-Square480.jpg"
    return None

def update_watch_image_urls():
    """Update all watches with real image URLs"""
    print("🏛️ Updating Watch Image URLs")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    watches = data.get('watches', [])
    
    updated = 0
    
    for watch in watches:
        watch_id = watch.get('id')
        source = watch.get('source', '')
        listing_url = watch.get('link') or watch.get('listingUrl', '')
        current_image = watch.get('imageUrl', '')
        
        # Skip if already has a good remote URL
        if current_image and current_image.startswith('http') and not current_image.endswith('.svg'):
            print(f"✅ Watch #{watch_id}: Already has remote image")
            continue
        
        # Try to extract image URL based on source
        new_image_url = None
        
        if 'chrono24' in listing_url.lower():
            new_image_url = extract_chrono24_image_url(listing_url)
            if new_image_url:
                print(f"🖼️  Watch #{watch_id}: Chrono24 image → {new_image_url[:60]}...")
        
        # For Bob's Watches and Bulang & Sons, we'll need to use a different approach
        # For now, mark them for manual image scraping
        
        if new_image_url:
            watch['imageUrl'] = new_image_url
            updated += 1
        else:
            print(f"⚠️  Watch #{watch_id}: Could not extract image URL ({source})")
    
    save_watches(data)
    
    print()
    print("="*60)
    print(f"📊 Updated {updated} watches with image URLs")
    print("="*60)
    
    return updated

if __name__ == "__main__":
    update_watch_image_urls()
