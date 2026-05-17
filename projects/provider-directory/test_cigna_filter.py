#!/usr/bin/env python3
"""Test Healthgrades with Cigna insurance filter."""

import asyncio
from playwright.async_api import async_playwright


async def test():
    """Test national REI search with Cigna filter."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Try with insurance filter
        url = "https://www.healthgrades.com/usearch?what=Fertility%20Specialist&insurance=Cigna"
        
        print(f"Testing: {url}")
        
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
        
        # Check for pagination
        pagination = await page.query_selector_all('[class*="pagination"] a, a[aria-label*="Page"]')
        print(f"Pagination links: {len(pagination)}")
        
        # Save screenshot
        await page.screenshot(path="hg_cigna_fertility.png", full_page=True)
        print("📸 Saved: hg_cigna_fertility.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test())
