#!/usr/bin/env python3
"""
Chrono24 Watch Search with FlareSolverr - Full Implementation
Searches Chrono24 for 1973 Rolex Datejust watches and extracts listings
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import sys

FLARESOLVERR_URL = "http://localhost:8191/v1"

def flaresolverr_get(url: str) -> Optional[Dict]:
    """Use FlareSolverr to fetch a URL bypassing Cloudflare"""
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    
    try:
        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=65)
        data = response.json()
        
        if data.get("status") == "ok":
            return data.get("solution", {})
        else:
            print(f"FlareSolverr error: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error calling FlareSolverr: {e}")
        return None

def extract_watch_listings(html: str) -> List[Dict]:
    """Extract watch listings from Chrono24 HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    watches = []
    
    # Find all watch listing items
    # Chrono24 uses div with class 'article-item-container' for listings
    listings = soup.find_all('div', class_='article-item-container')
    
    for listing in listings:
        try:
            # Get watch ID from data attribute
            watch_id = listing.get('data-articleid', '') or listing.get('id', '')
            
            # Extract title - look for the watch name link
            title_elem = listing.find('a', class_=re.compile('article-title')) or \
                        listing.find('div', class_=re.compile('text-bold|headline')) or \
                        listing.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Extract price - look for price class
            price_elem = listing.find('div', class_=re.compile('price|amount')) or \
                        listing.find('span', class_=re.compile('price|amount'))
            price = price_elem.get_text(strip=True) if price_elem else 'Price on request'
            
            # Extract image URL
            img_elem = listing.find('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            
            # Extract listing URL
            link_elem = listing.find('a', href=True)
            listing_url = ''
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    listing_url = 'https://www.chrono24.com' + href
                elif href.startswith('http'):
                    listing_url = href
            
            # Extract reference number from title
            ref_match = re.search(r'(1601|1603|16013|16014|16233|16234|116233|116234)', title)
            reference = ref_match.group(1) if ref_match else 'Unknown'
            
            # Extract year
            year_match = re.search(r'19(70|71|72|73|74|75|76|77|78|79)', title)
            year = '1973' if year_match else 'Unknown'
            
            # Determine dial color
            dial_color = 'unknown'
            title_lower = title.lower()
            if 'blue' in title_lower:
                dial_color = 'blue'
            elif 'black' in title_lower:
                dial_color = 'black'
            elif 'silver' in title_lower:
                dial_color = 'silver'
            elif 'champagne' in title_lower or 'gold' in title_lower:
                dial_color = 'champagne'
            elif 'white' in title_lower:
                dial_color = 'white'
            
            # Determine case type
            case_type = 'Unknown'
            if 'steel' in title_lower and ('gold' in title_lower or 'two-tone' in title_lower):
                case_type = 'Two-tone'
            elif 'steel' in title_lower:
                case_type = 'Steel'
            elif 'gold' in title_lower:
                case_type = 'Gold'
            
            watch = {
                'id': watch_id,
                'title': title,
                'reference': reference,
                'year': year,
                'price': price,
                'dialColor': dial_color,
                'case': case_type,
                'imageUrl': image_url,
                'listingUrl': listing_url,
                'source': 'Chrono24',
                'dateFound': datetime.now().isoformat()
            }
            
            watches.append(watch)
            
        except Exception as e:
            print(f"Error parsing listing: {e}")
            continue
    
    return watches

def search_1973_datejusts() -> List[Dict]:
    """Search for 1973 Rolex Datejust watches on Chrono24"""
    print("🔍 Searching Chrono24 for 1973 Rolex Datejust watches...")
    
    # Build search URL for 1973 Datejusts
    search_url = "https://www.chrono24.com/search/index.htm?query=Rolex+DateJust+1973&dosearch=true&minYear=1973&maxYear=1973"
    
    result = flaresolverr_get(search_url)
    if not result:
        print("❌ Failed to fetch search results")
        return []
    
    html = result.get("response", "")
    print(f"📄 Received {len(html)} characters of HTML")
    
    watches = extract_watch_listings(html)
    print(f"✅ Found {len(watches)} watch listings")
    
    return watches

def filter_by_preferences(watches: List[Dict]) -> List[Dict]:
    """Filter watches based on Geoff's preferences"""
    favorites = []
    acceptable = []
    avoid = []
    
    for watch in watches:
        dial = watch.get('dialColor', '').lower()
        
        if dial in ['blue', 'black']:
            watch['preference'] = 'favorite'
            favorites.append(watch)
        elif dial in ['champagne', 'linen']:
            watch['preference'] = 'acceptable'
            acceptable.append(watch)
        elif dial in ['silver', 'white']:
            watch['preference'] = 'avoid'
            avoid.append(watch)
        else:
            watch['preference'] = 'unknown'
            acceptable.append(watch)
    
    return favorites + acceptable + avoid

def save_results(watches: List[Dict]):
    """Save search results to JSON file"""
    output = {
        'searchDate': datetime.now().isoformat(),
        'query': 'Rolex DateJust 1973',
        'totalFound': len(watches),
        'watches': watches
    }
    
    output_file = '/tmp/chrono24_1973_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Results saved to {output_file}")
    return output_file

def print_summary(watches: List[Dict]):
    """Print a summary of found watches"""
    if not watches:
        print("\n❌ No watches found")
        return
    
    print(f"\n📊 SUMMARY: Found {len(watches)} watches")
    print("=" * 80)
    
    favorites = [w for w in watches if w.get('preference') == 'favorite']
    acceptable = [w for w in watches if w.get('preference') == 'acceptable']
    avoid = [w for w in watches if w.get('preference') == 'avoid']
    
    print(f"\n🔵 Favorites (Blue/Black dials): {len(favorites)}")
    for w in favorites[:5]:
        print(f"  • {w['title'][:60]}... - {w['price']}")
    
    print(f"\n🟡 Acceptable (Champagne/Linen): {len(acceptable)}")
    for w in acceptable[:3]:
        print(f"  • {w['title'][:60]}... - {w['price']}")
    
    print(f"\n⚪ Avoid (Silver/White): {len(avoid)}")
    for w in avoid[:3]:
        print(f"  • {w['title'][:60]}... - {w['price']}")

if __name__ == "__main__":
    print("🏛️ Chrono24 Watch Search with FlareSolverr")
    print("=" * 80)
    
    # Search for watches
    watches = search_1973_datejusts()
    
    if watches:
        # Filter by preferences
        sorted_watches = filter_by_preferences(watches)
        
        # Save results
        output_file = save_results(sorted_watches)
        
        # Print summary
        print_summary(sorted_watches)
        
        print(f"\n✅ Search complete! Check {output_file} for full details")
    else:
        print("\n❌ No watches found or search failed")
        sys.exit(1)
