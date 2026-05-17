#!/usr/bin/env python3
"""Debug the page structure to find correct selectors."""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&pt=32.67194%2C-117.105423&distances=National&payors=HPY00006F7&pageNum=1&sort.provider=bestmatch"
        
        print("Loading page...")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Check for h3 elements (names)
        h3_count = await page.evaluate('() => document.querySelectorAll("h3").length')
        print(f"\nFound {h3_count} h3 elements")
        
        # Get first few h3 texts
        h3_texts = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll("h3")).slice(0, 5).map(h => h.textContent.trim());
        }''')
        print("First 5 h3 texts:", h3_texts)
        
        # Check for links to physician pages
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href*="/physician/"]')).slice(0, 5).map(a => ({
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }));
        }''')
        print(f"\nFound {len(links)} physician links")
        print("Sample links:", links[:3])
        
        # Check page structure around first provider
        html_sample = await page.evaluate('''() => {
            const firstH3 = document.querySelector("h3");
            if (firstH3) {
                const parent = firstH3.closest("article, div[class], a");
                return parent ? parent.outerHTML.substring(0, 500) : "No parent found";
            }
            return "No h3 found";
        }''')
        print("\nHTML structure around first provider:")
        print(html_sample)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
