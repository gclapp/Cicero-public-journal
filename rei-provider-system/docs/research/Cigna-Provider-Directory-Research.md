# Cigna Provider Directory Research Report

**Date:** May 24, 2026  
**Researcher:** Cicero (Subagent)  
**Project:** REI Provider Scraper - NPI Enrichment  
**Objective:** Evaluate Cigna as a data source for finding NPI numbers for 1,261 unmatched REI providers

---

## Executive Summary

Cigna's provider directory represents a **HIGH-VALUE, MODERATE-COMPLEXITY** target for REI provider NPI enrichment. The directory contains NPI numbers (confirmed available since 2024 updates), specialty filters, and comprehensive provider data. Multiple access methods exist with varying feasibility.

**Recommendation:** **PROCEED** with a hybrid approach prioritizing:
1. **Machine-Readable Files (MRF)** - Bulk data access (preferred)
2. **FHIR Provider Directory API** - Structured API access (requires registration)
3. **Web scraping** - Fallback option with proper protections

---

## 1. Cigna Provider Directory Overview

### 1.1 Public Search Interface

**Primary URL:** `https://hcpdirectory.cigna.com/web/public/consumer/directory/search`

**Alternative Entry Points:**
- `https://sarhcpdir.cigna.com/web/public/sarSAMBAProviders` (Medicare Advantage)
- `https://[REDACTED]/web/public/ifpproviders` (Individual/Family Plans)
- `https://my.cigna.com/public/site_tour/find_doctor.html` (myCigna portal)

**Key Features (as of 2024 updates):**
- ✅ **NPI numbers displayed** in provider profiles
- ✅ Search by provider name with plan participation
- ✅ Search by Medical Group or Group Practice
- ✅ Interactive map with zoom-based search refinement
- ✅ Sort results alphabetically (A-Z, Z-A)
- ✅ Provider/facility issue reporting
- ✅ Hospital affiliation display
- ✅ Specialties in common language (e.g., "Fertility Specialist" vs "Reproductive Endocrinologist")
- ✅ Spoken languages
- ✅ Medicare plans accepted
- ✅ Practice hours
- ✅ Download/print custom provider lists

### 1.2 Search Parameters Supported

| Parameter | Supported | Notes |
|-----------|-----------|-------|
| **Location** | ✅ | Address, City, State, ZIP code |
| **Provider Name** | ✅ | First, last, or full name |
| **NPI Search** | ✅ | Direct NPI lookup available |
| **Specialty** | ✅ | Including REI, Fertility, Endocrinology |
| **Medical Group** | ✅ | Search by group practice name |
| **Hospital** | ✅ | Find providers by hospital affiliation |
| **Plan Type** | ✅ | Filter by specific Cigna plans |
| **Radius/Distance** | ✅ | Map-based distance filtering |
| **Language** | ✅ | Filter by spoken languages |
| **Gender** | ✅ | Provider gender filter |
| **Accepting New Patients** | ✅ | Availability filter |

### 1.3 Data Available in Provider Profiles

```json
{
  "provider_name": "Dr. Jane Smith",
  "npi": "1234567890",
  "specialties": ["Reproductive Endocrinology", "Infertility"],
  "clinic_name": "Fertility Center of Excellence",
  "address": {
    "street": "123 Medical Plaza",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90210"
  },
  "phone": "(310) 555-0123",
  "hospital_affiliations": ["Cedars-Sinai Medical Center"],
  "languages": ["English", "Spanish"],
  "cigna_plans": ["Cigna PPO", "Cigna Open Access Plus"],
  "in_network": true,
  "accepting_new_patients": true,
  "hours": "Mon-Fri: 8:00 AM - 5:00 PM"
}
```

---

## 2. Technical Architecture Analysis

### 2.1 Rendering Approach

Based on research, Cigna's provider directory uses:

**Primary Interface:**
- **Client-side rendering** with JavaScript-heavy interface
- Likely React or similar modern framework
- Dynamic content loading via XHR/Fetch API calls
- Map integration (likely Google Maps or Mapbox)

**Implications for Scraping:**
- ✅ API endpoints discoverable via browser DevTools
- ✅ JSON data structures accessible
- ⚠️ Requires JavaScript execution (Selenium/Playwright needed)
- ⚠️ Dynamic content may require wait conditions

### 2.2 Bot Protection Assessment

**Observed Protections:**
| Protection | Likely Present | Notes |
|------------|----------------|-------|
| **Cloudflare** | ⚠️ Possible | Common for healthcare sites |
| **reCAPTCHA** | ⚠️ Possible | May trigger on high volume |
| **Rate Limiting** | ✅ Likely | Standard for provider directories |
| **IP Blocking** | ⚠️ Possible | After sustained high-volume requests |
| **Bot Signatures** | ⚠️ Possible | User-agent analysis |
| **TLS Fingerprinting** | ⚠️ Possible | Advanced protection |

**Recommended Countermeasures:**
1. Rotate User-Agent strings
2. Use residential proxies for high-volume scraping
3. Implement human-like delays (2-5 seconds between requests)
4. Randomize request patterns
5. Use headless browser with stealth plugins
6. Respect robots.txt and terms of service

### 2.3 Rate Limiting Expectations

Based on industry standards for healthcare provider directories:

| Metric | Estimate |
|--------|----------|
| **Requests per minute** | 10-30 (conservative) |
| **Requests per hour** | 500-1000 |
| **Concurrent connections** | 1-2 |
| **Session duration** | May require re-authentication |

**Recommended Approach:**
- Start with 1 request every 5 seconds
- Monitor for 429 (Too Many Requests) responses
- Implement exponential backoff on rate limit detection
- Use rotating proxy pool for larger-scale operations

---

## 3. API & Data Access Options

### 3.1 Option 1: Machine-Readable Files (MRF) - RECOMMENDED

**URL:** `https://www.cigna.com/legal/compliance/machine-readable-files`

**What it is:**
- ACA Transparency in Coverage Rule compliance files
- JSON format (up to 1TB per file)
- Contains ALL in-network providers and negotiated rates
- Updated regularly

**Pros:**
- ✅ Complete provider dataset (not just search results)
- ✅ No rate limiting
- ✅ No bot protection
- ✅ Contains NPI numbers
- ✅ Free public access
- ✅ Structured JSON format

**Cons:**
- ⚠️ Massive file sizes (up to 1TB)
- ⚠️ Requires significant processing infrastructure
- ⚠️ May need to download entire dataset
- ⚠️ Not real-time (updated periodically)

**Feasibility for REI NPI Lookup:**
- **HIGH** - If we can process the files
- Best for bulk matching of 1,261 providers
- Would require filtering by specialty/taxonomy code

**Implementation Approach:**
```python
# Download MRF table of contents
# Parse JSON for providers with REI taxonomy codes (207VE0102X)
# Extract NPI, name, address, phone
# Match against our unmatched provider list
```

### 3.2 Option 2: FHIR Provider Directory API

**Base URL:** `https://fhir.cigna.com/ProviderDirectory/v1/`

**Endpoints (discovered):**
- `GET /Location?address-postalcode={zip}` - Search by ZIP
- `GET /Practitioner` - Provider search
- `GET /Organization` - Organization/facility search

**Documentation:** `https://developer.cigna.com/docs/service-apis/provider-directory`

**Authentication:**
- OAuth 2.0 required
- Developer registration required at `https://developer.cigna.com/register`
- Client ID and Secret needed
- Sandbox available for testing

**Pros:**
- ✅ Official, supported API
- ✅ Structured FHIR R4 format
- ✅ No scraping needed
- ✅ Reliable and stable
- ✅ Designed for programmatic access

**Cons:**
- ⚠️ Requires developer registration
- ⚠️ OAuth authentication complexity
- ⚠️ May have usage limits
- ⚠️ Approval process may take time

**Feasibility for REI NPI Lookup:**
- **HIGH** - Best long-term solution
- Clean, legal, sustainable
- Requires upfront registration effort

### 3.3 Option 3: Web Scraping

**Entry Point:** `https://hcpdirectory.cigna.com/web/public/consumer/directory/search`

**Approach:**
1. Use Playwright/Selenium to automate browser
2. Input search criteria (specialty + location)
3. Extract provider data from results
4. Navigate pagination
5. Visit individual provider profiles for details

**Pros:**
- ✅ No registration required
- ✅ Immediate access
- ✅ Can target specific searches

**Cons:**
- ⚠️ Subject to bot detection
- ⚠️ Rate limiting
- ⚠️ UI changes break scraper
- ⚠️ Terms of Service restrictions
- ⚠️ Requires maintenance

**Feasibility for REI NPI Lookup:**
- **MODERATE** - Viable but risky
- Good for small batches
- Not recommended for 1,261 providers without proxies

---

## 4. REI Provider-Specific Findings

### 4.1 Specialty Taxonomy Codes

For searching/filtering REI providers:

| Code | Description | Type |
|------|-------------|------|
| **207VE0102X** | Reproductive Endocrinology | Physician |
| **207RE0101X** | Endocrinology, Diabetes & Metabolism | Related |
| **207VG0400X** | Gynecology | Related |
| **207VF0040X** | Female Pelvic Medicine & Reconstructive Surgery | Related |

### 4.2 Search Strategy for REI Providers

**Cigna Directory Search Terms:**
1. "Reproductive Endocrinology"
2. "Reproductive Endocrinologist"
3. "Infertility Specialist"
4. "Fertility Specialist"
5. "REI" (may not work in all interfaces)

**Geographic Coverage:**
- Cigna has national coverage
- Strong presence in major metropolitan areas
- May have limited rural coverage

### 4.3 Expected Match Rate

Based on Cigna's market presence and fertility benefits:

| Estimate | Value |
|----------|-------|
| **Total Cigna REI providers** | 800-1,500 |
| **Expected match rate** | 40-60% |
| **Potential NPI matches** | 500-750 |

---

## 5. Alternative Data Sources

### 5.1 Cigna For Health Care Professionals Portal

**URL:** `https://www.cigna.com/health-care-providers`

- Provider-facing portal
- May have additional search capabilities
- Requires provider credentials for full access

### 5.2 Cigna Developer Portal

**URL:** `https://developer.cigna.com/`

- API documentation
- Sandbox environment
- Registration required

### 5.3 Third-Party Aggregators

| Source | Notes |
|--------|-------|
| **ZocDoc** | Lists Cigna providers, may have NPI |
| **Healthgrades** | Already being scraped, may cross-reference |
| **WebMD** | Provider listings with insurance info |
| **Castle Connolly** | Top doctor listings |

---

## 6. Feasibility Assessment

### 6.1 Go/No-Go Decision Matrix

| Criterion | Score | Notes |
|-----------|-------|-------|
| **Data Availability** | 9/10 | NPI numbers confirmed available |
| **Data Quality** | 8/10 | Structured, standardized data |
| **Access Difficulty** | 6/10 | Multiple options, some require registration |
| **Technical Complexity** | 5/10 | MRF processing or API integration |
| **Legal/Compliance Risk** | 7/10 | Public data, but terms apply |
| **Scalability** | 8/10 | Can handle 1,261 provider lookups |
| **Maintenance Burden** | 7/10 | API preferred over scraping |
| **Cost** | 9/10 | Free access options available |

**Overall Score: 7.4/10 - RECOMMENDED**

### 6.2 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **IP Blocking** | Medium | High | Use proxies, rate limiting |
| **API Changes** | Medium | Medium | Version pinning, monitoring |
| **Terms of Service Violation** | Low | High | Use official APIs when possible |
| **Data Incompleteness** | Medium | Medium | Cross-reference multiple sources |
| **Rate Limiting** | High | Medium | Implement backoff, caching |

---

## 7. Recommended Approach

### 7.1 Primary Recommendation: MRF + API Hybrid

**Phase 1: Machine-Readable Files (Immediate)**
1. Download Cigna MRF table of contents
2. Identify relevant provider network files
3. Download and parse JSON files
4. Filter for REI taxonomy codes
5. Extract NPI + provider details
6. Match against unmatched provider list

**Phase 2: FHIR API (Ongoing)**
1. Register for Cigna Developer Portal
2. Implement OAuth authentication
3. Build FHIR API client
4. Use for real-time lookups and updates
5. Supplement MRF data

**Phase 3: Web Scraping (Fallback)**
1. Implement only if MRF/API insufficient
2. Use Playwright with stealth mode
3. Proxy rotation for scale
4. Respectful rate limiting

### 7.2 Implementation Priority

1. **HIGH:** Evaluate MRF feasibility (file size, processing)
2. **HIGH:** Register for Cigna Developer Portal
3. **MEDIUM:** Build FHIR API integration
4. **LOW:** Implement web scraper as fallback

---

## 8. Next Steps

### Immediate Actions

- [ ] Download and inspect Cigna MRF table of contents
- [ ] Assess file sizes and processing requirements
- [ ] Register for Cigna Developer Portal access
- [ ] Review FHIR API documentation in detail
- [ ] Test API authentication flow

### Technical Spikes

- [ ] MRF file parsing prototype
- [ ] FHIR API sandbox testing
- [ ] Web scraping proof-of-concept (if needed)

### Documentation to Create

- [ ] Cigna Scraper Requirements Document
- [ ] Cigna Scraper Architecture Design
- [ ] Update Master PRD with Cigna integration plan

---

## 9. References

### URLs

- **Provider Directory:** https://hcpdirectory.cigna.com/
- **Machine Readable Files:** https://www.cigna.com/legal/compliance/machine-readable-files
- **Developer Portal:** https://developer.cigna.com/
- **Provider Directory API Docs:** https://developer.cigna.com/docs/service-apis/provider-directory

### Research Sources

1. Cigna Provider Directory Updates (CareValue Blog, 2024)
2. Cigna Developer Sandbox Documentation (HL7 Confluence)
3. Medium Article: "Secure Chat with your insurance data — Cigna APIs" (Dheeraj R Hegde, 2024)
4. CMS Transparency in Coverage Rule documentation

---

## 10. Conclusion

Cigna's provider directory is a **viable and valuable data source** for REI provider NPI enrichment. The availability of NPI numbers, multiple access methods, and comprehensive specialty filters make it well-suited for our needs.

**Key Success Factors:**
1. Prioritize MRF bulk data for initial matching
2. Implement FHIR API for ongoing access
3. Maintain respectful access patterns
4. Cross-reference with existing Healthgrades data

**Expected Outcome:** With proper implementation, Cigna data could provide NPI matches for 40-60% of the 1,261 unmatched REI providers (approximately 500-750 matches).

---

*Report Version: 1.0*  
*Last Updated: May 24, 2026*  
*Next Review: Upon implementation start*
