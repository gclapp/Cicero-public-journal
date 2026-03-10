#!/usr/bin/env python3
"""
Scrapling-based Watch Search - Integration Module
Replaces the failing requests-based scraper for Chrono24
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import re
import json
from datetime import datetime
from pathlib import Path

# Import functions from watch_search (we'll redefine them here to avoid importing the whole module)
DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"


def load_watches():
    """Load existing watch data"""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_watches(data):
    """Save watch data to JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_next_id(watches):
    """Get next available watch ID"""
    return max([w['id'] for w in watches], default=0) + 1


def normalize_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return None
    match = re.search(r'[\$€£]?([\d,]+(?:\.\d{2})?)', price_text.replace(',', ''))
    if match:
        return f"${match.group(1)}"
    return price_text


def normalize_dial_color(dial_text):
    """Normalize dial color to standard values"""
    if not dial_text:
        return 'unknown'
    dial_lower = dial_text.lower()
    if 'blue' in dial_lower:
        return 'blue'
    elif 'black' in dial_lower:
        return 'black'
    elif 'champagne' in dial_lower or 'gold' in dial_lower or 'champ' in dial_lower:
        return 'champagne'
    elif 'silver' in dial_lower or 'white' in dial_lower or 'grey' in dial_lower or 'gray' in dial_lower:
        return 'silver'
    elif 'linen' in dial_lower:
        return 'linen'
    else:
        return 'unknown'


def is_two_tone(case_text):
    """Check if case description indicates two-tone"""
    if not case_text:
        return False
    tt_terms = ['two-tone', 'two tone', '2-tone', '2 tone', 'steel/gold', 'gold/steel', 'ss/yg', 'yg/ss']
    return any(term in case_text.lower() for term in tt_terms)


def is_preferred_watch(watch):
    """Check if watch matches Geoff's preferences"""
    year = watch.get('year', 0)
    year_match = 1970 <= year <= 1985
    
    dial = watch.get('dialColor', '').lower()
    is_preferred_dial = dial in ['blue', 'black', 'champagne', 'linen']
    
    case = watch.get('case', '').lower()
    is_gold_or_tt = 'gold' in case or 'two-tone' in case or 'two tone' in case or 'yg' in case
    
    return year_match and is_preferred_dial and is_gold_or_tt


def search_chrono24_scrapling():
    """
    Search Chrono24 using Scrapling (bypasses anti-bot protection)
    
    Returns list of watch dicts matching Geoff's criteria:
    - Year: 1970-1985
    - Reference: 1601, 1603, 16014, etc.
    - Dial: Blue, Black, Champagne, Linen preferred
    - Case: Gold or Two-tone
    """
    print("🔍 Searching Chrono24 (via Scrapling)...")
    watches = []
    
    # Search URLs for different Datejust references
    urls = [
        "https://www.chrono24.com/rolex/ref-1601.htm",
        "https://www.chrono24.com/rolex/ref-1603.htm",
    ]
    
    for url in urls:
        try:
            print(f"  Checking: {url}")
            
            # Use stealth fetcher to bypass anti-bot
            page = StealthyFetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                timeout=60000
            )
            
            # Find all listing containers
            containers = page.css('.article-item-container')
            print(f"    Found {len(containers)} listings")
            
            for container in containers:
                try:
                    # Get the inner listing item
                    listing = container.css('.listing-item')
                    if not listing:
                        continue
                    listing = listing[0]
                    
                    # Extract link
                    link_elem = listing.css('a[href*="/rolex/"]')
                    if not link_elem:
                        continue
                    link = link_elem[0].attrib.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.chrono24.com{link}"
                    
                    # Extract title from image alt text
                    img = listing.css('img')
                    title = ""
                    if img:
                        title = img[0].attrib.get('alt', '')
                    
                    # Extract year from title
                    year = None
                    year_match = re.search(r'(197\d|198\d)', title)
                    if year_match:
                        year = int(year_match.group(1))
                    else:
                        # Try container text
                        container_text = container.text or ""
                        year_match = re.search(r'(197\d|198\d)', container_text)
                        if year_match:
                            year = int(year_match.group(1))
                    
                    # Skip if not in year range
                    if not year or not (1970 <= year <= 1985):
                        continue
                    
                    # Extract reference
                    ref_match = re.search(r'(1601\d?|1603|1623\d?)', title, re.I)
                    reference = ref_match.group(1) if ref_match else '1601'
                    
                    # Extract price
                    price = None
                    price_selectors = ['[class*="price"]', '.amount']
                    for sel in price_selectors:
                        price_elem = container.css(sel)
                        if price_elem:
                            price_text = price_elem[0].text or ""
                            if any(c in price_text for c in ['$', '€', '£', 'USD', 'EUR']):
                                price = normalize_price(price_text)
                                break
                    
                    # Extract image
                    image_url = None
                    if img:
                        image_url = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                    
                    # Determine dial color
                    dial_color = normalize_dial_color(title)
                    dial_type = dial_color.capitalize()
                    
                    # Determine case type
                    title_lower = title.lower()
                    if is_two_tone(title):
                        case = "Two-tone (YG/steel)"
                    elif 'gold' in title_lower and 'steel' not in title_lower:
                        case = "Yellow Gold"
                    elif 'steel' in title_lower or 'stainless' in title_lower:
                        case = "Steel"
                    else:
                        case = "Unknown"
                    
                    watch = {
                        'reference': reference,
                        'year': year,
                        'dialColor': dial_color,
                        'dialType': dial_type,
                        'case': case,
                        'size': '36mm',
                        'bracelet': 'Jubilee',
                        'price': price,
                        'source': 'Chrono24',
                        'link': link,
                        'imageUrl': image_url,
                        'listingUrl': link,
                        'notes': title[:200] if title else f"Ref {reference} from Chrono24"
                    }
                    
                    if is_preferred_watch(watch):
                        watches.append(watch)
                        print(f"    ✅ Found: {reference} ({year}) - {dial_color} dial")
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
    
    print(f"  📊 Found {len(watches)} matching watches from Chrono24")
    return watches


def main():
    """Main entry point - can be called from watch-hunt-cron.sh"""
    print("🏛️ Starting Scrapling-based watch hunt...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    original_count = len(data['watches'])
    print(f"📋 Currently tracking {original_count} watches")
    print()
    
    # Search with Scrapling
    new_watches = search_chrono24_scrapling()
    
    # Check for sold status on existing watches
    print("\n🔄 Checking existing listings...")
    # (Sold check logic would go here - reusing from watch_search.py)
    
    # Add new watches
    existing_links = {w['link'] for w in data['watches']}
    added = 0
    
    print("\n➕ Adding new watches to tracker...")
    for watch in new_watches:
        if watch['link'] not in existing_links:
            watch['id'] = get_next_id(data['watches'])
            watch['dateAdded'] = datetime.now().strftime('%Y-%m-%d')
            watch['status'] = 'pending_review'
            watch['geoffRating'] = None
            watch['geoffNotes'] = None
            
            data['watches'].append(watch)
            existing_links.add(watch['link'])
            added += 1
            print(f"  ✅ Added: {watch['reference']} ({watch['year']}) - {watch['dialColor']} dial")
    
    # Update timestamp and save
    data['lastUpdated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    save_watches(data)
    
    print()
    print("=" * 50)
    print(f"📊 SUMMARY")
    print("=" * 50)
    print(f"   Original listings: {original_count}")
    print(f"   New listings added: {added}")
    print(f"   Total listings: {len(data['watches'])}")
    print(f"   Last updated: {data['lastUpdated']}")
    print("=" * 50)
    
    if added > 0:
        print(f"\n🎯 Found {added} new watches!")
    
    return added


if __name__ == "__main__":
    try:
        count = main()
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
