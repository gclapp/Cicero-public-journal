#!/usr/bin/env python3
"""Explore Cigna public directory page structure.

This script maps the UI elements needed for scraping:
- Search form fields
- Results list structure
- Pagination controls
- Provider detail layout
"""

import asyncio
from playwright.async_api import async_playwright


async def explore_cigna():
    """Explore the Cigna provider directory page structure."""
    
    print("=" * 70)
    print("🔍 EXPLORING CIGNA PROVIDER DIRECTORY")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Headless for server environment
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        url = "https://[REDACTED]/web/public/ifpproviders"
        
        print(f"🌐 Navigating to: {url}")
        print()
        
        try:
            # Navigate and wait for page to load
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(5)  # Extra time for SPA to render
            
            # Basic page info
            title = await page.title()
            current_url = page.url
            
            print(f"📄 Page Title: {title}")
            print(f"🔗 Current URL: {current_url}")
            print()
            
            # Take full page screenshot
            screenshot_path = "cigna_explore_full.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            print()
            
            # Analyze page structure
            print("=" * 70)
            print("📋 PAGE STRUCTURE ANALYSIS")
            print("=" * 70)
            print()
            
            # 1. Look for search inputs
            print("🔤 SEARCH INPUT FIELDS:")
            inputs = await page.query_selector_all('input')
            for i, inp in enumerate(inputs[:20]):  # Limit to first 20
                attrs = await inp.evaluate("""el => ({
                    type: el.type,
                    name: el.name,
                    id: el.id,
                    placeholder: el.placeholder,
                    class: el.className,
                    ariaLabel: el.getAttribute('aria-label'),
                    dataTestId: el.getAttribute('data-testid')
                })""")
                
                print(f"\n  Input {i+1}:")
                for key, value in attrs.items():
                    if value:
                        print(f"    {key}: {value}")
            
            print()
            
            # 2. Look for select dropdowns (specialty, radius, etc.)
            print("📊 SELECT DROPDOWNS:")
            selects = await page.query_selector_all('select')
            for i, sel in enumerate(selects):
                attrs = await sel.evaluate("""el => ({
                    name: el.name,
                    id: el.id,
                    class: el.className,
                    ariaLabel: el.getAttribute('aria-label')
                })""")
                
                # Get options
                options = await sel.query_selector_all('option')
                option_texts = []
                for opt in options[:5]:  # First 5 options
                    text = await opt.text_content()
                    option_texts.append(text.strip() if text else '')
                
                print(f"\n  Select {i+1}:")
                for key, value in attrs.items():
                    if value:
                        print(f"    {key}: {value}")
                print(f"    options: {option_texts}")
            
            print()
            
            # 3. Look for buttons
            print("🔘 BUTTONS:")
            buttons = await page.query_selector_all('button')
            for i, btn in enumerate(buttons[:15]):
                text = await btn.text_content()
                attrs = await btn.evaluate("""el => ({
                    type: el.type,
                    id: el.id,
                    class: el.className,
                    ariaLabel: el.getAttribute('aria-label')
                })""")
                
                print(f"\n  Button {i+1}: '{text.strip() if text else 'no text'}'")
                for key, value in attrs.items():
                    if value:
                        print(f"    {key}: {value}")
            
            print()
            
            # 4. Look for forms
            print("📝 FORMS:")
            forms = await page.query_selector_all('form')
            for i, form in enumerate(forms):
                attrs = await form.evaluate("""el => ({
                    action: el.action,
                    method: el.method,
                    id: el.id,
                    class: el.className,
                    name: el.name
                })""")
                
                print(f"\n  Form {i+1}:")
                for key, value in attrs.items():
                    if value:
                        print(f"    {key}: {value}")
            
            print()
            
            # 5. Look for data attributes that might indicate search functionality
            print("🔎 SEARCH-RELATED ELEMENTS:")
            search_terms = ['search', 'zip', 'location', 'specialty', 'provider', 
                          'doctor', 'radius', 'distance', 'city', 'state']
            
            for term in search_terms:
                # Look for elements with search-related attributes
                selectors = [
                    f'[id*="{term}" i]',
                    f'[name*="{term}" i]',
                    f'[class*="{term}" i]',
                    f'[data-testid*="{term}" i]',
                    f'[placeholder*="{term}" i]'
                ]
                
                found = []
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            found.append(f"{selector}: {len(elements)}")
                    except:
                        pass
                
                if found:
                    print(f"  '{term}': {', '.join(found)}")
            
            print()
            
            # 6. Check for API/network patterns in page source
            print("🌐 NETWORK/API PATTERNS:")
            content = await page.content()
            
            patterns = {
                'fetch API': 'fetch(' in content,
                'axios': 'axios' in content,
                'XMLHttpRequest': 'XMLHttpRequest' in content,
                'GraphQL': 'graphql' in content.lower(),
                'REST API': '/api/' in content.lower(),
                'JSON endpoints': '.json' in content
            }
            
            for pattern, found in patterns.items():
                status = "✅" if found else "❌"
                print(f"  {status} {pattern}")
            
            print()
            
            # 7. Try to interact with search form
            print("🧪 ATTEMPTING SEARCH INTERACTION:")
            print()
            
            # Look for ZIP input
            zip_selectors = [
                'input[placeholder*="zip" i]',
                'input[name*="zip" i]',
                'input[id*="zip" i]',
                'input[aria-label*="zip" i]',
                'input[data-testid*="zip" i]'
            ]
            
            zip_input = None
            for selector in zip_selectors:
                try:
                    zip_input = await page.query_selector(selector)
                    if zip_input:
                        print(f"  ✅ Found ZIP input: {selector}")
                        break
                except:
                    pass
            
            if zip_input:
                print("  📝 Entering test ZIP code: 90210")
                await zip_input.fill("90210")
                await asyncio.sleep(1)
                
                # Look for search button
                search_btn_selectors = [
                    'button:has-text("Search")',
                    'button:has-text("Find")',
                    'button[type="submit"]',
                    'button[id*="search" i]',
                    'button[data-testid*="search" i]'
                ]
                
                search_btn = None
                for selector in search_btn_selectors:
                    try:
                        search_btn = await page.query_selector(selector)
                        if search_btn:
                            print(f"  ✅ Found search button: {selector}")
                            break
                    except:
                        pass
                
                if search_btn:
                    print("  🖱️  Clicking search button...")
                    await search_btn.click()
                    await asyncio.sleep(5)  # Wait for results
                    
                    # Take screenshot of results
                    results_screenshot = "cigna_explore_results.png"
                    await page.screenshot(path=results_screenshot, full_page=True)
                    print(f"  📸 Results screenshot: {results_screenshot}")
                    
                    # Look for result elements
                    print("\n  📊 RESULTS ANALYSIS:")
                    
                    # Common result container patterns
                    result_patterns = [
                        '[data-testid*="result" i]',
                        '[class*="result" i]',
                        '[class*="provider" i]',
                        '[class*="doctor" i]',
                        'article',
                        '.card',
                        '.list-item'
                    ]
                    
                    for pattern in result_patterns:
                        try:
                            results = await page.query_selector_all(pattern)
                            if results:
                                print(f"    Found {len(results)} elements matching: {pattern}")
                        except:
                            pass
            
            print()
            print("=" * 70)
            print("✅ EXPLORATION COMPLETE")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error during exploration: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            print("\n🛑 Browser closed")


if __name__ == "__main__":
    print("\nThis script will:")
    print("1. Open a browser window")
    print("2. Navigate to Cigna provider directory")
    print("3. Analyze the page structure")
    print("4. Attempt a test search")
    print("5. Save screenshots for analysis")
    print()
    print("Starting in 3 seconds...")
    import time
    time.sleep(3)
    
    asyncio.run(explore_cigna())
