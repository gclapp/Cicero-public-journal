#!/usr/bin/env python3
"""
Watch Image Downloader
Downloads watch images from URLs and saves them locally for the dashboard
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Paths
DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
IMAGES_DIR = Path.home() / ".openclaw" / "workspace" / "dashboard" / "images"

def load_watches():
    """Load watch data"""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    """Save watch data"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def download_image(url, watch_id, source):
    """Download image and save locally"""
    if not url:
        return None
    
    # Create source subdirectory
    source_dir = IMAGES_DIR / source.lower().replace(' ', '_').replace("'", '')
    source_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d')
    ext = '.jpg'
    if '.png' in url.lower():
        ext = '.png'
    elif '.webp' in url.lower():
        ext = '.webp'
    
    filename = f"watch_{watch_id}_{timestamp}{ext}"
    filepath = source_dir / filename
    
    # Skip if already exists
    if filepath.exists():
        return str(filepath.relative_to(Path.home() / ".openclaw" / "workspace" / "dashboard"))
    
    try:
        # Download with headers to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(data)
            
            print(f"  ✅ Downloaded: {filename}")
            return str(filepath.relative_to(Path.home() / ".openclaw" / "workspace" / "dashboard"))
            
    except Exception as e:
        print(f"  ⚠️  Failed to download image for watch {watch_id}: {e}")
        return None

def main():
    print("🏛️ Watch Image Downloader")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ensure images directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load watch data
    data = load_watches()
    watches = data.get('watches', [])
    
    print(f"📋 Processing {len(watches)} watches...")
    print()
    
    downloaded = 0
    failed = 0
    skipped = 0
    
    for watch in watches:
        watch_id = watch.get('id', 'unknown')
        image_url = watch.get('imageUrl')
        source = watch.get('source', 'unknown')
        
        # Skip if no image URL
        if not image_url:
            skipped += 1
            continue
        
        # Skip if already has local image
        if watch.get('localImagePath'):
            skipped += 1
            continue
        
        print(f"🔍 Watch #{watch_id} ({source}):")
        local_path = download_image(image_url, watch_id, source)
        
        if local_path:
            watch['localImagePath'] = local_path
            downloaded += 1
        else:
            failed += 1
    
    # Save updated data
    save_watches(data)
    
    print()
    print("=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"   Downloaded: {downloaded}")
    print(f"   Failed: {failed}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {len(watches)}")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
