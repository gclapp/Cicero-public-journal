# Resy API Fix - Research Results

## Problem
The Resy API `/3/find` endpoint was returning empty results (`{"results": []}`) while the website showed available slots.

## Solution
**Use `/4/find` instead of `/3/find`**

The `/3/find` endpoint has been deprecated. The Resy website and modern integrations use `/4/find`.

## Quick Fix

### Before (Not Working)
```python
url = "https://api.resy.com/3/find"
params = {
    "venue_id": 58528,
    "day": "2026-05-17",
    "party_size": 2,
    "lat": 40.7596,
    "long": -73.9685
}
# Returns: {"results": []}
```

### After (Working)
```python
url = "https://api.resy.com/4/find"  # Changed from /3/find
params = {
    "venue_id": 58528,
    "day": "2026-05-17",
    "party_size": 2,
    "lat": 40.7596,
    "long": -73.9685
}
headers = {
    "Authorization": 'ResyAPI api_key="AIcdK2rLXG6TYwJseSbmrBAy3RP81ocd"',
    "X-Resy-Auth-Token": "YOUR_AUTH_TOKEN",
    "X-Resy-Universal-Auth": "YOUR_AUTH_TOKEN",  # Same as above
    "User-Agent": "Mozilla/5.0 ...",
    "Origin": "https://resy.com",
    "Referer": "https://resy.com/"
}
# Returns: {"results": {"venues": [{"slots": [...]}]}}
```

## Files in This Directory

| File | Description |
|------|-------------|
| `RESEARCH_FINDINGS.md` | Detailed research documentation |
| `test_resy_api.py` | Test script comparing /3/find vs /4/find |
| `working_resy_client.py` | Complete working API client |
| `example_usage.py` | Usage examples |

## Getting Your Auth Token

1. Open [resy.com](https://resy.com) in your browser
2. Log in to your account
3. Open DevTools (F12) → Network tab
4. Look for any request to `api.resy.com`
5. Copy the value from `X-Resy-Auth-Token` header
6. Use this value in your requests

## Testing

```bash
# Test the endpoints
python test_resy_api.py

# Use the working client
python working_resy_client.py check --venue-id 58528 --date 2026-05-17 --party-size 2

# Search restaurants
python working_resy_client.py search --query "carbone"

# Get calendar
python working_resy_client.py calendar --venue-id 58528 --start-date 2026-05-17 --end-date 2026-05-23
```

## Key Differences

| Aspect | /3/find (Old) | /4/find (Current) |
|--------|---------------|-------------------|
| Status | Deprecated | Active |
| Response | `{"results": []}` | `{"results": {"venues": [...]}}` |
| Auth headers | Optional | Required for full access |
| lat/long | Optional | Required (can be 0) |

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/4/find` | GET | Check availability ✅ |
| `/3/venuesearch/search` | POST | Search restaurants |
| `/3/details` | POST | Get booking details |
| `/3/book` | POST | Book reservation |
| `/4/venue/calendar` | GET | Multi-day availability |

## References

- [resy-sniper](https://github.com/karthikvetrivel/resy-sniper) - Go library using /4/find
- [Jon Luca's Blog](https://jonluca.substack.com/p/resy-api) - Reverse engineering writeup
