#!/usr/bin/env python3
"""Get profile URLs and ACTUAL specialties from search results - fixed."""

import asyncio
import json
import sqlite3
from playwright.async_api import async_playwright

DB_PATH = '/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db'

async def get_data_from_page(page_num, context):
    """Get profile URLs and specialties from one search results page."""
    page = await context.new_page()
    
    url = f"https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&pt=32.67194%2C-117.105423&distances=National&payors=HPY00006F7&pageNum={page_num}&sort.provider=bestmatch"
    
    try:
        print(f"Page {page_num}...", end=' ', flush=True)
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        # Extract name, URL, and ACTUAL specialty
        results = await page.evaluate('''() => {
            const data = [];
            const h3s = document.querySelectorAll('h3[data-qa-target="provider-name"]');
            
            for (let i = 0; i < h3s.length; i++) {
                const h3 = h3s[i];
                const linkEl = h3.querySelector('a[data-qa-target="provider-name-link"]');
                
                if (linkEl) {
                    const name = linkEl.textContent.trim();
                    const profileUrl = 'https://www.healthgrades.com' + linkEl.getAttribute('href');
                    
                    // Get the parent and find specialty
                    const parent = h3.parentElement;
                    let specialty = 'REI Specialist';
                    
                    if (parent) {
                        const specEl = parent.querySelector('[data-qa-target="provider-specialty"]');
                        if (specEl) {
                            const specText = specEl.textContent.trim();
                            // Remove "Specialty: " prefix if present
                            specialty = specText.replace(/^Specialty:\s*/, '');
                        }
                    }
                    
                    // Skip if specialty contains "Healthy Living" (it's a UI element, not a specialty)
                    if (specialty.includes('Healthy Living')) {
                        specialty = 'REI Specialist';
                    }
                    
                    data.push({name, profileUrl, specialty});
                }
            }
            
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
    print("Getting profile URLs and specialties from search results...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        all_data = []
        
        # Get all 78 pages
        for page_num in range(1, 79):
            data = await get_data_from_page(page_num, context)
            all_data.extend(data)
            await asyncio.sleep(0.5)
        
        await browser.close()
    
    print(f"\nTotal providers scraped: {len(all_data)}")
    
    # Show samples
    print("\nSample specialties:")
    for item in all_data[:5]:
        print(f"  {item['name']}: {item['specialty']}")
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    updated_urls = 0
    updated_specs = 0
    
    for item in all_data:
        # Update URL
        conn.execute(
            "UPDATE providers SET source_url = ? WHERE name = ? AND source = 'healthgrades'",
            (item['profileUrl'], item['name'])
        )
        if conn.total_changes > 0:
            updated_urls += 1
        
        # Update specialty (replace "Healthy Living Newsletter")
        conn.execute(
            "UPDATE providers SET specialties = ? WHERE name = ? AND source = 'healthgrades' AND specialties LIKE '%Healthy Living%'",
            (json.dumps([item['specialty']]), item['name'])
        )
        if conn.total_changes > 0:
            updated_specs += 1
    
    conn.commit()
    
    # Check results
    with_urls = conn.execute("SELECT COUNT(*) FROM providers WHERE source = 'healthgrades' AND source_url IS NOT NULL").fetchone()[0]
    healthy_living = conn.execute("SELECT COUNT(*) FROM providers WHERE source = 'healthgrades' AND specialties LIKE '%Healthy Living%'").fetchone()[0]
    conn.close()
    
    print(f"\nUpdated {updated_urls} providers with URLs")
    print(f"Updated {updated_specs} providers with actual specialties")
    print(f"Total with URLs: {with_urls}")
    print(f"Still with 'Healthy Living': {healthy_living}")

if __name__ == "__main__":
    asyncio.run(main())
