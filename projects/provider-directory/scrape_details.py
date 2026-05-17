#!/usr/bin/env python3
"""Simple script to scrape provider details in batches."""

import asyncio
import sqlite3
from datetime import datetime
from playwright.async_api import async_playwright

DB_PATH = '/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db'

async def scrape_page_details(page_num, browser):
    """Scrape one page for provider details."""
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()
    
    url = f"https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&pt=32.67194%2C-117.105423&distances=National&payors=HPY00006F7&pageNum={page_num}&sort.provider=bestmatch"
    
    try:
        print(f"  Scraping page {page_num}...")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Extract provider data from the page
        providers = await page.evaluate('''() => {
            const results = [];
            const cards = document.querySelectorAll('article, [data-test-id="provider-card"], .provider-card');
            
            cards.forEach(card => {
                const nameEl = card.querySelector('h3');
                const name = nameEl ? nameEl.textContent.trim() : '';
                
                // Get rating
                let rating = null;
                const ratingEl = card.querySelector('[data-test-id="star-rating"], .star-rating');
                if (ratingEl) {
                    const ratingText = ratingEl.textContent;
                    const match = ratingText.match(/(\\d+\\.?\\d*)/);
                    if (match) rating = parseFloat(match[1]);
                }
                
                // Get review count
                let reviews = null;
                const reviewEl = card.querySelector('.review-count, [data-test-id="review-count"]');
                if (reviewEl) {
                    const match = reviewEl.textContent.match(/(\\d+)/);
                    if (match) reviews = parseInt(match[1]);
                }
                
                // Get profile URL
                let profileUrl = null;
                const linkEl = card.querySelector('a[href*="/physician/"]');
                if (linkEl) {
                    profileUrl = 'https://www.healthgrades.com' + linkEl.getAttribute('href');
                }
                
                // Get phone
                let phone = null;
                const phoneEl = card.querySelector('a[href^="tel:"]');
                if (phoneEl) {
                    phone = phoneEl.textContent.trim();
                }
                
                if (name) {
                    results.push({name, rating, reviews, profileUrl, phone});
                }
            });
            
            return results;
        }''')
        
        await context.close()
        print(f"    Found {len(providers)} providers on page {page_num}")
        return providers
        
    except Exception as e:
        print(f"    Error on page {page_num}: {e}")
        await context.close()
        return []

async def main():
    print("Starting detail extraction...")
    print(f"Database: {DB_PATH}")
    
    # Get provider count from DB
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM providers WHERE source='healthgrades'").fetchone()[0]
    print(f"Total providers in DB: {total}")
    conn.close()
    
    # Scrape pages 1-10 first (test batch)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        all_providers = []
        for page_num in range(1, 11):  # First 10 pages
            providers = await scrape_page_details(page_num, browser)
            all_providers.extend(providers)
            await asyncio.sleep(1)  # Small delay between pages
        
        await browser.close()
    
    print(f"\nTotal providers scraped: {len(all_providers)}")
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    updated = 0
    for p in all_providers:
        if p['name']:
            conn.execute("""
                UPDATE providers 
                SET healthgrades_rating = ?,
                    review_count = ?,
                    source_url = ?,
                    phone = ?,
                    scraped_at = ?
                WHERE name = ? AND source = 'healthgrades'
            """, (
                p.get('rating'),
                p.get('reviews'),
                p.get('profileUrl'),
                p.get('phone'),
                datetime.now().isoformat(),
                p['name']
            ))
            if conn.total_changes > 0:
                updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"Updated {updated} providers in database")
    
    # Show sample
    print("\nSample providers with ratings:")
    for p in all_providers[:5]:
        if p.get('rating'):
            print(f"  {p['name']}: {p['rating']} stars, {p.get('reviews', 0)} reviews")

if __name__ == "__main__":
    asyncio.run(main())
