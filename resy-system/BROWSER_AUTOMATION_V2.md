# Resy Browser Automation V2

A bulletproof browser automation system for Resy restaurant reservations. This is the **critical fallback system** when the Resy API returns 500 errors or empty results.

## Overview

When Resy's `/4/find` and `/3/find` API endpoints fail, this browser automation system takes over to:
- Check restaurant availability through the web interface
- Book reservations automatically when slots are found
- Handle all edge cases: CAPTCHAs, session timeouts, rate limits

## Features

### 🔒 Bulletproof Reliability
- **Circuit Breaker Pattern**: Temporarily disables venues with repeated failures to avoid hammering
- **Automatic Session Refresh**: Detects and refreshes expired sessions
- **Exponential Backoff**: Retries with increasing delays when rate limited
- **Graceful Degradation**: Continues to next restaurant if one fails

### 🥷 Stealth & Anti-Detection
- Playwright with stealth plugins
- Realistic viewport and user agent
- Human-like delays between actions
- Anti-automation detection bypass

### 📊 Comprehensive Observability
- Detailed logging to file and console
- Screenshot capture on errors
- Structured result objects
- Status tracking for all operations

### 🔄 Integration Ready
- Drop-in replacement for API calls
- Compatible with existing calendar_scanner.py
- Returns data in API-compatible format
- Supports both headless and headed modes

## Installation

### Prerequisites
```bash
# Install playwright
pip install playwright
playwright install chromium

# Optional: Install stealth plugin for extra protection
pip install playwright-stealth
```

### Credentials
Ensure your Resy credentials are stored in:
```bash
~/.openclaw/config/resy-credentials.json
```

Format:
```json
{
  "api_key": "your_api_key",
  "auth_token": "your_auth_token",
  "email": "optional@email.com",
  "password": "optional_password"
}
```

## Usage

### Command Line Testing

#### Test Login
```bash
python browser_automation_v2.py login
```

#### Check Availability
```bash
# Check The Naked Pig for May 17, 2026
python browser_automation_v2.py check the-naked-pig 2026-05-17

# Show browser window (headed mode)
python browser_automation_v2.py check the-naked-pig 2026-05-17 --headed
```

#### Test Booking (Dry Run)
```bash
# Test booking flow without actually booking
python browser_automation_v2.py book the-naked-pig 2026-05-17 "7:00 PM" --dry-run
```

#### Multi-Restaurant Booking
```bash
# Try to book best available slot across all restaurants
python browser_automation_v2.py multi 2026-05-17 --dry-run
```

### Python API

#### Basic Availability Check
```python
from browser_automation_v2 import ResyBrowserAutomationV2

with ResyBrowserAutomationV2(headless=True) as browser:
    # Login
    browser.login()
    
    # Check availability
    result = browser.check_availability(
        venue_id="58528",
        venue_slug="the-naked-pig",
        venue_name="The Naked Pig",
        date="2026-05-17",
        party_size=2
    )
    
    if result.status.value == "success":
        for slot in result.slots:
            print(f"Available: {slot.time}")
```

#### Book a Reservation
```python
from browser_automation_v2 import book_with_browser_fallback

result = book_with_browser_fallback(
    venue_id="58528",
    venue_slug="the-naked-pig",
    venue_name="The Naked Pig",
    date="2026-05-17",
    time_slot="7:00 PM",
    party_size=2,
    dry_run=True  # Set to False for actual booking
)

if result.success:
    print(f"Booked! Confirmation: {result.confirmation_code}")
else:
    print(f"Failed: {result.error_message}")
```

#### Priority-Based Multi-Restaurant Booking
```python
from browser_automation_v2 import find_and_book_best_slot

restaurants = [
    {"venue_id": "1501", "url_slug": "4-charles-prime-rib", "name": "4 Charles Prime Rib"},
    {"venue_id": "1478", "url_slug": "carbone", "name": "Carbone"},
    # ... more restaurants
]

result = find_and_book_best_slot(
    restaurants=restaurants,
    date="2026-05-17",
    party_size=2,
    preferred_start_hour=19,  # 7 PM
    preferred_end_hour=21,    # 9 PM
    dry_run=True
)

if result:
    print(f"Booked at {result.details['venue']}!")
```

### Integration with calendar_scanner.py

The browser automation can be used as a drop-in replacement for API calls:

```python
from browser_fallback_integration import (
    find_resy_reservations_with_browser_fallback,
    scan_and_book_with_browser_fallback
)

# Replace API call with automatic fallback
result, status = find_resy_reservations_with_browser_fallback(
    venue_id="58528",
    day="2026-05-17",
    party_size=2,
    venue_name="The Naked Pig"
)

# Or use the high-level scan function
results = scan_and_book_with_browser_fallback(
    dates=["2026-05-17", "2026-05-18"],
    party_size=2,
    dry_run=True
)
```

To patch calendar_scanner.py automatically:
```python
from browser_fallback_integration import patch_calendar_scanner
patch_calendar_scanner()
```

## Restaurant Priority Order

The system follows this priority when booking:

1. **4 Charles Prime Rib** (4-charles-prime-rib)
2. **Carbone** (carbone)
3. **Torrisi** (torrisi)
4. **Saga** (saga)
5. **The Naked Pig** (the-naked-pig)
6. Other restaurants (no specific priority)

## Configuration

### Constructor Options

```python
ResyBrowserAutomationV2(
    headless=True,           # Run without browser window
    dry_run=False,           # Don't actually book (for testing)
    max_retries=3,           # Number of retries on failure
    request_delay=(2.0, 5.0), # Random delay range between actions (seconds)
    screenshot_on_error=True # Capture screenshots on errors
)
```

### Circuit Breaker Settings

The circuit breaker automatically:
- Opens after 5 failures for a venue
- Resets after 30 minutes
- Prevents hammering problematic venues

## Error Handling

### Status Codes

| Status | Description |
|--------|-------------|
| `success` | Operation completed successfully |
| `no_availability` | No tables available for the requested date/time |
| `login_failed` | Could not authenticate with Resy |
| `captcha_detected` | CAPTCHA requires manual intervention |
| `rate_limited` | Too many requests, backed off |
| `session_expired` | Session expired and couldn't refresh |
| `error` | General error occurred |
| `dry_run` | Test mode, no actual booking made |

### Screenshots

When errors occur, screenshots are saved to:
```
logs/screenshots/{error_type}_{venue_slug}_{timestamp}.png
```

### Logs

Detailed logs are written to:
```
logs/browser_automation_v2.log
```

## Limitations

1. **CAPTCHA**: If CAPTCHA appears, the system will pause and require manual intervention
2. **Speed**: Browser automation is slower than API calls (~10-30 seconds per check)
3. **Rate Limiting**: Aggressive checking may trigger rate limits
4. **Session Lifetime**: Sessions expire after ~30 minutes of inactivity

## Testing

### Run All Tests
```bash
# Test login
python browser_automation_v2.py login --headed

# Test availability check
python browser_automation_v2.py check the-naked-pig 2026-05-17 --headed

# Test booking (dry run)
python browser_automation_v2.py book the-naked-pig 2026-05-17 "7:00 PM" --dry-run --headed

# Test multi-restaurant
python browser_automation_v2.py multi 2026-05-17 --dry-run --headed
```

### Integration Tests
```bash
# Test fallback integration
python browser_fallback_integration.py fallback 58528 2026-05-17

# Test multi-date scan
python browser_fallback_integration.py scan 2026-05-17 2026-05-18 --dry-run
```

## Troubleshooting

### Login Issues
- Verify credentials in `~/.openclaw/config/resy-credentials.json`
- Try headed mode (`--headed`) to see what's happening
- Check if auth token is expired (may need to re-authenticate)

### No Slots Found
- Restaurant may genuinely have no availability
- Try different dates or party sizes
- Check if restaurant is closed on that date

### Rate Limiting
- The system will automatically back off
- Wait 10-15 minutes between aggressive checks
- Circuit breaker will temporarily disable problematic venues

### CAPTCHA
- The system will detect and pause
- Run in headed mode to manually solve
- Consider using a residential proxy for production

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Calendar Scanner                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              find_resy_reservations_with_fallback           │
│  1. Try API first                                           │
│  2. If API fails → Browser Automation                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ResyBrowserAutomationV2                        │
│  - Login (token injection or credentials)                   │
│  - Check availability (with retries)                        │
│  - Book reservation (with confirmation)                     │
│  - Circuit breaker for reliability                          │
└─────────────────────────────────────────────────────────────┘
```

## Future Enhancements

- [ ] SMS/Email notifications on CAPTCHA detection
- [ ] Proxy rotation for distributed checking
- [ ] Machine learning for optimal booking times
- [ ] Integration with SMS-based 2FA handling

## Support

For issues or questions:
1. Check logs in `logs/browser_automation_v2.log`
2. Review screenshots in `logs/screenshots/`
3. Run with `--headed` flag to see browser behavior
4. Verify credentials are valid
