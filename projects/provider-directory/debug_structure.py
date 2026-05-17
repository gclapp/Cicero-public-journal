#!/usr/bin/env python3
"""Debug the actual HTML structure of Healthgrades provider cards."""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    """Debug provider card structure."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National"
        
        print(f"Loading: {url}")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Get HTML of first provider card
        print("\n🔍 ANALYZING PROVIDER CARD STRUCTURE:\n")
        
        # Try to find provider cards
        selectors = [
            'article',
            '[data-testid*="provider"]',
            '[data-testid*="result"]',
            '[class*="provider"]',
            '[class*="result"]',
            'a[href*="/physician/"]',
        ]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"\n{selector}: {len(elements)} elements")
                if len(elements) > 0:
                    # Get HTML of first element
                    html = await elements[0].evaluate('el => el.outerHTML')
                    print(f"  First element HTML (truncated):")
                    print(f"  {html[:500]}...")
        
        # Look for specific data points
        print("\n\n🔍 LOOKING FOR SPECIFIC DATA:\n")
        
        # Name
        name_selectors = ['h3', 'h2', 'h1', '[class*="name"]', 'a[href*="/physician/"]']
        for sel in name_selectors:
            elems = await page.query_selector_all(sel)
            if elems:
                texts = []
                for e in elems[:3]:
                    text = await e.text_content()
                    if text and len(text.strip()) > 5:
                        texts.append(text.strip()[:50])
                if texts:
                    print(f"{sel}: {texts}")
        
        # Address
        print("\nAddress elements:")
        addr_selectors = ['address', '[class*="address"]', '[class*="location"]', '[data-testid*="address"]']
        for sel in addr_selectors:
            elems = await page.query_selector_all(sel)
            if elems:
                texts = []
                for e in elems[:3]:
                    text = await e.text_content()
                    if text:
                        texts.append(text.strip()[:100])
                if texts:
                    print(f"{sel}: {texts}")
        
        # Save screenshot
        await page.screenshot(path="debug_structure.png", full_page=False)
        print("\n📸 Screenshot saved: debug_structure.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
