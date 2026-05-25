# REI Provider System - Implementation Plan

## Current Status (As of May 24, 2026)

### Database
- **Location**: `rei-provider-system/data/providers.db`
- **Total Providers**: 1,595
- **With NPI**: 298 (18.7%)
- **Without NPI**: 1,297 (81.3%)
- **Top States**: CA (218), NY (184), TX (106), FL (104), NJ (90)

### Project Structure (Created)
```
rei-provider-system/
├── data/
│   ├── providers.db          # Main database (copied from rei-provider-scraper)
│   ├── cache/                # API response cache
│   └── logs/                 # Operation logs
├── sources/
│   ├── base.py               # Base data source class
│   └── npi_registry.py       # NPI Registry API (WORKING - 69% success rate)
├── cli/
│   └── stats.py              # Statistics command
└── docs/                     # Documentation (copied)
```

---

## Phase 1: NPI Registry Enrichment (IN PROGRESS)

**Status**: Running now (session: tide-otter)

**Expected Results**:
- Process all 1,297 providers without NPI
- Expected matches: ~900 (69% of 1,297)
- Final NPI coverage: ~1,198 (75%)

**Command Running**:
```bash
cd rei-provider-system && python3 sources/npi_registry.py
```

**Time Estimate**: 30-45 minutes (0.5-1.5s delay per request)

---

## Phase 2: Cigna Integration Plan

### 2A: Cigna FHIR API

**Status**: ⚠️ Blocked - Needs OAuth registration

**Steps**:
1. **You register at**: https://developer.cigna.com/register
2. Provide: Organization name, use case, contact info
3. Wait for approval (1-2 business days)
4. Receive: Client ID, Client Secret
5. I implement OAuth flow in `sources/cigna_fhir.py`

**Expected Results**:
- 500-750 additional matches
- High confidence (0.95 weight)
- Real-time verification

**Implementation**:
```python
# sources/cigna_fhir.py
class CignaFHIRSource(DataSource):
    def __init__(self, client_id, client_secret):
        self.name = "cigna_fhir"
        self.weight = 0.95
        self.oauth_token = self._authenticate(client_id, client_secret)
    
    def search_by_name(self, name, state, city=None):
        # Use FHIR API to search providers
        # Return ProviderData with confidence scores
```

### 2B: Cigna MRF (Machine-Readable Files)

**Status**: ⚠️ Needs debugging

**Steps**:
1. Debug index parsing at https://www.cigna.com/legal/compliance/machine-readable-files
2. Find actual JSON index URL
3. Download provider reference files
4. Parse and filter for REI (taxonomy 207VE0102X)
5. Match against database

**Expected Results**:
- 500-750 additional matches
- Bulk data, no rate limits
- High confidence (0.95 weight)

**Implementation**:
```python
# sources/cigna_mrf.py
class CignaMRFSource(DataSource):
    def __init__(self):
        self.name = "cigna_mrf"
        self.weight = 0.95
        self.base_url = "https://www.cigna.com/legal/compliance/machine-readable-files"
    
    def download_index(self):
        # Find and parse MRF index
        pass
    
    def parse_provider_file(self, file_url):
        # Stream and parse large JSON files
        pass
```

---

## Phase 3: Confidence Scoring & Merging

**File**: `enrichment/confidence.py`

**Algorithm**:
```python
def calculate_provider_confidence(provider_id):
    sources = get_all_sources_for_provider(provider_id)
    
    # Weight by source reliability
    weighted_scores = []
    for source in sources:
        weight = SOURCE_WEIGHTS[source.name]  # 0.75-1.0
        match_quality = MATCH_MULTIPLIERS[source.match_type]  # 0.6-1.0
        weighted_scores.append(weight * match_quality)
    
    # Overall confidence
    overall = max(weighted_scores) if weighted_scores else 0
    
    # Agreement bonus
    if len(sources) >= 3:
        overall *= 1.1  # 10% bonus for multiple sources
    
    return min(1.0, overall)
```

**Source Weights**:
| Source | Weight | Status |
|--------|--------|--------|
| NPI Registry API | 1.00 | ✅ Working |
| Cigna FHIR API | 0.95 | ⚠️ Needs OAuth |
| Cigna MRF | 0.95 | ⚠️ Needs debugging |
| Healthgrades | 0.85 | ✅ Base data |
| Cigna Web | 0.75 | ⚠️ Fallback |

---

## Phase 4: UI & API

### API Endpoints (FastAPI)

```python
# api/routes/providers.py

@router.get("/providers")
def list_providers(
    state: Optional[str] = None,
    has_npi: Optional[bool] = None,
    cigna_network: Optional[bool] = None,
    min_confidence: float = 0.0,
    skip: int = 0,
    limit: int = 100
):
    """List providers with filters."""
    pass

@router.get("/providers/{provider_id}")
def get_provider(provider_id: int):
    """Get detailed provider info with all sources."""
    pass

@router.post("/providers/{provider_id}/verify")
def verify_provider(provider_id: int):
    """Manually verify a provider's data."""
    pass

@router.get("/search")
def search_providers(q: str, state: Optional[str] = None):
    """Search providers by name."""
    pass

@router.get("/stats")
def get_statistics():
    """Get database statistics."""
    pass
```

### Web UI Features

1. **Provider List View**
   - Table with sortable columns
   - Filters: state, NPI status, Cigna network, confidence
   - Export to CSV/Excel

2. **Provider Detail View**
   - All data sources shown
   - Confidence score visualization
   - Map with location
   - Edit/verify buttons

3. **Dashboard**
   - Statistics overview
   - Coverage charts
   - Recent enrichments
   - Data quality alerts

---

## Success Metrics

| Metric | Current | After NPI Registry | After Cigna | Target |
|--------|---------|-------------------|-------------|--------|
| Total Providers | 1,595 | 1,595 | 2,000+ | 2,500+ |
| NPI Coverage | 18.7% | ~75% | ~95% | 98%+ |
| Cigna Network | 0% | 0% | 100% | 100% |
| Avg Confidence | N/A | 0.85 | 0.92 | 0.95+ |
| Data Sources | 1 | 2 | 4+ | 5+ |

---

## Immediate Actions

### For You (This Week):
1. **Register for Cigna Developer Portal**
   - URL: https://developer.cigna.com/register
   - Use case: "Healthcare provider directory research"
   - Once approved, send me Client ID/Secret

### For Me (Today):
1. ✅ **Consolidate project** (DONE)
2. ⏳ **Run NPI Registry enrichment** (IN PROGRESS)
3. **Create confidence scoring module**
4. **Build CLI tools**

### For Me (Next Week):
1. Implement Cigna FHIR (once you have creds)
2. Debug Cigna MRF
3. Build API layer
4. Create web UI

---

## Files Created

| File | Purpose |
|------|---------|
| `rei-provider-system/` | Main project directory |
| `data/providers.db` | Unified database |
| `sources/base.py` | Base data source class |
| `sources/npi_registry.py` | NPI Registry API (WORKING) |
| `cli/stats.py` | Statistics command |
| `IMPLEMENTATION_PLAN.md` | This document |

---

## Next Steps

1. Wait for NPI Registry enrichment to complete (~30 min)
2. Review results
3. You register for Cigna Developer Portal
4. I implement remaining sources
5. Build UI/API

---

*Last Updated: May 24, 2026*
*Status: Phase 1 In Progress*
