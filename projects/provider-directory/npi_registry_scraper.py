#!/usr/bin/env python3
"""
NPI Registry Scraper

Uses the official NPPES NPI Registry API to look up NPI numbers
for providers by name and state. This is more reliable than web scraping.

API Documentation: https://npiregistry.cms.hhs.gov/api/
"""

import asyncio
import sqlite3
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, asdict
import urllib.parse
import urllib.request
import ssl


# Configuration
DB_PATH = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db")
PROGRESS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/npi_registry_progress.json")
RESULTS_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/npi_registry_results.json")
LOG_FILE = Path("/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/npi_registry.log")

# NPI Registry API
NPI_API_URL = "https://npiregistry.cms.hhs.gov/api/"

# Settings
MIN_DELAY = 0.5  # NPI registry allows faster requests
MAX_DELAY = 1.5
BATCH_SIZE = 100


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
    provider_data: Optional[Dict]
    confidence: str
    timestamp: str
    error: Optional[str] = None


class NPIRegistryScraper:
    """Scraper using the official NPI Registry API."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.results: List[ScrapeResult] = []
        self.processed_ids: set = set()
        self.stats = {'searched': 0, 'found': 0, 'errors': 0, 'multiple': 0}
        
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
    
    def _delay(self, min_s=MIN_DELAY, max_s=MAX_DELAY):
        time.sleep(random.uniform(min_s, max_s))
    
    def _extract_names(self, full_name: str) -> Tuple[str, str]:
        """Extract first and last name from full name."""
        # Remove prefixes and suffixes
        clean = re.sub(r'^(Dr\.?\s+|Doctor\s+|Prof\.?\s+)', '', full_name, flags=re.I)
        clean = re.sub(r',?\s+(MD|DO|PhD|NP|PA|RN|DVM|DDS|DMD|LCSW|CNM)$', '', clean, flags=re.I)
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
    
    def _search_npi_registry(self, first_name: str, last_name: str, state: str) -> Dict:
        """Search NPI Registry API."""
        params = {
            'version': '2.1',
            'first_name': first_name,
            'last_name': last_name,
            'state': state,
            'limit': 10
        }
        
        url = f"{NPI_API_URL}?{urllib.parse.urlencode(params)}"
        
        # Create SSL context that doesn't verify certificates (for compatibility)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ProviderDirectory/1.0)',
                'Accept': 'application/json'
            }
        )
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    
    def _search_by_name_only(self, last_name: str, state: str) -> Dict:
        """Search by last name only (broader search)."""
        params = {
            'version': '2.1',
            'last_name': last_name,
            'state': state,
            'limit': 20
        }
        
        url = f"{NPI_API_URL}?{urllib.parse.urlencode(params)}"
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ProviderDirectory/1.0)',
                'Accept': 'application/json'
            }
        )
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    
    def _find_best_match(self, results: List[Dict], first_name: str, last_name: str, state: str) -> Optional[Tuple[str, Dict, str]]:
        """Find the best matching NPI from results."""
        if not results:
            return None
        
        matches = []
        
        for result in results:
            npi = result.get('number')
            basic = result.get('basic', {})
            result_first = basic.get('first_name', '')
            result_last = basic.get('last_name', '')
            
            # Check for name match
            first_match = first_name.lower() in result_first.lower() or result_first.lower() in first_name.lower()
            last_match = last_name.lower() in result_last.lower() or result_last.lower() in last_name.lower()
            
            if last_match:
                if first_match:
                    matches.append((npi, result, 'high'))
                else:
                    matches.append((npi, result, 'medium'))
        
        if matches:
            # Return highest confidence match
            high_conf = [m for m in matches if m[2] == 'high']
            if high_conf:
                return high_conf[0]
            return matches[0]
        
        return None
    
    def _lookup_provider(self, provider: Provider) -> ScrapeResult:
        """Look up NPI for a provider."""
        result = ScrapeResult(
            provider_id=provider.id,
            name=provider.name,
            state=provider.state,
            npi_found=None,
            provider_data=None,
            confidence='none',
            timestamp=datetime.now().isoformat()
        )
        
        try:
            first, last = self._extract_names(provider.name)
            if not last:
                result.error = "Could not parse name"
                return result
            
            print(f"   Looking up: {first} {last} in {provider.state}")
            
            # Try exact search first
            data = self._search_npi_registry(first, last, provider.state)
            results = data.get('results', [])
            
            if len(results) == 0:
                # Try broader search with just last name
                print(f"   No exact match, trying broader search...")
                data = self._search_by_name_only(last, provider.state)
                results = data.get('results', [])
            
            if len(results) == 0:
                result.error = "No matches found"
                return result
            
            if len(results) > 1:
                self.stats['multiple'] += 1
                print(f"   Found {len(results)} matches, selecting best...")
            
            # Find best match
            match = self._find_best_match(results, first, last, provider.state)
            
            if match:
                npi, provider_data, confidence = match
                result.npi_found = str(npi)
                result.provider_data = provider_data
                result.confidence = confidence
                print(f"   ✅ Found NPI: {npi} (confidence: {confidence})")
            else:
                result.error = "No confident match"
                
        except Exception as e:
            result.error = str(e)
            print(f"   ❌ Error: {e}")
        
        return result
    
    def _update_db(self, result: ScrapeResult):
        """Update provider with found NPI."""
        if not result.npi_found:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE providers SET npi = ?, source = 'npi_registry' WHERE id = ?",
                (result.npi_found, result.provider_id)
            )
            conn.commit()
            conn.close()
            print(f"   💾 Saved NPI {result.npi_found}")
        except Exception as e:
            print(f"   ⚠️ DB error: {e}")
    
    def run(self, max_providers: Optional[int] = None):
        """Run the scraper."""
        print("=" * 70)
        print("🚀 NPI REGISTRY SCRAPER")
        print("=" * 70)
        print("Using official NPPES NPI Registry API")
        print()
        
        remaining = self._count_remaining()
        print(f"Providers without NPI: {remaining}")
        print(f"Previously processed: {len(self.processed_ids)}\n")
        
        if remaining == 0:
            print("✅ Nothing to do!")
            return
        
        to_process = min(remaining, max_providers or remaining)
        processed = 0
        
        try:
            while processed < to_process:
                batch = self._get_batch(BATCH_SIZE)
                if not batch:
                    break
                
                print(f"\n📦 Processing batch of {len(batch)}...")
                
                for i, provider in enumerate(batch):
                    processed += 1
                    print(f"\n[{processed}/{to_process}] {provider.name} ({provider.state})")
                    
                    result = self._lookup_provider(provider)
                    
                    self.stats['searched'] += 1
                    if result.npi_found:
                        self.stats['found'] += 1
                        self._update_db(result)
                    else:
                        self.stats['errors'] += 1
                    
                    self.results.append(result)
                    self.processed_ids.add(provider.id)
                    
                    if processed % 10 == 0:
                        self._save_progress()
                        self._save_results()
                    
                    if i < len(batch) - 1:
                        self._delay()
                
                print(f"\n⏸️ Batch done. Found {self.stats['found']}/{self.stats['searched']}")
                
                # Save after each batch
                self._save_progress()
                self._save_results()
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted")
        finally:
            self._save_progress()
            self._save_results()
    
    def summary(self):
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"Searched:     {self.stats['searched']}")
        print(f"Found:        {self.stats['found']}")
        print(f"Success rate: {self.stats['found']/max(self.stats['searched'],1)*100:.1f}%")
        print(f"Multiple:     {self.stats['multiple']}")
        print(f"Errors:       {self.stats['errors']}")
        print(f"Total processed: {len(self.processed_ids)}")
        print("=" * 70)


def main():
    scraper = NPIRegistryScraper()
    try:
        scraper.run(max_providers=None)  # Process all
    finally:
        scraper.summary()


if __name__ == "__main__":
    main()
