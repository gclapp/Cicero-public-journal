#!/usr/bin/env python3
"""
Integration module for browser automation fallback in calendar_scanner.py

This module provides a drop-in replacement for the API-based availability
checking with automatic fallback to browser automation when the API fails.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

# Import the browser automation v2
from browser_automation_v2 import (
    ResyBrowserAutomationV2, 
    BookingStatus,
    check_availability_with_fallback,
    book_with_browser_fallback,
    find_and_book_best_slot,
    RESTAURANT_PRIORITY
)

# Setup logging
logger = logging.getLogger("browser_fallback")

# Data files
DATA_DIR = Path(__file__).parent / "data"
RESTAURANTS_FILE = DATA_DIR / "restaurants.json"
RESERVATIONS_FILE = DATA_DIR / "reservations.json"


def load_restaurants() -> List[Dict]:
    """Load restaurant list"""
    if not RESTAURANTS_FILE.exists():
        return []
    with open(RESTAURANTS_FILE) as f:
        data = json.load(f)
        return data.get('restaurants', [])


def load_reservations() -> List[Dict]:
    """Load existing reservations"""
    if not RESERVATIONS_FILE.exists():
        return []
    with open(RESERVATIONS_FILE) as f:
        data = json.load(f)
        return data.get('reservations', [])


def has_existing_reservation(date: str, reservations: List[Dict] = None) -> Optional[Dict]:
    """Check if we already have a reservation for this date"""
    if reservations is None:
        reservations = load_reservations()
    
    for res in reservations:
        if res.get('date') == date:
            return res
    return None


def find_resy_reservations_with_browser_fallback(
    venue_id: str,
    day: str,
    party_size: int,
    venue_name: str = "",
    lat: str = None,
    long: str = None,
    force_browser: bool = False
) -> Tuple[Optional[Dict], str]:
    """
    Find available reservations with automatic browser fallback.
    
    This is a drop-in replacement for calendar_scanner.find_resy_reservations()
    that automatically falls back to browser automation when the API fails.
    
    Args:
        venue_id: Resy venue ID
        day: Date in YYYY-MM-DD format
        party_size: Number of guests
        venue_name: Human-readable restaurant name
        lat: Latitude (optional, for API)
        long: Longitude (optional, for API)
        force_browser: Force browser automation (skip API)
        
    Returns:
        Tuple of (result_dict, status)
        - result_dict: API-compatible response or None
        - status: 'success', 'api_error', 'no_availability', 'browser_fallback', 'error'
    """
    # Get venue slug from restaurants file
    venue_slug = None
    restaurants = load_restaurants()
    
    for r in restaurants:
        if str(r.get('venue_id')) == str(venue_id):
            venue_slug = r.get('url_slug')
            if not venue_name:
                venue_name = r.get('name', '')
            break
    
    if not venue_slug:
        logger.warning(f"No venue slug found for venue_id {venue_id}")
        venue_slug = venue_name.lower().replace(' ', '-') if venue_name else str(venue_id)
    
    # Use the browser automation fallback
    return check_availability_with_fallback(
        venue_id=venue_id,
        venue_slug=venue_slug,
        venue_name=venue_name,
        date=day,
        party_size=party_size
    )


def book_reservation_with_browser_fallback(
    venue_id: str,
    venue_slug: str,
    venue_name: str,
    date: str,
    time_slot: str,
    party_size: int = 2,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Book a reservation using browser automation.
    
    Args:
        venue_id: Resy venue ID
        venue_slug: Restaurant URL slug
        venue_name: Human-readable restaurant name
        date: Date in YYYY-MM-DD format
        time_slot: Time to book (e.g., "7:00 PM")
        party_size: Number of guests
        dry_run: Don't actually book (for testing)
        
    Returns:
        Dict with booking result
    """
    result = book_with_browser_fallback(
        venue_id=venue_id,
        venue_slug=venue_slug,
        venue_name=venue_name,
        date=date,
        time_slot=time_slot,
        party_size=party_size,
        headless=True,
        dry_run=dry_run
    )
    
    return {
        'success': result.success,
        'status': result.status.value,
        'reservation_id': result.reservation_id,
        'confirmation_code': result.confirmation_code,
        'error_message': result.error_message,
        'details': result.details
    }


def scan_and_book_with_browser_fallback(
    dates: List[str],
    party_size: int = 2,
    preferred_start_hour: int = 19,
    preferred_end_hour: int = 21,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Scan multiple dates and book the best available reservations.
    
    This is a high-level function that:
    1. Checks for existing reservations
    2. For each date without a reservation, tries to book one
    3. Follows priority order for restaurants
    4. Prefers times in the 7-9 PM window
    
    Args:
        dates: List of dates to book (YYYY-MM-DD format)
        party_size: Number of guests
        preferred_start_hour: Start of preferred time window
        preferred_end_hour: End of preferred time window
        dry_run: Don't actually book (for testing)
        
    Returns:
        List of booking results
    """
    results = []
    restaurants = load_restaurants()
    existing_reservations = load_reservations()
    
    logger.info(f"Scanning {len(dates)} dates for reservations...")
    logger.info(f"Party size: {party_size}")
    logger.info(f"Preferred time window: {preferred_start_hour}:00 - {preferred_end_hour}:00")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    for date in dates:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing date: {date}")
        
        # Check if we already have a reservation
        existing = has_existing_reservation(date, existing_reservations)
        if existing:
            logger.info(f"✅ Already have reservation at {existing.get('venue_name', 'Unknown')}")
            results.append({
                'date': date,
                'status': 'skipped',
                'reason': 'existing_reservation',
                'existing': existing
            })
            continue
        
        # Try to find and book
        logger.info(f"🔍 Looking for availability...")
        
        booking_result = find_and_book_best_slot(
            restaurants=restaurants,
            date=date,
            party_size=party_size,
            preferred_start_hour=preferred_start_hour,
            preferred_end_hour=preferred_end_hour,
            headless=True,
            dry_run=dry_run
        )
        
        if booking_result:
            result_data = {
                'date': date,
                'status': 'booked',
                'venue_name': booking_result.details.get('venue', 'Unknown'),
                'time': booking_result.details.get('time', 'Unknown'),
                'reservation_id': booking_result.reservation_id,
                'confirmation_code': booking_result.confirmation_code
            }
            logger.info(f"✅ Booked: {result_data['venue_name']} at {result_data['time']}")
            results.append(result_data)
        else:
            logger.info(f"❌ No availability for {date}")
            results.append({
                'date': date,
                'status': 'no_availability'
            })
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Scan complete. Results: {len([r for r in results if r['status'] == 'booked'])} booked, "
                f"{len([r for r in results if r['status'] == 'no_availability'])} no availability, "
                f"{len([r for r in results if r['status'] == 'skipped'])} skipped")
    
    return results


# Integration helper for calendar_scanner.py
def patch_calendar_scanner():
    """
    Monkey-patch calendar_scanner to use browser fallback.
    
    Usage in calendar_scanner.py:
        from browser_fallback_integration import patch_calendar_scanner
        patch_calendar_scanner()
    """
    try:
        import calendar_scanner
        
        # Store original function
        calendar_scanner._original_find_resy_reservations = calendar_scanner.find_resy_reservations
        
        # Replace with fallback version
        calendar_scanner.find_resy_reservations = find_resy_reservations_with_browser_fallback
        
        logger.info("✅ Patched calendar_scanner with browser fallback")
        
    except Exception as e:
        logger.error(f"Failed to patch calendar_scanner: {e}")


if __name__ == "__main__":
    # Test the integration
    import sys
    
    print("=" * 70)
    print("Browser Fallback Integration - Test Mode")
    print("=" * 70)
    
    test_type = sys.argv[1] if len(sys.argv) > 1 else "scan"
    
    if test_type == "fallback":
        # Test the fallback function
        venue_id = sys.argv[2] if len(sys.argv) > 2 else "58528"
        date = sys.argv[3] if len(sys.argv) > 3 else "2026-05-17"
        
        print(f"\n🧪 Testing fallback for venue {venue_id} on {date}")
        
        result, status = find_resy_reservations_with_browser_fallback(
            venue_id=venue_id,
            day=date,
            party_size=2
        )
        
        print(f"\n📊 Result:")
        print(f"   Status: {status}")
        if result:
            print(f"   Has data: Yes")
            venues = result.get('results', {}).get('venues', [])
            if venues:
                slots = venues[0].get('slots', [])
                print(f"   Slots found: {len(slots)}")
                for slot in slots[:5]:  # Show first 5
                    time = slot.get('date', {}).get('start', 'Unknown')
                    print(f"      - {time}")
        else:
            print(f"   Has data: No")
    
    elif test_type == "scan":
        # Test multi-date scan
        dates = sys.argv[2:] if len(sys.argv) > 2 else ["2026-05-17", "2026-05-18"]
        dry_run = '--dry-run' in sys.argv
        
        print(f"\n🧪 Testing multi-date scan for: {', '.join(dates)}")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        
        results = scan_and_book_with_browser_fallback(
            dates=dates,
            party_size=2,
            dry_run=dry_run
        )
        
        print(f"\n📊 Results:")
        for result in results:
            status = result['status']
            date = result['date']
            
            if status == 'booked':
                print(f"   ✅ {date}: {result['venue_name']} at {result['time']}")
            elif status == 'skipped':
                print(f"   ⏭️  {date}: Skipped (existing reservation)")
            else:
                print(f"   ❌ {date}: No availability")
    
    else:
        print("\nUsage:")
        print("  python browser_fallback_integration.py fallback [venue_id] [date]")
        print("  python browser_fallback_integration.py scan [date1] [date2] ... [--dry-run]")
