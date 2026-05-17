"""Healthgrades provider directory scraper v2 - with ratings and parallel page scraping."""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from models import SearchCriteria, SearchResult, SourceInfo, Provider, Address
from sources.base import ProviderSource


class HealthgradesSourceV2(ProviderSource):
    """Healthgrades scraper v2 - extracts ratings, photos, phones, uses parallel processing."""
    
    BASE_URL = "https://www.healthgrades.com"
    CIGNA_PAYOR_CODE = "HPY00006F7"
    
    DEFAULT_TIMEOUT = 30000
    NAVIGATION_TIMEOUT = 60000
    DELAY_BETWEEN_REQUESTS = 1.0  # Reduced for parallel processing
    
    def __init__(self, headless: bool = True):
        super().__init__()
        self.headless = headless
        self.playwright = None
    
    @property
    def info(self) -> SourceInfo:
        return SourceInfo(
            id="healthgrades_v2",
            name="Healthgrades v2 (with ratings)",
            description="Enhanced scraper with ratings, photos, phone numbers",
            status="beta",
            requires_auth=False,
            auth_type=None,
            rate_limit="20 req/min",
            reliability="medium",
            notes="Parallel page processing for faster scraping"
        )
    
    async def _create_browser_context(self):
        """Create a new browser context."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        return browser, context
    
    async def _extract_provider_from_card(self, card_html: str, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract provider data from a search result card."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(card_html, 'html.parser')
        
        # Find provider name
        name_elem = soup.find('h3')
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        
        # Find rating
        rating = None
        rating_elem = soup.find(attrs={"data-test-id": "star-rating"})
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Find review count
        review_count = None
        review_elem = soup.find(text=re.compile(r'\d+\s+reviews?'))
        if review_elem:
            review_match = re.search(r'(\d+)', review_elem)
            if review_match:
                review_count = int(review_match.group(1))
        
        # Find profile URL
        profile_url = None
        link_elem = soup.find('a', href=re.compile(r'/physician/'))
        if link_elem:
            profile_url = self.BASE_URL + link_elem['href']
        
        # Find photo URL
        photo_url = None
        img_elem = soup.find('img', src=re.compile(r'photos\.healthgrades\.com'))
        if img_elem:
            photo_url = img_elem['src']
        
        # Find address
        address_elem = soup.find('address')
        street = city = state = zip_code = ""
        if address_elem:
            addr_text = address_elem.get_text(strip=True)
            # Parse address
            addr_match = re.search(r'(.+?),\s*([A-Z]{2})\s*(\d{5})', addr_text)
            if addr_match:
                street = addr_match.group(1)
                state = addr_match.group(2)
                zip_code = addr_match.group(3)
                # Try to extract city from street
                parts = street.rsplit(',', 1)
                if len(parts) > 1:
                    city = parts[-1].strip()
                    street = parts[0].strip()
        
        # Find phone
        phone = None
        phone_elem = soup.find(text=re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}'))
        if phone_elem:
            phone = phone_elem.strip()
        
        # Find specialty
        specialty = "REI Specialist"
        spec_elem = soup.find(text=re.compile(r'(Reproductive|Endocrinology|Infertility)'))
        if spec_elem:
            specialty = spec_elem.strip()
        
        return {
            'name': name,
            'rating': rating,
            'review_count': review_count,
            'profile_url': profile_url,
            'photo_url': photo_url,
            'street': street,
            'city': city,
            'state': state,
            'zip': zip_code,
            'phone': phone,
            'specialty': specialty,
            'scraped_at': datetime.now().isoformat()
        }
    
    async def _scrape_page(self, page_num: int, context: BrowserContext) -> List[Dict[str, Any]]:
        """Scrape a single page."""
        page = await context.new_page()
        page.set_default_timeout(self.DEFAULT_TIMEOUT)
        
        try:
            url = self._build_page_url(page_num)
            print(f"  📄 Scraping page {page_num}: {url}")
            
            await page.goto(url, timeout=self.NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Wait for content to load
            
            # Extract provider cards
            providers = []
            
            # Get all provider card elements
            cards = await page.query_selector_all('[data-test-id="provider-card"], .provider-card, article')
            
            if not cards:
                # Try alternative selectors
                cards = await page.query_selector_all('h3')
            
            print(f"    Found {len(cards)} potential provider cards")
            
            for card in cards:
                try:
                    # Get the HTML of the card or its parent container
                    card_html = await card.evaluate('el => el.outerHTML')
                    
                    # Try to get parent container if this is just an h3
                    if card_html.startswith('<h3'):
                        parent_html = await card.evaluate('el => el.parentElement?.outerHTML || el.outerHTML')
                        card_html = parent_html
                    
                    provider_data = await self._extract_provider_from_card(card_html, self.BASE_URL)
                    if provider_data:
                        providers.append(provider_data)
                except Exception as e:
                    print(f"    Error extracting card: {e}")
                    continue
            
            print(f"    ✓ Extracted {len(providers)} providers from page {page_num}")
            return providers
            
        except Exception as e:
            print(f"    ✗ Error on page {page_num}: {e}")
            return []
        finally:
            await page.close()
    
    def _build_page_url(self, page_num: int) -> str:
        """Build URL for a specific page."""
        base_url = (
            f"{self.BASE_URL}/usearch?"
            f"what=Reproductive%20Endocrinology%20%26%20Infertility"
            f"&entityCode=PS310"
            f"&searchType=PracticingSpecialty"
            f"&pt=32.67194%2C-117.105423"
            f"&distances=National"
            f"&payors={self.CIGNA_PAYOR_CODE}"
            f"&pageNum={page_num}"
            f"&sort.provider=bestmatch"
        )
        return base_url
    
    async def search(self, criteria: SearchCriteria) -> SearchResult:
        """Search for providers with parallel page scraping."""
        print(f"\n🔍 Searching Healthgrades for REIs with Cigna...")
        print(f"   National search with ratings and details")
        
        providers = []
        browser = None
        
        try:
            # Create browser
            browser, context = await self._create_browser_context()
            
            # First, get total pages by scraping page 1
            print("  📊 Getting total results from page 1...")
            page1_providers = await self._scrape_page(1, context)
            providers.extend(page1_providers)
            
            # Determine total pages (usually 78 for this search)
            total_pages = criteria.max_pages or 78
            print(f"   Will scrape {total_pages} pages")
            
            # Scrape remaining pages in parallel batches
            batch_size = 5  # Process 5 pages at a time
            for batch_start in range(2, total_pages + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, total_pages)
                page_nums = list(range(batch_start, batch_end + 1))
                
                print(f"\n  🔄 Processing pages {batch_start}-{batch_end}...")
                
                # Create tasks for parallel scraping
                tasks = [self._scrape_page(pn, context) for pn in page_nums]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(batch_results):
                    if isinstance(result, list):
                        providers.extend(result)
                    else:
                        print(f"    Page {page_nums[i]} failed: {result}")
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            print(f"\n  ✅ Total providers extracted: {len(providers)}")
            
        except Exception as e:
            print(f"  ✗ Error during search: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if browser:
                await browser.close()
            if self.playwright:
                await self.playwright.stop()
        
        # Convert to Provider objects
        provider_objects = []
        for p in providers:
            addr = Address(
                street=p.get('street', ''),
                city=p.get('city', ''),
                state=p.get('state', ''),
                zip=p.get('zip', '')
            )
            
            provider = Provider(
                name=p['name'],
                credentials=None,
                specialties=[p.get('specialty', 'REI')],
                address=addr,
                phone=p.get('phone'),
                source='healthgrades',
                source_url=p.get('profile_url'),
                photo_url=p.get('photo_url'),
                healthgrades_rating=p.get('rating'),
                review_count=p.get('review_count'),
                scraped_at=datetime.fromisoformat(p['scraped_at'])
            )
            provider_objects.append(provider)
        
        return SearchResult(
            providers=provider_objects,
            total_count=len(provider_objects),
            source_info=self.info,
            search_criteria=criteria,
            timestamp=datetime.now()
        )
    
    async def authenticate(self, **kwargs) -> bool:
        """No authentication needed for Healthgrades."""
        self._authenticated = True
        return True
    
    async def health_check(self) -> bool:
        """Check if Healthgrades is accessible."""
        try:
            import requests
            response = requests.get(self.BASE_URL, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Clean up resources."""
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
