#!/usr/bin/env python3
"""Explore Healthgrades site structure."""

import asyncio
from playwright.async_api import async_playwright


async def explore_healthgrades():
    """Quick exploration of Healthgrades page."""
    
    print("=" * 70)
    print("🔍 EXPLORING HEALTHGRADES")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Healthgrades search URL
        url = "https://www.healthgrades.com/usearch?what=Doctor&where=90210"
        
        print(f"🌐 Loading: {url}")
        print()
        
        try:
            # Load the page
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)  # Wait for results to load
            
            # Basic info
            title = await page.title()
            current_url = page.url
            
            print(f"📄 Page Title: {title}")
            print(f"🔗 Current URL: {current_url}")
            print()
            
            # Take screenshot
            await page.screenshot(path="healthgrades_screenshot.png", full_page=True)
            print("📸 Screenshot saved: healthgrades_screenshot.png")
            print()
            
            # Quick check for key elements
            print("🔎 KEY ELEMENTS:")
            
            # Look for search inputs
            inputs = await page.query_selector_all('input')
            print(f"  Input fields: {len(inputs)}")
            
            # Look for provider cards/results
            provider_selectors = [
                '[data-testid*="provider"]',
                '[data-testid*="doctor"]',
                '[class*="provider-card"]',
                '[class*="doctor-card"]',
                'article',
                '.card',
            ]
            
            providers_found = 0
            for selector in provider_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  Providers with '{selector}': {len(elements)}")
                        providers_found = len(elements)
                        break
                except:
                    pass
            
            if not providers_found:
                print("  ⚠️  No provider elements found with standard selectors")
            
            # Look for buttons
            buttons = await page.query_selector_all('button')
            print(f"  Buttons: {len(buttons)}")
            
            # Look for forms
            forms = await page.query_selector_all('form')
            print(f"  Forms: {len(forms)}")
            
            print()
            
            # Get page text content (first 1000 chars)
            text = await page.text_content('body')
            if text:
                print("📝 PAGE TEXT (first 1000 chars):")
                print(text[:1000].replace('\n', ' '))
                print()
            
            # Check for specific terms
            content = await page.content()
            print("🔍 SEARCH TERMS FOUND:")
            terms = ['doctor', 'provider', 'specialty', 'address', 'phone', 'rating']
            for term in terms:
                count = content.lower().count(term)
                if count > 0:
                    print(f"  '{term}': {count} occurrences")
            
            # Try to extract provider names
            print("\n👨‍⚕️ ATTEMPTING TO EXTRACT PROVIDER NAMES:")
            name_selectors = [
                'h1', 'h2', 'h3', 'h4',
                '[class*="name"]',
                '[data-testid*="name"]',
            ]
            
            for selector in name_selectors[:3]:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\n  {selector} elements ({min(len(elements), 5)} shown):")
                        for i, elem in enumerate(elements[:5]):
                            text = await elem.text_content()
                            if text and len(text.strip()) > 2:
                                print(f"    - {text.strip()[:80]}")
                except:
                    pass
            
            print()
            print("=" * 70)
            print("✅ EXPLORATION COMPLETE")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            # Try to save screenshot anyway
            try:
                await page.screenshot(path="healthgrades_error.png")
                print("📸 Error screenshot saved: healthgrades_error.png")
            except:
                pass
        
        finally:
            await browser.close()


if __name__ == "__main__":
    print("\nThis script will:")
    print("1. Open a browser")
    print("2. Navigate to Healthgrades")
    print("3. Analyze the page structure")
    print("4. Save a screenshot")
    print()
    print("Starting in 2 seconds...")
    import time
    time.sleep(2)
    
    asyncio.run(explore_healthgrades())
