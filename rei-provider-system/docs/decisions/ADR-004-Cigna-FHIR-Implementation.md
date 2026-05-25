# ADR-004: Cigna FHIR API Implementation

## Status
Accepted

## Context
We have 1,261 REI (Reproductive Endocrinology & Infertility) providers in our database without NPI (National Provider Identifier) numbers. The NPI is critical for:
- Insurance claim processing
- Provider verification
- Cross-referencing with other healthcare databases

Cigna provides a public FHIR (Fast Healthcare Interoperability Resources) API at `fhir.cigna.com/ProviderDirectory/v1/` that allows searching for providers by specialty and location, returning structured data including NPI numbers.

## Decision
We will implement a Cigna FHIR API client to:
1. Search for REI providers by taxonomy code (207VE0102X)
2. Extract NPI numbers from the API responses
3. Match Cigna providers to our existing database providers
4. Update our database with verified NPI numbers

## Consequences

### Positive
- **High-quality data**: FHIR API returns structured, standardized healthcare data
- **No authentication required**: The Cigna Provider Directory API is publicly accessible
- **Real-time data**: API returns current provider information
- **Compliance**: Using official API respects terms of service vs. scraping
- **Match confidence**: Can cross-reference multiple data points (name, address, phone)

### Negative
- **Rate limiting**: Must implement respectful rate limiting (60 req/min)
- **API availability**: Dependent on Cigna's API uptime
- **Coverage gaps**: Not all REI providers may be in Cigna's network
- **Pagination complexity**: Large result sets require pagination handling

### Neutral
- **Implementation complexity**: Requires understanding FHIR R4 specification
- **Data mapping**: Need to transform FHIR resources to our schema

## Implementation Details

### API Endpoints Used
- `GET /PractitionerRole` - Search provider roles with specialty/location filters
- `GET /Practitioner` - Direct practitioner lookup by NPI or name

### Key Technical Decisions

1. **Rate Limiting**: Implemented 60 requests/minute limit with automatic backoff
2. **Retry Logic**: Exponential backoff for failed requests (max 3 retries)
3. **Matching Algorithm**: 
   - Exact NPI match = 100% confidence
   - Name + Address match = up to 90% confidence
   - Name + City/State match = up to 70% confidence
   - Minimum threshold: 60% confidence for updates
4. **Data Storage**: Store raw FHIR data for debugging, but extract key fields

### Code Structure
```
cigna_fhir_scraper.py
├── CignaFHIRClient          # API client with rate limiting
├── CignaProvider            # Data class for provider records
├── NPIMatcher               # Matching engine for database enrichment
└── CignaScraperRunner       # Batch processing orchestrator
```

## Alternatives Considered

### Alternative 1: Machine-Readable Files (MRF)
Cigna publishes bulk JSON files under ACA Transparency in Coverage rule.
- **Pros**: Complete dataset, no rate limits
- **Cons**: Files are 1TB+, complex parsing, stale data
- **Decision**: Rejected due to processing complexity

### Alternative 2: Web Scraping
Scrape Cigna's provider directory website.
- **Pros**: Can get all visible data
- **Cons**: Fragile, against ToS, requires browser automation
- **Decision**: Rejected in favor of official API

### Alternative 3: NPPES API Only
Use CMS NPPES API directly without Cigna.
- **Pros**: Official government source
- **Cons**: Lower match rates without cross-reference
- **Decision**: Use both - Cigna for matching, NPPES for verification

## Related Decisions
- ADR-001: NPI Enrichment Strategy
- ADR-002: Quick Wins Implementation

## References
- [Cigna FHIR API Documentation](https://developer.cigna.com/)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [REI Taxonomy Code 207VE0102X](https://taxonomy.nucc.org/)

## Date
2026-05-24