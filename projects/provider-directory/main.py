#!/usr/bin/env python3
"""Provider Directory Scraper - Main CLI Interface.

Unified interface for scraping provider directories from multiple sources:
- Cigna API (pending approval)
- Cigna Scraping (Playwright browser automation)
- Healthgrades Scraping (Thunderbit API)

Usage:
    python main.py                          # Interactive mode
    python main.py --list-sources           # Show available sources
    python main.py --source cigna-scraper --zip 90210 --specialty "Internal Medicine"
"""

import argparse
import asyncio
import sys
from typing import Optional

from models import SearchCriteria
from sources import list_sources, get_source
from storage import ProviderStorage


def print_header():
    """Print application header."""
    print("=" * 70)
    print("🏥  PROVIDER DIRECTORY SCRAPER")
    print("=" * 70)
    print()


def print_sources():
    """Print available data sources."""
    print("\n📋 AVAILABLE DATA SOURCES:\n")
    
    sources = list_sources()
    
    for source in sources:
        # Status emoji
        status_emoji = {
            'active': '✅',
            'beta': '🚧',
            'pending': '⏳',
            'disabled': '❌'
        }.get(source.status, '❓')
        
        # Reliability indicator
        reliability_emoji = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }.get(source.reliability, '⚪')
        
        print(f"{status_emoji} {source.name}")
        print(f"   ID: {source.id}")
        print(f"   Status: {source.status.upper()}")
        print(f"   Reliability: {reliability_emoji} {source.reliability}")
        print(f"   Auth: {'🔐 ' + source.auth_type if source.requires_auth else '🔓 None'}")
        if source.rate_limit:
            print(f"   Rate Limit: {source.rate_limit}")
        print(f"   Description: {source.description}")
        if source.notes:
            print(f"   Notes: {source.notes}")
        print()


def interactive_mode():
    """Run interactive source selection."""
    print_header()
    print_sources()
    
    sources = list_sources()
    active_sources = [s for s in sources if s.status in ('active', 'beta')]
    
    if not active_sources:
        print("❌ No active sources available.")
        print("   Please check your configuration or wait for API approvals.")
        return
    
    print("\n🎯 SELECT A DATA SOURCE:\n")
    
    available_choices = []
    for i, source in enumerate(sources, 1):
        status_emoji = {
            'active': '✅',
            'beta': '🚧',
            'pending': '⏳',
            'disabled': '❌'
        }.get(source.status, '❓')
        
        print(f"{i}. {status_emoji} {source.name}")
        
        # Only allow selection of active/beta sources
        if source.status in ('active', 'beta'):
            available_choices.append((i, source))
    
    print()
    
    # Get user selection
    while True:
        try:
            choice = input(f"Select source (1-{len(sources)}, or q to quit): ").strip().lower()
            
            if choice == 'q':
                print("Goodbye!")
                return
            
            choice_num = int(choice)
            
            # Check if choice is pending/disabled
            selected = sources[choice_num - 1]
            if selected.status == 'pending':
                print(f"\n⏳ {selected.name} is not yet available.")
                print(f"   {selected.notes or 'Please wait for this source to become active.'}")
                print()
                continue
            elif selected.status == 'disabled':
                print(f"\n❌ {selected.name} is currently disabled.")
                print()
                continue
            
            # Valid active/beta selection
            if 1 <= choice_num <= len(sources):
                selected_source = sources[choice_num - 1]
                print(f"\n✅ Selected: {selected_source.name}\n")
                return selected_source.id
            else:
                print("Invalid selection. Please try again.")
        
        except (ValueError, IndexError):
            print("Invalid input. Please enter a number or 'q'.")


def get_search_criteria_interactive() -> SearchCriteria:
    """Get search criteria from user interactively."""
    print("\n🔍 SEARCH CRITERIA:\n")
    
    # ZIP code (required)
    while True:
        zip_code = input("ZIP Code (required): ").strip()
        if zip_code:
            break
        print("ZIP code is required.")
    
    # Radius
    radius_input = input("Search radius in miles [10]: ").strip()
    radius = int(radius_input) if radius_input.isdigit() else 10
    
    # Specialty
    specialty = input("Specialty (optional, e.g., 'Internal Medicine'): ").strip() or None
    
    # Provider name
    provider_name = input("Provider name (optional): ").strip() or None
    
    # Accepting new patients only
    accepting_input = input("Accepting new patients only? [y/N]: ").strip().lower()
    accepting_only = accepting_input == 'y'
    
    criteria = SearchCriteria(
        zip_code=zip_code,
        radius_miles=radius,
        specialty=specialty,
        provider_name=provider_name,
        accepting_new_patients_only=accepting_only
    )
    
    print(f"\n📍 Search: {criteria.zip_code} (+{criteria.radius_miles}mi)")
    if criteria.specialty:
        print(f"   Specialty: {criteria.specialty}")
    if criteria.provider_name:
        print(f"   Name: {criteria.provider_name}")
    print()
    
    return criteria


async def run_search(source_id: str, criteria: SearchCriteria, export: bool = True):
    """Run a search with the specified source and criteria."""
    print(f"🚀 Starting search with {source_id}...\n")
    
    # Get source instance
    try:
        # Always use headless mode (required for server environments)
        if source_id == 'cigna-scraper':
            source = get_source(source_id, headless=True)
        else:
            source = get_source(source_id)
    except Exception as e:
        print(f"❌ Error initializing source: {e}")
        return
    
    # Run search
    async with source:
        result = await source.search(criteria)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 SEARCH RESULTS")
    print("=" * 70)
    print(f"Source: {result.source}")
    print(f"Search time: {result.search_time_ms or 'N/A'}ms")
    
    if result.error:
        print(f"\n❌ Error: {result.error}")
        return
    
    print(f"Providers found: {len(result.providers)}")
    if result.total_count:
        print(f"Total available: {result.total_count}")
    
    if result.providers:
        print("\n📝 First 5 providers:")
        for i, provider in enumerate(result.providers[:5], 1):
            print(f"\n{i}. {provider.name}")
            if provider.specialties:
                print(f"   Specialties: {', '.join(provider.specialties[:3])}")
            if provider.address:
                print(f"   Location: {provider.address.city}, {provider.address.state}")
            if provider.phone:
                print(f"   Phone: {provider.phone}")
    
    # Save results
    if export and result.providers:
        storage = ProviderStorage()
        saved = storage.save_providers(result.providers)
        
        json_path = storage.export_to_json()
        csv_path = storage.export_to_csv()
        
        print(f"\n💾 Saved {saved} providers to database")
        print(f"   JSON: {json_path}")
        print(f"   CSV: {csv_path}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Provider Directory Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Interactive mode
  python main.py --list-sources               # Show available sources
  python main.py --source cigna-scraper --zip 90210
  python main.py --source healthgrades --zip 10001 --specialty "Cardiology"
        """
    )
    
    parser.add_argument(
        '--list-sources', '-l',
        action='store_true',
        help='List all available data sources'
    )
    
    parser.add_argument(
        '--source', '-s',
        choices=['cigna-api', 'cigna-scraper', 'healthgrades'],
        help='Data source to use'
    )
    
    parser.add_argument(
        '--zip', '-z',
        help='ZIP code to search (required for search)'
    )
    
    parser.add_argument(
        '--radius', '-r',
        type=int,
        default=10,
        help='Search radius in miles (default: 10)'
    )
    
    parser.add_argument(
        '--specialty',
        help='Medical specialty filter'
    )
    
    parser.add_argument(
        '--name',
        help='Provider name filter'
    )
    
    parser.add_argument(
        '--accepting-new',
        action='store_true',
        help='Only show providers accepting new patients'
    )
    
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Skip exporting results to files'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=10,
        help='Maximum pages to scrape (default: 10)'
    )
    
    args = parser.parse_args()
    
    # List sources mode
    if args.list_sources:
        print_header()
        print_sources()
        return
    
    # Interactive mode
    if not args.source:
        source_id = interactive_mode()
        if not source_id:
            return
        
        criteria = get_search_criteria_interactive()
    
    # Command-line mode
    else:
        source_id = args.source
        
        if not args.zip:
            print("❌ ZIP code is required. Use --zip or run in interactive mode.")
            sys.exit(1)
        
        criteria = SearchCriteria(
            zip_code=args.zip,
            radius_miles=args.radius,
            specialty=args.specialty,
            provider_name=args.name,
            accepting_new_patients_only=args.accepting_new,
            max_pages=args.max_pages
        )
    
    # Run the search
    await run_search(source_id, criteria, export=not args.no_export)


if __name__ == '__main__':
    asyncio.run(main())
