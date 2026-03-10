#!/usr/bin/env python3
"""
Deep inspection test - figure out the actual HTML structure
"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/venvs/scrapling/lib/python3.12/site-packages')

from scrapling.fetchers import StealthyFetcher
import re

def inspect_chrono24():
    """Inspect Chrono24 page structure"""
    print("=" * 60)
    print("🔍 Inspecting Chrono24 HTML Structure")
    print("=" * 60)
    
    url = "https://www.chrono24.com/rolex/ref-1601.htm"
    
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
    
    # Get the HTML content - page is a Selector-like object
    html = str(page)
    
    print(f"\n📄 Page type: {type(page)}")
    print(f"📄 Page length: {len(html)} characters")
    print(f"📄 Page dir: {[m for m in dir(page) if not m.startswith('_')][:20]}")
    
    # Save full HTML for inspection
    with open('/tmp/chrono24_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("💾 Full HTML saved to /tmp/chrono24_page.html")
    
    # Look for article items we found
    containers = page.css('.article-item-container')
    print(f"\n✅ Found {len(containers)} .article-item-container elements")
    
    if containers:
        print("\n--- First container structure ---")
        first = containers[0]
        
        # Try to find the actual content
        print(f"HTML snippet:\n{str(first)[:800]}\n")
        
        # Look for title
        title_elem = first.css('h2, .title, [class*="title"], [class*="name"]')
        print(f"Found {len(title_elem)} potential title elements")
        for i, t in enumerate(title_elem[:3]):
            text = t.css('::text').get() or t.text
            print(f"  {i+1}. {text[:100] if text else 'No text'}")
        
        # Look for price
        price_elem = first.css('[class*="price"], .amount, [data-testid*="price"]')
        print(f"\nFound {len(price_elem)} potential price elements")
        for i, p in enumerate(price_elem[:3]):
            text = p.css('::text').get() or p.text
            print(f"  {i+1}. {text[:50] if text else 'No text'}")
        
        # Look for year in any text
        all_text = first.text
        year_matches = re.findall(r'(197\d|198\d)', all_text)
        print(f"\n📅 Years found in container: {year_matches}")
    
    # Try alternative selectors
    print("\n--- Alternative selectors ---")
    selectors = [
        'article',
        '[data-article-id]',
        '.article-item',
        '.product-item',
        '[class*="article"]',
        '[class*="listing"]',
    ]
    
    for sel in selectors:
        elems = page.css(sel)
        if len(elems) > 0:
            print(f"  {sel}: {len(elems)} elements")
    
    return containers


def inspect_bobs_watches():
    """Inspect Bob's Watches structure"""
    print("\n" + "=" * 60)
    print("🔍 Inspecting Bob's Watches HTML Structure")
    print("=" * 60)
    
    url = "https://www.bobswatches.com/rolex/datejust-36-1.html"
    
    page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
    
    html = page.html if hasattr(page, 'html') else str(page)
    
    print(f"\n📄 Page length: {len(html)} characters")
    print(f"🔤 Title: {page.css('title::text').get()}")
    
    # Save HTML
    with open('/tmp/bobs_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("💾 Full HTML saved to /tmp/bobs_page.html")
    
    # Check what we got redirected to
    print(f"\n🔄 Current URL content suggests: {'datejust' in html.lower()} datejust content")
    
    # Try various selectors
    selectors = [
        '.product-item',
        '.product-card',
        '[data-product]',
        '.grid-item',
        'article',
        '.product',
        '[class*="watch"]',
        '[class*="rolex"]',
    ]
    
    print("\n--- Selector results ---")
    for sel in selectors:
        elems = page.css(sel)
        if len(elems) > 0:
            print(f"  {sel}: {len(elems)} elements")
            if len(elems) > 0:
                # Show first element text sample
                text = elems[0].text[:100] if hasattr(elems[0], 'text') else 'N/A'
                print(f"    Sample: {text}...")


if __name__ == "__main__":
    print("🏛️ Scrapling Deep Inspection Test\n")
    
    inspect_chrono24()
    inspect_bobs_watches()
    
    print("\n" + "=" * 60)
    print("✅ Inspection complete!")
    print("Check /tmp/chrono24_page.html and /tmp/bobs_page.html")
    print("=" * 60)
