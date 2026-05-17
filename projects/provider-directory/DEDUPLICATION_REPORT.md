# Database Deduplication Report

## Date: May 15, 2026

## Issue Discovered

The database contained **4,356 rows** but only **36 unique provider names**, indicating severe duplication issues.

## Root Cause

The scraper was extracting data incorrectly:
- Found 20 h3 elements (provider names) per page
- Found 40 address elements per page (2 per provider - multiple practice locations)
- Matched them by index, causing misalignment
- Same providers were being extracted repeatedly across pages

## Deduplication Results

### Before
- **Total rows:** 4,356
- **Unique names:** 36
- **Unique name+state+city combinations:** 56

### After Deduplication
- **Total rows:** 56 unique providers
- **States covered:** 8
- **Breakdown:**
  - FL: 4 providers
  - TX: 4 providers
  - NJ: 2 providers
  - AL: 2 providers
  - AZ: 2 providers
  - KY: 2 providers
  - PA: 2 providers
  - OH: 2 providers

## Files Updated

1. **Database:** `data/providers.db` - Now contains 56 unique providers
2. **CSV:** `data/providers_deduped.csv` - Clean export of unique providers

## Data Quality Issues

1. **Only 56 unique providers** instead of expected 1,559
2. **Specialty field** shows "Healthy Living Newsletter" instead of actual specialty
3. **Address parsing** has some issues (city names concatenated with street)

## Recommendation

The scraper needs to be re-run with fixed extraction logic to get all 1,559 providers. The current data represents only ~3.6% of the expected dataset.

## Next Steps

1. Fix the provider extraction logic to properly pair names with addresses
2. Re-run the full 78-page scrape
3. Verify unique provider count matches expected 1,559
