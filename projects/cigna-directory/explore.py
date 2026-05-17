"""Explore Cigna site structure without login."""

import asyncio
from playwright.async_api import async_playwright

async def explore():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # The actual provider directory URL
        url = "https://[REDACTED]/web/public/ifpproviders"
        
        print(f"Exploring Cigna provider directory: {url}")
        print('='*60)
        
        try:
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(5)  # Wait for SPA to load
            
            # Get page info
            title = await page.title()
            print(f"Page title: {title}")
            print(f"Current URL: {page.url}")
            
            # Save screenshot
            screenshot_name = "explore_directory_main.png"
            await page.screenshot(path=screenshot_name, full_page=True)
            print(f"Screenshot saved: {screenshot_name}")
            
            # Get page content
            content = await page.content()
            print(f"Page content length: {len(content)} chars")
            
            # Look for search forms
            search_inputs = await page.query_selector_all('input')
            print(f"\nFound {len(search_inputs)} input fields")
            
            for i, inp in enumerate(search_inputs[:15]):
                input_type = await inp.get_attribute('type') or 'text'
                input_name = await inp.get_attribute('name') or ''
                input_id = await inp.get_attribute('id') or ''
                input_placeholder = await inp.get_attribute('placeholder') or ''
                input_class = await inp.get_attribute('class') or ''
                print(f"  Input {i}: type={input_type}, name={input_name}, id={input_id}")
                if input_placeholder:
                    print(f"           placeholder={input_placeholder}")
                if input_class:
                    print(f"           class={input_class[:50]}")
            
            # Look for buttons
            buttons = await page.query_selector_all('button')
            print(f"\nFound {len(buttons)} buttons")
            
            for i, btn in enumerate(buttons[:10]):
                text = await btn.text_content()
                btn_type = await btn.get_attribute('type') or 'button'
                btn_class = await btn.get_attribute('class') or ''
                print(f"  Button {i}: type={btn_type}, text={text.strip() if text else 'no text'}")
                if btn_class:
                    print(f"            class={btn_class[:50]}")
            
            # Look for selects (dropdowns)
            selects = await page.query_selector_all('select')
            print(f"\nFound {len(selects)} select dropdowns")
            
            for i, sel in enumerate(selects[:5]):
                sel_name = await sel.get_attribute('name') or ''
                sel_id = await sel.get_attribute('id') or ''
                print(f"  Select {i}: name={sel_name}, id={sel_id}")
            
            # Look for forms
            forms = await page.query_selector_all('form')
            print(f"\nFound {len(forms)} forms")
            
            # Check for any data attributes that might indicate search functionality
            print("\nLooking for search-related elements...")
            search_terms = ['search', 'zip', 'location', 'specialty', 'provider', 'doctor']
            
            for term in search_terms:
                elements = await page.query_selector_all(f'[id*="{term}" i], [name*="{term}" i], [class*="{term}" i]')
                if elements:
                    print(f"  Found {len(elements)} elements matching '{term}'")
            
            # Try to find network/API calls
            print("\nChecking for API endpoints in page source...")
            if 'api' in content.lower():
                print("  Page contains 'api' references")
            if 'graphql' in content.lower():
                print("  Page contains 'graphql' references")
            if 'fetch(' in content or 'axios' in content or '$.ajax' in content:
                print("  Page contains AJAX/fetch calls")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explore())
