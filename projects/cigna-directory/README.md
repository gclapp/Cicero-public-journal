# Cigna Provider Directory Scraper

Browser automation scraper for Cigna's provider directory using Playwright.

## Status
- **Phase 1:** Playwright-based scraping (in progress)
- **Phase 2:** Thunderbit evaluation (pending)
- **Phase 3:** Official API integration (pending Cigna approval)

## Approach

### Why Playwright First?
1. Immediate progress while waiting for API access
2. Validates data structure and search patterns
3. Creates baseline for comparing Thunderbit/API results
4. Full control over login session and pagination

### Fragility Factors
| Risk | Mitigation |
|------|------------|
| UI changes | Snapshot-based selectors, not hardcoded XPaths |
| Rate limiting | 2-3 second delays between requests |
| Session expiry | Automatic re-auth with stored credentials |
| Anti-bot detection | Human-like delays, realistic user agent |

## Files

- `scraper.py` - Main scraper with login and search
- `config.py` - Credentials and settings
- `storage.py` - Data persistence (JSON/CSV/SQLite)
- `requirements.txt` - Python dependencies

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper
python scraper.py --zip 90210 --radius 10 --specialty "Internal Medicine"
```

## Data Schema

```json
{
  "provider_id": "string",
  "name": "string",
  "specialties": ["string"],
  "address": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip": "string"
  },
  "phone": "string",
  "accepting_new_patients": boolean,
  "languages": ["string"],
  "education": ["string"],
  "hospital_affiliations": ["string"],
  "scraped_at": "ISO timestamp"
}
```

## Security
- Credentials stored in `~/.openclaw/credentials/cigna-credentials.json`
- Never commit credentials to git
- Session cookies stored separately from credentials
