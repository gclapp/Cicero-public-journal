# Resy Automation System - Quick Start

## What You Just Got

A complete automated restaurant reservation system that:
1. ✅ Scans your calendar for NYC trips
2. ✅ Manages a priority list of restaurants via web interface
3. ✅ Automatically books reservations after 5pm
4. ✅ Tracks what was booked and rotates priorities

## Files Created

```
resy-system/
├── app.py                 # Web application
├── calendar_scanner.py    # Auto-booking script
├── start.sh              # Start web interface
├── run_scanner.sh        # Run calendar scanner
├── setup.sh              # Setup script
├── data/
│   ├── restaurants.json  # Your restaurant list
│   ├── users.json        # User accounts
│   └── reservations.json # Booking history
└── templates/            # HTML templates
```

## Start Using It

### 1. Start the Web Interface

```bash
cd /home/ubuntu/.openclaw/workspace/resy-system
./start.sh
```

Then open: **http://localhost:5000**

Login with:
- Email: `[REDACTED]`
- Password: `changeme123`

### 2. View Your Trips

Click **Trips** in the navigation to see:
- Upcoming NYC trips from your calendar
- Reservation status for each night
- Progress toward fully booked trips

### 3. Add Your NYC Restaurants

1. Click "+ Add Restaurant"
2. Enter:
   - **Name**: Restaurant name
   - **Venue ID**: Resy venue ID (from resy.com URL)
   - **City**: NYC
   - **Cuisine**: Optional
   - **Notes**: Optional

3. Drag to reorder (top = highest priority)

### 3. Run the Scanner

```bash
./run_scanner.sh
```

This will:
- Check your calendar for NYC trips
- Find nights without reservations
- Try to book from your priority list
- Only book times after 5pm

### 4. 12-Hour Automated Scanning (Already Set Up!)

✅ **Cron job already installed** - scans every 12 hours at 00:00 and 12:00 UTC

Check status:
```bash
./status.sh
```

View recent scans:
```bash
tail -f logs/cron-scan.log
```

The scanner will:
- Check for new NYC trips every 12 hours
- Only book nights without existing reservations
- Try restaurants in priority order
- Book times after 5pm local time
- Rotate booked restaurants to bottom of list
- Update the Trips page with booking status

**Manual scan** (if needed):
```bash
./run_scanner.sh
```

## Finding Resy Venue IDs

### Method 1: From Resy Website
1. Go to resy.com
2. Find a restaurant
3. URL looks like: `resy.com/cities/new-york-ny/venues/12345-name`
4. Venue ID = `12345`

### Method 2: Search via API
```bash
python3 ../scripts/resy_search.py --lat 40.7128 --long -74.0060 --date 2026-04-15
```

## User Management

As admin, go to **Users** tab to:
- Add new users
- Delete users
- Grant admin privileges

## How Booking Works

1. Scanner finds NYC trip dates
2. Checks each night for existing reservations
3. For missing nights:
   - Starts with #1 priority restaurant
   - Looks for availability after 5pm
   - Books first available slot
   - Moves restaurant to bottom of list
4. Saves confirmation to history

## Security

- ✅ Passwords SHA-256 hashed
- ✅ Session-based auth
- ✅ File permissions 600
- ✅ Credentials stored securely

## Need Help?

- Check `README.md` for detailed docs
- View logs in `logs/` directory
- Test Resy API: `python3 ../scripts/resy_search.py`

## Next Steps

1. [ ] Add 5-10 NYC restaurants to your list
2. [ ] Reorder by priority
3. [ ] Run scanner to test
4. [ ] Set up cron for automation
5. [ ] Change default password

---

**🎉 You're all set! The system is ready to automatically book your NYC dinners.**
