# ADR-001: NPI Enrichment Strategy

**Status:** Accepted  
**Date:** May 24, 2026  
**Deciders:** Geoffrey Clapp, Cicero  
**Affected:** REI Provider Scraper System

---

## Context

The REI Provider Scraper collects provider data from Healthgrades but lacks National Provider Identifier (NPI) numbers, which are essential for:
- Unique provider identification
- Integration with healthcare systems
- Insurance network verification
- Regulatory compliance

We needed to select a strategy for enriching scraped provider records with NPI numbers.

---

## Decision

We will use the **CMS NPPES NPI Registry API** as our primary NPI enrichment source, implementing a multi-strategy fuzzy matching approach.

### Selected Approach

1. **Primary Data Source:** CMS NPPES NPI Registry API (https://npiregistry.cms.hhs.gov/)
2. **Matching Strategy:** Name + State + City with fuzzy similarity scoring
3. **Confidence Thresholds:**
   - Exact (>0.9): Auto-accept
   - Probable (0.7-0.9): Auto-accept with flag
   - Fuzzy (0.5-0.7): Store for review
   - Unmatched (<0.5): Mark for alternative strategies

---

## Consequences

### Positive
- **Free:** No cost for API usage
- **Authoritative:** Official CMS registry
- **Comprehensive:** 7+ million active NPIs
- **Rich Data:** Includes addresses, specialties, phone numbers

### Negative
- **Rate Limited:** 1000 requests/hour per IP
- **No Bulk Query:** Must query one name combination at a time
- **Name Sensitivity:** Requires exact first name matching
- **Current Match Rate:** Only 18.7% (298/1,595 providers)

---

## Current Results

| Metric | Value |
|--------|-------|
| Total Providers | 1,595 |
| With NPI | 298 |
| Match Rate | 18.7% |
| Exact Matches | ~150 (9.4%) |
| Probable Matches | ~100 (6.3%) |
| Fuzzy Matches | ~48 (3.0%) |
| Unmatched | ~1,297 (81.3%) |

---

## Why 18.7% is Insufficient

An 18.7% match rate is inadequate for operational use because:

1. **Sales Team Needs:** Field reps need NPIs to verify providers in payer systems
2. **Network Analysis:** 80%+ coverage required for meaningful geographic analysis
3. **Data Integration:** Most healthcare systems require NPI as primary key
4. **Regulatory Reporting:** NPIs required for compliance and quality reporting

**Target Match Rate:** 80%+

---

## Proposed Quick Win Strategies

To improve the match rate from 18.7% to 80%+, we will implement three parallel strategies:

### Strategy A: Phone-Based NPI Lookup

**Hypothesis:** Phone numbers are unique identifiers that can directly match to NPI records.

**Implementation:**
1. Scrape phone numbers from Healthgrades profile pages
2. Query NPPES API using phone number as primary search parameter
3. Match single result or highest confidence result

**Expected Improvement:** +40-50% additional matches  
**Effort:** Medium (requires profile page scraping)  
**Status:** Partially implemented in `phone_backfill.py`

**Example:**
```python
# Query by phone number
params = {'number': '(555) 123-4567', 'version': '2.1'}
# NPPES returns provider with matching practice phone
```

---

### Strategy B: Broader Name Variations

**Hypothesis:** Name parsing is too strict, missing valid matches due to:
- Middle names in NPI registry but not in Healthgrades
- Suffixes (Jr., Sr., III) causing mismatches
- Nicknames vs. formal names

**Implementation:**
1. Generate multiple name variants for each provider:
   - Full name as scraped
   - Name without middle name
   - Name without suffix
   - Common nickname mappings
2. Query NPPES with each variant
3. Accept highest confidence match across all variants

**Expected Improvement:** +15-20% additional matches  
**Effort:** Low  
**Status:** Not yet implemented

**Example:**
```python
name_variants = [
    "John Michael Smith",
    "John Smith",  # Without middle
    "John Smith Jr.",  # With suffix
    "Johnny Smith"  # Nickname variant
]
```

---

### Strategy C: Organization-Based Search

**Hypothesis:** Providers practicing at the same clinic can be found by searching for the organization first.

**Implementation:**
1. Extract practice/clinic names from Healthgrades
2. Query NPPES by organization name
3. For each provider at that address, search within organization's NPI results
4. Match by name similarity within reduced candidate set

**Expected Improvement:** +10-15% additional matches  
**Effort:** Medium  
**Status:** Not yet implemented

**Example:**
```python
# Step 1: Find organization NPI
org_params = {'organization_name': 'Fertility Clinic of LA'}
# Step 2: Get all providers at that organization
# Step 3: Match individual providers to org's provider list
```

---

## Combined Impact Projection

| Strategy | Current | Improvement | Cumulative |
|----------|---------|-------------|------------|
| Baseline | 18.7% | - | 18.7% |
| Phone Lookup | 18.7% | +45% | 63.7% |
| Name Variations | 63.7% | +17% | 80.7% |
| Organization Search | 80.7% | +12% | 92.7% |

**Projected Final Match Rate:** 90%+

---

## Alternative Approaches Considered

### Alternative 1: Commercial NPI Database
- **Options:** IQVIA, Definitive Healthcare, CarePrecise
- **Pros:** Higher match rates, pre-cleaned data
- **Cons:** $5,000-20,000/year cost, licensing restrictions
- **Decision:** Rejected for now due to cost; reconsider if open-source strategies fail

### Alternative 2: Machine Learning Matching
- **Approach:** Train ML model on confirmed matches
- **Pros:** Could achieve 95%+ accuracy
- **Cons:** Requires labeled training data, complex implementation
- **Decision:** Deferred to Phase 2; revisit after quick wins implemented

### Alternative 3: Manual Matching
- **Approach:** Human reviewers match unmatched providers
- **Pros:** 100% accuracy for reviewed records
- **Cons:** Time-intensive, not scalable
- **Decision:** Use for fuzzy matches only, not primary strategy

---

## Implementation Timeline

| Phase | Strategy | Duration | Target Match Rate |
|-------|----------|----------|-------------------|
| 1 | Phone Lookup | 1 week | 60% |
| 2 | Name Variations | 3 days | 75% |
| 3 | Organization Search | 1 week | 85% |
| 4 | Review & Optimize | 3 days | 90% |

---

## Success Criteria

This decision will be considered successful when:
- [ ] NPI match rate reaches 80%+
- [ ] Phone coverage reaches 70%+
- [ ] Average match confidence > 0.85
- [ ] Processing time < 2 seconds per provider

---

## Related Documents

- `/docs/requirements/REI-Provider-Scraper-PRD.md` - Full project requirements
- `/rei-provider-scraper/npi_enrichment.py` - Implementation
- `/rei-provider-scraper/PHONE_EXTRACTION_NOTES.md` - Phone strategy details

---

## Notes

- NPPES API documentation: https://npiregistry.cms.hhs.gov/api/documentation
- Rate limiting requires implementing request throttling
- Consider caching NPPES responses to reduce API calls
- Monitor for API changes (version 2.1 current as of May 2026)

---

*This ADR is a living document. Updates should be made as strategies are implemented and results measured.*
