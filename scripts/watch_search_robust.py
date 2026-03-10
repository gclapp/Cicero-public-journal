#!/usr/bin/env python3
"""
Multi-Search Watch Scraper - Robust Edition
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import re
import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "watch-data.json"
CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "search-config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_watches():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_watches(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_next_id(watches):
    return max([w['id'] for w in watches], default=0) + 1

def normalize_price(price_text):
    if not price_text:
        return None
    match = re.search(r'[\$€£]?([\d,]+(?:\.\d{2})?)', str(price_text).replace(',', ''))
    if match:
        return f"${match.group(1)}"
    return price_text

def normalize_dial_color(dial_text):
    if not dial_text:
        return 'unknown'
    dial_lower = str(dial_text).lower()
    colors = {
        'blue': ['blue', 'navy', 'royal'],
        'black': ['black', 'matte black', 'gloss black'],
        'champagne': ['champagne', 'champ', 'gold', 'yellow gold'],
        'silver': ['silver', 'white', 'grey', 'gray', 'opaline'],
        'linen': ['linen', 'textured'],
        'green': ['green', 'olive', 'emerald'],
        'brown': ['brown', 'bronze', 'copper', 'chocolate'],
        'red': ['red', 'burgundy', 'maroon'],
    }
    for color, keywords in colors.items():
        if any(kw in dial_lower for kw in keywords):
            return color
    return 'unknown'

def is_two_tone(case_text):
    if not case_text:
        return False
    tt_terms = ['two-tone', 'two tone', '2-tone', '2 tone', 'steel/gold', 'gold/steel', 
                'ss/yg', 'yg/ss', 'steel-gold', 'bi-color', 'bicolor']
    return any(term in str(case_text).lower() for term in tt_terms)

def matches_search(watch, search):
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
    return has_material

def extract_year_from_text(text):
    if not text:
        return None
    matches = re.findall(r'(19[5-9]\d|20[0-2]\d)', str(text))
    if matches:
        return int(matches[0])
    return None

def get_text_from_selectors(element, selectors):
    for selector in selectors:
        try:
            elems = element.css(selector)
            if elems and len(elems) > 0:
                text = elems[0].text or elems[0].attrib.get('text', '') or elems[0].attrib.get('title', '')
                if text:
                    return text.strip()
        except:
            continue
    return ""

def get_attr_from_selectors(element, selectors, attr='href'):
    for selector in selectors:
        try:
            elems = element.css(selector)
            if elems and len(elems) > 0:
                val = elems[0].attrib.get(attr, '')
                if val:
                    return val
        except:
            continue
    return ""

def create_watch_dict(reference, year, dial_color, case, price, image_url, link, source, title, search):
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

# Import all site scrapers
from watch_search_sites import (
    search_chrono24, search_ebay, search_bobs_watches,
    search_bulang_sons, search_bezel, search_crown_and_caliber,
    search_watches_of_espionage, search_watchrecon, search_reddit_watchexchange
)

def run_search(search):
    print(f"\n{'='*60}")
    print(f"🎯 Running Search: {search['name']}")
    print(f"   Brand: {search['brand']}")
    print(f"   Models: {', '.join(search['modelNumbers'])}")
    print(f"   Years: {search['years']['min']}-{search['years']['max']}")
    print(f"{'='*60}")
    
    all_watches = []
    sources = search.get('sources', ['chrono24'])
    
    source_map = {
        'chrono24': search_chrono24,
        'ebay': search_ebay,
        'bobs_watches': search_bobs_watches,
        'bulang_sons': search_bulang_sons,
        'bezel': search_bezel,
        'crown_and_caliber': search_crown_and_caliber,
        'woe': search_watches_of_espionage,
        'watchrecon': search_watchrecon,
        'reddit_watchexchange': search_reddit_watchexchange,
    }
    
    for source in sources:
        if source in source_map:
            all_watches.extend(source_map[source](search))
    
    return all_watches

def main():
    print("🏛️ Multi-Search Watch Hunt - Robust Edition")
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
