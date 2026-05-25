# REI Provider Scraper - Product Requirements Document

## Overview
System for scraping and enriching REI (Reproductive Endocrinology & Infertility) provider data from multiple sources and matching to NPI (National Provider Identifier) registry.

## Current Status
- **Total Providers:** 1,595
- **With NPI:** 298 (18.7%)
- **With Phone:** 79 (5.0%)
- **Goal:** Improve NPI match rate to >50%

---

## Data Sources

### 1. Healthgrades (Primary Source)
**Status:** ✅ IMPLEMENTED

**Description:** Healthgrades is the primary source for REI provider listings.
- 1,559 REI providers scraped
- Includes name, address, credentials, specialties
- Source URL: https://www.healthgrades.com

**Fields Extracted:**
- Provider name (first, last, full)
- Credentials (MD, DO, etc.)
- Specialties
- Address (street, city, state, zip)
- Phone (when available)
- Healthgrades rating and reviews

---

### 2. Cigna FHIR API (New Data Source)
**Status:** ✅ IMPLEMENTED

**Description:** Cigna's FHIR Provider Directory API provides structured healthcare provider data including NPI numbers.
- API Endpoint: `fhir.cigna.com/ProviderDirectory/v1/`
- No authentication required (public API)
- Returns FHIR R4 compliant JSON

**Implementation:**
- **Script:** `cigna_fhir_scraper.py`
- **Client:** `CignaFHIRClient` class with rate limiting
- **Matching:** `NPIMatcher` class for database enrichment

**API Capabilities:**
- Search by taxonomy code (207VE0102X for REI)
- Search by state, city, ZIP code
- Search by provider name
- Lookup by NPI
- Pagination support for large result sets

**Rate Limiting:**
- 60 requests per minute maximum
- Exponential backoff on 429 responses
- Automatic retry with 3 attempts

**Fields Extracted:**
- NPI (10-digit National Provider Identifier)
- Provider name (first, middle, last)
- Credentials and specialties
- Taxonomy codes
- Address (line1, line2, city, state, zip)
- Phone, fax, email
- Organization affiliation
- Languages spoken
- Cigna plan acceptance

**Matching Algorithm:**
1. **Exact NPI Match** (100% confidence)
   - Direct comparison of NPI numbers
   - Highest confidence level
   
2. **Name + Address Match** (up to 90% confidence)
   - Fuzzy string matching on names
   - Address similarity scoring
   - Weighted: 60% name, 30% address, 10% location
   
3. **Name + City/State Match** (up to 70% confidence)
   - Used when address details differ
   - Minimum threshold: 60% confidence for database updates

**Expected Improvement:**
- Estimated 15-25% additional NPI matches
- Particularly effective for providers in Cigna network
- Cross-validates existing NPI data

**Usage:**
```bash
# Test API connection
python3 cigna_fhir_scraper.py --test-api

# Run for specific state
python3 cigna_fhir_scraper.py --state CA --db data/providers.db

# Run for all states with unmatched providers
python3 cigna_fhir_scraper.py --db data/providers.db

# Dry run (no database updates)
python3 cigna_fhir_scraper.py --state CA --dry-run

# Show database statistics
python3 cigna_fhir_scraper.py --stats --db data/providers.db
```

---

## Quick Win Enhancements

### 1. Phone Lookup Enhancement

**Status:** ✅ IMPLEMENTED

**Script:** `npi_phone_lookup.py`

**How it works:**
- Queries NPPES API using the `telephone_number` parameter
- Phone numbers are unique identifiers in the NPI registry
- For each provider with a phone number but no NPI:
  1. Normalize phone to 10-digit format
  2. Query: `https://npiregistry.cms.hhs.gov/api/?number=<phone>&version=2.1`
  3. Match returned results against provider name
  4. Update database with NPI if confidence >= 0.8

**Expected Improvement:**
- Current providers with phones: 79
- All already have NPIs (extracted during previous enrichment)
- **Future potential:** As we extract more phones via profile scraping, this will yield matches

**Results:**
- All 79 providers with phones already have NPIs
- Ready for future phone extractions

---

### 2. Name Variation Strategy

**Status:** ✅ IMPLEMENTED

**Script:** `name_variations.py`

**How it works:**
- Many providers use nicknames, middle names, or variations not matching Healthgrades
- Generates variations like:
  - "Robert" → "Bob", "Rob", "Robby", "Bert"
  - "William" → "Bill", "Will", "Billy", "Liam"
  - "Elizabeth" → "Liz", "Beth", "Betty", "Lisa"
  - Try with/without middle initial
- Queries each variation against NPPES API
- Tracks best match across all variations

**Name Variations Database:**
- 50+ common names with 2-5 variations each
- Covers ~80% of common nickname patterns
- Includes both male and female names

**Expected Improvement:**
- Estimated 5-10% additional matches
- Particularly effective for providers using nicknames professionally

**Results:**
- TBD after running on full dataset

---

### 3. Organization Lookup Strategy

**Status:** ✅ IMPLEMENTED

**Script:** `npi_org_lookup.py`

**How it works:**
- Many REI providers work at fertility clinics registered as organizations
- NPPES API supports `organization_name` parameter
- For each location with unmatched providers:
  1. Extract potential org names from addresses
  2. Generate common fertility clinic patterns (e.g., "{City} Fertility Center")
  3. Query: `https://npiregistry.cms.hhs.gov/api/?organization_name=<org>&state=<state>`
  4. Match returned individual providers against our unmatched list
  5. Update database with NPIs for matches

**Organization Patterns:**
- Extracted from street addresses
- Generated patterns: "{City} Fertility", "{City} Reproductive Medicine", "{City} IVF Center"
- Keywords: fertility, reproductive, ivf, women's health, clinic, center

**Expected Improvement:**
- Estimated 10-15% additional matches
- Particularly effective for providers at large fertility clinic groups

**Results:**
- TBD after running on full dataset

---

## Web UI Integration

### Cigna Data Source Features

**1. Cigna-Verified Provider Badge**
- Providers matched via Cigna FHIR API show special badge
- Badge indicates "✓ Cigna FHIR" for API-verified providers
- Visual distinction in search results table

**2. Filter: Show Cigna-Verified Only**
- Checkbox filter on results page
- URL parameter: `?cigna_verified=true`
- Filters to show only providers with Cigna-derived NPI data

**3. Provider Detail Enhancements**
- Shows NPI source attribution (Cigna FHIR, Cigna, Healthgrades)
- Displays match confidence percentage
- Shows data source for transparency

**4. API Endpoints**
- `GET /api/cigna/search` - Search Cigna FHIR API directly
- `GET /api/cigna/status` - Check API status and stats
- `POST /api/cigna/match` - Run matching for a state
- `GET /api/cigna/provider/<id>` - Get provider with Cigna data

---

## Implementation Notes

### Running the Quick Wins

```bash
# 1. Phone-based lookup
cd /home/ubuntu/.openclaw/workspace/rei-provider-scraper
python3 npi_phone_lookup.py

# 2. Name variation enrichment
python3 name_variations.py --limit 100  # Start with subset

# 3. Organization lookup
python3 npi_org_lookup.py --limit 50  # Start with subset

# 4. Cigna FHIR API enrichment
python3 cigna_fhir_scraper.py --state CA
```

### All Quick Wins (Batch)

```bash
# Run all strategies
python3 npi_phone_lookup.py
python3 name_variations.py
python3 npi_org_lookup.py
python3 cigna_fhir_scraper.py

# Check final stats
python3 -c "
import sqlite3
conn = sqlite3.connect('data/providers.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM providers')
total = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM providers WHERE npi IS NOT NULL AND npi != \"\"')
npi = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM providers WHERE npi_match_source = \"cigna_fhir\"')
cigna = cursor.fetchone()[0]
print(f'NPI: {npi}/{total} ({npi/total*100:.1f}%)')
print(f'Cigna FHIR matches: {cigna}')
"
```

---

## Future Enhancements

### Profile Page Phone Scraping
- Scrape individual Healthgrades profile pages
- Capture phone numbers not shown in search results
- Requires unique provider IDs from search results

### Address Normalization
- Standardize address formats for better matching
- Handle suite numbers, building names, etc.

### Multi-Source Verification
- Cross-reference with other provider directories
- Validate NPI matches across multiple sources

### Additional FHIR API Features
- Search by organization/clinic name
- Filter by Cigna plan acceptance
- Extract hospital affiliations

---

## Success Metrics

| Metric | Before | Target | After Quick Wins |
|--------|--------|--------|------------------|
| NPI Match Rate | 18.7% | 40%+ | TBD |
| Providers with Phone | 5.0% | 20%+ | TBD |
| Exact Matches | 298 | 600+ | TBD |
| Cigna FHIR Matches | 0 | 100+ | TBD |

---

## Last Updated
2026-05-24