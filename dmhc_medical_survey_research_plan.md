# DMHC Medical Survey Reports - Research Findings & Download Plan

## Executive Summary

The previous attempt downloaded **complaint forms** instead of **medical survey reports**. This document explains the difference and provides a concrete plan to access the actual medical survey reports.

---

## What Are Medical Survey Reports?

### Definition
Medical survey reports are **official compliance audit reports** conducted by the DMHC (Department of Managed Health Care) Office of Plan Monitoring, Division of Plan Surveys. These are NOT complaint forms.

### Report Types
1. **Routine Surveys** - Conducted every 3 years for each licensed plan
2. **Focused Surveys** - Special investigations (e.g., MHPAEA - Mental Health Parity and Addiction Equity Act)
3. **Follow-up Surveys** - Re-inspection after deficiencies found
4. **Non-Routine Surveys** - For-cause investigations

### Survey Sub-Types
- **Full Service** - Comprehensive health plans
- **Behavioral Health** - Mental health and substance use disorder services
- **MHPAEA** - Mental Health Parity and Addiction Equity Act compliance
- **Provider Directory** - Network adequacy surveys

---

## File Naming Convention

### Pattern Identified
```
[PLAN_ID]_[r|nr]_[SURVEY_TYPE]_[DATE].pdf
```

### Examples Found
| File | Plan | Type | Date |
|------|------|------|------|
| `055_r_full service_021121.pdf` | Kaiser | Routine Full Service | 02/11/2021 |
| `055_r_MHPAEA_070218.pdf` | Kaiser | MHPAEA Survey | 07/02/2018 |
| `126_r_MHPAEA_071818.pdf` | UnitedHealthcare | MHPAEA Survey | 07/18/2018 |
| `322_r_full service_040419.pdf` | Molina | Routine Full Service | 04/04/2019 |
| `348_r_full service_040419.pdf` | Unknown | Routine Full Service | 04/04/2019 |
| `486_r_MHPAEA_031218.pdf` | MediExcel | MHPAEA Survey | 03/12/2018 |

### Legend
- `_r_` = Routine survey
- `_nr_` = Non-routine survey
- `full service` = Comprehensive health plan survey
- `behavioral` or `behavioral health` = Mental health focus
- `MHPAEA` = Mental Health Parity and Addiction Equity Act
- `follow up` = Follow-up inspection

---

## URL Structure

### Base URL for Survey Files
```
https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/[FILENAME].pdf
```

### Health Plan Pages
```
https://www.dmhc.ca.gov/LicensingReporting/HealthPlanComplianceMedicalSurvey/ViewMedicalSurveyReports/hmoPlan/[PLAN_ID].aspx
```

### Known Plan IDs
| Plan ID | Health Plan |
|---------|-------------|
| 055 | Kaiser Foundation Health Plan, Inc. |
| 126 | UnitedHealthcare of California |
| 303 | Blue Cross of California |
| 322 | Molina Health Care of California |
| 348 | Unknown (found in search results) |
| 486 | MediExcel Health Plan |

---

## What Medical Survey Reports Contain

### Report Sections
1. **Executive Summary** - Key findings and deficiencies
2. **Survey Methodology** - How the audit was conducted
3. **Standards Reviewed** - Specific Knox-Keene Act requirements checked
4. **Findings** - Detailed compliance/deficiency findings
5. **Plan's Response** - Health plan's corrective action plan
6. **Exhibits** - Supporting documentation

### Specific Content Examples
- Utilization Management (UM) program reviews
- Grievance and appeal file reviews
- Behavioral health access investigations
- Provider network adequacy
- Timely access to care compliance
- Mental health parity compliance

---

## Access Requirements & Obstacles

### Current Obstacles
1. **Website Blocks Automated Access** - DMHC website returns 403 Forbidden to automated requests
2. **Browser Required** - The ViewMedicalSurveyReports.aspx page requires JavaScript/interactive browser
3. **Dynamic Content** - Health plan list is loaded dynamically via dropdown
4. **No Public API** - No documented API for accessing reports programmatically

### Access Methods

#### Option 1: Manual Browser Download (Immediate)
1. Visit: https://www.dmhc.ca.gov/LicensingReporting/HealthPlanComplianceMedicalSurvey/ViewMedicalSurveyReports.aspx
2. Select health plan from dropdown
3. Click individual report links to download PDFs

#### Option 2: Direct URL Access (If Pattern Known)
- If plan ID and filename pattern are known, direct PDF URLs work:
  - Example: `https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/055_r_full%20service_021121.pdf`

#### Option 3: Browser Automation (Recommended for Bulk)
- Use Selenium/Playwright to:
  1. Load the ViewMedicalSurveyReports.aspx page
  2. Extract all health plan options from dropdown
  3. Iterate through each plan
  4. Extract all report links
  5. Download each PDF

---

## Recommended Approach

### Phase 1: Discovery (1-2 hours)
1. **Use browser automation** to load `ViewMedicalSurveyReports.aspx`
2. **Extract all health plan IDs** from the dropdown menu
3. **Map plan IDs to health plan names**
4. **Document the complete list** of available plans

### Phase 2: Inventory (2-4 hours)
1. For each health plan page (`hmoPlan/[ID].aspx`):
   - Extract all available report links
   - Document report types, dates, and filenames
   - Create a master inventory spreadsheet

### Phase 3: Bulk Download (4-8 hours)
1. Use the direct PDF URLs from inventory
2. Download all reports with proper error handling
3. Organize files by health plan and date
4. Verify completeness

### Tools Needed
- Python with Selenium or Playwright
- requests library for PDF downloads
- pandas for inventory management
- Proper error handling and retry logic

---

## Key Differences: Complaint Forms vs. Medical Survey Reports

| Aspect | Complaint Forms | Medical Survey Reports |
|--------|-----------------|------------------------|
| **Purpose** | Consumer complaints | Official compliance audits |
| **Source** | Public submissions | DMHC Office of Plan Monitoring |
| **Content** | Individual grievances | Systemic compliance findings |
| **Frequency** | Ongoing | Every 3 years (routine) |
| **Format** | Forms/templates | Detailed PDF reports |
| **Value** | Consumer assistance | Regulatory compliance intelligence |

---

## Estimated Volume

Based on research:
- **~40-50 licensed health plans** in California
- **3+ reports per plan** (routine, follow-up, focused)
- **Reports dating back to ~2012**
- **Estimated total: 200-500 PDF reports**

---

## Next Steps

1. **Approve browser automation approach** for discovery
2. **Set up Python environment** with Selenium/Playwright
3. **Execute discovery phase** to map all plan IDs
4. **Create inventory** of all available reports
5. **Execute bulk download** with proper organization

---

## Files Referenced

### Direct PDF URLs (Confirmed Working)
- `https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/126_r_MHPAEA_071818.pdf`
- `https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/348_r_full%20service_040419.pdf`
- `https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/322_r_full%20service%20follow%20up_021721.pdf`
- `https://www.dmhc.ca.gov/desktopmodules/dmhc/medsurveys/surveys/055_r_MHPAEA_070218.pdf`

### Health Plan Pages
- `https://www.dmhc.ca.gov/LicensingReporting/HealthPlanComplianceMedicalSurvey/ViewMedicalSurveyReports/hmoPlan/055.aspx` (Kaiser)
- `https://www.dmhc.ca.gov/LicensingReporting/HealthPlanComplianceMedicalSurvey/ViewMedicalSurveyReports/hmoPlan/322.aspx` (Molina)

---

*Research completed: 2026-05-30*
