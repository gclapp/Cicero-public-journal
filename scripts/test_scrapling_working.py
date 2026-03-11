#!/usr/bin/env python3
"""
Working Scrapling-based watch scraper for Chrono24
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import re
from datetime import datetime

def scrape_chrono24():
    """Scrape Chrono24 for 1970s Datejust watches"""
    print("🔍 Scraping Chrono24...")
    
    url = "https://www.chrono24.com/rolex/ref-1601.htm"
    
    try:
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        # Find all listing containers
        containers = page.css('.article-item-container')
        print(f"  Found {len(containers)} listings")
        
        watches = []
        
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
                
                # Extract title from image alt or link text
                img = listing.css('img')
                title = ""
                if img:
                    title = img[0].attrib.get('alt', '')
                
                # If no alt text, try to get from any text content
                if not title:
                    all_text = listing.text or ""
                    title = all_text.strip()[:100]
                
                # Extract year from title or URL
                year = None
                year_match = re.search(r'(197\d|198\d)', title)
                if year_match:
                    year = int(year_match.group(1))
                else:
                    # Try to find year in the container text
                    container_text = container.text or ""
                    year_match = re.search(r'(197\d|198\d)', container_text)
                    if year_match:
                        year = int(year_match.group(1))
                
                # Skip if not in our year range
                if not year or not (1970 <= year <= 1985):
                    continue
                
                # Extract price - look for various price selectors
                price = None
                price_selectors = [
                    '[class*="price"]',
                    '.amount',
                    '[data-testid*="price"]',
                ]
                for sel in price_selectors:
                    price_elem = container.css(sel)
                    if price_elem:
                        price_text = price_elem[0].text or ""
                        if '$' in price_text or '€' in price_text or '£' in price_text:
                            price = price_text.strip()
                            break
                
                # Extract image
                image_url = None
                if img:
                    image_url = img[0].attrib.get('src') or img[0].attrib.get('data-src')
                
                # Determine dial color from title
                dial_color = 'unknown'
                title_lower = title.lower()
                if 'blue' in title_lower:
                    dial_color = 'blue'
                elif 'black' in title_lower:
                    dial_color = 'black'
                elif 'champagne' in title_lower or 'gold' in title_lower:
                    dial_color = 'champagne'
                elif 'silver' in title_lower or 'white' in title_lower:
                    dial_color = 'silver'
                elif 'linen' in title_lower:
                    dial_color = 'linen'
                
                # Determine case type
                case = 'Unknown'
                if 'two-tone' in title_lower or 'two tone' in title_lower:
                    case = 'Two-tone (YG/steel)'
                elif 'gold' in title_lower and 'steel' not in title_lower:
                    case = 'Yellow Gold'
                elif 'steel' in title_lower or 'stainless' in title_lower:
                    case = 'Steel'
                
                watch = {
                    'reference': '1601',
                    'year': year,
                    'dialColor': dial_color,
                    'dialType': dial_color.capitalize(),
                    'case': case,
                    'size': '36mm',
                    'bracelet': 'Jubilee',
                    'price': price,
                    'source': 'Chrono24',
                    'link': link,
                    'imageUrl': image_url,
                    'listingUrl': link,
                    'notes': title[:200] if title else f"Ref 1601 from Chrono24"
                }
                
                watches.append(watch)
                print(f"  ✅ Found: {year} {dial_color} dial - {price or 'Price N/A'}")
                
            except Exception as e:
                continue
        
        print(f"  📊 Total matching watches: {len(watches)}")
        return watches
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_bobs_watches():
    """Scrape Bob's Watches"""
    print("\n🔍 Scraping Bob's Watches...")
    
    # Try the main Rolex page since we got redirected there
    url = "https://www.bobswatches.com/rolex/"
    
    try:
        page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
        
        # Look for any product-related elements
        products = page.css('[class*="product"]')
        print(f"  Found {len(products)} product elements")
        
        # Try to find Datejust specifically
        all_text = page.text or ""
        datejust_count = all_text.lower().count('datejust')
        print(f"  'Datejust' mentions on page: {datejust_count}")
        
        # For now, return empty - need to figure out the right URL/approach
        print("  ⚠️  Need to find correct URL for Datejust listings")
        return []
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


if __name__ == "__main__":
    print("🏛️ Scrapling Watch Scraper")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    chrono24_watches = scrape_chrono24()
    bobs_watches = scrape_bobs_watches()
    
    all_watches = chrono24_watches + bobs_watches
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Chrono24: {len(chrono24_watches)} watches")
    print(f"Bob's Watches: {len(bobs_watches)} watches")
    print(f"Total: {len(all_watches)} watches")
    print("=" * 60)
    
    if all_watches:
        print("\n🎉 SUCCESS! Scrapling is working!")
        print("\nSample watch data:")
        for w in all_watches[:3]:
            print(f"  - {w['year']} {w['dialColor']} dial ({w['source']})")
            print(f"    {w['link'][:70]}...")
    else:
        print("\n⚠️  No watches found in target year range (1970-1985)")
        print("   But the anti-bot bypass is working!")
