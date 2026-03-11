#!/usr/bin/env python3
"""
Test Scrapling for watch hunting
Try to scrape Chrono24 and Bob's Watches using stealth features
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher, Fetcher
from scrapling.parser import Selector
import re
import json
from datetime import datetime

def test_chrono24():
    """Test scraping Chrono24 with StealthyFetcher"""
    print("=" * 60)
    print("🧪 Testing Chrono24 with StealthyFetcher")
    print("=" * 60)
    
    url = "https://www.chrono24.com/rolex/ref-1601.htm"
    
    try:
        print(f"\n📡 Fetching: {url}")
        print("⏳ This may take 10-30 seconds (browser automation)...")
        
        # Use stealth mode with headless browser
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,  # Wait for network to be idle
            timeout=60000  # 60 second timeout
        )
        
        print(f"✅ Page fetched successfully!")
        print(f"📄 Status: {page.status}")
        title_elem = page.css('title::text').get()
        print(f"🔤 Title: {title_elem if title_elem else 'No title found'}")
        
        # Try to find watch listings
        # Chrono24 uses various selectors, let's try common ones
        selectors_to_try = [
            '.article-item',
            '[data-testid="article-item"]',
            '.article-item-container',
            '.product-item',
            '.listing-item',
            'article[data-article-id]',
            '.m-b-3',
        ]
        
        listings = []
        for selector in selectors_to_try:
            listings = page.css(selector)
            if listings:
                print(f"\n✅ Found {len(listings)} listings with selector: {selector}")
                break
        
        if not listings:
            print("\n⚠️  No listings found with standard selectors")
            print("🔍 Let's check what elements are on the page...")
            
            # Try to find any article or product-like elements
            all_articles = page.css('article')
            all_divs = page.css('div[class*="item"]')
            print(f"   Found {len(all_articles)} <article> tags")
            print(f"   Found {len(all_divs)} divs with 'item' in class")
            
            # Save a snippet for debugging
            html_snippet = page.css('body')[0].html[:2000] if page.css('body') else "No body found"
            print(f"\n📄 First 2000 chars of body:\n{html_snippet}")
            
            return []
        
        # Extract watch data from listings
        watches = []
        for i, listing in enumerate(listings[:5]):  # Limit to first 5 for testing
            try:
                print(f"\n--- Listing {i+1} ---")
                
                # Try various selectors for title/price
                title = (listing.css('h2::text').get() or 
                        listing.css('.title::text').get() or
                        listing.css('[data-testid="article-title"]::text').get() or
                        listing.css('a::text').get() or
                        "Unknown")
                
                price = (listing.css('.price::text').get() or
                        listing.css('[data-testid="article-price"]::text').get() or
                        listing.css('.amount::text').get() or
                        "Price not found")
                
                link = listing.css('a::attr(href)').get() or ""
                if link and not link.startswith('http'):
                    link = f"https://www.chrono24.com{link}"
                
                print(f"   Title: {title.strip() if title else 'N/A'}")
                print(f"   Price: {price.strip() if price else 'N/A'}")
                print(f"   Link: {link[:60]}..." if len(link) > 60 else f"   Link: {link}")
                
                # Extract year if present
                year_match = re.search(r'(197\d|198\d)', title) if title else None
                year = int(year_match.group(1)) if year_match else None
                
                if year and 1970 <= year <= 1985:
                    watches.append({
                        'title': title.strip() if title else '',
                        'price': price.strip() if price else '',
                        'year': year,
                        'link': link,
                        'source': 'Chrono24'
                    })
                    
            except Exception as e:
                print(f"   ⚠️  Error parsing listing: {e}")
                continue
        
        print(f"\n✅ Found {len(watches)} watches from 1970-1985")
        return watches
        
    except Exception as e:
        print(f"\n❌ Error fetching Chrono24: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_bobs_watches():
    """Test scraping Bob's Watches"""
    print("\n" + "=" * 60)
    print("🧪 Testing Bob's Watches with StealthyFetcher")
    print("=" * 60)
    
    url = "https://www.bobswatches.com/rolex/datejust-36-1.html"
    
    try:
        print(f"\n📡 Fetching: {url}")
        print("⏳ This may take 10-30 seconds...")
        
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            timeout=60000
        )
        
        print(f"✅ Page fetched successfully!")
        print(f"📄 Status: {page.status}")
        title_elem = page.css('title::text').get()
        print(f"🔤 Title: {title_elem if title_elem else 'No title found'}")
        
        # Try to find listings
        selectors = [
            '.product-item',
            '.product-card',
            '[data-product]',
            '.grid-item',
        ]
        
        listings = []
        for selector in selectors:
            listings = page.css(selector)
            if listings:
                print(f"\n✅ Found {len(listings)} listings with selector: {selector}")
                break
        
        if not listings:
            print("\n⚠️  No listings found with standard selectors")
            all_products = page.css('[class*="product"]')
            print(f"   Found {len(all_products)} elements with 'product' in class")
            return []
        
        watches = []
        for i, listing in enumerate(listings[:3]):
            try:
                title = (listing.css('h2::text').get() or 
                        listing.css('.product-title::text').get() or
                        listing.css('a::text').get() or "Unknown")
                
                print(f"\n--- Listing {i+1} ---")
                print(f"   Title: {title.strip()[:80] if title else 'N/A'}")
                
            except Exception as e:
                continue
        
        return watches
        
    except Exception as e:
        print(f"\n❌ Error fetching Bob's Watches: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_simple_fetch():
    """Test basic fetch without browser"""
    print("\n" + "=" * 60)
    print("🧪 Testing simple HTTP fetch (no browser)")
    print("=" * 60)
    
    url = "https://www.chrono24.com/rolex/ref-1601.htm"
    
    try:
        print(f"\n📡 Fetching: {url}")
        page = Fetcher.get(url, stealthy_headers=True)
        
        print(f"✅ Page fetched!")
        print(f"📄 Status: {page.status}")
        title_elem = page.css('title::text').get()
        print(f"🔤 Title: {title_elem if title_elem else 'No title found'}")
        
        # Check if we got blocked
        if page.status != 200 or 'cloudflare' in page.text.lower() or 'captcha' in page.text.lower():
            print("\n⚠️  Likely blocked or got CAPTCHA challenge")
            print(f"   Page contains 'cloudflare': {'cloudflare' in page.text.lower()}")
            print(f"   Page contains 'captcha': {'captcha' in page.text.lower()}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🏛️ Scrapling Watch Hunt Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'chrono24': [],
        'bobs_watches': [],
        'simple_fetch': False
    }
    
    # Test 1: Simple fetch (likely to fail with 403)
    results['simple_fetch'] = test_simple_fetch()
    
    # Test 2: Chrono24 with stealth
    results['chrono24'] = test_chrono24()
    
    # Test 3: Bob's Watches with stealth
    results['bobs_watches'] = test_bobs_watches()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Simple HTTP fetch: {'✅ PASSED' if results['simple_fetch'] else '❌ FAILED'}")
    print(f"Chrono24 stealth:  {'✅ PASSED' if results['chrono24'] else '❌ FAILED'} ({len(results['chrono24'])} watches found)")
    print(f"Bob's Watches:     {'✅ PASSED' if results['bobs_watches'] else '❌ FAILED'} ({len(results['bobs_watches'])} watches found)")
    print("=" * 60)
    
    if results['chrono24'] or results['bobs_watches']:
        print("\n🎉 SUCCESS! Scrapling can bypass the anti-bot protection!")
        print("   Ready to integrate into watch_search.py")
    else:
        print("\n⚠️  No watches found yet, but the pages loaded.")
        print("   May need to adjust selectors based on actual page structure.")
