# Resy Automation System

Automated restaurant reservation system for NYC trips.

## Features

1. **Calendar Integration** - Automatically scans your Google Calendar for NYC trips
2. **Trip Dashboard** - Visual overview of upcoming trips and reservation status
3. **Restaurant List Management** - Web interface to manage your preferred restaurants
4. **Auto-Booking** - Automatically books reservations at available restaurants
5. **Priority System** - Restaurants are booked in priority order (top of list = highest priority)
6. **User Management** - Multi-user support with admin controls

## Components

| Component | Purpose |
|-----------|---------|
| `app.py` | Flask web application for restaurant/user management |
| `calendar_scanner.py` | Scans calendar and auto-books reservations |
| `trips.py` | Trip detection and management |
| `monitoring.py` | System health tracking and logging |
| `data/restaurants.json` | Your restaurant list |
| `data/users.json` | User accounts |
| `data/reservations.json` | Reservation history |
| `data/trips_cache.json` | Cached trip data |
| `data/monitoring.json` | System health and activity logs |

## Quick Start

```bash
# 1. Setup (one-time)
cd /home/ubuntu/.openclaw/workspace/resy-system
./setup.sh

# 2. Start the web interface
./start.sh

# 3. Open browser to http://localhost:5000
#    Login: [REDACTED] / changeme123

# 4. Add restaurants via web UI

# 5. Scanner runs automatically every 12 hours!
#    (cron job already installed)
```

Then open http://localhost:5000 in your browser.

**Default Login:**
- Email: `[REDACTED]`
- Password: `changeme123`

## Usage

### 1. Add Restaurants

1. Login to the web interface
2. Click "+ Add Restaurant"
3. Enter:
   - Restaurant Name
   - Resy Venue ID (find this in Resy URL or API)
   - City (NYC, LA, SF, etc.)
   - Cuisine type (optional)
   - Notes (optional)

### 2. View Your Trips

Click **Trips** in the navigation to see:
- Upcoming NYC trips detected from your calendar
- Which nights have reservations ✅
- Which nights still need booking ⏳
- Progress bars showing booking status
- Trip statistics (total trips, nights, booked, pending)

### 3. Prioritize Your List

- Drag and drop restaurants to reorder
- Restaurants at the top have higher priority
- When a restaurant is booked, it automatically moves to the bottom

### 4. Monitor System Health (Admin)

Visit **Monitoring** page to see:
- **System Status**: Healthy / Degraded / Critical
- **Last Scan**: Time since last calendar scan
- **Last Booking**: Time since successful reservation
- **Recent Errors**: Any issues from scanner or web UI
- **Scan History**: Detailed log of all scans
- **Booking History**: All reservations made
- **Log Files**: View system logs

### 5. Automated Scanning (Already Running!)

✅ **Cron job installed** - scans automatically every 12 hours

**Schedule:** 00:00 and 12:00 UTC daily

Check status:
```bash
./status.sh
```

View recent scans:
```bash
tail -f logs/cron-scan.log
```

Manual scan (if needed):
```bash
./run_scanner.sh
```

The scanner will:
- Find NYC trips in your calendar
- Check each night for missing reservations
- Try to book from your priority list
- Only book times after 5pm local time
- Avoid duplicate scans within 6 hours
- Log all activity to the monitoring dashboard

## Finding Resy Venue IDs

1. Go to resy.com and find a restaurant
2. Look at the URL: `https://resy.com/cities/new-york-ny/venues/12345-restaurant-name`
3. The venue ID is `12345`

Or use the API search:

```bash
python3 ../scripts/resy_search.py --lat 40.7128 --long -74.0060 --date 2026-04-15
```

## User Management

As an admin, you can:
- Add/remove users
- Grant admin privileges
- All users can manage the restaurant list

## How It Works

1. **Scanner runs** (manually or via cron)
2. **Calendar checked** for NYC events
3. **Trip dates extracted** from consecutive NYC events
4. **Each night checked** for existing reservations
5. **Missing nights** trigger booking attempts
6. **Priority list** is traversed top-to-bottom
7. **First available** slot after 5pm is booked
8. **Confirmation** saved to reservation history
9. **Restaurant** moved to bottom of priority list

## Security

- Passwords are SHA-256 hashed
- Session-based authentication
- File permissions set to 600 for sensitive data
- No passwords stored in plain text

## Troubleshooting

### Scanner can't find calendar events

Make sure calendar_reader.py has run recently:
```bash
python3 ../scripts/calendar_reader.py
```

### No restaurants showing

Add restaurants via the web interface first.

### Booking fails

- Check your Resy credentials are valid
- Ensure payment method is set up on Resy
- Some restaurants require deposits (not supported yet)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/restaurants` | GET | List all restaurants |
| `/api/restaurants` | POST | Add/remove/reorder |
| `/api/restaurants/nyc` | GET | Get NYC restaurants only |
| `/api/users` | GET | List users (admin only) |
| `/api/users` | POST | Add user (admin only) |
| `/api/users` | DELETE | Delete user (admin only) |
| `/api/reservations` | GET | List reservations |
| `/api/reservations` | POST | Add reservation |

## Future Enhancements

- [ ] SMS/email notifications when bookings made
- [ ] Support for deposits/pre-paid reservations
- [ ] Waitlist monitoring
- [ ] Multiple party sizes
- [ ] Preferred time ranges
- [ ] Blackout dates
- [ ] Restaurant ratings/reviews
