#!/usr/bin/env python3
"""
Watch Search Script - Searches for 1973 Rolex Datejust watches
Updates watch-data.json with new listings from real sources
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re
import time
import random

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
}

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
    match = re.search(r'\$?([\d,]+)', price_text.replace(',', ''))
    if match:
        return f"${match.group(1)}"
    return price_text

def normalize_dial_color(dial_text):
    """Normalize dial color to standard values"""
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
        return 'other'

def is_two_tone(case_text):
    """Check if case description indicates two-tone"""
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

def search_bobs_watches():
    """Search Bob's Watches for Datejust listings"""
    print("🔍 Searching Bob's Watches...")
    watches = []
    
    try:
        urls = [
            "https://www.bobswatches.com/rolex/datejust-36-1.html",
            "https://www.bobswatches.com/rolex/datejust-yellow_gold",
        ]
        
        for url in urls:
            try:
                print(f"  Checking: {url}")
                response = requests.get(url, headers=HEADERS, timeout=30)
                
                if response.status_code == 403:
                    print(f"  ⚠️  Access denied (403)")
                    continue
                    
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.find_all('div', class_=re.compile(r'product|listing|item|card', re.I))
                
                if not listings:
                    listings = soup.find_all('article')
                if not listings:
                    listings = soup.find_all('a', href=re.compile(r'/rolex/', re.I))
                
                print(f"  Found {len(listings)} potential listings")
                
                for listing in listings:
                    try:
                        link_elem = listing.find('a', href=True) if listing.name != 'a' else listing
                        if not link_elem:
                            continue
                        
                        href = link_elem.get('href', '')
                        title_text = link_elem.get_text(strip=True)
                        
                        ref_match = re.search(r'(1601\d?|1603|1623\d?)', title_text, re.I)
                        if not ref_match and href:
                            ref_match = re.search(r'(1601\d?|1603|1623\d?)', href, re.I)
                        
                        if not ref_match:
                            continue
                        
                        reference = ref_match.group(1)
                        
                        year_match = re.search(r'(197\d|198\d)', title_text)
                        year = int(year_match.group(1)) if year_match else None
                        
                        if not year or not (1970 <= year <= 1985):
                            continue
                        
                        price_elem = listing.find(['span', 'div'], class_=re.compile(r'price|cost', re.I))
                        price = normalize_price(price_elem.get_text(strip=True)) if price_elem else None
                        
                        dial_color = normalize_dial_color(title_text)
                        dial_type = dial_color.capitalize()
                        
                        if is_two_tone(title_text):
                            case = "Two-tone (YG/steel)"
                        elif 'gold' in title_text.lower() and 'steel' not in title_text.lower():
                            case = "Yellow Gold"
                        elif 'steel' in title_text.lower() or 'ss' in title_text.lower():
                            case = "Steel"
                        else:
                            case = "Unknown"
                        
                        if href.startswith('http'):
                            link = href
                        else:
                            link = f"https://www.bobswatches.com{href}"
                        
                        img_elem = listing.find('img')
                        image_url = None
                        if img_elem:
                            src = img_elem.get('src') or img_elem.get('data-src')
                            if src:
                                image_url = src if src.startswith('http') else f"https://www.bobswatches.com{src}"
                        
                        watch = {
                            'reference': reference,
                            'year': year,
                            'dialColor': dial_color,
                            'dialType': dial_type,
                            'case': case,
                            'size': '36mm',
                            'bracelet': 'Jubilee',
                            'price': price,
                            'source': "Bob's Watches",
                            'link': link,
                            'imageUrl': image_url,
                            'listingUrl': link,
                            'notes': f"Ref {reference} from Bob's Watches"
                        }
                        
                        if is_preferred_watch(watch):
                            watches.append(watch)
                            print(f"  ✅ Found: {reference} ({year}) - {dial_color} dial")
                        
                        time.sleep(random.uniform(0.3, 0.8))
                        
                    except Exception as e:
                        continue
                        
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"  ⚠️  Access denied (403)")
                continue
            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Bob's Watches")
        
    except Exception as e:
        print(f"  ❌ Error searching Bob's Watches: {e}")
    
    return watches

def search_chrono24():
    """Search Chrono24 for Datejust listings"""
    print("🔍 Searching Chrono24...")
    watches = []
    
    print("  ⚠️  Chrono24 blocks automated scraping (403 Forbidden)")
    print("  💡 Manual search: https://www.chrono24.com/rolex/ref-1601.htm")
    
    return watches

def search_bezel():
    """Search Bezel for Datejust listings"""
    print("🔍 Searching Bezel...")
    watches = []
    
    print("  ⚠️  Bezel requires manual search")
    print("  💡 Visit: https://www.getbezel.com")
    
    return watches

def search_bulang_sons():
    """Search Bulang & Sons for Datejust listings"""
    print("🔍 Searching Bulang & Sons...")
    watches = []
    
    try:
        url = "https://bulangandsons.com/collections/rolex-datejust"
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code == 403:
            print("  ⚠️  Access denied (403)")
            return watches
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        listings = soup.find_all('div', class_=re.compile(r'product|grid-item', re.I))
        
        for listing in listings:
            try:
                title_elem = listing.find(['h2', 'h3', 'h4', 'a'])
                if not title_elem:
                    continue
                
                title_text = title_elem.get_text(strip=True)
                
                if 'datejust' not in title_text.lower():
                    continue
                
                ref_match = re.search(r'(1601\d?|1603)', title_text, re.I)
                if not ref_match:
                    continue
                
                reference = ref_match.group(1)
                
                year_match = re.search(r'(197\d|198\d)', title_text)
                year = int(year_match.group(1)) if year_match else None
                
                if not year or not (1970 <= year <= 1985):
                    continue
                
                price_elem = listing.find(['span', 'div'], class_=re.compile(r'price|money', re.I))
                price = normalize_price(price_elem.get_text(strip=True)) if price_elem else None
                
                dial_color = normalize_dial_color(title_text)
                dial_type = dial_color.capitalize()
                
                if is_two_tone(title_text):
                    case = "Two-tone (YG/steel)"
                elif 'gold' in title_text.lower():
                    case = "Yellow Gold"
                else:
                    case = "Steel"
                
                link_elem = listing.find('a', href=True)
                link = None
                if link_elem:
                    href = link_elem['href']
                    link = href if href.startswith('http') else f"https://bulangandsons.com{href}"
                
                if not link:
                    continue
                
                img_elem = listing.find('img', src=True)
                image_url = None
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src:
                        image_url = src if src.startswith('http') else f"https:{src}" if src.startswith('//') else f"https://bulangandsons.com{src}"
                
                watch = {
                    'reference': reference,
                    'year': year,
                    'dialColor': dial_color,
                    'dialType': dial_type,
                    'case': case,
                    'size': '36mm',
                    'bracelet': 'Jubilee',
                    'price': price,
                    'source': 'Bulang & Sons',
                    'link': link,
                    'imageUrl': image_url,
                    'listingUrl': link,
                    'notes': f"Ref {reference} from Bulang & Sons"
                }
                
                if is_preferred_watch(watch):
                    watches.append(watch)
                    print(f"  ✅ Found: {reference} ({year}) - {dial_color} dial")
                
                time.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Bulang & Sons")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("  ⚠️  Access denied (403)")
    except Exception as e:
        print(f"  ❌ Error searching Bulang & Sons: {e}")
    
    return watches

def check_sold_status(watch):
    """Check if a watch listing is still active"""
    try:
        response = requests.head(watch['link'], headers=HEADERS, timeout=10, allow_redirects=True)
        if response.status_code == 404:
            return 'sold'
        if response.status_code in [301, 302]:
            if 'sold' in response.headers.get('Location', '').lower():
                return 'sold'
        return watch.get('status', 'pending_review')
    except:
        return watch.get('status', 'pending_review')

def main():
    print("🏛️ Starting watch hunt search...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    data = load_watches()
    original_count = len(data['watches'])
    
    print(f"📋 Currently tracking {original_count} watches")
    print()
    
    new_watches = []
    new_watches.extend(search_bobs_watches())
    new_watches.extend(search_chrono24())
    new_watches.extend(search_bulang_sons())
    new_watches.extend(search_bezel())
    
    print()
    print("🔄 Checking existing listings for sold status...")
    sold_count = 0
    for watch in data['watches']:
        if watch['status'] not in ['sold', 'passed']:
            new_status = check_sold_status(watch)
            if new_status == 'sold' and watch['status'] != 'sold':
                print(f"  ⚠️  Watch #{watch['id']} appears sold: {watch['reference']} - {watch['dialColor']} dial")
                watch['status'] = 'sold'
                sold_count += 1
    
    if sold_count == 0:
        print("  ✓ No sold listings detected")
    
    existing_links = {w['link'] for w in data['watches']}
    added = 0
    
    print()
    print("➕ Adding new watches to tracker...")
    
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
            print(f"  ✅ Added: {watch['reference']} ({watch['year']}) - {watch['dialColor']} dial from {watch['source']}")
    
    data['lastUpdated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    save_watches(data)
    
    print()
    print("=" * 50)
    print(f"📊 SUMMARY")
    print("=" * 50)
    print(f"   Original listings: {original_count}")
    print(f"   New listings added: {added}")
    print(f"   Listings marked sold: {sold_count}")
    print(f"   Total listings: {len(data['watches'])}")
    print(f"   Last updated: {data['lastUpdated']}")
    print("=" * 50)
    
    if added > 0:
        print()
        print(f"🎯 Found {added} new watches matching your criteria!")
    else:
        print()
        print("ℹ️  No new watches found this search.")
    
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
