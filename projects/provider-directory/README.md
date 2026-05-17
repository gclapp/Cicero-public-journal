# Provider Directory Scraper

Unified interface for scraping provider directories from multiple sources.

## Data Sources

| Source | Status | Method | Priority |
|--------|--------|--------|----------|
| **Cigna API** | ⏳ Pending approval | Official REST API | 1 (when available) |
| **Cigna Scraping** | 🚧 In development | Playwright browser automation | 2 |
| **Healthgrades Scraping** | 📋 Planned | Thunderbit API | 3 |

## Architecture

```
┌─────────────────────────────────────────┐
│         Provider Directory CLI          │
│              (main.py)                  │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌──────────┐
   │ Cigna  │  │ Cigna  │  │Healthgrad│
   │  API   │  │Scraper │  │ Thunderbi│
   │(Future)│  │(Active)│  │ (Planned)│
   └────────┘  └────────┘  └──────────┘
```

## Usage

```bash
# Interactive mode
python main.py

# Direct source selection
python main.py --source cigna-scraper --zip 90210 --specialty "Internal Medicine"
python main.py --source healthgrades --zip 90210 --specialty "Cardiology"

# List available sources
python main.py --list-sources
```

## Project Structure

```
provider-directory/
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── config.py              # Global configuration
├── models.py              # Shared data models
├── storage.py             # Data persistence
├── sources/               # Data source implementations
│   ├── __init__.py
│   ├── base.py            # Abstract base class
│   ├── cigna_api.py       # Cigna API (future)
│   ├── cigna_scraper.py   # Cigna Playwright scraper
│   └── healthgrades.py    # Healthgrades Thunderbit scraper
├── data/                  # SQLite + exports
└── README.md
```

## Data Schema

All sources return standardized `Provider` objects:

```python
Provider:
  - name: str
  - specialties: List[str]
  - address: Address
  - phone: str
  - accepting_new_patients: bool
  - education: List[str]
  - hospital_affiliations: List[str]
  - source: str  # Which scraper found this
  - scraped_at: datetime
```

## Source-Specific Notes

### Cigna API (Future)
- Requires developer portal approval
- Rate limits: TBD
- Authentication: OAuth2

### Cigna Scraper (Active)
- Requires Cigna login credentials
- Stores session state for reuse
- Rate limited to 20 req/min
- Fragile to UI changes

### Healthgrades Thunderbit (Planned)
- Requires Thunderbit API key
- More reliable than raw scraping
- Handles JavaScript SPAs
