#!/usr/bin/env python3
"""Explore Healthgrades state-based search."""

import asyncio
from playwright.async_api import async_playwright


async def explore():
    """Explore Healthgrades state search."""
    
    print("=" * 70)
    print("🔍 EXPLORING HEALTHGRADES STATE SEARCH")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Try different URL formats for state search
        urls_to_try = [
            "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinologist&where=California",
            "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinologist&where=CA",
            "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology&where=California",
            "https://www.healthgrades.com/usearch?what=REI&where=California",
            "https://www.healthgrades.com/usearch?what=Fertility%20Specialist&where=California",
        ]
        
        for i, url in enumerate(urls_to_try):
            print(f"\n{'='*60}")
            print(f"Test {i+1}: {url}")
            print('='*60)
            
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(5)
                
                title = await page.title()
                print(f"Title: {title}")
                
                # Check for results count
                content = await page.content()
                
                # Look for "results" text
                if "result" in content.lower():
                    # Try to extract result count
                    import re
                    match = re.search(r'(\d+)\s+results?', content, re.IGNORECASE)
                    if match:
                        print(f"✅ Found {match.group(1)} results")
                    else:
                        print("✅ Page has results")
                else:
                    print("⚠️  No results found on page")
                
                # Save screenshot
                await page.screenshot(path=f"hg_state_test_{i+1}.png")
                print(f"📸 Screenshot: hg_state_test_{i+1}.png")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(explore())
