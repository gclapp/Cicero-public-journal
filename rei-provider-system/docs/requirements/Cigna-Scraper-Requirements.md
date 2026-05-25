# Cigna Scraper Requirements Document

**Project:** REI Provider Scraper - Cigna Integration  
**Version:** 1.0  
**Date:** May 24, 2026  
**Owner:** Geoffrey Clapp / PGNY  

---

## 1. Overview

### 1.1 Purpose

Define requirements for integrating Cigna provider directory data into the REI Provider Scraper system to enrich 1,261 unmatched REI providers with NPI numbers and insurance network information.

### 1.2 Scope

This document covers:
- Data extraction from Cigna provider directory
- NPI matching and enrichment
- Integration with existing Healthgrades data
- Technical implementation requirements

### 1.3 Success Criteria

| Metric | Target |
|--------|--------|
| NPI Match Rate | ≥40% of unmatched providers |
| Data Accuracy | ≥95% correct NPI matches |
| Processing Time | ≤48 hours for full enrichment |
| API Uptime | ≥99% availability |

---

## 2. Functional Requirements

### 2.1 Data Source Integration

#### 2.1.1 Machine-Readable Files (MRF) - Priority 1

**FR-MRF-001:** The system SHALL download Cigna MRF table of contents from `https://www.cigna.com/legal/compliance/machine-readable-files`

**FR-MRF-002:** The system SHALL parse JSON MRF files to extract provider data

**FR-MRF-003:** The system SHALL filter providers by REI taxonomy codes:
- 207VE0102X (Reproductive Endocrinology)
- 207RE0101X (Endocrinology, Diabetes & Metabolism)
- 207VG0400X (Gynecology)

**FR-MRF-004:** The system SHALL extract the following fields:
| Field | Required | Source Path |
|-------|----------|-------------|
| NPI | ✅ | provider_references.npi |
| Provider Name | ✅ | provider_references.name |
| Taxonomy Code | ✅ | provider_references.taxonomy |
| Address | ✅ | provider_references.address |
| Phone | ⚠️ | provider_references.phone |
| Network Status | ✅ | in_network |
| Plan Names | ✅ | plans.plan_name |

**FR-MRF-005:** The system SHALL handle files up to 1TB in size through streaming/chunked processing

#### 2.1.2 FHIR Provider Directory API - Priority 2

**FR-API-001:** The system SHALL authenticate with Cigna FHIR API using OAuth 2.0

**FR-API-002:** The system SHALL implement the following endpoints:
- `GET /Practitioner` - Search providers
- `GET /Practitioner/{id}` - Get provider details
- `GET /Location` - Search by location
- `GET /Organization` - Search organizations

**FR-API-003:** The system SHALL support FHIR R4 search parameters:
| Parameter | Usage |
|-----------|-------|
| `name` | Provider name search |
| `address-postalcode` | ZIP code search |
| `address-state` | State filter |
| `address-city` | City filter |
| `specialty` | Taxonomy/specialty code |
| `identifier` | NPI lookup |

**FR-API-004:** The system SHALL handle API rate limits gracefully with exponential backoff

**FR-API-005:** The system SHALL refresh OAuth tokens automatically before expiration

#### 2.1.3 Web Scraping - Priority 3 (Fallback)

**FR-SCRAPE-001:** The system SHALL navigate to `https://hcpdirectory.cigna.com/web/public/consumer/directory/search`

**FR-SCRAPE-002:** The system SHALL input search criteria:
- Specialty: "Reproductive Endocrinology" or "Infertility"
- Location: State, ZIP, or City
- Plan type filter (optional)

**FR-SCRAPE-003:** The system SHALL extract provider data from search results:
- Name
- NPI (if visible in results)
- Address
- Phone
- Specialties

**FR-SCRAPE-004:** The system SHALL navigate pagination to collect all results

**FR-SCRAPE-005:** The system SHALL visit individual provider profile pages for detailed data

### 2.2 Data Matching & Enrichment

#### 2.2.1 Provider Matching

**FR-MATCH-001:** The system SHALL match Cigna providers to existing Healthgrades data using:
1. Exact NPI match (highest confidence)
2. Name + Address match (high confidence)
3. Name + City + State match (medium confidence)
4. Phone match (medium confidence)

**FR-MATCH-002:** The system SHALL assign confidence scores to matches:
| Match Type | Confidence Score |
|------------|------------------|
| NPI exact | 1.0 |
| Name + Address | 0.9 |
| Name + City + State | 0.7 |
| Phone only | 0.5 |

**FR-MATCH-003:** The system SHALL flag ambiguous matches for manual review

**FR-MATCH-004:** The system SHALL handle name variations (e.g., "Robert" vs "Bob", "St." vs "Saint")

#### 2.2.2 Data Enrichment

**FR-ENRICH-001:** The system SHALL update existing provider records with:
- Cigna NPI (if missing)
- Cigna in-network status
- Accepted Cigna plans
- Additional contact information

**FR-ENRICH-002:** The system SHALL create new provider records for Cigna-only providers

**FR-ENRICH-003:** The system SHALL preserve all existing Healthgrades data

**FR-ENRICH-004:** The system SHALL track data source provenance

### 2.3 Data Export

**FR-EXPORT-001:** The system SHALL export enriched data to CSV format

**FR-EXPORT-002:** The system SHALL export enriched data to JSON format

**FR-EXPORT-003:** The export SHALL include the following fields:
```
- provider_id
- full_name
- npi (enriched)
- clinic_name
- address
- city
- state
- zip
- phone
- specialties
- healthgrades_score
- cigna_in_network
- cigna_plans
- match_confidence
- data_sources
- last_updated
```

---

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-PERF-001:** MRF processing SHALL handle files up to 1TB

**NFR-PERF-002:** API requests SHALL be rate-limited to ≤10 requests/minute

**NFR-PERF-003:** Web scraping SHALL use delays of 2-5 seconds between requests

**NFR-PERF-004:** Full enrichment process SHALL complete within 48 hours

**NFR-PERF-005:** Individual provider lookup SHALL complete within 5 seconds

### 3.2 Reliability

**NFR-REL-001:** The system SHALL retry failed requests up to 3 times with exponential backoff

**NFR-REL-002:** The system SHALL resume interrupted processes from checkpoint

**NFR-REL-003:** The system SHALL log all errors with context for debugging

**NFR-REL-004:** The system SHALL validate data integrity before storage

### 3.3 Security

**NFR-SEC-001:** API credentials SHALL be stored in environment variables or secure vault

**NFR-SEC-002:** OAuth tokens SHALL never be logged or exposed

**NFR-SEC-003:** The system SHALL use HTTPS for all API communications

**NFR-SEC-004:** The system SHALL implement certificate pinning for API endpoints

### 3.4 Compliance

**NFR-COMP-001:** The system SHALL respect Cigna Terms of Service

**NFR-COMP-002:** The system SHALL respect robots.txt directives

**NFR-COMP-003:** The system SHALL not store patient data or PHI

**NFR-COMP-004:** The system SHALL comply with applicable data privacy regulations

### 3.5 Maintainability

**NFR-MAINT-001:** The system SHALL use modular architecture for easy updates

**NFR-MAINT-002:** The system SHALL include comprehensive logging

**NFR-MAINT-003:** The system SHALL have unit test coverage ≥80%

**NFR-MAINT-004:** The system SHALL document all API changes

---

## 4. Data Schema

### 4.1 Cigna Provider Record

```python
{
    "cigna_provider_id": str,           # Cigna internal ID
    "npi": str,                         # 10-digit NPI
    "name": {
        "first": str,
        "middle": str,
        "last": str,
        "suffix": str,
        "full": str
    },
    "specialties": [str],               # List of specialties
    "taxonomy_codes": [str],            # NPI taxonomy codes
    "address": {
        "line1": str,
        "line2": str,
        "city": str,
        "state": str,
        "zip": str,
        "country": str
    },
    "phone": str,
    "fax": str,
    "email": str,
    "hospital_affiliations": [str],
    "languages": [str],
    "cigna_plans": [str],               # Accepted plans
    "in_network": bool,
    "accepting_new_patients": bool,
    "data_source": str,                 # 'mrf', 'api', 'scrape'
    "last_updated": datetime,
    "raw_data": dict                    # Original source data
}
```

### 4.2 Match Result Record

```python
{
    "match_id": str,
    "healthgrades_provider_id": str,
    "cigna_provider_id": str,
    "match_type": str,                  # 'npi', 'name_address', etc.
    "confidence_score": float,          # 0.0 - 1.0
    "match_status": str,                # 'confirmed', 'pending', 'rejected'
    "matched_fields": [str],            # Which fields matched
    "discrepancies": [str],             # Any data conflicts
    "created_at": datetime,
    "reviewed_by": str,                 # User who reviewed (if manual)
    "notes": str
}
```

---

## 5. Technical Requirements

### 5.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| HTTP Client | httpx / aiohttp |
| Browser Automation | Playwright |
| Data Processing | pandas, pydantic |
| JSON Processing | ijson (streaming) |
| Database | SQLite / PostgreSQL |
| Authentication | authlib (OAuth) |
| Testing | pytest |

### 5.2 Dependencies

```
# Core
httpx>=0.27.0
pydantic>=2.0.0
pandas>=2.0.0

# API
authlib>=1.3.0

# Scraping
playwright>=1.40.0

# Data Processing
ijson>=3.2.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### 5.3 Infrastructure

**REQ-INFRA-001:** The system SHALL run on Python 3.11 or higher

**REQ-INFRA-002:** MRF processing SHALL require minimum 16GB RAM for streaming

**REQ-INFRA-003:** The system SHALL have 100GB disk space available for MRF downloads

**REQ-INFRA-004:** Web scraping SHALL use proxy rotation for production

---

## 6. User Stories

### 6.1 As a Data Analyst

- **US-001:** I want to enrich our REI provider database with NPI numbers from Cigna
- **US-002:** I want to see confidence scores for all provider matches
- **US-003:** I want to export enriched data in CSV format
- **US-004:** I want to review and approve low-confidence matches

### 6.2 As a System Administrator

- **US-005:** I want to monitor API usage and rate limits
- **US-006:** I want to resume interrupted enrichment jobs
- **US-007:** I want to configure authentication credentials securely
- **US-008:** I want to receive alerts for processing errors

### 6.3 As a Network Manager

- **US-009:** I want to identify which REI providers are Cigna in-network
- **US-010:** I want to see which Cigna plans each provider accepts
- **US-011:** I want to compare Healthgrades and Cigna data side-by-side

---

## 7. Error Handling

### 7.1 API Errors

| Error Code | Handling |
|------------|----------|
| 400 Bad Request | Log request details, skip record |
| 401 Unauthorized | Refresh token, retry once |
| 403 Forbidden | Log and alert, stop processing |
| 404 Not Found | Mark provider as not found, continue |
| 429 Too Many Requests | Exponential backoff, retry |
| 500 Server Error | Retry with backoff, alert after 3 failures |
| 503 Service Unavailable | Wait 60 seconds, retry |

### 7.2 Data Errors

| Error Type | Handling |
|------------|----------|
| Missing NPI | Skip record, log warning |
| Invalid NPI format | Validate and correct, or skip |
| Malformed address | Attempt standardization, or flag |
| Duplicate provider | Merge or flag for review |

### 7.3 System Errors

| Error Type | Handling |
|------------|----------|
| Network timeout | Retry with exponential backoff |
| Disk space full | Pause processing, alert |
| Memory exhaustion | Use streaming, reduce batch size |
| Authentication failure | Alert, halt processing |

---

## 8. Testing Requirements

### 8.1 Unit Tests

**TEST-001:** All API client methods SHALL have unit tests

**TEST-002:** All data matching algorithms SHALL have unit tests

**TEST-003:** All data validation functions SHALL have unit tests

### 8.2 Integration Tests

**TEST-004:** API authentication flow SHALL be tested

**TEST-005:** End-to-end enrichment process SHALL be tested

**TEST-006:** Error handling and recovery SHALL be tested

### 8.3 Test Data

**TEST-007:** Tests SHALL use mock API responses

**TEST-008:** Tests SHALL use sample MRF data (not full files)

**TEST-009:** Tests SHALL cover edge cases (empty responses, malformed data)

---

## 9. Documentation Requirements

### 9.1 Code Documentation

**DOC-001:** All public functions SHALL have docstrings

**DOC-002:** Complex algorithms SHALL have inline comments

**DOC-003:** Configuration options SHALL be documented

### 9.2 User Documentation

**DOC-004:** Setup instructions SHALL be provided

**DOC-005:** API credential configuration SHALL be documented

**DOC-006:** Troubleshooting guide SHALL be provided

### 9.3 API Documentation

**DOC-007:** All internal APIs SHALL be documented

**DOC-008:** Data schemas SHALL be documented

---

## 10. Open Questions

1. **Q1:** What is the estimated size of Cigna's REI provider dataset?
2. **Q2:** How frequently are MRF files updated?
3. **Q3:** What are the specific API rate limits for Cigna FHIR API?
4. **Q4:** Is there a sandbox environment for testing?
5. **Q5:** Are there any restrictions on commercial use of MRF data?

---

## 11. Appendix

### 11.1 REI Taxonomy Codes

| Code | Description |
|------|-------------|
| 207VE0102X | Reproductive Endocrinology |
| 207RE0101X | Endocrinology, Diabetes & Metabolism |
| 207VG0400X | Gynecology |
| 207VF0040X | Female Pelvic Medicine & Reconstructive Surgery |

### 11.2 Cigna URLs

| Purpose | URL |
|---------|-----|
| Provider Directory | https://hcpdirectory.cigna.com/ |
| Machine Readable Files | https://www.cigna.com/legal/compliance/machine-readable-files |
| Developer Portal | https://developer.cigna.com/ |
| FHIR API Base | https://fhir.cigna.com/ProviderDirectory/v1/ |

### 11.3 Glossary

| Term | Definition |
|------|------------|
| **MRF** | Machine-Readable File - JSON files published under ACA Transparency in Coverage Rule |
| **FHIR** | Fast Healthcare Interoperability Resources - HL7 standard for healthcare data exchange |
| **NPI** | National Provider Identifier - 10-digit unique identifier for healthcare providers |
| **REI** | Reproductive Endocrinology and Infertility |
| **PHI** | Protected Health Information |

---

*Document Version: 1.0*  
*Last Updated: May 24, 2026*  
*Next Review: Upon implementation completion*
