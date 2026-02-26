# OpenTable Skill for OpenClaw

**Author:** Geoffrey Clapp (@gclapp)  
**Version:** 1.0.0  
**License:** MIT (see LICENSE section below)

A comprehensive OpenClaw skill for restaurant discovery, reservations, and sharing via the OpenTable platform.

---

## Features

- 🔍 **Search restaurants** by location, cuisine, price, time, and availability
- 📍 **Find nearby restaurants** using IP-based geolocation or coordinates
- 📅 **Check availability** for specific dates and party sizes
- ✓ **Make reservations** with confirmation numbers
- ✗ **Cancel reservations** when plans change
- 📋 **View reservations** (upcoming or complete history)
- 📤 **Share reservations** via OpenTable, WhatsApp, SMS, or Email

---

## Installation

### Prerequisites
- OpenClaw installed and configured
- Python 3.8+
- OpenTable API credentials

### Install the Skill

```bash
# Via ClawHub (once published)
clawhub install opentable

# Or manually
cd ~/.openclaw/workspace/skills
# Extract opentable.skill to this directory
```

### Configure API Credentials

Create the config file:

```bash
mkdir -p ~/.openclaw/config
cat > ~/.openclaw/config/opentable.json << 'EOF'
{
  "api_key": "your_opentable_api_key_here"
}
EOF
```

Or use environment variables:

```bash
export OPENTABLE_API_KEY=your_opentable_api_key_here
```

---

## Use Cases & Examples

### 1. Search for Restaurants by Time, Location, Price, and Cuisine

Find Italian restaurants in Portland, $$ price range, available tonight at 7pm for 4 people:

```bash
python3 scripts/search_restaurants.py \
  --city "Portland" \
  --cuisine "Italian" \
  --price 2 \
  --date 2026-02-27 \
  --time 19:00 \
  --party-size 4 \
  --available-only
```

**Parameters:**
- `--city` - City name (e.g., "Portland")
- `--cuisine` - Cuisine type (e.g., "Italian", "Japanese", "Mexican")
- `--price` - Price level 1-4 ($ to $$$$)
- `--date` - Date in YYYY-MM-DD format
- `--time` - Time in HH:MM (24-hour format)
- `--party-size` - Number of guests
- `--available-only` - Only show restaurants with availability
- `--name` - Search by restaurant name
- `--lat` / `--lng` - Search by coordinates
- `--radius` - Search radius in meters (default: 5000)

---

### 2. Cancel an Existing Reservation

Cancel a reservation using the confirmation number:

```bash
python3 scripts/cancel_reservation.py \
  --confirmation-number OT12345678 \
  --email john@example.com \
  --reason "Change of plans"
```

**Parameters:**
- `--confirmation-number` (required) - The OpenTable confirmation number
- `--email` (required) - Email address used for the booking
- `--reason` (optional) - Cancellation reason

**Response includes:**
- Cancellation confirmation
- Refund eligibility information
- Cancellation policy details

---

### 3. See All Reservations

View upcoming reservations (default):

```bash
python3 scripts/list_reservations.py \
  --email john@example.com
```

View all reservations including past history:

```bash
python3 scripts/list_reservations.py \
  --email john@example.com \
  --all
```

Look up a specific reservation:

```bash
python3 scripts/list_reservations.py \
  --confirmation-number OT12345678
```

**Parameters:**
- `--email` - Filter by diner email address
- `--confirmation-number` - Look up specific reservation
- `--all` - Show all reservations (not just upcoming)

---

### 4. Find Restaurants Near Me

Find restaurants using automatic IP-based location detection:

```bash
python3 scripts/find_nearby.py \
  --use-ip-location \
  --cuisine "Sushi" \
  --radius 3000 \
  --available-only
```

Find restaurants using specific coordinates:

```bash
python3 scripts/find_nearby.py \
  --lat 45.5231 \
  --lng -122.6765 \
  --radius 5000 \
  --price 3 \
  --party-size 2
```

**Parameters:**
- `--use-ip-location` - Auto-detect location from IP address
- `--lat` / `--lng` - Specific coordinates
- `--radius` - Search radius in meters (default: 5000)
- `--cuisine` - Filter by cuisine type
- `--price` - Filter by price level (1-4)
- `--date` / `--time` / `--party-size` - Check availability
- `--available-only` - Only show available restaurants

---

### 5. Share a Reservation

Share via OpenTable (native share link):

```bash
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel opentable
```

Share via WhatsApp:

```bash
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel whatsapp \
  --to "+12065551234"
```

Share via SMS:

```bash
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel sms \
  --to "+12065551234"
```

Share via Email:

```bash
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel email \
  --to "friend@example.com" \
  --message "Looking forward to dinner with you!"
```

Copy to clipboard (outputs shareable text):

```bash
python3 scripts/share_reservation.py \
  --confirmation-number OT12345678 \
  --channel copy
```

**Parameters:**
- `--confirmation-number` (required) - Reservation confirmation number
- `--channel` (required) - Sharing method: `opentable`, `whatsapp`, `sms`, `email`, or `copy`
- `--to` (required for whatsapp/sms/email) - Recipient contact
- `--message` (optional) - Custom message to include

---

## Additional Commands

### Check Availability

Check available times at a specific restaurant:

```bash
python3 scripts/check_availability.py \
  --restaurant-id 12345 \
  --date 2026-02-27 \
  --time 19:00 \
  --party-size 4
```

### Make a Reservation

Book a table at a restaurant:

```bash
python3 scripts/make_reservation.py \
  --restaurant-id 12345 \
  --date 2026-02-27 \
  --time 19:00 \
  --party-size 4 \
  --first-name "John" \
  --last-name "Doe" \
  --email "john@example.com" \
  --phone "503-555-0123" \
  --special-requests "Anniversary dinner - window seat if possible"
```

### Get Restaurant Details

Get comprehensive information about a restaurant:

```bash
python3 scripts/get_restaurant.py --id 12345
```

Returns: name, address, phone, cuisine, price, rating, hours, dress code, photos, etc.

---

## Output Format

All scripts return JSON output with the following structure:

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message description"
}
```

---

## Change History

### Version 1.0.0 (2026-02-26)
- Initial release
- Restaurant search by city, cuisine, price, date, time
- Nearby restaurant discovery with IP geolocation
- Reservation creation and cancellation
- Reservation listing (upcoming and all history)
- Multi-channel reservation sharing (OpenTable, WhatsApp, SMS, Email)
- Availability checking
- Restaurant details retrieval

---

## License

```
MIT License

Copyright (c) 2026 Geoffrey Clapp (@gclapp)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Contributing

This skill was created for personal use by Geoffrey Clapp but is freely available for anyone to use, modify, and distribute under the MIT License.

If you find bugs or have suggestions, feel free to reach out or fork the project.

---

## Author

**Geoffrey Clapp**  
- GitHub: [@gclapp](https://github.com/gclapp)
- Location: Los Angeles / San Francisco
- Created: February 2026

Built with ❤️ for the OpenClaw community.
