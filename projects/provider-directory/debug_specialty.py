#!/usr/bin/env python3
"""Debug what the scraper is seeing for specialties."""

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
        
        # Check what the specialty element contains
        specialties = await page.evaluate('''() => {
            const results = [];
            const h3s = document.querySelectorAll('h3[data-qa-target="provider-name"]');
            
            h3s.slice(0, 3).forEach(h3 => {
                const nameEl = h3.querySelector('a[data-qa-target="provider-name-link"]');
                const specialtyEl = h3.parentElement.querySelector('[data-qa-target="provider-specialty"]');
                
                results.push({
                    name: nameEl ? nameEl.textContent.trim() : 'N/A',
                    specialty_html: specialtyEl ? specialtyEl.outerHTML : 'Not found',
                    specialty_text: specialtyEl ? specialtyEl.textContent.trim() : 'Not found'
                });
            });
            
            return results;
        }''')
        
        for s in specialties:
            print(f"\nProvider: {s['name']}")
            print(f"Specialty text: {s['specialty_text']}")
            print(f"HTML: {s['specialty_html'][:200]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
