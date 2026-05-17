#!/usr/bin/env python3
"""Debug Healthgrades pagination."""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    """Debug pagination."""
    
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
        
        print("\n🔍 LOOKING FOR PAGINATION:")
        
        # Try various pagination selectors
        selectors = [
            'a[aria-label*="page" i]',
            'a[aria-label*="next" i]',
            '[class*="pagination"]',
            '[class*="page"]',
            'a:has-text("Next")',
            'button:has-text("Next")',
            'a:has-text(">")',
            'button:has-text(">")',
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\n  {selector}: {len(elements)} elements")
                    for i, elem in enumerate(elements[:3]):
                        text = await elem.text_content()
                        aria = await elem.get_attribute('aria-label')
                        href = await elem.get_attribute('href')
                        visible = await elem.is_visible()
                        print(f"    [{i}] text='{text}', aria='{aria}', visible={visible}")
            except Exception as e:
                print(f"  {selector}: error - {e}")
        
        # Look for any link with numbers (page numbers)
        print("\n🔢 LOOKING FOR PAGE NUMBERS:")
        all_links = await page.query_selector_all('a')
        page_links = []
        for link in all_links:
            try:
                text = await link.text_content()
                if text and text.strip().isdigit():
                    page_links.append(text.strip())
            except:
                pass
        
        if page_links:
            print(f"  Found page numbers: {page_links[:10]}")
        
        # Save screenshot
        await page.screenshot(path="debug_pagination.png", full_page=True)
        print("\n📸 Screenshot saved: debug_pagination.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
