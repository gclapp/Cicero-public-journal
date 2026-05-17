"""Cigna Provider Directory scraper using Playwright."""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from models import SearchCriteria, SearchResult, SourceInfo, Provider, Address
from sources.base import ProviderSource


class CignaScraperSource(ProviderSource):
    """Cigna Provider Directory scraper using Playwright browser automation."""
    
    # URLs
    DIRECTORY_URL = "https://[REDACTED]/web/public/ifpproviders"
    
    # Settings
    DEFAULT_TIMEOUT = 30000
    NAVIGATION_TIMEOUT = 60000
    DELAY_BETWEEN_REQUESTS = 2.5
    
    def __init__(self, headless: bool = True):
        super().__init__()
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Credentials storage
        self.credentials_dir = Path.home() / ".openclaw" / "credentials"
        self.storage_state_path = self.credentials_dir / "cigna-storage-state.json"
    
    @property
    def info(self) -> SourceInfo:
        return SourceInfo(
            id="cigna-scraper",
            name="Cigna Directory (Browser)",
            description="Playwright-based scraper for Cigna provider directory",
            status="beta",
            requires_auth=False,
            auth_type=None,
            rate_limit="20 req/min",
            reliability="medium",
            notes="Uses public directory. No login required for basic search."
        )
    
    async def _start_browser(self) -> None:
        """Initialize browser and context."""
        if self.browser:
            return
            
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Try to load existing session
        if self.storage_state_path.exists():
            self.context = await self.browser.new_context(
                storage_state=str(self.storage_state_path),
                viewport={'width': 1920, 'height': 1080}
            )
        else:
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.DEFAULT_TIMEOUT)
    
    async def _stop_browser(self) -> None:
        """Clean up browser resources."""
        if self.context:
            await self.context.storage_state(path=str(self.storage_state_path))
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def close(self):
        """Clean up resources."""
        await self._stop_browser()
    
    async def authenticate(self, username: Optional[str] = None, 
                          password: Optional[str] = None) -> bool:
        """Authentication not required for public directory."""
        self._authenticated = True
        return True
    
    async def health_check(self) -> bool:
        """Check if Cigna directory is accessible."""
        try:
            await self._start_browser()
            await self.page.goto(self.DIRECTORY_URL, timeout=self.NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            title = await self.page.title()
            return "cigna" in title.lower()
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    async def _handle_plan_modal(self) -> bool:
        """Handle the 'Select a plan for your search' modal if present."""
        try:
            # Check if modal is present
            modal_selectors = [
                'text="Select a plan for your search"',
                '[class*="modal"]:has-text("plan")',
                '[class*="dialog"]:has-text("plan")',
            ]
            
            modal_present = False
            for selector in modal_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            modal_present = True
                            print(f"    Found plan modal: {selector}")
                            break
                except:
                    continue
            
            if not modal_present:
                return False
            
            # Try to select "Medical Plans" first
            print("    🏥 Looking for Medical Plans option...")
            medical_selectors = [
                'text="Medical Plans"',
                'button:has-text("Medical")',
                '[class*="medical"]',
                'div:has-text("Medical Plans")',
            ]
            
            for selector in medical_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        print("    ✅ Clicked Medical Plans")
                        await asyncio.sleep(2)
                        break
                except Exception as e:
                    print(f"    Could not click {selector}: {e}")
                    continue
            
            # Try to find and click a specific plan option
            print("    📋 Looking for plan options...")
            
            # First try to find radio buttons or plan buttons
            plan_selectors = [
                'input[type="radio"]',
                'button[class*="plan"]',
                '[class*="plan-option"]',
                'label:has(input[type="radio"])',
            ]
            
            plan_selected = False
            for selector in plan_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"    Found {len(elements)} plan options with {selector}")
                        # Click the first visible one
                        for elem in elements:
                            try:
                                is_visible = await elem.is_visible()
                                if is_visible:
                                    await elem.click()
                                    print(f"    ✅ Selected plan option")
                                    await asyncio.sleep(1)
                                    plan_selected = True
                                    break
                            except:
                                continue
                        if plan_selected:
                            break
                except Exception as e:
                    continue
            
            # If no plan selected, try clicking on specific plan names
            if not plan_selected:
                print("    🔄 Trying specific plan names...")
                plan_names = ['PPO', 'HMO', 'EPO', 'Advantage', 'Total', 'Select', 'Open Access']
                for plan_name in plan_names:
                    try:
                        elem = await self.page.query_selector(f'text="{plan_name}"')
                        if elem:
                            is_visible = await elem.is_visible()
                            if is_visible:
                                await elem.click()
                                print(f"    ✅ Clicked {plan_name}")
                                await asyncio.sleep(1)
                                plan_selected = True
                                break
                    except:
                        continue
            
            # Look for Continue/Choose button
            print("    🔘 Looking for Continue button...")
            continue_selectors = [
                'button:has-text("Continue")',
                'button:has-text("Choose")',
                'button:has-text("Select")',
                'button[type="submit"]',
            ]
            
            for selector in continue_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        is_enabled = await button.is_enabled()
                        if is_enabled:
                            await button.click()
                            print("    ✅ Clicked Continue/Choose")
                            await asyncio.sleep(3)
                            return True
                except Exception as e:
                    continue
            
            # If no button found, try pressing Enter
            print("    ⌨️  Pressing Enter to continue...")
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            print(f"    ⚠️  Error handling modal: {e}")
            return False
    
    async def _fill_search_form(self, criteria: SearchCriteria) -> bool:
        """Fill in the search form."""
        try:
            # Look for the location input field
            print("  🔍 Looking for location input...")
            
            # Wait for the page to be fully loaded
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            location_selectors = [
                'input[placeholder*="Address" i]',
                'input[placeholder*="City" i]',
                'input[placeholder*="Zip" i]',
                'input[placeholder*="Enter" i]',
                'input[type="text"]',
                'input',
            ]
            
            location_input = None
            for selector in location_selectors:
                try:
                    # Wait for element to be visible
                    await self.page.wait_for_selector(selector, timeout=5000)
                    location_input = await self.page.query_selector(selector)
                    if location_input:
                        is_visible = await location_input.is_visible()
                        if is_visible:
                            print(f"  ✅ Found location input: {selector}")
                            break
                        else:
                            location_input = None
                except Exception as e:
                    print(f"    Tried {selector}: {e}")
                    continue
            
            if not location_input:
                print("  ❌ Could not find visible location input field")
                # Save debug info
                html = await self.page.content()
                with open("debug_no_input.html", "w") as f:
                    f.write(html)
                print("  💾 Saved debug_no_input.html")
                return False
            
            # Clear and fill the location field
            print("  🖱️  Scrolling to input field...")
            await location_input.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            
            print("  🖱️  Clicking input field...")
            try:
                await location_input.click(force=True)
            except:
                # If force click fails, try regular click with timeout
                await location_input.click(timeout=5000)
            
            print("  📝 Clearing field...")
            await location_input.fill("")
            await asyncio.sleep(0.5)
            
            search_text = criteria.zip_code
            if criteria.city:
                search_text = f"{criteria.city}, {criteria.state or ''} {criteria.zip_code}".strip()
            
            print(f"  📝 Entering: {search_text}")
            await location_input.fill(search_text)
            await asyncio.sleep(2)  # Wait for autocomplete
            
            # Select from autocomplete dropdown
            print("  🖱️  Selecting from autocomplete...")
            
            # Try to find and click the first autocomplete suggestion
            autocomplete_selectors = [
                '[role="option"]',
                '.pac-item',
                '[class*="suggestion"]',
                '[class*="autocomplete"]',
                'div:has-text("' + search_text + '")',
            ]
            
            for selector in autocomplete_selectors:
                try:
                    options = await self.page.query_selector_all(selector)
                    if options:
                        print(f"    Found {len(options)} autocomplete options")
                        # Click the first one
                        await options[0].click()
                        print(f"    Clicked first option")
                        await asyncio.sleep(1)
                        break
                except Exception as e:
                    continue
            
            # Close any autocomplete dropdown by pressing Escape
            print("  ⌨️  Closing autocomplete dropdown...")
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
            # Click "Doctor by Type" tile
            print("  🖱️  Clicking 'Doctor by Type'...")
            doctor_by_type = await self.page.query_selector('text="Doctor by Type"')
            if doctor_by_type:
                await doctor_by_type.click()
                await asyncio.sleep(2)
                print("    Clicked 'Doctor by Type'")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error filling form: {e}")
            return False
    
    async def _click_search(self) -> bool:
        """Click the search button or submit the form."""
        try:
            # After clicking "Doctor by Type", the page should navigate to results
            # or show a specialty selection interface
            
            # Check if we're already on results page
            current_url = self.page.url
            if "search" in current_url and "results" in current_url.lower():
                print("  ✅ Already on results page")
                return True
            
            # Look for a continue/search button
            search_selectors = [
                'button:has-text("Search")',
                'button:has-text("Find")',
                'button:has-text("Continue")',
                'button[type="submit"]',
                'a:has-text("Search")',
            ]
            
            for selector in search_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        print(f"  🖱️  Clicking: {selector}")
                        await button.click()
                        await asyncio.sleep(3)
                        return True
                except:
                    continue
            
            # If no button found, assume the click on "Doctor by Type" was enough
            print("  ⏭️  Proceeding with current page")
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            print(f"  ❌ Error clicking search: {e}")
            return False
    
    async def _extract_providers(self) -> List[Provider]:
        """Extract provider data from search results."""
        providers = []
        
        try:
            # Wait for results to load
            await asyncio.sleep(3)
            
            # Look for result containers
            # Common patterns for provider listings
            result_selectors = [
                '[data-testid*="provider" i]',
                '[data-testid*="result" i]',
                '[class*="provider" i]',
                '[class*="result" i]',
                'article',
                '.card',
            ]
            
            results = []
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"  Found {len(elements)} results with: {selector}")
                        results = elements
                        break
                except:
                    continue
            
            if not results:
                print("  ⚠️  No results found with standard selectors")
                # Save page content for debugging
                content = await self.page.content()
                with open("debug_page.html", "w") as f:
                    f.write(content)
                print("  💾 Saved debug_page.html for analysis")
                return providers
            
            # Extract data from each result
            for i, result in enumerate(results[:10]):  # Limit to first 10 for now
                try:
                    # Try to extract provider name
                    name_elem = await result.query_selector('h1, h2, h3, h4, [class*="name"], [data-testid*="name"]')
                    name = await name_elem.text_content() if name_elem else f"Provider {i+1}"
                    
                    # Try to extract specialty
                    specialty_elem = await result.query_selector('[class*="specialty"], [data-testid*="specialty"]')
                    specialty = await specialty_elem.text_content() if specialty_elem else None
                    
                    # Try to extract address
                    address_elem = await result.query_selector('[class*="address"], [data-testid*="address"]')
                    address_text = await address_elem.text_content() if address_elem else None
                    
                    # Parse address (simplified)
                    address = None
                    if address_text:
                        address = Address(
                            street=address_text,
                            city="",
                            state="",
                            zip=""
                        )
                    
                    provider = Provider(
                        name=name.strip() if name else f"Provider {i+1}",
                        specialties=[specialty.strip()] if specialty else [],
                        address=address,
                        source="cigna-scraper"
                    )
                    providers.append(provider)
                    
                except Exception as e:
                    print(f"  ⚠️  Error extracting provider {i}: {e}")
                    continue
            
            return providers
            
        except Exception as e:
            print(f"  ❌ Error extracting providers: {e}")
            return providers
    
    async def search(self, criteria: SearchCriteria) -> SearchResult:
        """Search for providers on Cigna."""
        start_time = datetime.utcnow()
        
        try:
            await self._start_browser()
            
            print(f"🔍 Searching Cigna directory...")
            print(f"   ZIP: {criteria.zip_code}, Radius: {criteria.radius_miles}mi")
            if criteria.specialty:
                print(f"   Specialty: {criteria.specialty}")
            
            # Navigate to directory
            print("  🌐 Loading directory...")
            await self.page.goto(self.DIRECTORY_URL, timeout=self.NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(5)  # Wait longer for SPA to render
            
            # Take initial screenshot
            await self.page.screenshot(path="cigna_search_start.png", full_page=True)
            print("  📸 Initial screenshot saved: cigna_search_start.png")
            
            # Handle plan selection modal if present
            print("  🔄 Checking for plan selection modal...")
            modal_handled = await self._handle_plan_modal()
            if modal_handled:
                print("  ✅ Plan modal handled")
            else:
                print("  ℹ️  No plan modal detected or skipped")
            
            # Fill search form
            print("  📝 Filling search form...")
            form_filled = await self._fill_search_form(criteria)
            if not form_filled:
                search_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                return SearchResult(
                    source="cigna-scraper",
                    criteria=criteria,
                    providers=[],
                    error="Could not fill search form",
                    search_time_ms=search_time
                )
            
            # Submit search
            print("  🔎 Submitting search...")
            search_clicked = await self._click_search()
            if not search_clicked:
                search_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                return SearchResult(
                    source="cigna-scraper",
                    criteria=criteria,
                    providers=[],
                    error="Could not submit search",
                    search_time_ms=search_time
                )
            
            # Wait for results and extract
            print("  ⏳ Waiting for results...")
            await asyncio.sleep(5)
            
            # Take results screenshot
            await self.page.screenshot(path="cigna_search_results.png", full_page=True)
            print("  📸 Saved: cigna_search_results.png")
            
            # Extract providers
            print("  📊 Extracting provider data...")
            providers = await self._extract_providers()
            
            search_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            print(f"  ✅ Found {len(providers)} providers")
            
            return SearchResult(
                source="cigna-scraper",
                criteria=criteria,
                providers=providers,
                total_count=len(providers),
                has_more=False,
                search_time_ms=search_time
            )
            
        except Exception as e:
            search_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            # Try to save error screenshot
            try:
                if self.page:
                    await self.page.screenshot(path="cigna_error.png")
            except:
                pass
            
            return SearchResult(
                source="cigna-scraper",
                criteria=criteria,
                providers=[],
                error=str(e),
                search_time_ms=search_time
            )
