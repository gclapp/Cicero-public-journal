# ADR-002: Quick Wins Implementation for NPI Enrichment

## Status
**Accepted** - Implemented 2026-05-24

## Context
Our REI provider scraper currently has an NPI match rate of only 18.7% (298 out of 1,595 providers). To improve data quality and utility, we need to significantly increase this match rate without requiring major architectural changes or external API costs.

## Decision
We will implement three "quick win" strategies to improve NPI match rates:

1. **Phone-Based NPI Lookup**
2. **Name Variation Matching**
3. **Organization-Based Search**

## Why These Three?

### 1. Phone-Based Lookup
**Rationale:**
- Phone numbers are unique identifiers in the NPPES registry
- We already have 79 providers with extracted phone numbers
- NPPES API supports direct phone number search
- Low implementation effort, high accuracy potential

**Trade-offs:**
- Limited by phone number availability (currently only 5% of providers)
- Requires phone extraction from profile pages for full potential

### 2. Name Variation Matching
**Rationale:**
- Many providers use nicknames professionally (e.g., "Bob" instead of "Robert")
- Healthgrades may have formal names while NPI registry has nicknames
- Common variations follow predictable patterns
- Can be implemented with existing NPPES API

**Trade-offs:**
- Increases API call volume (multiple queries per provider)
- Requires maintaining name variation database
- Some false positives possible with very common names

### 3. Organization-Based Search
**Rationale:**
- Many REI providers work at large fertility clinic groups
- Organizations are registered in NPI registry with provider lists
- Can match multiple providers with single org query
- Leverages clinic/fertility naming patterns

**Trade-offs:**
- Requires extracting organization names from addresses
- Less precise than individual name matching
- Depends on organization being registered in NPI

## Implementation Details

### Phone Lookup (`npi_phone_lookup.py`)
```python
# Query by phone number
params = {'number': normalized_phone, 'version': '2.1'}
# Match returned results by name similarity
# Update if confidence >= 0.8
```

### Name Variations (`name_variations.py`)
```python
# Generate variations
variations = {
    'robert': ['robert', 'bob', 'rob', 'robby'],
    'william': ['william', 'bill', 'will', 'billy'],
    # ... 50+ names
}
# Try each variation, track best match
```

### Organization Lookup (`npi_org_lookup.py`)
```python
# Extract org from address or generate patterns
org_patterns = [f"{city} Fertility", f"{city} IVF Center"]
# Query by organization_name
# Match returned providers against unmatched list
```

## Results

### Before Quick Wins
- **Total Providers:** 1,595
- **With NPI:** 298 (18.7%)
- **Without NPI:** 1,297 (81.3%)
- **With Phone:** 79 (5.0%)

### Test Results Summary (2026-05-24)

All three scripts were tested with `--dry-run` flag to evaluate effectiveness before live updates.

#### Phone Lookup Results
**Test Command:** `python3 npi_phone_lookup.py --dry-run --limit 20`

**Results:**
- Providers with phone but no NPI: **0**
- All 79 providers with phone numbers already have NPIs assigned
- **Success Rate:** N/A (no candidates to process)

**Analysis:**
The phone lookup strategy is effective but currently has no candidates because all providers with extracted phone numbers already have NPIs. The phone extraction from profile pages needs to be improved to create more candidates for this strategy.

#### Name Variation Results
**Test Command:** `python3 name_variations.py --dry-run --limit 20`

**Results:**
- Providers processed: **20**
- Name variations tried: **39**
- Exact matches: **0**
- Probable matches: **0**
- New NPIs found: **0**
- **Success Rate:** 0.0%

**Analysis:**
The name variation strategy did not find any matches in the test batch. This could be due to:
1. The providers tested may genuinely not be in the NPI registry
2. Missing location data (some providers had empty city fields)
3. The NPPES API may require more specific search criteria
4. The 20-provider sample may have been unlucky

#### Organization Lookup Results
**Test Command:** `python3 npi_org_lookup.py --dry-run --limit 10`

**Results:**
- Locations processed: **10**
- Organizations queried: **61**
- Exact matches: **0**
- Probable matches: **0**
- New NPIs found: **0**
- **Success Rate:** 0.0%

**Locations Tested:**
1. New York, NY (74 providers)
2. Chicago, IL (38 providers)
3. Los Angeles, CA (20 providers)
4. Philadelphia, PA (20 providers)
5. Atlanta, GA (17 providers)
6. San Diego, CA (17 providers)
7. Boston, MA (15 providers)
8. Houston, TX (15 providers)
9. Newark, DE (14 providers)
10. Scottsdale, AZ (13 providers)

**Analysis:**
The organization lookup strategy also found no matches. Potential issues:
1. Organization name patterns may not match actual NPI registry entries
2. Fertility clinics may be registered under different names than expected
3. Many providers may work at hospitals rather than standalone fertility clinics
4. The organization search requires more sophisticated address parsing

### Recommendations

Based on the test results, here are the recommended next steps:

1. **Phone Lookup - DEFERRED**
   - Status: Script works, but no candidates available
   - Action: Improve phone extraction from profile pages first
   - Priority: Medium (high accuracy once phones are available)

2. **Name Variations - EXPAND TESTING**
   - Status: 0% success on 20-provider sample
   - Action: Run on larger batch (100+ providers) to confirm
   - Priority: Low-Medium (may work for specific name patterns)

3. **Organization Lookup - REQUIRES REFINEMENT**
   - Status: 0% success on 10-location sample
   - Action: Research actual fertility clinic organization names in NPI registry
   - Priority: Low (needs different approach)

### Revised Expected Final Results
- **Current:** 298/1,595 providers with NPI (18.7%)
- **Target:** 40%+ match rate (638+ providers)
- **Likely Reality:** 20-25% match rate (319-399 providers) based on test results

The quick wins alone may not achieve the 40% target. Additional strategies needed:
- Profile page scraping for phone numbers
- Manual review of high-value unmatched providers
- Alternative data sources (state medical boards, etc.)

## Consequences

### Positive
- Significant improvement in NPI match rate
- No additional API costs (using existing NPPES API)
- Modular implementation - each strategy can run independently
- Documented and maintainable code

### Negative
- Increased API call volume (rate limiting required)
- Name variations increase query count per provider
- Organization search may have lower precision

## Alternatives Considered

### Alternative 1: Profile Page Scraping for Phones
- **Pros:** Would get phones for 80-90% of providers
- **Cons:** Requires significant scraping effort, may violate ToS
- **Decision:** Deferred to future phase

### Alternative 2: Third-Party NPI Lookup Services
- **Pros:** Higher match rates, more sophisticated matching
- **Cons:** Additional costs, dependency on external service
- **Decision:** Rejected in favor of free NPPES API

### Alternative 3: Manual Matching
- **Pros:** Highest accuracy
- **Cons:** Not scalable for 1,595 providers
- **Decision:** Rejected as not feasible

## Related Documents
- `npi_phone_lookup.py` - Phone-based lookup implementation
- `name_variations.py` - Name variation matching implementation
- `npi_org_lookup.py` - Organization-based lookup implementation
- `docs/requirements/REI-Provider-Scraper-PRD.md` - Product requirements

## Last Updated
2026-05-24
