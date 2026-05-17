#!/usr/bin/env python3
"""Debug why we're only getting 36 unique providers instead of 1,559."""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    """Debug provider extraction across multiple pages."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Check page 1
        url1 = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National"
        print(f"Loading page 1...")
        await page.goto(url1, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        h3_elements = await page.query_selector_all('h3')
        names1 = []
        for h3 in h3_elements[:10]:
            text = await h3.text_content()
            if text:
                names1.append(text.strip())
        
        print(f"\nPage 1 first 10 names:")
        for i, name in enumerate(names1, 1):
            print(f"  {i}. {name}")
        
        # Check page 2
        url2 = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National&page=2"
        print(f"\nLoading page 2...")
        await page.goto(url2, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        h3_elements = await page.query_selector_all('h3')
        names2 = []
        for h3 in h3_elements[:10]:
            text = await h3.text_content()
            if text:
                names2.append(text.strip())
        
        print(f"\nPage 2 first 10 names:")
        for i, name in enumerate(names2, 1):
            print(f"  {i}. {name}")
        
        # Check page 10
        url10 = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National&page=10"
        print(f"\nLoading page 10...")
        await page.goto(url10, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        h3_elements = await page.query_selector_all('h3')
        names10 = []
        for h3 in h3_elements[:10]:
            text = await h3.text_content()
            if text:
                names10.append(text.strip())
        
        print(f"\nPage 10 first 10 names:")
        for i, name in enumerate(names10, 1):
            print(f"  {i}. {name}")
        
        # Compare
        print(f"\n\nComparison:")
        print(f"  Page 1 == Page 2: {names1 == names2}")
        print(f"  Page 1 == Page 10: {names1 == names10}")
        
        if names1 == names2:
            print("\n  ⚠️  PAGES ARE IDENTICAL - pagination not working!")
        else:
            print("\n  ✅ Pages have different providers")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
