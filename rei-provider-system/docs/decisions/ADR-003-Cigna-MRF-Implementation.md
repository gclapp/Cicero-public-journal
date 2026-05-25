# ADR-003: Cigna Machine-Readable Files (MRF) Implementation

**Status:** Accepted  
**Date:** 2026-05-24  
**Author:** Cicero (Subagent)  
**Related:** ADR-002 (NPI Enrichment Strategy), Cigna-Scraper-Design.md

## Context

We have 1,261 REI (Reproductive Endocrinology and Infertility) providers in our database without NPIs. NPIs are critical for:
- Insurance verification
- Provider identification
- Data interoperability
- Regulatory compliance

Cigna publishes Machine-Readable Files (MRFs) as required by the CMS Transparency in Coverage Final Rule. These files contain comprehensive provider data including NPIs, specialties, and locations.

## Decision

We will implement a Cigna MRF download and parsing system to extract NPIs for our unmatched REI providers.

### Key Decisions

1. **Primary Strategy: Selective MRF Download with Streaming Parse**
   - Download relevant MRF files (not all 1TB)
   - Stream-parse to extract only REI providers
   - Match against our database using name + state

2. **Data Source Priority**
   - Primary: Cigna MRF files (most comprehensive)
   - Secondary: Cigna FHIR API (if available)
   - Tertiary: Web scraping (fallback)

3. **Matching Strategy**
   - Exact NPI match (if partial NPI exists)
   - Name + State matching with fuzzy logic
   - Confidence scoring (high/medium/low)
   - Manual review for low-confidence matches

## Consequences

### Positive

- **High Match Rate Expected:** 40-60% (500-750 providers)
- **Authoritative Source:** Cigna is a major insurer with comprehensive provider data
- **Cost Effective:** No API fees for MRF data
- **Scalable:** Can process multiple MRF files
- **Compliant:** Uses publicly available transparency data

### Negative

- **Large File Sizes:** MRF files can be 10-100GB each
- **Processing Time:** May take hours to download and parse
- **Storage Requirements:** Need temporary storage for downloads
- **Data Freshness:** MRFs updated monthly, may lag real-time
- **Matching Complexity:** Name variations require fuzzy matching

### Risks

| Risk | Mitigation |
|------|------------|
| Download failures | Resume capability, retry logic |
| Storage exhaustion | Streaming parse, delete after processing |
| Low match accuracy | Confidence scoring, manual review queue |
| Cigna blocking | Rate limiting, respectful headers |
| Data format changes | Version detection, flexible parser |

## Implementation Details

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CIGNA MRF PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ MRF Index    │───▶│ Downloader   │───▶│ Parser       │  │
│  │ Parser       │    │ (resume)     │    │ (streaming)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                   │         │
│                                                   ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Database     │◀───│ NPI Matcher  │◀───│ REI Filter   │  │
│  │ Updater      │    │ (fuzzy)      │    │ (taxonomy)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **MRFIndexParser**
   - Fetches Cigna's MRF index
   - Identifies relevant files (by plan type, state)
   - Prioritizes national PPO files

2. **MRFDownloader**
   - Downloads files with resume capability
   - Progress tracking with tqdm
   - Verifies gzip integrity
   - Manages download state

3. **MRFStreamingParser**
   - Stream-parses large JSON files
   - Extracts provider references
   - Filters by REI taxonomy codes
   - Yields CignaProvider objects

4. **NPIMatcher**
   - Matches against SQLite database
   - Exact NPI matching
   - Fuzzy name + state matching
   - Confidence scoring
   - Updates database with matches

### Taxonomy Codes

We filter for these REI-related taxonomy codes:

| Code | Description |
|------|-------------|
| 207VE0102X | Reproductive Endocrinology/Infertility |
| 207RE0101X | Endocrinology, Diabetes & Metabolism |
| 207VG0400X | Gynecology (REI-related) |

### File Locations

- **Script:** `cigna_mrf_downloader.py`
- **Data Directory:** `data/cigna_mrf/`
- **Logs:** `logs/cigna_mrf.log`
- **State:** `data/cigna_mrf/download_state.json`

## Usage

```bash
# Run full pipeline
python cigna_mrf_downloader.py --full-pipeline

# Test with small sample
python cigna_mrf_downloader.py --test-small

# Download only
python cigna_mrf_downloader.py --download

# Process specific number of files
python cigna_mrf_downloader.py --full-pipeline --max-files 5
```

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| NPI Match Rate | ≥40% | Matched / Total Unmatched |
| High Confidence Matches | ≥60% | High / Total Matches |
| Processing Time | ≤24 hours | Start to completion |
| Data Accuracy | ≥95% | Manual sample validation |

## Alternatives Considered

### Alternative 1: NPPES NPI Registry API
- **Pros:** Official CMS source, free, comprehensive
- **Cons:** Rate limited, requires exact name matching, no specialty filtering
- **Decision:** Use as secondary source

### Alternative 2: Commercial NPI Lookup Services
- **Pros:** Easy to use, fast, high accuracy
- **Cons:** Cost ($0.01-0.05 per lookup), 1,261 providers = $50-150
- **Decision:** Not cost-effective at our volume

### Alternative 3: Direct Cigna API
- **Pros:** Real-time, structured data
- **Cons:** Requires OAuth, rate limits, may not exist for bulk queries
- **Decision:** Investigate as secondary option

## Related Decisions

- ADR-002: NPI Enrichment Strategy (overall approach)
- Cigna-Scraper-Design.md: Detailed architecture

## References

- [CMS Transparency in Coverage Final Rule](https://www.cms.gov/healthplan-price-transparency)
- [Cigna MRF Documentation](https://www.cigna.com/legal/compliance/machine-readable-files)
- [MRF System Requirements PDF](https://static.cigna.com/assets/cignaaccess/en-us/pdf/MRF-System-Requirements.pdf)

## Notes

- MRF files are updated monthly (typically first week)
- Files use CloudFront CDN with signed URLs
- JSON format follows CMS specification
- Provider references may include multiple NPIs (individual + group)
