#!/usr/bin/env python3
"""
Cigna NPI Scraper - Production Version

Searches Cigna's provider directory to find NPI numbers for REI providers.
Uses Playwright for browser automation with anti-detection measures.
"""

import asyncio
import sqlite3
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass, asdict

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# Configuration
DB_PATH = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db")
PROGRESS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_progress.json")
RESULTS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_results.json")
LOG_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/cigna_scraper.log")

CIGNA_URL = "https://hcpdirectory.cigna.com/web/public/consumer/directory/search"

# Settings
MIN_DELAY = 3.0
MAX_DELAY = 6.0
BATCH_SIZE = 25


@dataclass
class Provider:
    id: int
    name: str
    first_name: Optional[str]
    last_name: Optional[str]
    state: str
    city: str


@dataclass
class ScrapeResult:
    provider_id: int
    name: str
    state: str
    npi_found: Optional[str]
    profile_url: Optional[str]
    confidence: str
    timestamp: str
    error: Optional[str] = None


class CignaScraper:
    def __init__(self):
        self.db_path = DB_PATH
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.results: List[ScrapeResult] = []
        self.processed_ids: set = set()
        self.stats = {'searched': 0, 'found': 0, 'errors': 0}
        
        self._load_progress()
        self._init_log()
    
    def _init_log(self):
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(f"\n{'='*60}\nSession: {datetime.now().isoformat()}\n{'='*60}\n")
    
    def _log(self, msg: str):
        ts = datetime.now().strftime('%H:%M:%S')
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{ts}] {msg}\n")
    
    def _load_progress(self):
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE) as f:
                data = json.load(f)
                self.processed_ids = set(data.get('processed_ids', []))
                self.stats = data.get('stats', self.stats)
            print(f"📂 Loaded {len(self.processed_ids)} previously processed providers")
    
    def _save_progress(self):
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                'processed_ids': list(self.processed_ids),
                'stats': self.stats,
                'updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def _save_results(self):
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RESULTS_FILE, 'w') as f:
            json.dump({
                'results': [asdict(r) for r in self.results],
                'stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
    
    async def init_browser(self):
        print("🚀 Starting browser...")
        self._log("Browser init")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)
        print("✅ Browser ready")
    
    async def close(self):
        if self.browser:
            await self.browser.close()
            print("🛑 Browser closed")
    
    def _delay(self, min_s=MIN_DELAY, max_s=MAX_DELAY):
        time.sleep(random.uniform(min_s, max_s))
    
    def _extract_names(self, full_name: str) -> Tuple[str, str]:
        clean = re.sub(r'^(Dr\.?\s+|Doctor\s+)', '', full_name, flags=re.I)
        clean = re.sub(r',?\s+(MD|DO|PhD|NP|PA|RN)$', '', clean, flags=re.I)
        parts = clean.strip().split()
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return clean, ""
    
    def _get_batch(self, limit: int = BATCH_SIZE) -> List[Provider]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, first_name, last_name, state, city
            FROM providers
            WHERE (npi IS NULL OR npi = '') AND state IS NOT NULL AND state != ''
            ORDER BY state, name
            LIMIT ?
        """, (limit,))
        
        providers = []
        for row in cursor.fetchall():
            if row[0] not in self.processed_ids:
                providers.append(Provider(*row))
        conn.close()
        return providers
    
    def _count_remaining(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM providers
            WHERE (npi IS NULL OR npi = '') AND state IS NOT NULL AND state != ''
        """)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    async def _search_provider(self, provider: Provider) -> ScrapeResult:
        result = ScrapeResult(
            provider_id=provider.id,
            name=provider.name,
            state=provider.state,
            npi_found=None,
            profile_url=None,
            confidence='none',
            timestamp=datetime.now().isoformat()
        )
        
        try:
            first, last = self._extract_names(provider.name)
            if not last:
                result.error = "Name parse failed"
                return result
            
            print(f"   Searching: {first} {last} in {provider.state}")
            
            # Navigate to search page
            await self.page.goto(CIGNA_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Find location input (usually the main search)
            loc_input = await self.page.wait_for_selector('input[placeholder*="Address"], input[placeholder*="Zip"]', timeout=5000)
            if not loc_input:
                result.error = "No location input found"
                return result
            
            # Enter location (city, state or zip)
            location = f"{provider.city}, {provider.state}" if provider.city else provider.state
            await loc_input.fill("")
            await loc_input.type(location, delay=50)
            await asyncio.sleep(0.5)
            
            # Look for provider name input
            name_input = await self.page.query_selector('input[placeholder*="doctor"], input[placeholder*="provider"], input[name*="provider"]')
            if name_input:
                await name_input.type(f"{first} {last}", delay=50)
                await asyncio.sleep(0.5)
            
            # Click search
            search_btn = await self.page.query_selector('button:has-text("Search"), button[type="submit"]')
            if search_btn:
                await search_btn.click()
            else:
                await loc_input.press('Enter')
            
            await asyncio.sleep(4)
            
            # Check for results
            content = await self.page.content()
            text = await self.page.inner_text('body')
            
            if 'no results' in text.lower() or 'no provider' in text.lower():
                result.error = "No results"
                return result
            
            if 'captcha' in text.lower():
                result.error = "CAPTCHA"
                return result
            
            # Look for provider cards
            cards = await self.page.query_selector_all('[data-testid*="provider"], [class*="provider-card"], article, .card')
            
            if not cards:
                # Try any clickable element
                cards = await self.page.query_selector_all('a[href*="provider"], a[href*="detail"]')
            
            print(f"   Found {len(cards)} result(s)")
            
            for card in cards[:3]:
                try:
                    card_text = await card.inner_text()
                    if last.lower() not in card_text.lower():
                        continue
                    
                    # Click for details
                    await card.click()
                    await asyncio.sleep(3)
                    
                    # Extract NPI
                    detail = await self.page.content()
                    match = re.search(r'NPI[:\s#]*(\d{10})', detail, re.I)
                    
                    if match:
                        npi = match.group(1)
                        if len(npi) == 10 and npi[0] in ['1', '2']:
                            result.npi_found = npi
                            result.profile_url = self.page.url
                            result.confidence = 'high' if first.lower() in detail.lower() else 'medium'
                            print(f"   ✅ NPI: {npi}")
                            return result
                    
                    await self.page.go_back()
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    continue
            
            result.error = "NPI not found"
            
        except Exception as e:
            result.error = str(e)
            print(f"   ❌ Error: {e}")
        
        return result
    
    def _update_db(self, result: ScrapeResult):
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
            print(f"   💾 Saved NPI {result.npi_found}")
        except Exception as e:
            print(f"   ⚠️ DB error: {e}")
    
    async def run(self, max_providers: Optional[int] = None):
        print("=" * 60)
        print("🚀 CIGNA NPI SCRAPER")
        print("=" * 60)
        
        remaining = self._count_remaining()
        print(f"Providers without NPI: {remaining}")
        print(f"Previously processed: {len(self.processed_ids)}\n")
        
        if remaining == 0:
            print("✅ Nothing to do!")
            return
        
        await self.init_browser()
        
        try:
            to_process = min(remaining, max_providers or remaining)
            processed = 0
            
            while processed < to_process:
                batch = self._get_batch(BATCH_SIZE)
                if not batch:
                    break
                
                print(f"\n📦 Processing batch of {len(batch)}...")
                
                for i, provider in enumerate(batch):
                    processed += 1
                    print(f"\n[{processed}/{to_process}] {provider.name} ({provider.state})")
                    
                    result = await self._search_provider(provider)
                    
                    self.stats['searched'] += 1
                    if result.npi_found:
                        self.stats['found'] += 1
                        self._update_db(result)
                    else:
                        self.stats['errors'] += 1
                    
                    self.results.append(result)
                    self.processed_ids.add(provider.id)
                    
                    if processed % 5 == 0:
                        self._save_progress()
                        self._save_results()
                    
                    if i < len(batch) - 1:
                        self._delay(3, 6)
                
                print(f"\n⏸️ Batch done. Found {self.stats['found']}/{self.stats['searched']}")
                
                if processed < to_process:
                    await asyncio.sleep(random.uniform(10, 20))
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted")
        finally:
            await self.close()
            self._save_progress()
            self._save_results()
    
    def summary(self):
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"Searched: {self.stats['searched']}")
        print(f"Found:    {self.stats['found']}")
        print(f"Rate:     {self.stats['found']/max(self.stats['searched'],1)*100:.1f}%")
        print(f"Errors:   {self.stats['errors']}")
        print("=" * 60)


async def main():
    scraper = CignaScraper()
    try:
        await scraper.run(max_providers=50)  # Start with 50 for testing
    finally:
        scraper.summary()


if __name__ == "__main__":
    asyncio.run(main())
