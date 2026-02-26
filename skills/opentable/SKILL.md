---
name: opentable
description: Restaurant discovery, reservations, and sharing via OpenTable API. Use when the user wants to find restaurants (by location, cuisine, price, time), check availability, make or cancel reservations, view upcoming reservations, find nearby restaurants, or share reservations with others. Triggers on dining-related requests like "find restaurants", "book a table", "cancel reservation", "see my reservations", "restaurants near me", or "share my reservation".
---

# OpenTable

Restaurant discovery, reservations, and sharing through OpenTable.

## Capabilities

- **Search restaurants** by city, cuisine, price, time, and availability
- **Find nearby restaurants** using geolocation
- **Check availability** for specific dates/times
- **Make reservations** at supported restaurants
- **Cancel reservations** with confirmation numbers
- **View reservations** (upcoming or all history)
- **Share reservations** via OpenTable, WhatsApp, SMS, or Email

## Quick Start

```python
# Search for Italian restaurants in Portland, $$ price, available tonight
python3 scripts/search_restaurants.py --city "Portland" --cuisine "Italian" --price 2 --date 2026-02-27 --party-size 4 --available-only

# Find restaurants near you (auto-detect location)
python3 scripts/find_nearby.py --use-ip-location --cuisine "Japanese" --radius 3000

# Check availability at a specific restaurant
python3 scripts/check_availability.py --restaurant-id 12345 --date 2026-02-27 --time 19:00 --party-size 4

# Make a reservation
python3 scripts/make_reservation.py --restaurant-id 12345 --date 2026-02-27 --time 19:00 --party-size 4 --first-name "John" --last-name "Doe" --email "john@example.com" --phone "503-555-0123"

# See upcoming reservations
python3 scripts/list_reservations.py --email john@example.com

# Cancel a reservation
python3 scripts/cancel_reservation.py --confirmation-number OT12345678 --email john@example.com

# Share a reservation via WhatsApp
python3 scripts/share_reservation.py --confirmation-number OT12345678 --channel whatsapp --to +12065551234

# Share via email
python3 scripts/share_reservation.py --confirmation-number OT12345678 --channel email --to friend@example.com

# Get restaurant details
python3 scripts/get_restaurant.py --id 12345
```

## Authentication

Requires OpenTable API credentials. Configure in one of two ways:

1. **Config file** (preferred): `~/.openclaw/config/opentable.json`
   ```json
   {
     "api_key": "your_api_key",
     "api_secret": "your_api_secret"
   }
   ```

2. **Environment variables**:
   - `OPENTABLE_API_KEY`
   - `OPENTABLE_API_SECRET`

## Scripts

### Restaurant Discovery
- `search_restaurants.py` - Search by city, cuisine, price, time
- `find_nearby.py` - Find restaurants near current location (IP-based or coordinates)
- `get_restaurant.py` - Get detailed restaurant info

### Reservations
- `check_availability.py` - Check table availability
- `make_reservation.py` - Book a table
- `cancel_reservation.py` - Cancel existing reservation
- `list_reservations.py` - View upcoming or all reservations

### Sharing
- `share_reservation.py` - Share via OpenTable, WhatsApp, SMS, Email, or copy

## Common Use Cases

### Find a restaurant for tonight
```bash
python3 scripts/search_restaurants.py \
  --city "Portland" \
  --cuisine "Italian" \
  --price 2 \
  --date $(date +%Y-%m-%d) \
  --time 19:00 \
  --party-size 4 \
  --available-only
```

### Find restaurants near me right now
```bash
python3 scripts/find_nearby.py \
  --use-ip-location \
  --radius 5000 \
  --cuisine "Sushi" \
  --available-only
```

### Share reservation with dinner guests
```bash
# Via WhatsApp
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel whatsapp \
  --to "+12065551234"

# Via Email
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel email \
  --to "friend@example.com" \
  --message "Looking forward to dinner!"
```

## Error Handling

All scripts return JSON with:
- `success` (boolean)
- `data` or `error` fields

Common errors:
- Missing API credentials
- Restaurant not found
- No availability for requested time
- Reservation not found (wrong confirmation number)
- Cancellation deadline passed

## API Reference

See [references/api_reference.md](references/api_reference.md) for complete endpoint documentation.
