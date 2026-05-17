#!/usr/bin/env python3
"""Test California state search for REIs."""

import asyncio
from playwright.async_api import async_playwright


async def test():
    """Test CA state search."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Try Los Angeles as a proxy for CA
        url = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology&where=Los%20Angeles%20CA"
        
        print(f"Testing: {url}")
        
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        title = await page.title()
        print(f"Title: {title}")
        
        # Get result count from page text
        text = await page.text_content('body')
        
        # Look for results text
        import re
        match = re.search(r'(\d+)\s+results?', text, re.IGNORECASE)
        if match:
            print(f"✅ Found {match.group(1)} results")
        
        # Save screenshot
        await page.screenshot(path="hg_la_rei.png", full_page=True)
        print("📸 Saved: hg_la_rei.png")
        
        # Check for pagination
        pagination = await page.query_selector_all('a[aria-label*="Page"], [class*="pagination"]')
        print(f"Pagination elements: {len(pagination)}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test())
