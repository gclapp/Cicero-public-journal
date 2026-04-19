#!/usr/bin/env python3
"""
Example Usage of the Working Resy API Client

This demonstrates the complete flow for checking availability
using the correct /4/find endpoint.
"""

from working_resy_client import ResyClient

# Your Resy auth token (get from browser DevTools)
# Leave as None for limited access (some restaurants may not show availability)
AUTH_TOKEN = None  # Replace with your token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9..."

# Initialize client
client = ResyClient(auth_token=AUTH_TOKEN)

# Example 1: Check availability (the working way)
print("=" * 60)
print("Example 1: Check Availability")
print("=" * 60)

venue_id = 58528  # Your venue ID
date = "2026-05-17"
party_size = 2

print(f"\nChecking venue {venue_id} for {date}, party of {party_size}...")

try:
    slots = client.check_availability(
        venue_id=venue_id,
        day=date,
        party_size=party_size,
        lat=40.7596,  # NYC coordinates (can be 0)
        long=-73.9685
    )
    
    print(f"\n✅ Found {len(slots)} available slot(s):\n")
    
    for slot in slots:
        print(f"  Time: {slot['date']}")
        print(f"  Table Type: {slot['table_type']}")
        print(f"  Token: {slot['token'][:50]}...")
        print()

except Exception as e:
    print(f"❌ Error: {e}")


# Example 2: Search for restaurants
print("\n" + "=" * 60)
print("Example 2: Search Restaurants")
print("=" * 60)

try:
    venues = client.search_restaurants("carbone")
    print(f"\nFound {len(venues)} restaurant(s):\n")
    
    for venue in venues[:3]:  # Show first 3
        venue_id = venue.get("id", {}).get("resy")
        name = venue.get("name")
        print(f"  {name} (ID: {venue_id})")

except Exception as e:
    print(f"❌ Error: {e}")


# Example 3: Get calendar
print("\n" + "=" * 60)
print("Example 3: Get Venue Calendar")
print("=" * 60)

try:
    calendar = client.get_venue_calendar(
        venue_id=venue_id,
        start_date="2026-05-17",
        end_date="2026-05-23",
        party_size=2
    )
    
    print(f"\nCalendar for venue {venue_id}:\n")
    
    for day in calendar:
        date = day.get("date")
        status = day.get("inventory", {}).get("reservation", "unknown")
        print(f"  {date}: {status}")

except Exception as e:
    print(f"❌ Error: {e}")


# Summary
print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("""
Key takeaways:
1. Use /4/find endpoint (not /3/find)
2. Include lat/long parameters (can be 0)
3. Use both X-Resy-Auth-Token and X-Resy-Universal-Auth headers
4. Response structure: results.venues[].slots

The /3/find endpoint returns empty results because it's deprecated.
The /4/find endpoint is what the Resy website currently uses.
""")
