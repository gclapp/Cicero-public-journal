# DMHC Financial Statement Download Status

## Date: 2026-05-30

## Task Summary
Download financial statement PDFs from California Department of Managed Health Care (DMHC) for major health plans.

## Target Health Plans
1. Blue Cross of California (933 0303)
2. Blue Shield of California Promise Health Plan (933 0326)
3. Kaiser Foundation Health Plan, Inc. (933 0055)
4. Health Net of California, Inc. (933 0300)
5. Aetna Health of California Inc. (933 0176)
6. Blue Cross of California Partnership Plan, Inc. (933 0415)
7. Health Net Community Solutions, Inc. (933 0426)
8. Aetna Better Health of California Inc. (933 0521)

## Target Document Types
- Annual DMHC Financial Reporting Form (Statement Type 1)
- Annual Independent Auditor's Report (Statement Type 6)

## Technical Challenges Encountered

### 1. Akamai Protection
The DMHC website (wpso.dmhc.ca.gov) is protected by Akamai CDN/EdgeSuite. Direct access returns:
```
Access Denied
Reference #18.e7263e17.1780106309.5a3a3471
```

### 2. ScraperAPI Key Issues
The provided ScraperAPI key (`9ff51b…9983`) is returning "Unauthorized request" errors:
- Tested with multiple URL formats
- Tested against httpbin.org/ip (also fails)
- Account endpoint returns: "Sorry, your current plan does not include access to this feature"

**Conclusion**: The API key appears to be invalid, revoked, or the account has been suspended/deactivated.

## Attempted Solutions

### Approach 1: Direct Requests via ScraperAPI
- Used Python requests library with proper URL encoding
- Result: 401 Unauthorized

### Approach 2: Curl via Subprocess
- Used curl command-line tool
- Result: 401 Unauthorized

### Approach 3: Browser Automation
- Attempted to use OpenClaw browser tool
- Result: Browser unavailable (gateway restart required)

## What Would Be Needed to Complete

1. **Valid ScraperAPI Key**: A working API key with ultra_premium access for Akamai-protected sites
2. **Alternative Proxy Service**: Such as ScrapingBee, ScrapingAnt, or Oxylabs
3. **Residential Proxy**: Direct proxy access to bypass Akamai
4. **Browser Automation**: Selenium/Playwright with residential proxy

## Website Structure Analysis (from cached data)

The DMHC search page uses ASP.NET WebForms with:
- `__VIEWSTATE` - Form state
- `__EVENTVALIDATION` - Security validation
- `__VIEWSTATEGENERATOR` - ViewState generator
- Dropdown controls:
  - `ctl00$ctl00$MainContent$MainContent$ddlHPType` - Health Plan Type
  - `ctl00$ctl00$MainContent$MainContent$ddlHP` - Health Plan
  - `ctl00$ctl00$MainContent$MainContent$ddlStatementType` - Statement Type
- Search button: `ctl00$ctl00$MainContent$MainContent$btnSearch`

## PDF Download URLs
Once search results are obtained, PDFs are available at:
`https://wpso.dmhc.ca.gov/fe/document/{document_id}.pdf`

## Scripts Created
1. `download_dmhc_financials.py` - Initial attempt with requests
2. `download_dmhc_v2.py` - Improved session handling
3. `download_dmhc_v3.py` - Fixed URL encoding
4. `download_dmhc_v4.py` - Curl-based approach

All scripts are ready to run once a valid API key is provided.

## Next Steps
1. Obtain a valid ScraperAPI key or alternative proxy service
2. Re-run the download script
3. Verify PDF downloads and update database
