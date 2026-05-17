#!/usr/bin/env python3
"""
Extract detailed provider information from Healthgrades individual provider pages.
"""

import sqlite3
import asyncio
import re
import json
from urllib.parse import quote
from playwright.async_api import async_playwright

DB_PATH = '/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db'


def get_providers_to_process(limit=50):
    """Get providers that need data enrichment."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, first_name, last_name, street, city, state, zip, 
               phone, credentials, specialties, source_url
        FROM providers 
        WHERE source = 'healthgrades' 
        AND phone IS NULL
        AND city IS NOT NULL
        AND LENGTH(city) > 2
        AND LENGTH(city) < 50
        AND state IS NOT NULL
        AND LENGTH(state) = 2
        LIMIT ?
    ''', (limit,))
    
    providers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return providers


def construct_healthgrades_url(name, city, state):
    """Construct Healthgrades profile URL from provider info."""
    # Clean up the name
    name = name.replace('Dr. ', '').replace(',', '').strip()
    name_parts = name.split()
    
    if len(name_parts) >= 2:
        first = name_parts[0].lower()
        last = name_parts[-1].lower()
        city_clean = city.lower().replace(' ', '-')
        state_clean = state.lower()
        
        # Format: https://www.healthgrades.com/physician/dr-first-last-city
        url = f"https://www.healthgrades.com/physician/dr-{first}-{last}-{city_clean}"
        return url
    return None


async def extract_provider_data(page, url, provider):
    """Extract data from a Healthgrades provider page."""
    result = {
        'id': provider['id'],
        'name': provider['name'],
        'url': url,
        'phone': None,
        'credentials': None,
        'specialty': None,
        'photo_url': None,
        'success': False,
        'error': None
    }
    
    try:
        # Navigate to the page
        response = await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        
        if response and response.status == 404:
            result['error'] = 'Page not found (404)'
            return result
        
        # Wait for content to load
        await page.wait_for_timeout(3000)
        
        # Check if we got a valid provider page
        title = await page.title()
        if 'Not Found' in title or '404' in title:
            result['error'] = 'Page not found'
            return result
        
        # Try to find phone number
        phone_selectors = [
            'a[href^="tel:"]',
            '[data-testid*="phone"]',
            '.phone-number',
            '.office-phone',
            'span:has-text("(")',  # Phone numbers start with area code
        ]
        
        for selector in phone_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    text = await el.inner_text()
                    # Match US phone number pattern
                    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
                    if phone_match:
                        result['phone'] = phone_match.group(0)
                        break
                if result['phone']:
                    break
            except:
                continue
        
        # Try to find credentials (MD, DO, etc.)
        try:
            # Look for credentials in the title or headings
            heading = await page.query_selector('h1')
            if heading:
                heading_text = await heading.inner_text()
                cred_match = re.search(r',\s*(MD|DO|ND|PA|NP|CNP|APRN|LAC|RN|WHNP|FNP)[,.\s]', heading_text)
                if cred_match:
                    result['credentials'] = cred_match.group(1)
        except:
            pass
        
        # Try to find specialty
        specialty_selectors = [
            '[data-testid*="specialty"]',
            '.specialty',
            '.provider-specialty',
            'span:has-text("Reproductive")',
            'span:has-text("Endocrinology")',
            'span:has-text("OB-GYN")',
            'span:has-text("Gynecology")',
        ]
        
        for selector in specialty_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    text = await el.inner_text()
                    if any(keyword in text for keyword in ['Reproductive', 'Endocrinology', 'Infertility', 'OB-GYN', 'Gynecology']):
                        result['specialty'] = text.strip()
                        break
                if result['specialty']:
                    break
            except:
                continue
        
        # Try to find photo URL
        try:
            img_selectors = [
                'img[alt*="photo" i]',
                'img[data-testid*="photo"]',
                '.provider-photo img',
                'img[src*="healthgrades.com"][alt*="Dr"]',
            ]
            
            for selector in img_selectors:
                img = await page.query_selector(selector)
                if img:
                    src = await img.get_attribute('src')
                    if src and ('healthgrades' in src or 'cdn' in src):
                        result['photo_url'] = src
                        break
        except:
            pass
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


async def update_provider(conn, provider_id, data):
    """Update provider record with extracted data."""
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if data.get('phone'):
        updates.append('phone = ?')
        params.append(data['phone'])
    
    if data.get('credentials'):
        updates.append('credentials = ?')
        params.append(data['credentials'])
    
    if data.get('specialty'):
        updates.append('specialties = ?')
        params.append(json.dumps([data['specialty']]))
    
    if data.get('photo_url'):
        updates.append('source_url = ?')
        params.append(data['photo_url'])
    
    if updates:
        params.append(provider_id)
        query = f"UPDATE providers SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return True
    
    return False


async def main():
    """Main extraction process."""
    providers = get_providers_to_process(50)
    print(f"Processing {len(providers)} providers...")
    print()
    
    results = []
    updated_count = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Connect to database for updates
        conn = sqlite3.connect(DB_PATH)
        
        try:
            for i, provider in enumerate(providers):
                print(f"[{i+1}/{len(providers)}] Processing: {provider['name']} ({provider['city']}, {provider['state']})")
                
                url = construct_healthgrades_url(
                    provider['name'], 
                    provider['city'], 
                    provider['state']
                )
                
                if not url:
                    print(f"  Could not construct URL for {provider['name']}")
                    continue
                
                print(f"  URL: {url}")
                
                result = await extract_provider_data(page, url, provider)
                results.append(result)
                
                if result['success']:
                    print(f"  ✓ Phone: {result['phone'] or 'Not found'}")
                    print(f"  ✓ Credentials: {result['credentials'] or 'Not found'}")
                    print(f"  ✓ Specialty: {result['specialty'] or 'Not found'}")
                    print(f"  ✓ Photo: {result['photo_url'] or 'Not found'}")
                    
                    # Update database
                    if await update_provider(conn, provider['id'], result):
                        updated_count += 1
                        print(f"  ✓ Database updated")
                    else:
                        print(f"  - No data to update")
                else:
                    print(f"  ✗ Error: {result['error']}")
                
                print()
                
                # Small delay to be respectful
                await asyncio.sleep(1)
        
        finally:
            conn.close()
            await browser.close()
    
    # Summary
    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"Database updates: {updated_count}")
    print()
    
    # Show sample of what was found
    print("SAMPLE RESULTS:")
    print("-" * 60)
    for r in results[:5]:
        if r['success'] and (r['phone'] or r['credentials'] or r['specialty']):
            print(f"Name: {r['name']}")
            print(f"  Phone: {r['phone']}")
            print(f"  Credentials: {r['credentials']}")
            print(f"  Specialty: {r['specialty']}")
            print(f"  Photo: {r['photo_url'][:80] + '...' if r['photo_url'] and len(r['photo_url']) > 80 else r['photo_url']}")
            print()


if __name__ == '__main__':
    asyncio.run(main())
