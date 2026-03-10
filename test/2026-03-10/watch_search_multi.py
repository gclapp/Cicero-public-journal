#!/usr/bin/env python3
"""
Multi-Search Watch Scraper - Complete Edition
Handles multiple active searches across all watch sites with full parsing
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
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
    year = watch.get('year', 0)
    if not (search['years']['min'] <= year <= search['years']['max']):
        return False
    
    dial = watch.get('dialColor', '').lower()
    if dial not in [c.lower() for c in search['dialColors']]:
        return False
    
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


def extract_year_from_text(text):
    """Extract year from text - flexible matching"""
    if not text:
        return None
    # Look for 4-digit years in reasonable range
    matches = re.findall(r'(19[5-9]\d|20[0-2]\d)', str(text))
    if matches:
        return int(matches[0])
    return None


def create_watch_dict(reference, year, dial_color, case, price, image_url, link, source, title, search):
    """Create a standardized watch dictionary"""
    return {
        'reference': reference,
        'year': year,
        'dialColor': dial_color,
        'dialType': dial_color.capitalize() if dial_color else 'Unknown',
        'case': case,
        'size': '36mm',
        'bracelet': 'Unknown',
        'price': price,
        'source': source,
        'link': link,
        'imageUrl': image_url,
        'listingUrl': link,
        'notes': title[:200] if title else f"Ref {reference} from {source}",
        'searchId': search['id'],
        'searchName': search['name'],
        'brand': search['brand']
    }


# ==================== SITE-SPECIFIC SCRAPERS ====================

def search_chrono24(search):
    """Search Chrono24 for watches"""
    print(f"\n🔍 Searching Chrono24 for: {search['name']}")
    watches = []
    
    brand_slug = search['brand'].lower().replace(' ', '-')
    
    for model in search['modelNumbers']:
        try:
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
                    
                    link_elem = listing.css('a[href]')
                    if not link_elem:
                        continue
                    link = link_elem[0].attrib.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.chrono24.com{link}"
                    
                    img = listing.css('img')
                    title = img[0].attrib.get('alt', '') if img else ""
                    
                    year = extract_year_from_text(title) or extract_year_from_text(container.text)
                    if not year:
                        continue
                    
                    price = None
                    price_elem = container.css('[class*="price"], .amount')
                    if price_elem:
                        price = normalize_price(price_elem[0].text)
                    
                    image_url = img[0].attrib.get('src') or img[0].attrib.get('data-src') if img else None
                    
                    dial_color = normalize_dial_color(title)
                    
                    title_lower = title.lower()
                    if is_two_tone(title):
                        case = "Two-tone"
                    elif 'gold' in title_lower and 'steel' not in title_lower:
                        case = "Gold"
                    elif 'steel' in title_lower or 'stainless' in title_lower:
                        case = "Steel"
                    else:
                        case = "Unknown"
                    
                    watch = create_watch_dict(model, year, dial_color, case, price, image_url, link, 'Chrono24', title, search)
                    
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
        brand = search['brand'].replace(' ', '+')
        model = search['modelNumbers'][0] if search['modelNumbers'] else ''
        url = f"https://www.ebay.com/sch/i.html?_nkw={brand}+{model}&_sacat=260324&_ipg=240"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        listings = page.css('.s-item')
        print(f"    Found {len(listings)} listings")
        
        for listing in listings:
            try:
                title_elem = listing.css('.s-item__title')
                if not title_elem:
                    continue
                title = title_elem[0].text or ""
                if "Shop on eBay" in title or not title:
                    continue
                
                link_elem = listing.css('.s-item__link')
                if not link_elem:
                    continue
                link = link_elem[0].attrib.get('href', '')
                
                price_elem = listing.css('.s-item__price')
                price = normalize_price(price_elem[0].text) if price_elem else None
                
                img = listing.css('.s-item__image-img')
                image_url = img[0].attrib.get('src') if img else None
                
                year = extract_year_from_text(title)
                if not year:
                    continue
                
                dial_color = normalize_dial_color(title)
                
                title_lower = title.lower()
                if is_two_tone(title):
                    case = "Two-tone"
                elif 'gold' in title_lower:
                    case = "Gold"
                elif 'steel' in title_lower or 'stainless' in title_lower:
                    case = "Steel"
                else:
                    case = "Unknown"
                
                # Extract reference from title
                ref = search['modelNumbers'][0] if search['modelNumbers'] else 'Unknown'
                for model_num in search['modelNumbers']:
                    if model_num in title:
                        ref = model_num
                        break
                
                watch = create_watch_dict(ref, year, dial_color, case, price, image_url, link, 'eBay', title, search)
                
                if matches_search(watch, search):
                    watches.append(watch)
                    print(f"    ✅ Found: {ref} ({year}) - ${price or 'N/A'}")
                
            except Exception as e:
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from eBay")
        
    except Exception as e:
        print(f"  ❌ Error searching eBay: {e}")
    
    return watches


def search_bobs_watches(search):
    """Search Bob's Watches"""
    print(f"\n🔍 Searching Bob's Watches for: {search['name']}")
    watches = []
    
    try:
        # Bob's Watches organizes by brand/model
        brand = search['brand'].lower()
        
        # Try to search by model numbers
        for model in search['modelNumbers'][:2]:  # Limit to first 2 models
            try:
                # Bob's uses different URL patterns
                url = f"https://www.bobswatches.com/rolex/{model}.html"
                print(f"  Checking: {url}")
                
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
                
                # Look for product grid items
                products = page.css('.product-item-info, .product-item, [data-product-id]')
                print(f"    Found {len(products)} products")
                
                for product in products:
                    try:
                        title_elem = product.css('.product-item-link, .product-name a, h2 a')
                        if not title_elem:
                            continue
                        title = title_elem[0].text or ""
                        
                        link = title_elem[0].attrib.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://www.bobswatches.com{link}"
                        
                        price_elem = product.css('.price, .product-price')
                        price = normalize_price(price_elem[0].text) if price_elem else None
                        
                        img = product.css('.product-image-photo, img')
                        image_url = img[0].attrib.get('src') if img else None
                        
                        year = extract_year_from_text(title)
                        if not year:
                            continue
                        
                        dial_color = normalize_dial_color(title)
                        
                        title_lower = title.lower()
                        if is_two_tone(title):
                            case = "Two-tone"
                        elif 'gold' in title_lower:
                            case = "Gold"
                        elif 'steel' in title_lower:
                            case = "Steel"
                        else:
                            case = "Unknown"
                        
                        watch = create_watch_dict(model, year, dial_color, case, price, image_url, link, "Bob's Watches", title, search)
                        
                        if matches_search(watch, search):
                            watches.append(watch)
                            print(f"    ✅ Found: {model} ({year})")
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ⚠️  Could not fetch {url}: {e}")
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Bob's Watches")
        
    except Exception as e:
        print(f"  ❌ Error searching Bob's Watches: {e}")
    
    return watches


def search_bulang_sons(search):
    """Search Bulang & Sons"""
    print(f"\n🔍 Searching Bulang & Sons for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        
        # Try collection pages
        urls = [
            f"https://bulangandsons.com/collections/{brand}",
            f"https://bulangandsons.com/collections/{brand}-watches",
        ]
        
        for url in urls:
            try:
                print(f"  Checking: {url}")
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
                
                products = page.css('.product-card, .grid__item, [data-product-handle]')
                print(f"    Found {len(products)} products")
                
                for product in products:
                    try:
                        title_elem = product.css('.product-card__title, .h4, a[href*="/products/"]')
                        if not title_elem:
                            continue
                        title = title_elem[0].text or ""
                        
                        link = title_elem[0].attrib.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://bulangandsons.com{link}"
                        
                        price_elem = product.css('.price, .money')
                        price = normalize_price(price_elem[0].text) if price_elem else None
                        
                        img = product.css('.product-card__image, img')
                        image_url = img[0].attrib.get('src') or img[0].attrib.get('data-src') if img else None
                        
                        year = extract_year_from_text(title)
                        if not year:
                            continue
                        
                        # Check if any model number matches
                        ref = None
                        for model in search['modelNumbers']:
                            if model in title:
                                ref = model
                                break
                        
                        if not ref:
                            ref = search['modelNumbers'][0] if search['modelNumbers'] else 'Unknown'
                        
                        dial_color = normalize_dial_color(title)
                        
                        title_lower = title.lower()
                        if is_two_tone(title):
                            case = "Two-tone"
                        elif 'gold' in title_lower:
                            case = "Gold"
                        elif 'steel' in title_lower:
                            case = "Steel"
                        else:
                            case = "Unknown"
                        
                        watch = create_watch_dict(ref, year, dial_color, case, price, image_url, link, 'Bulang & Sons', title, search)
                        
                        if matches_search(watch, search):
                            watches.append(watch)
                            print(f"    ✅ Found: {ref} ({year})")
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ⚠️  Could not fetch {url}: {e}")
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Bulang & Sons")
        
    except Exception as e:
        print(f"  ❌ Error searching Bulang & Sons: {e}")
    
    return watches


def search_bezel(search):
    """Search Bezel"""
    print(f"\n🔍 Searching Bezel for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        model = search['modelNumbers'][0] if search['modelNumbers'] else ''
        
        url = f"https://www.getbezel.com/search?q={brand}+{model}"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        listings = page.css('[data-testid*="listing"], .listing-card, [class*="ListingCard"]')
        print(f"    Found {len(listings)} listings")
        
        for listing in listings:
            try:
                title_elem = listing.css('h3, [data-testid*="title"], .listing-title')
                if not title_elem:
                    continue
                title = title_elem[0].text or ""
                
                link_elem = listing.css('a[href*="/listing/"]')
                if not link_elem:
                    continue
                link = link_elem[0].attrib.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.getbezel.com{link}"
                
                price_elem = listing.css('[data-testid*="price"], .price')
                price = normalize_price(price_elem[0].text) if price_elem else None
                
                img = listing.css('img')
                image_url = img[0].attrib.get('src') if img else None
                
                year = extract_year_from_text(title)
                if not year:
                    continue
                
                ref = model
                for model_num in search['modelNumbers']:
                    if model_num in title:
                        ref = model_num
                        break
                
                dial_color = normalize_dial_color(title)
                
                title_lower = title.lower()
                if is_two_tone(title):
                    case = "Two-tone"
                elif 'gold' in title_lower:
                    case = "Gold"
                elif 'steel' in title_lower:
                    case = "Steel"
                else:
                    case = "Unknown"
                
                watch = create_watch_dict(ref, year, dial_color, case, price, image_url, link, 'Bezel', title, search)
                
                if matches_search(watch, search):
                    watches.append(watch)
                    print(f"    ✅ Found: {ref} ({year})")
                
            except Exception as e:
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Bezel")
        
    except Exception as e:
        print(f"  ❌ Error searching Bezel: {e}")
    
    return watches


def search_crown_and_caliber(search):
    """Search Crown & Caliber"""
    print(f"\n🔍 Searching Crown & Caliber for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        
        urls = [
            f"https://www.crownandcaliber.com/collections/{brand}",
            f"https://www.crownandcaliber.com/collections/all",
        ]
        
        for url in urls:
            try:
                print(f"  Checking: {url}")
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
                
                products = page.css('.product-card, .grid__item, [data-product-handle]')
                print(f"    Found {len(products)} products")
                
                for product in products:
                    try:
                        title_elem = product.css('.product-card__title, .product-title, a[href*="/products/"]')
                        if not title_elem:
                            continue
                        title = title_elem[0].text or ""
                        
                        # Check if this product matches our brand/models
                        brand_match = search['brand'].lower() in title.lower()
                        model_match = any(m in title for m in search['modelNumbers'])
                        
                        if not (brand_match or model_match):
                            continue
                        
                        link = title_elem[0].attrib.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://www.crownandcaliber.com{link}"
                        
                        price_elem = product.css('.price, .product-price')
                        price = normalize_price(price_elem[0].text) if price_elem else None
                        
                        img = product.css('.product-card__image, img')
                        image_url = img[0].attrib.get('src') if img else None
                        
                        year = extract_year_from_text(title)
                        if not year:
                            continue
                        
                        ref = search['modelNumbers'][0] if search['modelNumbers'] else 'Unknown'
                        for model in search['modelNumbers']:
                            if model in title:
                                ref = model
                                break
                        
                        dial_color = normalize_dial_color(title)
                        
                        title_lower = title.lower()
                        if is_two_tone(title):
                            case = "Two-tone"
                        elif 'gold' in title_lower:
                            case = "Gold"
                        elif 'steel' in title_lower:
                            case = "Steel"
                        else:
                            case = "Unknown"
                        
                        watch = create_watch_dict(ref, year, dial_color, case, price, image_url, link, 'Crown & Caliber', title, search)
                        
                        if matches_search(watch, search):
                            watches.append(watch)
                            print(f"    ✅ Found: {ref} ({year})")
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ⚠️  Could not fetch {url}: {e}")
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Crown & Caliber")
        
    except Exception as e:
        print(f"  ❌ Error searching Crown & Caliber: {e}")
    
    return watches


def search_watches_of_espionage(search):
    """Search Watches of Espionage marketplace"""
    print(f"\n🔍 Searching Watches of Espionage for: {search['name']}")
    watches = []
    
    try:
        brand = search['brand'].lower().replace(' ', '-')
        
        url = f"https://watchesofespionage.com/collections/{brand}"
        print(f"  Checking: {url}")
        
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        products = page.css('.product-item, .grid__item, [data-product-handle]')
        print(f"    Found {len(products)} products")
        
        for product in products:
            try:
                title_elem = product.css('.product-title, h3, a[href*="/products/"]')
                if not title_elem:
                    continue
                title = title_elem[0].text or ""
                
                # Check for model match
                model_match = any(m in title for m in search['modelNumbers'])
                if not model_match and search['modelNumbers']:
                    continue
                
                link = title_elem[0].attrib.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://watchesofespionage.com{link}"
                
                price_elem = product.css('.price')
                price = normalize_price(price_elem[0].text) if price_elem else None
                
                img = product.css('.product-image, img')
                image_url = img[0].attrib.get('src') if img else None
                
                year = extract_year_from_text(title)
                if not year:
                    continue
                
                ref = search['modelNumbers'][0] if search['modelNumbers'] else 'Unknown'
                for model in search['modelNumbers']:
                    if model in title:
                        ref = model
                        break
                
                dial_color = normalize_dial_color(title)
                
                title_lower = title.lower()
                if is_two_tone(title):
                    case = "Two-tone"
                elif 'gold' in title_lower:
                    case = "Gold"
                elif 'steel' in title_lower:
                    case = "Steel"
                else:
                    case = "Unknown"
                
                watch = create_watch_dict(ref, year, dial_color, case, price, image_url, link, 'WoE', title, search)
                
                if matches_search(watch, search):
                    watches.append(watch)
                    print(f"    ✅ Found: {ref} ({year})")
                
            except Exception as e:
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from WoE")
        
    except Exception as e:
        print(f"  ❌ Error searching WoE: {e}")
    
    return watches


def search_watchrecon(search):
    """Search WatchRecon - watch forum aggregator"""
    print(f"\n🔍 Searching WatchRecon for: {search['name']}")
    watches = []
    
    try:
        for model in search['modelNumbers'][:2]:
            try:
                query = f"{search['brand']} {model}".replace(' ', '+')
                url = f"https://www.watchrecon.com/?query={query}"
                print(f"  Checking: {url}")
                
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
                
                listings = page.css('.listing-item, [data-listing-id], .search-result')
                print(f"    Found {len(listings)} listings")
                
                for listing in listings[:15]:
                    try:
                        title_elem = listing.css('.listing-title, .title, h3, a')
                        if not title_elem:
                            continue
                        title = title_elem[0].text or ""
                        
                        link_elem = listing.css('a[href*="/listing/"], a[href]')
                        if not link_elem:
                            continue
                        link = link_elem[0].attrib.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://www.watchrecon.com{link}"
                        
                        price_elem = listing.css('.price, .listing-price')
                        price = normalize_price(price_elem[0].text) if price_elem else None
                        
                        year = extract_year_from_text(title)
                        if not year:
                            continue
                        
                        ref = model
                        for model_num in search['modelNumbers']:
                            if model_num in title:
                                ref = model_num
                                break
                        
                        dial_color = normalize_dial_color(title)
                        
                        title_lower = title.lower()
                        if is_two_tone(title):
                            case = "Two-tone"
                        elif 'gold' in title_lower:
                            case = "Gold"
                        elif 'steel' in title_lower:
                            case = "Steel"
                        else:
                            case = "Unknown"
                        
                        watch = create_watch_dict(ref, year, dial_color, case, price, None, link, 'WatchRecon', title, search)
                        
                        if matches_search(watch, search):
                            watches.append(watch)
                            print(f"    ✅ Found: {ref} ({year})")
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ⚠️  Error with model {model}: {e}")
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from WatchRecon")
        
    except Exception as e:
        print(f"  ❌ Error searching WatchRecon: {e}")
    
    return watches


def search_reddit_watchexchange(search):
    """Search Reddit r/Watchexchange via Pushshift API"""
    print(f"\n🔍 Searching Reddit r/Watchexchange for: {search['name']}")
    watches = []
    
    try:
        import requests
        
        for model in search['modelNumbers'][:2]:
            try:
                query = f"{search['brand']} {model}"
                # Use Pushshift API to search Reddit
                url = f"https://api.pullpush.io/reddit/search/submission/?q={query}&subreddit=Watchexchange&size=25&sort=desc"
                print(f"  Checking API for: {query}")
                
                response = requests.get(url, timeout=30)
                if response.status_code != 200:
                    print(f"    ⚠️  API returned {response.status_code}")
                    continue
                
                data = response.json()
                posts = data.get('data', [])
                print(f"    Found {len(posts)} posts")
                
                for post in posts:
                    try:
                        title = post.get('title', '')
                        if not title or '[WTS]' not in title:
                            continue
                        
                        year = extract_year_from_text(title)
                        if not year:
                            continue
                        
                        # Check if year is in range
                        if not (search['years']['min'] <= year <= search['years']['max']):
                            continue
                        
                        link = f"https://reddit.com{post.get('permalink', '')}"
                        
                        # Try to extract price from title
                        price_match = re.search(r'\$([\d,]+)', title)
                        price = f"${price_match.group(1)}" if price_match else None
                        
                        ref = model
                        for model_num in search['modelNumbers']:
                            if model_num in title:
                                ref = model_num
                                break
                        
                        dial_color = normalize_dial_color(title)
                        
                        title_lower = title.lower()
                        if is_two_tone(title):
                            case = "Two-tone"
                        elif 'gold' in title_lower:
                            case = "Gold"
                        elif 'steel' in title_lower:
                            case = "Steel"
                        else:
                            case = "Unknown"
                        
                        watch = create_watch_dict(ref, year, dial_color, case, price, None, link, 'Reddit r/Watchexchange', title, search)
                        
                        if matches_search(watch, search):
                            watches.append(watch)
                            print(f"    ✅ Found: {ref} ({year}) - {price or 'Price in post'}")
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ⚠️  Error with model {model}: {e}")
                continue
        
        print(f"  📊 Found {len(watches)} matching watches from Reddit")
        
    except Exception as e:
        print(f"  ❌ Error searching Reddit: {e}")
    
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
        elif source == 'watchrecon':
            all_watches.extend(search_watchrecon(search))
        elif source == 'reddit_watchexchange':
            all_watches.extend(search_reddit_watchexchange(search))
    
    return all_watches


def main():
    """Main entry point - runs all active searches"""
    print("🏛️ Multi-Search Watch Hunt")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    config = load_config()
    data = load_watches()
    
    active_searches = [s for s in config['searches'] if s['status'] == 'active']
    
    if not active_searches:
        print("⚠️  No active searches found!")
        return 0
    
    print(f"📋 Found {len(active_searches)} active search(es)")
    print()
    
    original_count = len(data['watches'])
    total_new = 0
    
    for search in active_searches:
        watches = run_search(search)
        
        existing_links = {w['link'] for w in data['watches']}
        
        for watch in watches:
            if watch['link'] not in existing_links:
                watch['id'] = get_next_id(data['watches'])
                watch['dateAdded'] = datetime.now().strftime('%Y-%m-%d')
                watch['status'] = 'pending_review'
                watch['geoffRating'] = None
                watch['geoffNotes'] = None
                
                data['watches'].append(watch)
                existing_links.add(watch['link'])
                total_new += 1
                print(f"  ➕ Added: {watch['reference']} ({watch['year']}) - {watch['dialColor']} dial")
        
        search['watchesFound'] = len([w for w in data['watches'] if w.get('searchId') == search['id']])
        search['lastRun'] = datetime.now().isoformat()
    
    data['lastUpdated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    save_watches(data)
    save_config(config)
    
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
