#!/usr/bin/env python3
"""Save the scraped Healthgrades v2 data to the database."""

import asyncio
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/projects/provider-directory')

from sources.healthgrades_v2 import HealthgradesSourceV2
from models import SearchCriteria, Provider, Address
from storage import ProviderStorage


async def main():
    """Re-run the scraper and save data properly."""
    print("=" * 70)
    print("🏥  HEALTHGRADES V2 SCRAPER - Saving to Database")
    print("=" * 70)
    print()
    
    # Create source
    source = HealthgradesSourceV2(headless=True)
    
    # Create search criteria
    criteria = SearchCriteria(
        zip_code="90210",
        radius_miles=100,
        max_pages=78
    )
    
    print(f"🔍 Scraping up to {criteria.max_pages} pages...")
    print(f"   Parallel processing: 5 pages at a time")
    print()
    
    start_time = datetime.now()
    
    try:
        # Run search
        result = await source.search(criteria)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("📊 SCRAPING RESULTS")
        print("=" * 70)
        print(f"Duration: {duration:.1f} seconds")
        print(f"Total providers extracted: {len(result.providers)}")
        print()
        
        # Count providers with various data
        with_ratings = sum(1 for p in result.providers if p.healthgrades_rating)
        with_photos = sum(1 for p in result.providers if p.photo_url)
        with_phones = sum(1 for p in result.providers if p.phone)
        with_reviews = sum(1 for p in result.providers if p.review_count)
        with_profile_urls = sum(1 for p in result.providers if p.source_url)
        
        print("📈 Data Quality Summary:")
        print(f"   Providers with ratings: {with_ratings} ({with_ratings/len(result.providers)*100:.1f}%)")
        print(f"   Providers with review counts: {with_reviews} ({with_reviews/len(result.providers)*100:.1f}%)")
        print(f"   Providers with photos: {with_photos} ({with_photos/len(result.providers)*100:.1f}%)")
        print(f"   Providers with phones: {with_phones} ({with_phones/len(result.providers)*100:.1f}%)")
        print(f"   Providers with profile URLs: {with_profile_urls} ({with_profile_urls/len(result.providers)*100:.1f}%)")
        print()
        
        # Show sample providers with rich data
        print("📝 Sample Providers with Rich Data:")
        rich_providers = [p for p in result.providers if p.healthgrades_rating or p.photo_url or p.phone]
        for i, provider in enumerate(rich_providers[:10], 1):
            print(f"\n{i}. {provider.name}")
            if provider.healthgrades_rating:
                print(f"   ⭐ Rating: {provider.healthgrades_rating}/5 ({provider.review_count or 0} reviews)")
            if provider.photo_url:
                print(f"   📷 Photo: {provider.photo_url[:60]}...")
            if provider.phone:
                print(f"   📞 Phone: {provider.phone}")
            if provider.source_url:
                print(f"   🔗 Profile: {provider.source_url[:60]}...")
            if provider.address:
                print(f"   📍 Location: {provider.address.city}, {provider.address.state}")
            if provider.scraped_at:
                print(f"   🕐 Scraped: {provider.scraped_at}")
        
        # Save to database
        print("\n" + "=" * 70)
        print("💾 SAVING TO DATABASE")
        print("=" * 70)
        
        storage = ProviderStorage()
        
        # First, let's see what we have in the database
        existing = storage.get_all_providers()
        print(f"Existing providers in DB: {len(existing)}")
        
        # Save new providers
        saved_count = storage.save_providers(result.providers)
        print(f"Saved {saved_count} providers to database")
        
        # Export to JSON and CSV
        json_path = storage.export_to_json()
        csv_path = storage.export_to_csv()
        print(f"   JSON: {json_path}")
        print(f"   CSV: {csv_path}")
        
        # Show final DB stats
        final = storage.get_all_providers()
        print(f"\nFinal provider count in DB: {len(final)}")
        
        print("\n" + "=" * 70)
        print("✅ SCRAPING COMPLETE")
        print("=" * 70)
        
        return {
            'total_scraped': len(result.providers),
            'with_ratings': with_ratings,
            'with_photos': with_photos,
            'with_phones': with_phones,
            'with_reviews': with_reviews,
            'duration_seconds': duration,
            'saved_count': saved_count
        }
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await source.close()


if __name__ == '__main__':
    results = asyncio.run(main())
    print("\n📋 Final Summary:")
    for key, value in results.items():
        print(f"   {key}: {value}")
