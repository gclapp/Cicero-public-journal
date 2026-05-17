#!/usr/bin/env python3
"""Simple exploration of Cigna directory - quick check."""

import asyncio
from playwright.async_api import async_playwright


async def simple_explore():
    """Quick exploration of Cigna page."""
    
    print("=" * 70)
    print("🔍 QUICK CIGNA EXPLORATION")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        url = "https://[REDACTED]/web/public/ifpproviders"
        
        print(f"🌐 Loading: {url}")
        print()
        
        try:
            # Just load the page without waiting for everything
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(5)  # Give it time to render
            
            # Basic info
            title = await page.title()
            current_url = page.url
            
            print(f"📄 Page Title: {title}")
            print(f"🔗 Current URL: {current_url}")
            print()
            
            # Take screenshot
            await page.screenshot(path="cigna_screenshot.png", full_page=True)
            print("📸 Screenshot saved: cigna_screenshot.png")
            print()
            
            # Quick check for key elements
            print("🔎 KEY ELEMENTS:")
            
            # Look for any input fields
            inputs = await page.query_selector_all('input')
            print(f"  Input fields: {len(inputs)}")
            
            # Look for buttons
            buttons = await page.query_selector_all('button')
            print(f"  Buttons: {len(buttons)}")
            
            # Look for forms
            forms = await page.query_selector_all('form')
            print(f"  Forms: {len(forms)}")
            
            # Look for select dropdowns
            selects = await page.query_selector_all('select')
            print(f"  Selects: {len(selects)}")
            
            print()
            
            # Get page text content (first 500 chars)
            text = await page.text_content('body')
            if text:
                print("📝 PAGE TEXT (first 1000 chars):")
                print(text[:1000].replace('\n', ' '))
                print()
            
            # Check for specific terms
            content = await page.content()
            print("🔍 SEARCH TERMS FOUND:")
            terms = ['zip', 'search', 'location', 'specialty', 'provider', 'doctor', 'find']
            for term in terms:
                count = content.lower().count(term)
                if count > 0:
                    print(f"  '{term}': {count} occurrences")
            
            print()
            print("=" * 70)
            print("✅ EXPLORATION COMPLETE")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            # Try to save screenshot anyway
            try:
                await page.screenshot(path="cigna_error.png")
                print("📸 Error screenshot saved: cigna_error.png")
            except:
                pass
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(simple_explore())
