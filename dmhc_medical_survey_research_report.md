# DMHC Medical Survey Reports - Research Findings & Download Plan

## Executive Summary

The DMHC (California Department of Managed Health Care) medical survey reports are **actual PDF documents** that are publicly available, but accessing them in bulk presents significant technical challenges due to Akamai EdgeSuite protection blocking automated access.

---

## What Are Medical Survey Reports?

### Content
Medical survey reports are comprehensive PDF documents containing:
- **Routine Surveys**: Conducted once every 3 years for each licensed health plan
- **Focused Surveys**: Targeted investigations (e.g., MHPAEA - Mental Health Parity and Addiction Equity Act)
- **Follow-Up Surveys**: Conducted within 18 months if deficiencies are found
- **Behavioral Health Surveys**: Specific to mental health and substance use disorder services
- **Non-Routine Surveys**: Investigative surveys conducted as needed

### Report Structure
Each report typically includes:
- Executive summary of findings
- Detailed compliance review
- Deficiencies identified
- Plan's corrective actions
- Appendices with reviewed files and documentation

---

## File Naming Convention

Based on discovered URLs, the pattern is:
```
https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/{PLAN_ID}_{SURVEY_TYPE}_{DESCRIPTION}_{DATE}.pdf
```

### Components:
- **PLAN_ID**: 3-digit numeric code (e.g., 055, 126, 303, 348)
- **SURVEY_TYPE**:
  - `r` = Routine survey
  - `nr` = Non-routine survey
- **DESCRIPTION**:
  - `full service` = Full service health plan
  - `behavioral` = Behavioral health only
  - `full service-behavioral health` = Combined
  - `dental` = Dental plan
  - `MHPAEA` = Mental Health Parity focused survey
  - `follow up` = Follow-up survey
- **DATE**: MMDDYY format

### Examples Found:
- `055_r_full service_022525.pdf` (Kaiser - Routine, Full Service, Feb 25, 2025)
- `055_nr_full service_022525.pdf` (Kaiser - Non-routine, Feb 25, 2025)
- `126_r_MHPAEA_071818.pdf` (UHC - MHPAEA focused, July 18, 2018)
- `303_r_dental_072125.pdf` (Anthem Blue Cross - Dental, July 21, 2025)
- `348_r_full service_040419.pdf` (Unknown plan - Full Service, April 4, 2019)

---

## Scale of Available Reports

### Health Plans
- **98 full-service health plans** licensed by DMHC (as of 2024)
- Plus specialty plans (dental, vision, behavioral health only)
- Total estimated: **100-120+ licensed plans**

### Survey Frequency
- Routine surveys: Every 3 years per plan
- Follow-up surveys: As needed (within 18 months of deficiencies)
- Focused surveys: As needed for specific compliance issues
- Historical data: Reports dating back to at least 2011

### Estimated Total Reports
- With 100+ plans and surveys every 3 years, plus follow-ups and focused surveys
- **Estimated 300-500+ individual PDF reports** available

---

## Access Methods

### Method 1: Web Interface (Manual)
**URL**: `https://www.dmhc.ca.gov/LicensingReporting/HealthPlanComplianceMedicalSurvey/ViewMedicalSurveyReports.aspx`

**Process**:
1. Select health plan from dropdown menu
2. View list of available documents for that plan
3. Click individual PDF links to download

**Obstacles**:
- Requires manual interaction for each plan
- No bulk download option
- Time-consuming for 100+ plans

### Method 2: Direct PDF URLs (Automated - BLOCKED)
**Base URL**: `https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/`

**Status**: ❌ **BLOCKED by Akamai EdgeSuite**

**Error**: `Access Denied - Reference #18.4718d017...`

The website uses Akamai's Web Application Firewall (WAF) which:
- Blocks automated requests (curl, wget, scripts)
- Requires browser-like headers and cookies
- May require JavaScript execution
- Implements rate limiting and bot detection

### Method 3: Public Records Act Request
**URL**: `https://www.dmhc.ca.gov/Resources/RequestforPublicRecords.aspx`

**Process**:
1. Submit formal Public Records Act request
2. Specify: "All medical survey reports for all licensed health plans"
3. DMHC has 10 days to respond (may extend for large requests)
4. May incur fees for reproduction

**Advantages**:
- Legal right to access
- Can request bulk data
- No technical barriers

**Disadvantages**:
- Processing time (weeks to months)
- Potential fees
- May receive files on physical media or via secure portal

### Method 4: Browser Automation (Selenium/Playwright)
**Approach**: Use headless browser to simulate human interaction

**Requirements**:
- Selenium, Playwright, or Puppeteer
- Proper browser headers and cookies
- Rate limiting to avoid detection
- CAPTCHA solving (if triggered)

**Challenges**:
- Akamai may still detect and block
- Requires sophisticated anti-detection measures
- Time-consuming to implement
- May violate Terms of Service

---

## Why Previous Attempts Got Complaint Forms

The confusion likely arose because:
1. **Different URL paths**:
   - Medical surveys: `/desktopmodules/dmhc/medsurveys/surveys/`
   - Complaint forms: Different section of the website

2. **The ViewMedicalSurveyReports.aspx page** requires:
   - JavaScript to populate the dropdown
   - POST requests to retrieve document lists
   - Session cookies

3. **Direct PDF access** was attempted but blocked by WAF

---

## Recommended Approach

### Option 1: Public Records Act Request (RECOMMENDED)
**Best for**: Comprehensive, legal, bulk access

**Steps**:
1. Submit PRA request via: `https://www.dmhc.ca.gov/Resources/RequestforPublicRecords.aspx`
2. Request: "All medical survey reports (routine, focused, follow-up, and behavioral health) for all DMHC-licensed health plans from 2020 to present"
3. Specify preferred format: PDF files via secure download link or cloud storage
4. Be prepared for potential fees ($0.10-$0.25 per page, but may be waived for public interest)
5. Follow up if no response within 10 business days

**Timeline**: 2-6 weeks

### Option 2: Browser Automation with Human Oversight
**Best for**: Faster turnaround, technical teams

**Steps**:
1. Use Playwright or Selenium with stealth plugins
2. Implement:
   - Real browser headers
   - Cookie persistence
   - Random delays between requests
   - User-agent rotation
3. Navigate to ViewMedicalSurveyReports.aspx
4. Extract all health plan IDs from dropdown
5. For each plan:
   - Select plan from dropdown
   - Parse document list
   - Download each PDF (may need to handle new tabs/downloads)
6. Store with metadata (plan name, survey type, date)

**Timeline**: 1-2 weeks development + 1-2 days execution

### Option 3: Manual Download with Organized Approach
**Best for**: Small-scale needs, immediate results

**Steps**:
1. Access `ViewMedicalSurveyReports.aspx` in browser
2. Systematically select each health plan
3. Download available PDFs
4. Organize by plan ID and date

**Timeline**: 2-3 days of manual work

---

## Technical Requirements for Automation

If pursuing browser automation:

```python
# Key requirements for successful scraping
- Playwright or Selenium with stealth mode
- Realistic browser fingerprint
- Proxy rotation (residential IPs preferred)
- Request throttling (5-10 seconds between requests)
- Cookie jar persistence
- User-agent rotation
- Headless browser detection evasion
```

**Anti-Detection Libraries**:
- `playwright-stealth`
- `selenium-stealth`
- Puppeteer with `puppeteer-extra-plugin-stealth`

---

## Data Organization Recommendations

Once obtained, organize reports as:
```
dmhc_medical_surveys/
├── by_plan/
│   ├── 055_kaiser/
│   │   ├── 055_r_full_service_20250225.pdf
│   │   ├── 055_nr_full_service_20250225.pdf
│   │   └── ...
│   ├── 126_uhc/
│   └── ...
├── by_type/
│   ├── routine/
│   ├── non_routine/
│   ├── follow_up/
│   ├── behavioral/
│   └── MHPAEA/
└── metadata.json
```

---

## Key Findings Summary

| Aspect | Finding |
|--------|---------|
| **Are reports available as PDFs?** | ✅ Yes, actual PDF documents |
| **Do they require authentication?** | ❌ No, publicly available |
| **Are they in a different format?** | ❌ No, standard PDFs |
| **What's the correct download mechanism?** | Web interface or direct URL (but blocked by WAF) |
| **How many reports exist?** | 300-500+ across 100+ health plans |
| **How far back do they go?** | At least to 2011 |
| **Can they be bulk downloaded?** | ⚠️ Only via PRA request or sophisticated automation |

---

## Next Steps

1. **Immediate**: Submit Public Records Act request for comprehensive access
2. **Parallel**: Attempt browser automation with proper anti-detection measures
3. **Fallback**: Manual download for priority health plans

---

## Contact Information

**DMHC Public Records Request**:
- URL: https://www.dmhc.ca.gov/Resources/RequestforPublicRecords.aspx
- Email: Available through the form
- Phone: 1-888-466-2219 (Help Center)

**Public Records Act Guidelines**:
- PDF: https://www.dmhc.ca.gov/Portals/0/AbouttheDMHC/RequestingInformation/praguidelines.pdf
