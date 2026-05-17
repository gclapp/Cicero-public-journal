#!/usr/bin/env python3
"""Debug Healthgrades results count."""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    """Debug the results count."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        url = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National"
        
        print(f"Loading: {url}")
        print()
        
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Get page title
        title = await page.title()
        print(f"Title: {title}")
        print()
        
        # Get full page text
        text = await page.text_content('body')
        
        # Look for results text
        import re
        
        print("🔍 SEARCHING FOR RESULT COUNTS:")
        print()
        
        # Various patterns
        patterns = [
            r'(\d+,?\d*)\s+results?',
            r'We found (\d+,?\d*)',
            r'(\d+,?\d*)\s+doctors?',
            r'(\d+,?\d*)\s+providers?',
            r'(\d+,?\d*)\s+matches?',
            r'results?[:\s]+(\d+,?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  Pattern '{pattern}': {matches}")
        
        print()
        print("📄 PAGE TEXT SNIPPETS (looking for results):")
        
        # Find lines with "result" in them
        lines = text.split('\n')
        for line in lines:
            if 'result' in line.lower() and any(c.isdigit() for c in line):
                clean_line = line.strip()
                if len(clean_line) > 10 and len(clean_line) < 200:
                    print(f"  {clean_line}")
        
        print()
        print("🎯 COUNTING PROVIDER CARDS:")
        
        # Count different element types
        selectors = [
            'article',
            '[data-testid*="provider"]',
            '[data-testid*="doctor"]',
            '[class*="provider-card"]',
            '[class*="doctor-card"]',
            '[class*="search-result"]',
            'h3',
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"  {selector}: {len(elements)}")
            except:
                pass
        
        # Save screenshot
        await page.screenshot(path="debug_hg_results.png", full_page=True)
        print()
        print("📸 Screenshot saved: debug_hg_results.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug())
