#!/usr/bin/env python3
"""Get profile URLs from search results - fixed selectors."""

import asyncio
import json
import sqlite3
from playwright.async_api import async_playwright

DB_PATH = '/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db'

async def get_urls_from_page(page_num, context):
    """Get profile URLs from one search results page."""
    page = await context.new_page()
    
    url = f"https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&pt=32.67194%2C-117.105423&distances=National&payors=HPY00006F7&pageNum={page_num}&sort.provider=bestmatch"
    
    try:
        print(f"Page {page_num}...", end=' ', flush=True)
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        # Extract name, URL, and specialty
        results = await page.evaluate('''() => {
            const data = [];
            const h3s = document.querySelectorAll('h3[data-qa-target="provider-name"]');
            
            h3s.forEach(h3 => {
                const linkEl = h3.querySelector('a[data-qa-target="provider-name-link"]');
                const specialtyEl = h3.parentElement.querySelector('[data-qa-target="provider-specialty"]');
                
                if (linkEl) {
                    data.push({
                        name: linkEl.textContent.trim(),
                        url: 'https://www.healthgrades.com' + linkEl.getAttribute('href'),
                        specialty: specialtyEl ? specialtyEl.textContent.trim() : 'REI Specialist'
                    });
                }
            });
            
            return data;
        }''')
        
        await page.close()
        print(f"{len(results)} providers")
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        await page.close()
        return []

async def main():
    print("Getting profile URLs from search results...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        all_data = []
        
        # Get all 78 pages
        for page_num in range(1, 79):
            data = await get_urls_from_page(page_num, context)
            all_data.extend(data)
            await asyncio.sleep(0.5)
        
        await browser.close()
    
    print(f"\nTotal providers with URLs: {len(all_data)}")
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    updated = 0
    for item in all_data:
        conn.execute(
            "UPDATE providers SET source_url = ?, specialties = ? WHERE name = ? AND source = 'healthgrades'",
            (item['url'], json.dumps([item['specialty']]), item['name'])
        )
        if conn.total_changes > 0:
            updated += 1
    
    conn.commit()
    
    # Check how many now have URLs
    with_urls = conn.execute("SELECT COUNT(*) FROM providers WHERE source = 'healthgrades' AND source_url IS NOT NULL").fetchone()[0]
    conn.close()
    
    print(f"Updated {updated} providers")
    print(f"Total providers with URLs: {with_urls}")
    
    # Show samples
    print("\nSamples:")
    for item in all_data[:3]:
        print(f"  {item['name']}")
        print(f"    {item['url']}")

if __name__ == "__main__":
    asyncio.run(main())
