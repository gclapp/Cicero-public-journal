#!/usr/bin/env python3
"""
Watch Image Downloader
Downloads actual images from watch listings and updates watch-data.json
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import hashlib
import time

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
IMAGES_DIR = Path.home() / ".openclaw" / "workspace" / "dashboard" / "images"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
}

def load_watches():
    """Load existing watch data"""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    """Save watch data to JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_image_filename(watch_id, source, url):
    """Generate a unique filename for the image"""
    # Create source-specific directory
    source_dir = source.lower().replace(' ', '_').replace('&', 'and')
    source_path = IMAGES_DIR / source_dir
    source_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename from URL hash to avoid duplicates
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    ext = Path(url).suffix.split('?')[0]  # Remove query params
    if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        ext = '.jpg'
    
    return source_path / f"watch_{watch_id}_{url_hash}{ext}"

def download_image(url, filepath):
    """Download image from URL to filepath"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return False
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"    ❌ Failed to download: {e}")
        return False

def update_watch_images():
    """Main function to download images for all watches"""
    print("🏛️ Watch Image Downloader")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    watches = data.get('watches', [])
    
    print(f"📋 Checking {len(watches)} watches for images...")
    print()
    
    downloaded = 0
    failed = 0
    already_local = 0
    no_image_url = 0
    
    for watch in watches:
        watch_id = watch.get('id', 'unknown')
        source = watch.get('source', 'unknown')
        image_url = watch.get('imageUrl')
        local_path = watch.get('localImagePath')
        
        # Skip if already has local image
        if local_path and Path(local_path).exists():
            already_local += 1
            continue
        
        # Skip if no image URL
        if not image_url or image_url.startswith('data:image') or 'svg' in image_url.lower():
            no_image_url += 1
            continue
        
        print(f"🖼️  Watch #{watch_id} ({source}):")
        print(f"   URL: {image_url[:80]}...")
        
        # Determine filepath
        filepath = get_image_filename(watch_id, source, image_url)
        
        # Download the image
        if download_image(image_url, filepath):
            # Update watch data with local path
            relative_path = filepath.relative_to(Path.home() / ".openclaw" / "workspace" / "dashboard")
            watch['localImagePath'] = str(relative_path)
            downloaded += 1
            print(f"   ✅ Downloaded to: {relative_path}")
        else:
            failed += 1
            print(f"   ❌ Failed to download")
        
        # Small delay to be polite
        time.sleep(0.5)
    
    # Save updated data
    save_watches(data)
    
    print()
    print("="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"   Already had local images: {already_local}")
    print(f"   Newly downloaded: {downloaded}")
    print(f"   Failed downloads: {failed}")
    print(f"   No image URL available: {no_image_url}")
    print("="*60)
    
    return downloaded

def clean_broken_images():
    """Remove references to images that don't exist"""
    data = load_watches()
    watches = data.get('watches', [])
    
    cleaned = 0
    for watch in watches:
        local_path = watch.get('localImagePath')
        if local_path:
            full_path = Path.home() / ".openclaw" / "workspace" / "dashboard" / local_path
            if not full_path.exists():
                del watch['localImagePath']
                cleaned += 1
    
    if cleaned > 0:
        save_watches(data)
        print(f"🧹 Cleaned {cleaned} broken image references")
    
    return cleaned

if __name__ == "__main__":
    try:
        # First clean broken references
        clean_broken_images()
        
        # Then download new images
        count = update_watch_images()
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
