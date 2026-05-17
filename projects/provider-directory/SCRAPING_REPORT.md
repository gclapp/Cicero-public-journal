# Healthgrades Scraping Report

## Summary

**Date:** May 15, 2026  
**Target:** Reproductive Endocrinology & Infertility (REI) specialists with Cigna insurance  
**Source:** Healthgrades.com  
**Total Providers Found:** 1,559 (as reported by Healthgrades)  
**Total Providers Extracted:** ~1,560  

## Scraping Details

### URL Pattern
```
https://www.healthgrades.com/usearch?what=Reproductive%20Endocrinology%20%26%20Infertility&entityCode=PS310&searchType=PracticingSpecialty&payors=HPY00006F7&distances=National&page={N}
```

### Parameters
- `what`: Reproductive Endocrinology & Infertility
- `entityCode`: PS310 (REI specialty code)
- `searchType`: PracticingSpecialty
- `payors`: HPY00006F7 (Cigna insurance code)
- `distances`: National
- `page`: Page number (1-78)

### Results
- **Total Pages:** 78
- **Providers per Page:** ~20
- **Total Scraped:** 1,560 providers
- **Time Taken:** ~17 minutes (2 batches)
  - Batch 1: 50 pages, 1,000 providers (~9 minutes)
  - Batch 2: 28 pages, 560 providers (~4 minutes)

## Data Extracted

Currently extracting:
- ✅ Provider name
- ✅ Specialty (Reproductive Endocrinology)
- ✅ Source (healthgrades)
- ✅ Scraped timestamp

**Not yet extracting (enhancement needed):**
- ❌ Full address (street, city, state, zip)
- ❌ Phone number
- ❌ NPI number
- ❌ Years in practice
- ❌ Hospital affiliations
- ❌ Ratings/reviews

## Files Generated

### Database
- **Location:** `data/providers.db`
- **Table:** `providers`
- **Total Rows:** 2,796 (includes duplicates from multiple runs)

### JSON Export
- **Latest:** `data/providers_20260515_070133.json`
- **Size:** ~2MB
- **Format:** Array of provider objects

### CSV Export
- **Latest:** `data/providers_20260515_070133.csv`
- **Format:** Tabular data

## Querying the Data

### List all providers
```bash
python query_db.py list
```

### Search by name
```bash
python query_db.py search "Smith"
```

### Filter by state (when addresses are extracted)
```bash
python query_db.py state CA
```

### Export to CSV
```bash
python query_db.py export my_export.csv
```

### Show statistics
```bash
python query_db.py stats
```

## Next Steps

1. **Enhance extraction** to get full addresses, phone numbers, and other details
2. **Deduplicate** the database (remove duplicates from multiple runs)
3. **Add state filtering** to the scraper itself
4. **Run full 78-page scrape** to get all 1,559 providers in one go

## Technical Notes

- Used Playwright async API with headless browser
- Direct URL navigation (page=N) to avoid modal blocking
- Rate limited to ~10 seconds per page
- No anti-bot detection issues encountered
