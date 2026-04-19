# Resy API Research Findings

## Problem Summary
The `/3/find` endpoint returns empty results (`{"results": []}`) while the Resy website shows available slots (7:00 PM, 6:30 PM, 7:30 PM).

## Root Cause
**The `/3/find` endpoint has been deprecated/superseded by `/4/find`.**

The Resy website and modern integrations use the `/4/find` endpoint, not `/3/find`. The older endpoint may still respond with HTTP 200 but returns empty results.

## Key Findings

### 1. Endpoint Version Mismatch
- **Old/Not Working:** `GET /3/find` - Returns empty results
- **Current/Working:** `GET /4/find` - Returns actual availability

### 2. Required Parameters for `/4/find`
| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `venue_id` | int | Yes | Restaurant ID |
| `day` | string | Yes | Date in `YYYY-MM-DD` format |
| `party_size` | int | Yes | Number of guests |
| `lat` | float | Yes | Use `0` if unknown |
| `long` | float | Yes | Use `0` if unknown |

### 3. Required Headers
```http
Authorization: ResyAPI api_key="YOUR_API_KEY"
X-Resy-Auth-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9...
X-Resy-Universal-Auth: eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9...
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
Origin: https://resy.com
Referer: https://resy.com/
```

### 4. API Key
The API key is public and embedded in Resy's website:
```
AIcdK2rLXG6TYwJseSbmrBAy3RP81ocd
```

### 5. Auth Token
- JWT token from browser's `X-Resy-Auth-Token` header
- Both `X-Resy-Auth-Token` and `X-Resy-Universal-Auth` must have the **same value**
- Expires after ~45 days

## Response Structure Difference

### `/3/find` Response (Empty)
```json
{"results": []}
```

### `/4/find` Response (With Data)
```json
{
  "results": {
    "venues": [
      {
        "venue": {
          "id": {"resy": 58528},
          "name": "Restaurant Name"
        },
        "slots": [
          {
            "date": {
              "start": "2026-05-17 18:30:00",
              "end": "2026-05-17 20:30:00"
            },
            "config": {
              "id": 1521664,
              "type": "Dining Room",
              "token": "rgs://resy/58528/1521664/2/2026-05-17/2026-05-17/18:30:00/2/Dining Room"
            }
          }
        ]
      }
    ]
  }
}
```

## Other Working Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/4/find` | GET | Check availability (CURRENT) |
| `/3/find` | GET | Check availability (DEPRECATED) |
| `/3/venuesearch/search` | POST | Search restaurants |
| `/3/details` | POST | Get booking details |
| `/3/book` | POST | Book reservation |
| `/4/venue/calendar` | GET | Multi-day availability |
| `/2/user` | GET | User profile |
| `/3/user/reservations` | GET | User reservations |

## Solution

**Use `/4/find` instead of `/3/find`** with the following changes:

1. Change endpoint URL from `/3/find` to `/4/find`
2. Keep `lat` and `long` parameters (can be `0`)
3. Use proper headers including `X-Resy-Universal-Auth`
4. Parse the nested response structure (`results.venues[].slots`)

## Working Example

See `test_resy_api.py` for a complete working implementation.

## References

1. [resy-sniper GitHub](https://github.com/karthikvetrivel/resy-sniper) - Go library with `/4/find` usage
2. [Jon Luca's Resy API Blog](https://jonluca.substack.com/p/resy-api) - Reverse engineering writeup
3. [resy-booking-bot](https://github.com/Alkaar/resy-booking-bot) - Popular booking bot using `/3/find` (may be outdated)

## Date of Research
April 19, 2026
