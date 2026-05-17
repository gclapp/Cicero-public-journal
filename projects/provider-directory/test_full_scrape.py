#!/usr/bin/env python3
"""Test scraping multiple pages from Healthgrades."""

import asyncio
from sources.healthgrades import HealthgradesSource
from models import SearchCriteria


async def test():
    """Test scraping multiple pages."""
    
    # Scrape first 10 pages (~200 providers)
    criteria = SearchCriteria(
        zip_code='',
        state='',
        specialty='Reproductive Endocrinology',
        max_pages=10
    )
    
    print("=" * 70)
    print("🔍 SCRAPING HEALTHGRADES - REIs with Cigna")
    print("=" * 70)
    print()
    print("Target: First 10 pages (~200 providers)")
    print("Total available: 1,559 providers")
    print()
    
    async with HealthgradesSource(headless=True) as source:
        result = await source.search(criteria)
        
        print()
        print("=" * 70)
        print("📊 RESULTS")
        print("=" * 70)
        print(f"Providers extracted: {len(result.providers)}")
        print(f"Search time: {result.search_time_ms}ms")
        
        if result.error:
            print(f"Error: {result.error}")
        
        print()
        print("First 10 providers:")
        for i, provider in enumerate(result.providers[:10], 1):
            print(f"  {i}. {provider.name}")


if __name__ == "__main__":
    asyncio.run(test())
