"""Cigna provider directory scraper using Playwright."""

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from config import (
    CIGNA_LOGIN_URL, CIGNA_PROVIDER_SEARCH_URL, 
    DEFAULT_TIMEOUT, NAVIGATION_TIMEOUT, DELAY_BETWEEN_REQUESTS,
    load_credentials, get_storage_state_path
)
from models import Provider, Address, SearchCriteria, SearchResult
from storage import ProviderStorage


class CignaScraper:
    """Scraper for Cigna provider directory."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.storage = ProviderStorage(Path(__file__).parent / "data")
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self) -> None:
        """Initialize browser and context."""
        print("Starting browser...")
        self.playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Try to load existing session
        storage_state = get_storage_state_path()
        if storage_state.exists():
            print("Loading existing session...")
            self.context = await self.browser.new_context(
                storage_state=str(storage_state),
                viewport={'width': 1920, 'height': 1080}
            )
        else:
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(DEFAULT_TIMEOUT)
        
        # Set up console logging
        self.page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
    
    async def stop(self) -> None:
        """Clean up browser resources."""
        print("Stopping browser...")
        if self.context:
            # Save session state
            storage_state = get_storage_state_path()
            await self.context.storage_state(path=str(storage_state))
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def is_logged_in(self) -> bool:
        """Check if currently logged in."""
        try:
            await self.page.goto(CIGNA_LOGIN_URL, timeout=NAVIGATION_TIMEOUT)
            await asyncio.sleep(1)
            
            # Look for indicators of being logged in
            # This will need adjustment based on actual page structure
            logged_in_indicators = [
                'text="Sign Out"',
                'text="My Account"',
                '[data-testid="account-menu"]',
                '.user-name',
                '#logout'
            ]
            
            for indicator in logged_in_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=2000)
                    print(f"Found login indicator: {indicator}")
                    return True
                except:
                    continue
            
            # Check for login form (indicates not logged in)
            login_form_indicators = [
                'input[type="password"]',
                'input[name="username"]',
                'button:has-text("Sign In")',
                'button:has-text("Log In")'
            ]
            
            for indicator in login_form_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=2000)
                    print(f"Found login form: {indicator}")
                    return False
                except:
                    continue
            
            # Ambiguous - assume not logged in to be safe
            print("Login status unclear, assuming not logged in")
            return False
            
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False
    
    async def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Log in to Cigna."""
        # Get credentials
        if not username or not password:
            creds = load_credentials()
            username = username or creds.get('username')
            password = password or creds.get('password')
        
        if not username or not password:
            raise ValueError("Cigna credentials not found. Please provide username and password.")
        
        print(f"Logging in as {username}...")
        
        try:
            await self.page.goto(CIGNA_LOGIN_URL, timeout=NAVIGATION_TIMEOUT)
            await asyncio.sleep(2)
            
            # Take screenshot for debugging
            await self.page.screenshot(path="debug_login_page.png")
            
            # Look for and fill username field
            # Note: These selectors will need to be adjusted based on actual page
            username_selectors = [
                'input[name="username"]',
                'input[type="email"]',
                'input[id*="user"]',
                'input[placeholder*="user" i]',
                'input[placeholder*="email" i]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    await self.page.fill(selector, username)
                    print(f"Filled username using: {selector}")
                    username_filled = True
                    break
                except:
                    continue
            
            if not username_filled:
                print("Could not find username field")
                return False
            
            # Look for and fill password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="pass"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.fill(selector, password)
                    print(f"Filled password using: {selector}")
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                print("Could not find password field")
                return False
            
            # Look for and click submit button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'input[type="submit"]'
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    await self.page.click(selector)
                    print(f"Clicked submit using: {selector}")
                    submit_clicked = True
                    break
                except:
                    continue
            
            if not submit_clicked:
                print("Could not find submit button")
                return False
            
            # Wait for navigation
            await asyncio.sleep(5)
            
            # Check for 2FA or additional challenges
            # TODO: Handle 2FA if needed
            
            # Verify login success
            if await self.is_logged_in():
                print("Login successful!")
                # Save credentials for future use
                from config import save_credentials
                save_credentials(username, password)
                return True
            else:
                print("Login may have failed - check screenshot")
                await self.page.screenshot(path="debug_login_failed.png")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            await self.page.screenshot(path="debug_login_error.png")
            return False
    
    async def navigate_to_directory(self) -> bool:
        """Navigate to the provider search page."""
        try:
            print("Navigating to provider directory...")
            await self.page.goto(CIGNA_PROVIDER_SEARCH_URL, timeout=NAVIGATION_TIMEOUT)
            await asyncio.sleep(2)
            
            # Take screenshot to see what we're working with
            await self.page.screenshot(path="debug_directory.png")
            print("Saved screenshot to debug_directory.png")
            
            return True
        except Exception as e:
            print(f"Error navigating to directory: {e}")
            return False
    
    async def search_providers(self, criteria: SearchCriteria) -> SearchResult:
        """Search for providers with given criteria."""
        print(f"Searching: zip={criteria.zip_code}, radius={criteria.radius_miles}, specialty={criteria.specialty}")
        
        # Navigate to search page
        await self.navigate_to_directory()
        
        # TODO: Fill in search form based on actual page structure
        # This will need to be customized after inspecting the page
        
        # Placeholder implementation
        providers = []
        
        return SearchResult(
            criteria=criteria,
            providers=providers,
            total_count=0,
            has_more=False
        )
    
    async def scrape_search_results(self, criteria: SearchCriteria) -> List[Provider]:
        """Scrape all results for a search."""
        all_providers = []
        has_more = True
        page = 1
        
        while has_more and page <= 10:  # Limit to 10 pages for safety
            print(f"Scraping page {page}...")
            
            criteria.page = page
            result = await self.search_providers(criteria)
            
            if result.providers:
                all_providers.extend(result.providers)
                print(f"Found {len(result.providers)} providers on page {page}")
            
            has_more = result.has_more
            page += 1
            
            # Rate limiting
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        return all_providers


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scrape Cigna provider directory")
    parser.add_argument("--zip", required=True, help="ZIP code to search")
    parser.add_argument("--radius", type=int, default=10, help="Search radius in miles")
    parser.add_argument("--specialty", help="Medical specialty filter")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--headed", action="store_true", help="Show browser window (for debugging)")
    parser.add_argument("--username", help="Cigna username (or set in credentials)")
    parser.add_argument("--password", help="Cigna password (or set in credentials)")
    parser.add_argument("--explore", action="store_true", help="Just explore the site structure")
    
    args = parser.parse_args()
    
    headless = not args.headed
    
    async with CignaScraper(headless=headless) as scraper:
        if args.explore:
            # Just explore the site
            print("Exploring Cigna site structure...")
            await scraper.page.goto(CIGNA_LOGIN_URL)
            await asyncio.sleep(3)
            await scraper.page.screenshot(path="explore_login.png")
            print("Saved: explore_login.png")
            
            await scraper.page.goto(CIGNA_PROVIDER_SEARCH_URL)
            await asyncio.sleep(3)
            await scraper.page.screenshot(path="explore_directory.png")
            print("Saved: explore_directory.png")
            return
        
        # Check if logged in
        if not await scraper.is_logged_in():
            print("Not logged in, attempting login...")
            success = await scraper.login(args.username, args.password)
            if not success:
                print("Login failed. Please check credentials.")
                return
        
        # Perform search
        criteria = SearchCriteria(
            zip_code=args.zip,
            radius_miles=args.radius,
            specialty=args.specialty
        )
        
        providers = await scraper.scrape_search_results(criteria)
        
        # Save results
        if providers:
            saved = scraper.storage.save_providers(providers)
            print(f"Saved {saved} providers to database")
            
            # Export to CSV and JSON
            json_path = scraper.storage.export_to_json()
            csv_path = scraper.storage.export_to_csv()
            print(f"Exported to: {json_path}")
            print(f"Exported to: {csv_path}")
        else:
            print("No providers found")


if __name__ == "__main__":
    asyncio.run(main())
