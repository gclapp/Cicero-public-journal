#!/usr/bin/env python3
"""Test national REI search on Healthgrades."""

import asyncio
from playwright.async_api import async_playwright


async def test():
    """Test national REI search."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Try national search (no location)
        urls_to_try = [
            "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology",
            "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinologist",
            "https://www.healthgrades.com/usearch?what=Fertility%20Specialist",
        ]
        
        for url in urls_to_try:
            print(f"\n{'='*60}")
            print(f"Testing: {url}")
            print('='*60)
            
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(5)
                
                title = await page.title()
                print(f"Title: {title}")
                
                # Get result count
                text = await page.text_content('body')
                import re
                match = re.search(r'(\d+)\s+results?', text, re.IGNORECASE)
                if match:
                    print(f"✅ Found {match.group(1)} results")
                else:
                    print("⚠️  Could not determine result count")
                
                # Check for pagination
                pagination = await page.query_selector_all('[class*="pagination"] a, a[aria-label*="Page"]')
                print(f"Pagination links: {len(pagination)}")
                
                # Save screenshot
                safe_name = url.split('what=')[1].split('&')[0][:20]
                await page.screenshot(path=f"hg_national_{safe_name}.png", full_page=True)
                print(f"📸 Screenshot saved")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test())
