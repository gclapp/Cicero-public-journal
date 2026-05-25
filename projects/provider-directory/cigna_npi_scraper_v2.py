#!/usr/bin/env python3
"""
Cigna NPI Scraper v2 - Direct API Approach

This version attempts to use the Cigna provider directory API directly
or scrape the public-facing pages more effectively.
"""

import asyncio
import sqlite3
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
import urllib.parse

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# Configuration
DB_PATH = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db")
PROGRESS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_v2_progress.json")
RESULTS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_v2_results.json")
LOG_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_v2_log.txt")

# Cigna Directory URLs
CIGNA_PUBLIC_URL = "https://hcpdirectory.cigna.com/"
CIGNA_SEARCH_URL = "https://hcpdirectory.cigna.com/web/public/providers"

# Anti-detection settings
MIN_DELAY = 3.0
MAX_DELAY = 7.0
PAGE_TIMEOUT = 45000


@dataclass
class Provider:
    id: int
    name: str
    first_name: Optional[str]
    last_name: Optional[str]
    state: str
    city: str
    zip_code: Optional[str]
    npi: Optional[str]


@dataclass
class ScrapeResult:
    provider_id: int
    name: str
    state: str
    npi_found: Optional[str]
    profile_url: Optional[str]
    match_confidence: str
    timestamp: str
    error: Optional[str] = None


class CignaNPIScraper:
    """Advanced scraper for Cigna NPI extraction."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.results: List[ScrapeResult] = []
        self.processed_ids: set = set()
        self.stats = {'searched': 0, 'found': 0, 'errors': 0, 'skipped': 0}
        self.session_start = datetime.now().isoformat()
        
        self._load_progress()
        self._init_logging()
    
    def _init_logging(self):
        """Initialize log file."""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Session started: {self.session_start}\n")
            f.write(f"{'='*70}\n")
    
    def _log(self, message: str):
        """Write to log file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _load_progress(self):
        """Load progress from previous run."""
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE) as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_ids', []))
                    self.stats = data.get('stats', self.stats)
                    print(f"📂 Loaded progress: {len(self.processed_ids)} providers already processed")
            except Exception as e:
                print(f"⚠️  Could not load progress: {e}")
    
    def _save_progress(self):
        """Save progress to resume later."""
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                'processed_ids': list(self.processed_ids),
                'stats': self.stats,
                'last_update': datetime.now().isoformat()
            }, f, indent=2)
    
    def _save_results(self):
        """Save results to JSON file."""
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                'results': [asdict(r) for r in self.results],
                'stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
    
    async def init_browser(self):
        """Initialize browser with advanced stealth."""
        print("🚀 Initializing browser with stealth mode...")
        self._log("Initializing browser")
        
        playwright = await async_playwright().start()
        
        # Launch with extensive stealth args
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
            ]
        )
        
        # Create context with realistic fingerprint
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation'],
            color_scheme='light',
        )
        
        # Inject stealth scripts
        await self.context.add_init_script("""
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            
            // Override chrome
            window.chrome = { runtime: {} };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Add notification permission
            if (!window.Notification) {
                window.Notification = { permission: 'default' };
            }
        """)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(PAGE_TIMEOUT)
        
        print("✅ Browser initialized")
        self._log("Browser initialized successfully")
    
    async def close_browser(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
            print("🛑 Browser closed")
            self._log("Browser closed")
    
    def _random_delay(self, min_sec: float = MIN_DELAY, max_sec: float = MAX_DELAY):
        """Random delay between actions."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        return delay
    
    def _extract_name_parts(self, full_name: str) -> Tuple[str, str]:
        """Extract first and last name from full name."""
        # Remove prefixes and suffixes
        clean_name = re.sub(r'^(Dr\.?\s+|Doctor\s+|Prof\.?\s+)', '', full_name, flags=re.IGNORECASE)
        clean_name = re.sub(r',?\s+(MD|DO|PhD|NP|PA|RN|DVM|DDS|DMD)$', '', clean_name, flags=re.IGNORECASE)
        
        parts = clean_name.strip().split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[-1]
            # Handle compound last names
            if len(parts) > 2 and parts[-2].lower() in ['van', 'de', 'di', 'da', 'del', 'dos', 'du', 'la', 'le', 'mc', 'mac']:
                last_name = f"{parts[-2]} {parts[-1]}"
            return first_name, last_name
        return clean_name, ""
    
    def _get_providers_batch(self, batch_size: int = 100) -> List[Provider]:
        """Get batch of providers without NPIs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, first_name, last_name, state, city, zip, npi
            FROM providers
            WHERE (npi IS NULL OR npi = '') 
              AND state IS NOT NULL 
              AND state != ''
              AND name IS NOT NULL
              AND name != ''
            ORDER BY state, name
            LIMIT ?
        """, (batch_size,))
        
        rows = cursor.fetchall()
        conn.close()
        
        providers = []
        for row in rows:
            if row[0] not in self.processed_ids:
                providers.append(Provider(
                    id=row[0],
                    name=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    state=row[4],
                    city=row[5] or "",
                    zip_code=row[6] if len(row) > 6 else None,
                    npi=row[7] if len(row) > 7 else None
                ))
        
        return providers
    
    def _count_remaining(self) -> int:
        """Count providers still needing NPI lookup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM providers
            WHERE (npi IS NULL OR npi = '') 
              AND state IS NOT NULL 
              AND state != ''
        """)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    async def _navigate_to_search(self):
        """Navigate to Cigna search page."""
        try:
            await self.page.goto(CIGNA_PUBLIC_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Wait for any redirects
            current_url = self.page.url
            print(f"   Current URL: {current_url}")
            
            # Look for search link/button
            search_links = await self.page.query_selector_all('a[href*="provider"], a[href*="search"], button:has-text("Search")')
            if search_links:
                for link in search_links[:3]:
                    try:
                        await link.click()
                        await asyncio.sleep(2)
                        break
                    except:
                        continue
            
            return True
        except Exception as e:
            print(f"   ❌ Navigation error: {e}")
            self._log(f"Navigation error: {e}")
            return False
    
    async def _search_and_extract_npi(self, provider: Provider) -> ScrapeResult:
        """Search for provider and extract NPI."""
        result = ScrapeResult(
            provider_id=provider.id,
            name=provider.name,
            state=provider.state,
            npi_found=None,
            profile_url=None,
            match_confidence='none',
            timestamp=datetime.now().isoformat()
        )
        
        try:
            first_name, last_name = self._extract_name_parts(provider.name)
            if not last_name:
                result.error = "Could not parse name"
                return result
            
            print(f"   Searching: {first_name} {last_name} in {provider.state}")
            
            # Navigate to search page
            success = await self._navigate_to_search()
            if not success:
                result.error = "Failed to navigate to search page"
                return result
            
            await asyncio.sleep(random.uniform(2, 4))
            
            # Find and fill search inputs
            # Try multiple strategies
            
            # Strategy 1: Look for specific input patterns
            input_selectors = [
                'input[name*="provider" i]',
                'input[name*="name" i]',
                'input[placeholder*="name" i]',
                'input[placeholder*="provider" i]',
                'input[id*="provider" i]',
                'input[id*="name" i]',
                'input[data-testid*="name" i]',
                'input[data-testid*="provider" i]',
                'input[type="search"]',
                'input[aria-label*="search" i]',
                'input[aria-label*="name" i]',
            ]
            
            name_input = None
            for selector in input_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        visible = await elem.is_visible()
                        if visible:
                            name_input = elem
                            print(f"   Found name input: {selector}")
                            break
                except:
                    continue
            
            # Strategy 2: Get all inputs and try to identify search
            if not name_input:
                inputs = await self.page.query_selector_all('input:not([type="hidden"])')
                for inp in inputs:
                    try:
                        input_type = await inp.get_attribute('type') or 'text'
                        placeholder = await inp.get_attribute('placeholder') or ''
                        aria_label = await inp.get_attribute('aria-label') or ''
                        
                        if input_type in ['text', 'search']:
                            if any(keyword in (placeholder + aria_label).lower() for keyword in ['name', 'provider', 'doctor', 'search']):
                                visible = await inp.is_visible()
                                if visible:
                                    name_input = inp
                                    print(f"   Found name input by heuristic")
                                    break
                    except:
                        continue
            
            if not name_input:
                result.error = "Could not find name input field"
                self._log(f"No name input found for {provider.name}")
                return result
            
            # Fill name
            await name_input.click()
            await name_input.fill("")
            await asyncio.sleep(0.5)
            await name_input.type(f"{first_name} {last_name}", delay=random.uniform(50, 150))
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Look for state input
            state_selectors = [
                'select[name*="state" i]',
                'select[id*="state" i]',
                'input[name*="state" i]',
                'input[placeholder*="state" i]',
            ]
            
            state_input = None
            for selector in state_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        visible = await elem.is_visible()
                        if visible:
                            state_input = elem
                            break
                except:
                    continue
            
            if state_input:
                tag_name = await state_input.evaluate('el => el.tagName.toLowerCase()')
                if tag_name == 'select':
                    try:
                        await state_input.select_option(label=provider.state)
                    except:
                        try:
                            await state_input.select_option(value=provider.state)
                        except:
                            pass
                else:
                    await state_input.fill(provider.state)
                await asyncio.sleep(random.uniform(0.5, 1))
            
            # Find and click search button
            search_btn_selectors = [
                'button:has-text("Search")',
                'button:has-text("Find")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button[data-testid*="search" i]',
                'button[class*="search" i]',
                'a:has-text("Search")',
            ]
            
            search_btn = None
            for selector in search_btn_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        visible = await elem.is_visible()
                        enabled = await elem.is_enabled()
                        if visible and enabled:
                            search_btn = elem
                            break
                except:
                    continue
            
            if search_btn:
                await search_btn.click()
                print("   Clicked search button")
            else:
                # Try pressing Enter
                await name_input.press('Enter')
                print("   Pressed Enter to search")
            
            # Wait for results
            await asyncio.sleep(random.uniform(4, 6))
            
            # Check for results or no results message
            page_content = await self.page.content()
            page_text = await self.page.inner_text('body')
            
            if 'no results' in page_text.lower() or 'no providers' in page_text.lower():
                result.error = "No results found"
                return result
            
            if 'captcha' in page_text.lower() or 'recaptcha' in page_text.lower():
                result.error = "CAPTCHA detected"
                self._log(f"CAPTCHA for {provider.name}")
                return result
            
            # Look for result cards/items
            result_selectors = [
                '[data-testid*="result" i]',
                '[data-testid*="provider" i]',
                '[class*="provider-card" i]',
                '[class*="result-card" i]',
                '[class*="search-result" i]',
                'article',
                '.card',
                '[role="listitem"]',
            ]
            
            results = []
            for selector in result_selectors:
                try:
                    elems = await self.page.query_selector_all(selector)
                    if elems and len(elems) > 0:
                        results = elems
                        print(f"   Found {len(results)} results with selector: {selector}")
                        break
                except:
                    continue
            
            if not results:
                # Try to find any clickable elements that might be results
                links = await self.page.query_selector_all('a[href*="provider"], a[href*="detail"]')
                if links:
                    results = links[:5]
                    print(f"   Found {len(results)} provider links")
            
            if not results:
                result.error = "No results found on page"
                return result
            
            # Process results to find best match
            for idx, result_elem in enumerate(results[:5]):
                try:
                    # Get text content
                    elem_text = await result_elem.inner_text()
                    
                    # Check if last name appears
                    if last_name.lower() not in elem_text.lower():
                        continue
                    
                    print(f"   Checking result {idx+1}: {elem_text[:80]}...")
                    
                    # Click for details
                    await result_elem.click()
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Look for NPI in page content
                    detail_content = await self.page.content()
                    detail_text = await self.page.inner_text('body')
                    
                    # Multiple NPI patterns
                    npi_patterns = [
                        r'NPI[\s#:]*(\d{10})',
                        r'NPI\s*Number[\s#:]*(\d{10})',
                        r'National\s+Provider\s+Identifier[\s#:]*(\d{10})',
                        r'[\s#:](\d{10})[\s<]',
                    ]
                    
                    for pattern in npi_patterns:
                        match = re.search(pattern, detail_content, re.IGNORECASE)
                        if match:
                            npi = match.group(1)
                            # Validate NPI (10 digits, starts with 1 or 2)
                            if len(npi) == 10 and npi[0] in ['1', '2']:
                                result.npi_found = npi
                                result.profile_url = self.page.url
                                
                                # Determine confidence
                                if first_name.lower() in detail_text.lower() and last_name.lower() in detail_text.lower():
                                    if provider.state in detail_text:
                                        result.match_confidence = 'high'
                                    else:
                                        result.match_confidence = 'medium'
                                else:
                                    result.match_confidence = 'low'
                                
                                print(f"   ✅ Found NPI: {npi} (confidence: {result.match_confidence})")
                                self._log(f"Found NPI {npi} for {provider.name}")
                                return result
                    
                    # Go back to results
                    await self.page.go_back()
                    await asyncio.sleep(random.uniform(2, 3))
                    
                except Exception as e:
                    continue
            
            result.error = "NPI not found in results"
            
        except Exception as e:
            result.error = str(e)
            print(f"   ❌ Error: {e}")
            self._log(f"Error for {provider.name}: {e}")
        
        return result
    
    def _update_database(self, result: ScrapeResult):
        """Update provider with found NPI."""
        if not result.npi_found:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE providers SET npi = ?, source = 'cigna_web' WHERE id = ?",
                (result.npi_found, result.provider_id)
            )
            conn.commit()
            conn.close()
            print(f"   💾 Updated database with NPI {result.npi_found}")
            self._log(f"Updated DB: provider {result.provider_id} with NPI {result.npi_found}")
        except Exception as e:
            print(f"   ⚠️  DB update failed: {e}")
            self._log(f"DB update failed: {e}")
    
    async def run(self, max_providers: Optional[int] = None):
        """Run the scraper."""
        print("=" * 70)
        print("🚀 CIGNA NPI SCRAPER v2")
        print("=" * 70)
        
        remaining = self._count_remaining()
        print(f"📋 Providers without NPI: {remaining}")
        print(f"   Already processed: {len(self.processed_ids)}")
        print()
        
        if remaining == 0:
            print("✅ No providers to process!")
            return
        
        await self.init_browser()
        
        try:
            total_to_process = min(remaining, max_providers or remaining)
            processed = 0
            
            while processed < total_to_process:
                # Get batch
                batch = self._get_providers_batch(batch_size=50)
                if not batch:
                    break
                
                print(f"\n📦 Processing batch of {len(batch)} providers...")
                
                for i, provider in enumerate(batch):
                    processed += 1
                    print(f"\n[{processed}/{total_to_process}] {provider.name} ({provider.state})")
                    
                    result = await self._search_and_extract_npi(provider)
                    
                    self.stats['searched'] += 1
                    if result.npi_found:
                        self.stats['found'] += 1
                        self._update_database(result)
                    elif result.error:
                        self.stats['errors'] += 1
                    
                    self.results.append(result)
                    self.processed_ids.add(provider.id)
                    
                    # Save progress every 5 providers
                    if processed % 5 == 0:
                        self._save_progress()
                        self._save_results()
                        print(f"\n💾 Progress: {self.stats['found']}/{self.stats['searched']} NPIs found")
                    
                    # Delay between searches
                    if i < len(batch) - 1:
                        delay = self._random_delay(3, 6)
                        print(f"   ⏱️  Waiting {delay:.1f}s...")
                
                # Longer pause between batches
                if processed < total_to_process:
                    pause = random.uniform(15, 30)
                    print(f"\n⏸️  Batch complete. Pausing {pause:.1f}s...")
                    await asyncio.sleep(pause)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            self._log("Interrupted by user")
        finally:
            await self.close_browser()
            self._save_progress()
            self._save_results()
    
    def print_summary(self):
        """Print final summary."""
        print()
        print("=" * 70)
        print("📊 FINAL SUMMARY")
        print("=" * 70)
        print(f"Total searched:      {self.stats['searched']}")
        print(f"NPIs found:          {self.stats['found']}")
        print(f"Success rate:        {self.stats['found']/max(self.stats['searched'],1)*100:.1f}%")
        print(f"Errors:              {self.stats['errors']}")
        print(f"Total processed:     {len(self.processed_ids)}")
        print()
        print(f"Results:  {RESULTS_FILE}")
        print(f"Progress: {PROGRESS_FILE}")
        print(f"Log:      {LOG_FILE}")
        print("=" * 70)
        self._log(f"Session complete. Found {self.stats['found']} NPIs out of {self.stats['searched']} searched")


async def main():
    scraper = CignaNPIScraper()
    try:
        await scraper.run(max_providers=None)
    finally:
        scraper.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
