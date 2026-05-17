#!/usr/bin/env python3
"""Debug the correct pagination URL format for Healthgrades."""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    """Find the correct pagination URL pattern."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Load page 1
        url1 = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National"
        print(f"Loading page 1...")
        await page.goto(url1, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Get the current URL
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        # Look for pagination links and extract their hrefs
        print("\nLooking for pagination links...")
        
        # Try to find page 2 link
        page2_link = await page.query_selector('a[aria-label="Page 2"]')
        if page2_link:
            href = await page2_link.get_attribute('href')
            print(f"Page 2 link href: {href}")
            
            # Navigate to that URL
            full_url = f"https://www.healthgrades.com{href}"
            print(f"\nNavigating to: {full_url}")
            await page.goto(full_url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            # Get first provider name
            h3 = await page.query_selector('h3')
            if h3:
                name = await h3.text_content()
                print(f"First provider on page 2: {name}")
        
        # Also check what happens when we click the "Next Page" button
        print("\n\nNow trying to click 'Next Page' button...")
        await page.goto(url1, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        next_btn = await page.query_selector('a[aria-label="Next Page"]')
        if next_btn:
            href = await next_btn.get_attribute('href')
            print(f"Next Page button href: {href}")
            
            # Click it and see what URL we end up on
            await next_btn.click()
            await asyncio.sleep(5)
            
            new_url = page.url
            print(f"URL after clicking Next: {new_url}")
            
            h3 = await page.query_selector('h3')
            if h3:
                name = await h3.text_content()
                print(f"First provider after click: {name}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
