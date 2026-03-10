#!/usr/bin/env python3
"""
Multi-Search Watch Scraper - Scrapling Edition
Handles multiple active searches across all watch sites
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher, Fetcher
import re
import json
from datetime import datetime
from pathlib import Path

# Paths
DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "search-config.json"


def load_config():
    """Load search configuration"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_config(config):
    """Save search configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


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
    match = re.search(r'[\$€£]?([\d,]+(?:\.\d{2})?)', str(price_text).replace(',', ''))
    if match:
        return f"${match.group(1)}"
    return price_text


def normalize_dial_color(dial_text):
    """Normalize dial color to standard values"""
    if not dial_text:
        return 'unknown'
    dial_lower = str(dial_text).lower()
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
    elif 'green' in dial_lower:
        return 'green'
    elif 'brown' in dial_lower:
        return 'brown'
    else:
        return 'unknown'


def is_two_tone(case_text):
    """Check if case description indicates two-tone"""
    if not case_text:
        return False
    tt_terms = ['two-tone', 'two tone', '2-tone', '2 tone', 'steel/gold', 'gold/steel', 'ss/yg', 'yg/ss', 'steel-gold']
    return any(term in str(case_text).lower() for term in tt_terms)


def matches_search(watch, search):
    """Check if a watch matches the search criteria"""
    # Check year range
    year = watch.get('year', 0)
    if not (search['years']['min'] <= year <= search['years']['max']):
        return False
    
    # Check dial color
    dial = watch.get('dialColor', '').lower()
    if dial not in [c.lower() for c in search['dialColors']]:
        return False
    
    # Check case material
    case = watch.get('case', '').lower()
    materials = [m.lower() for m in search['caseMaterials']]
    has_material = False
    for material in materials:
        if material == 'two-tone' and is_two_tone(case):
            has_material = True
            break
        elif material in case:
            has_material = True
            break
    
    if not has_material:
        return False
    
    return True


# ==================== SITE-SPECIFIC SCRAPERS ====================

def search_chrono24(search):
    """Search Chrono24 for watches matching the search criteria"""
    print(f"\n🔍 Searching Chrono24 for: {search['name']}")
    watches = []
    
    brand_slug = search['brand'].lower().replace(' ', '-')
    
    for model in search['modelNumbers']:
        try:
            # Build Chrono24 URL
            url = f"https://www.chrono24.com/{brand_slug}/ref-{model}.htm"
            print(f"  Checking: {url}")
            
            page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
            
            containers = page.css('.article-item-container')
            print(f"    Found {len(containers)} listings")
            
            for container in containers:
                try:
                    listing = container.css('.listing-item')
                    if not listing:
                        continue
                    listing = listing[0]
                    
                    # Extract link
                    link_elem = listing.css('a[href*="/rolex/"], a[href*="/omega/"], a[href*="/patek-philippe/"], a[href*="/cartier/"], a[href]')
                    if not link_elem:
                        continue
                    link = link_elem[0].attrib.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.chrono24.com{link}"
                    
                    # Extract title from image alt
                    img = listing.css('img')
                    title = ""
                    if img:
                        title = img[0].attrib.get('alt', '')
                    
                    # Extract year
                    year = None
                    year_match = re.search(r'(19\d\d|20\d\d)', title)
                    if year_match:
                        year = int(year_match.group(1))
                    else:
                        container_text = container.text or ""
                        year_match = re.search(r'(19\d\d|20\d\d)', container_text)
                        if year_match:
                            year = int(year_match.group(1))
                    
                    if not year:
                        continue
                    
                    # Extract price
                    price = None
                    price_elem = container.css('[class*="price"], .amount')
                    if price_elem:
                        price_text = price_elem[0].text or ""
                        price = normalize_price(price_text)
                    
                    # Extract image
                    image_url = None
                    if img:
                        image_url = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                    
                    # Determine dial color
                    dial_color = normalize_dial_color(title)
                    
                    # Determine case type
                    title_lower = title.lower()
                    if is_two_tone(title):
                        case = "Two-tone"
                    elif 'gold' in title_lower and 'steel' not in title_lower:
                        case = "Gold"
                    elif 'steel' in title_lower or 'stainless' in title_lower:
                        case = "Steel"
                    else:
                        case = "Unknown"
                    
                    watch = {
                        'reference': model,
                        'year': year,
                        'dialColor': dial_color,
                        'dialType': dial_color.capitalize(),
                        'case': case,
                        'size': '36mm',  # Default, could be extracted
                        'bracelet': 'Unknown',
                        'price': price,
                        'source': 'Chrono24',
                        'link': link,
                        'imageUrl': image_url,
                        'listingUrl': link,
                        'notes': title[:200] if title else f"Ref {model} from Chrono24",
                        'searchId': search['id'],
                        'searchName': search['name']
                    }
                    
                    if matches_search(watch, search):
                        watches.append(watch)
                        print(f"    ✅ Found: {model} ({year}) - {dial_color} dial")
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
    
    print(f"  📊 Found {len(watches)} matching watches from Chrono24")
    return watches


def search_ebay(search):
    """Search eBay for watches"""
    print(f"\n🔍 Searching eBay for: {search['name']}")
    watches = []
    
    try:
        # Build eBay search URL
        brand = search['brand'].replace(' ', '+')
        models = '+'.join(search['modelNumbers'])
        year_min = search['years']['min']
        year_max = search['years']['max']
        
        # eBay advanced search URL
        url = f"https://www.ebay.com/sch/i.html?_nkw={brand}+{models}&_sacat=260324"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        # eBay listings
        listings = page.css('.s-item')
        print(f"    Found {len(listings)} listings")
        
        # eBay processing stub - needs more development
        print(f"    ⚠️  eBay parsing not fully implemented yet")
        
    except Exception as e:
        print(f"  ❌ Error searching eBay: {e}")
    
    return watches


def search_bobs_watches(search):
    """Search Bob's Watches"""
    print(f"\n🔍 Searching Bob's Watches for: {search['name']}")
    watches = []
    
    try:
        # Try different URL patterns
        brand = search['brand'].lower().replace(' ', '-')
        urls_to_try = [
            f"https://www.bobswatches.com/{brand}/",
            "https://www.bobswatches.com/rolex/",
            "https://www.bobswatches.com/shop/",
        ]
        
        for url in urls_to_try:
            try:
                print(f"  Trying: {url}")
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
                
                # Look for product listings
                products = page.css('.product-item, .product-card, [class*="product"]')
                print(f"    Found {len(products)} product elements")
                
                if len(products) > 0:
                    # Check if any match our models
                    page_text = page.text or ""
                    for model in search['modelNumbers']:
                        if model in page_text:
                            print(f"    ✅ Found reference {model} mentioned on page")
                    
                    # For now, just acknowledge we can access the site
                    print(f"    ✅ Bob's Watches is accessible")
                    break
                    
            except Exception as e:
                print(f"    ⚠️  Failed: {e}")
                continue
                
    except Exception as e:
        print(f"  ❌ Error searching Bob's Watches: {e}")
    
    return watches


def search_bulang_sons(search):
    """Search Bulang & Sons"""
    print(f"\n🔍 Searching Bulang & Sons for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        url = f"https://bulangandsons.com/collections/{brand}"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        products = page.css('.product-item, .grid-item')
        print(f"    Found {len(products)} products")
        
        # Check for model numbers
        page_text = page.text or ""
        for model in search['modelNumbers']:
            if model in page_text:
                print(f"    ✅ Found reference {model} mentioned")
        
    except Exception as e:
        print(f"  ❌ Error searching Bulang & Sons: {e}")
    
    return watches


def search_bezel(search):
    """Search Bezel"""
    print(f"\n🔍 Searching Bezel for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        url = f"https://www.getbezel.com/search?q={brand}+{search['modelNumbers'][0]}"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        # Look for listings
        listings = page.css('[class*="listing"], [class*="product"], [class*="watch"]')
        print(f"    Found {len(listings)} potential listings")
        
    except Exception as e:
        print(f"  ❌ Error searching Bezel: {e}")
    
    return watches


def search_crown_and_caliber(search):
    """Search Crown & Caliber"""
    print(f"\n🔍 Searching Crown & Caliber for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', ' ')
        model = search['modelNumbers'][0]
        url = f"https://www.crownandcaliber.com/collections/{brand.lower().replace(' ', '-')}"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        products = page.css('.product-card, .product-item')
        print(f"    Found {len(products)} products")
        
    except Exception as e:
        print(f"  ❌ Error searching Crown & Caliber: {e}")
    
    return watches


def search_watches_of_espionage(search):
    """Search Watches of Espionage (WoE) marketplace"""
    print(f"\n🔍 Searching Watches of Espionage for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        url = f"https://watchesofespionage.com/collections/{brand}"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        products = page.css('.product-item, [class*="product"]')
        print(f"    Found {len(products)} products")
        
    except Exception as e:
        print(f"  ❌ Error searching WoE: {e}")
    
    return watches


# ==================== MAIN FUNCTIONS ====================

def run_search(search):
    """Run a single search across all configured sources"""
    print(f"\n{'='*60}")
    print(f"🎯 Running Search: {search['name']}")
    print(f"   Brand: {search['brand']}")
    print(f"   Models: {', '.join(search['modelNumbers'])}")
    print(f"   Years: {search['years']['min']}-{search['years']['max']}")
    print(f"{'='*60}")
    
    all_watches = []
    sources = search.get('sources', ['chrono24'])
    
    for source in sources:
        if source == 'chrono24':
            all_watches.extend(search_chrono24(search))
        elif source == 'ebay':
            all_watches.extend(search_ebay(search))
        elif source == 'bobs_watches':
            all_watches.extend(search_bobs_watches(search))
        elif source == 'bulang_sons':
            all_watches.extend(search_bulang_sons(search))
        elif source == 'bezel':
            all_watches.extend(search_bezel(search))
        elif source == 'crown_and_caliber':
            all_watches.extend(search_crown_and_caliber(search))
        elif source == 'woe':
            all_watches.extend(search_watches_of_espionage(search))
    
    return all_watches


def main():
    """Main entry point - runs all active searches"""
    print("🏛️ Multi-Search Watch Hunt")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load configuration
    config = load_config()
    data = load_watches()
    
    # Get active searches
    active_searches = [s for s in config['searches'] if s['status'] == 'active']
    
    if not active_searches:
        print("⚠️  No active searches found!")
        print("   Create a search with: python3 scripts/search_manager.py create ...")
        return 0
    
    print(f"📋 Found {len(active_searches)} active search(es)")
    print()
    
    original_count = len(data['watches'])
    total_new = 0
    
    # Run each active search
    for search in active_searches:
        watches = run_search(search)
        
        # Add watches to main data
        existing_links = {w['link'] for w in data['watches']}
        search_new_count = 0
        
        for watch in watches:
            if watch['link'] not in existing_links:
                watch['id'] = get_next_id(data['watches'])
                watch['dateAdded'] = datetime.now().strftime('%Y-%m-%d')
                watch['status'] = 'pending_review'
                watch['geoffRating'] = None
                watch['geoffNotes'] = None
                
                data['watches'].append(watch)
                existing_links.add(watch['link'])
                search_new_count += 1
                total_new += 1
                print(f"  ➕ Added: {watch['reference']} ({watch['year']}) - {watch['dialColor']} dial")
        
        # Update search stats
        search['watchesFound'] = len([w for w in data['watches'] if w.get('searchId') == search['id']])
        search['lastRun'] = datetime.now().isoformat()
    
    # Save updated data
    data['lastUpdated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    save_watches(data)
    save_config(config)
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"   Original listings: {original_count}")
    print(f"   New listings added: {total_new}")
    print(f"   Total listings: {len(data['watches'])}")
    print(f"   Active searches: {len(active_searches)}")
    print(f"   Last updated: {data['lastUpdated']}")
    print("="*60)
    
    if total_new > 0:
        print(f"\n🎉 Found {total_new} new watches across all searches!")
    else:
        print("\nℹ️  No new watches found this run.")
    
    return total_new


if __name__ == "__main__":
    try:
        count = main()
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
