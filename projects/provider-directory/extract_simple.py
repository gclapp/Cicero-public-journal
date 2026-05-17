#!/usr/bin/env python3
"""
Extract detailed provider information from Healthgrades - Simplified version.
"""

import sqlite3
import re
import json
from playwright.sync_api import sync_playwright

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
    name = name.replace('Dr. ', '').replace(',', '').strip()
    name_parts = name.split()
    
    if len(name_parts) >= 2:
        first = name_parts[0].lower()
        last = name_parts[-1].lower()
        city_clean = city.lower().replace(' ', '-')
        
        url = f"https://www.healthgrades.com/physician/dr-{first}-{last}-{city_clean}"
        return url
    return None


def extract_provider_data(page, url, provider):
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
        print(f"  Navigating to {url}...")
        response = page.goto(url, wait_until='domcontentloaded', timeout=15000)
        
        if response and response.status == 404:
            result['error'] = 'Page not found (404)'
            return result
        
        page.wait_for_timeout(2000)
        
        title = page.title()
        if 'Not Found' in title or '404' in title:
            result['error'] = 'Page not found'
            return result
        
        print(f"  Page loaded: {title[:60]}...")
        
        # Extract phone number
        try:
            # Look for tel: links
            tel_links = page.query_selector_all('a[href^="tel:"]')
            for link in tel_links:
                href = link.get_attribute('href')
                if href:
                    phone = href.replace('tel:', '').strip()
                    if re.match(r'\d{3}-\d{3}-\d{4}', phone):
                        result['phone'] = phone
                        break
        except Exception as e:
            print(f"  Phone extraction error: {e}")
        
        # Extract credentials from title
        try:
            heading = page.query_selector('h1')
            if heading:
                heading_text = heading.inner_text()
                cred_match = re.search(r',\s*(MD|DO|ND|PA|NP|CNP|APRN|LAC|RN|WHNP|FNP)[,.\s]', heading_text)
                if cred_match:
                    result['credentials'] = cred_match.group(1)
        except Exception as e:
            print(f"  Credentials extraction error: {e}")
        
        # Extract specialty
        try:
            # Look for text containing specialty keywords
            page_text = page.content()
            if 'Reproductive Endocrinology' in page_text:
                result['specialty'] = 'Reproductive Endocrinology'
            elif 'Reproductive Endocrinologist' in page_text:
                result['specialty'] = 'Reproductive Endocrinology'
        except Exception as e:
            print(f"  Specialty extraction error: {e}")
        
        # Extract photo URL
        try:
            img = page.query_selector('img[alt*="photo" i]')
            if img:
                src = img.get_attribute('src')
                if src:
                    result['photo_url'] = src
        except Exception as e:
            print(f"  Photo extraction error: {e}")
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        print(f"  Error: {e}")
    
    return result


def update_provider(conn, provider_id, data):
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


def main():
    """Main extraction process."""
    providers = get_providers_to_process(50)
    print(f"Processing {len(providers)} providers...")
    print()
    
    results = []
    updated_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        conn = sqlite3.connect(DB_PATH)
        
        try:
            for i, provider in enumerate(providers):
                print(f"[{i+1}/{len(providers)}] {provider['name']} ({provider['city']}, {provider['state']})")
                
                url = construct_healthgrades_url(
                    provider['name'], 
                    provider['city'], 
                    provider['state']
                )
                
                if not url:
                    print(f"  Could not construct URL")
                    continue
                
                result = extract_provider_data(page, url, provider)
                results.append(result)
                
                if result['success']:
                    print(f"  Phone: {result['phone'] or 'N/A'}")
                    print(f"  Credentials: {result['credentials'] or 'N/A'}")
                    print(f"  Specialty: {result['specialty'] or 'N/A'}")
                    
                    if update_provider(conn, provider['id'], result):
                        updated_count += 1
                        print(f"  ✓ Updated")
                    else:
                        print(f"  - No data to update")
                else:
                    print(f"  ✗ {result['error']}")
                
                print()
                
                # Be respectful
                page.wait_for_timeout(1000)
        
        finally:
            conn.close()
            browser.close()
    
    # Summary
    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"Database updates: {updated_count}")
    print()
    
    # Show sample results
    print("SAMPLE RESULTS WITH DATA:")
    print("-" * 60)
    found_count = 0
    for r in results:
        if r['success'] and (r['phone'] or r['credentials'] or r['specialty']):
            print(f"Name: {r['name']}")
            print(f"  Phone: {r['phone']}")
            print(f"  Credentials: {r['credentials']}")
            print(f"  Specialty: {r['specialty']}")
            print(f"  Photo: {r['photo_url']}")
            print()
            found_count += 1
            if found_count >= 10:
                break


if __name__ == '__main__':
    main()
