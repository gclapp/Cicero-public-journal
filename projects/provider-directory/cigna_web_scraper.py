#!/usr/bin/env python3
"""
Cigna Web Scraper for NPI Enrichment

Searches Cigna's provider directory by name + state to find NPI numbers
for REI providers missing NPIs in the database.

Features:
- Playwright browser automation with stealth
- Resume capability
- Progress tracking
- Anti-detection measures
- SQLite database integration
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

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# Configuration
BASE_URL = "https://hcpdirectory.cigna.com/"
SEARCH_URL = "https://hcpdirectory.cigna.com/web/public/providers"
DB_PATH = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db")
PROGRESS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_scraper_progress.json")
RESULTS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_npi_results.json")

# Anti-detection settings
MIN_DELAY = 2.0
MAX_DELAY = 5.0
PAGE_TIMEOUT = 30000

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]


@dataclass
class Provider:
    id: int
    name: str
    first_name: Optional[str]
    last_name: Optional[str]
    state: str
    city: str
    npi: Optional[str]


@dataclass
class ScrapeResult:
    provider_id: int
    name: str
    state: str
    npi_found: Optional[str]
    profile_url: Optional[str]
    confidence: str  # 'high', 'medium', 'low'
    timestamp: str
    error: Optional[str] = None


class CignaWebScraper:
    """Scraper for extracting NPI numbers from Cigna provider directory."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.results: List[ScrapeResult] = []
        self.processed_ids: set = set()
        self.stats = {
            'searched': 0,
            'found': 0,
            'errors': 0,
            'skipped': 0,
        }
        
        # Load progress if exists
        self._load_progress()
    
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
        """Initialize browser with stealth settings."""
        print("🚀 Initializing browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with stealth
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(USER_AGENTS),
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            java_script_enabled=True,
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)
        
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(PAGE_TIMEOUT)
        
        print("✅ Browser initialized")
    
    async def close_browser(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
            print("🛑 Browser closed")
    
    def _random_delay(self, min_sec: float = MIN_DELAY, max_sec: float = MAX_DELAY):
        """Add random delay to avoid detection."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _extract_name_parts(self, full_name: str) -> Tuple[str, str]:
        """Extract first and last name from full name."""
        # Remove common prefixes and suffixes
        clean_name = re.sub(r'^(Dr\.?\s+|Doctor\s+)', '', full_name, flags=re.IGNORECASE)
        clean_name = re.sub(r',?\s+(MD|DO|PhD|NP|PA|RN)$', '', clean_name, flags=re.IGNORECASE)
        
        parts = clean_name.strip().split()
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return clean_name, ""
    
    def _get_providers_without_npi(self, limit: Optional[int] = None) -> List[Provider]:
        """Fetch providers from database that need NPI lookup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, name, first_name, last_name, state, city, npi
            FROM providers
            WHERE (npi IS NULL OR npi = '') AND state IS NOT NULL AND state != ''
            ORDER BY state, name
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        providers = []
        for row in rows:
            provider = Provider(
                id=row[0],
                name=row[1],
                first_name=row[2],
                last_name=row[3],
                state=row[4],
                city=row[5] or "",
                npi=row[6]
            )
            # Skip already processed
            if provider.id not in self.processed_ids:
                providers.append(provider)
        
        return providers
    
    async def _search_provider(self, provider: Provider) -> Optional[ScrapeResult]:
        """Search for a provider on Cigna and extract NPI."""
        result = ScrapeResult(
            provider_id=provider.id,
            name=provider.name,
            state=provider.state,
            npi_found=None,
            profile_url=None,
            confidence='low',
            timestamp=datetime.now().isoformat()
        )
        
        try:
            # Extract name parts for search
            first_name, last_name = self._extract_name_parts(provider.name)
            if not last_name:
                print(f"  ⚠️  Could not parse name: {provider.name}")
                result.error = "Name parsing failed"
                return result
            
            print(f"  🔍 Searching: {first_name} {last_name} in {provider.state}")
            
            # Navigate to search page
            await self.page.goto(SEARCH_URL, wait_until="networkidle")
            await asyncio.sleep(random.uniform(1, 2))
            
            # Fill search form
            # Look for name input
            name_selectors = [
                'input[placeholder*="name" i]',
                'input[name*="name" i]',
                'input[id*="name" i]',
                'input[aria-label*="name" i]',
                'input[data-testid*="name" i]',
                'input[type="search"]',
                'input:first-of-type',
            ]
            
            name_input = None
            for selector in name_selectors:
                try:
                    name_input = await self.page.query_selector(selector)
                    if name_input:
                        break
                except:
                    continue
            
            if not name_input:
                # Try to find any input that might be for search
                inputs = await self.page.query_selector_all('input')
                for inp in inputs:
                    input_type = await inp.get_attribute('type') or 'text'
                    if input_type in ['text', 'search']:
                        name_input = inp
                        break
            
            if not name_input:
                result.error = "Could not find name input field"
                return result
            
            # Clear and fill name
            await name_input.click()
            await name_input.fill("")
            await name_input.fill(f"{first_name} {last_name}")
            await asyncio.sleep(random.uniform(0.5, 1))
            
            # Look for state dropdown or input
            state_selectors = [
                'select[name*="state" i]',
                'select[id*="state" i]',
                'input[placeholder*="state" i]',
                'input[name*="state" i]',
            ]
            
            state_input = None
            for selector in state_selectors:
                try:
                    state_input = await self.page.query_selector(selector)
                    if state_input:
                        break
                except:
                    continue
            
            if state_input:
                tag_name = await state_input.evaluate('el => el.tagName.toLowerCase()')
                if tag_name == 'select':
                    await state_input.select_option(value=provider.state)
                else:
                    await state_input.fill(provider.state)
                await asyncio.sleep(random.uniform(0.3, 0.7))
            
            # Click search button
            search_btn_selectors = [
                'button:has-text("Search")',
                'button:has-text("Find")',
                'button[type="submit"]',
                'button[data-testid*="search" i]',
                'button[class*="search" i]',
                'button:first-of-type',
            ]
            
            search_btn = None
            for selector in search_btn_selectors:
                try:
                    search_btn = await self.page.query_selector(selector)
                    if search_btn:
                        visible = await search_btn.is_visible()
                        if visible:
                            break
                except:
                    continue
            
            if search_btn:
                await search_btn.click()
            else:
                # Try pressing Enter
                await name_input.press('Enter')
            
            # Wait for results
            await asyncio.sleep(random.uniform(3, 5))
            
            # Check for results
            result_selectors = [
                '[data-testid*="result" i]',
                '[class*="result" i]',
                '[class*="provider" i]',
                '[class*="card" i]',
                'article',
                '.list-item',
                '[role="listitem"]',
            ]
            
            results = []
            for selector in result_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        results = elements
                        break
                except:
                    continue
            
            if not results:
                # Check for "no results" message
                page_text = await self.page.content()
                if 'no results' in page_text.lower() or 'not found' in page_text.lower():
                    result.error = "No results found"
                else:
                    result.error = "Could not find results container"
                return result
            
            print(f"    📊 Found {len(results)} result(s)")
            
            # Process first few results to find best match
            for idx, result_elem in enumerate(results[:3]):
                try:
                    # Get provider name from result
                    name_elem = await result_elem.query_selector('h3, h4, .name, [class*="name"], a')
                    if name_elem:
                        result_name = await name_elem.text_content()
                        result_name = result_name.strip() if result_name else ""
                        
                        # Check if this matches our search
                        name_match = last_name.lower() in result_name.lower()
                        
                        if name_match:
                            # Click to get details
                            await result_elem.click()
                            await asyncio.sleep(random.uniform(2, 3))
                            
                            # Look for NPI on the page
                            page_content = await self.page.content()
                            npi_match = re.search(r'NPI[\s#:]*(\d{10})', page_content, re.IGNORECASE)
                            
                            if npi_match:
                                npi = npi_match.group(1)
                                result.npi_found = npi
                                result.profile_url = self.page.url
                                result.confidence = 'high' if name_match else 'medium'
                                print(f"    ✅ Found NPI: {npi}")
                                return result
                            
                            # Go back to results
                            await self.page.go_back()
                            await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    continue
            
            result.error = "NPI not found in search results"
            
        except Exception as e:
            result.error = str(e)
            print(f"    ❌ Error: {e}")
        
        return result
    
    def _update_database(self, result: ScrapeResult):
        """Update provider record with found NPI."""
        if not result.npi_found:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE providers SET npi = ? WHERE id = ?",
                (result.npi_found, result.provider_id)
            )
            conn.commit()
            conn.close()
            print(f"    💾 Database updated with NPI {result.npi_found}")
        except Exception as e:
            print(f"    ⚠️  Failed to update database: {e}")
    
    async def run(self, batch_size: int = 100, max_providers: Optional[int] = None):
        """Run the scraper on providers without NPIs."""
        print("=" * 70)
        print("🚀 CIGNA WEB SCRAPER - NPI ENRICHMENT")
        print("=" * 70)
        print()
        
        # Get providers to process
        providers = self._get_providers_without_npi(limit=max_providers)
        print(f"📋 Found {len(providers)} providers to process")
        print(f"   (Already processed: {len(self.processed_ids)})")
        print()
        
        if not providers:
            print("✅ No providers to process!")
            return
        
        # Initialize browser
        await self.init_browser()
        
        try:
            # Process in batches
            for i, provider in enumerate(providers):
                print(f"\n[{i+1}/{len(providers)}] Processing: {provider.name} ({provider.state})")
                
                # Search and extract
                result = await self._search_provider(provider)
                
                # Update stats
                self.stats['searched'] += 1
                if result.npi_found:
                    self.stats['found'] += 1
                    self._update_database(result)
                elif result.error:
                    self.stats['errors'] += 1
                
                self.results.append(result)
                self.processed_ids.add(provider.id)
                
                # Save progress periodically
                if (i + 1) % 10 == 0:
                    self._save_progress()
                    self._save_results()
                    print(f"\n💾 Progress saved: {self.stats['found']} NPIs found out of {self.stats['searched']} searched")
                
                # Random delay between searches
                if i < len(providers) - 1:
                    self._random_delay()
                
                # Batch pause
                if (i + 1) % batch_size == 0 and i < len(providers) - 1:
                    pause_time = random.uniform(10, 20)
                    print(f"\n⏸️  Batch complete. Pausing for {pause_time:.1f} seconds...")
                    await asyncio.sleep(pause_time)
        
        finally:
            # Cleanup
            await self.close_browser()
            self._save_progress()
            self._save_results()
    
    def print_summary(self):
        """Print summary of scraping results."""
        print()
        print("=" * 70)
        print("📊 SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Total searched:     {self.stats['searched']}")
        print(f"NPIs found:         {self.stats['found']}")
        print(f"Match rate:         {self.stats['found']/max(self.stats['searched'],1)*100:.1f}%")
        print(f"Errors:             {self.stats['errors']}")
        print(f"Already processed:  {len(self.processed_ids)}")
        print()
        print(f"Results saved to: {RESULTS_FILE}")
        print(f"Progress saved to: {PROGRESS_FILE}")
        print("=" * 70)


async def main():
    """Main entry point."""
    scraper = CignaWebScraper()
    
    try:
        # Run scraper - process all providers
        await scraper.run(batch_size=50, max_providers=None)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        scraper.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
