# REI Provider Directory System - Master Plan

## Goal
Create the most comprehensive, accurate REI (Reproductive Endocrinology & Infertility) provider directory by combining multiple data sources with confidence scoring.

## Current State
- **Primary Database**: rei-provider-scraper/ (1,595 providers, 298 NPIs = 18.7%)
- **Secondary Database**: projects/provider-directory/ (1,575 providers, 236 NPIs)
- **Scattered Scripts**: Multiple locations, inconsistent approaches

## Target State
Single unified system with:
- One database
- Multiple data source modules
- Confidence scoring
- UI for browsing
- Direct API/CLI for power users

---

## Data Sources (Priority Order)

### 1. NPI Registry API (CMS) - PRIMARY
**Status**: ✅ Working (69% success rate in testing)
**File**: `sources/npi_registry.py`
**Confidence**: HIGH
**Rate**: 0.5-1.5s delay between requests
**Expected**: 900+ NPIs from 1,297 unmatched

### 2. Healthgrades - EXISTING
**Status**: ✅ Already scraped (1,595 providers)
**File**: `sources/healthgrades.py`
**Confidence**: MEDIUM-HIGH
**Note**: Base data, needs NPI enrichment

### 3. Cigna FHIR API - PENDING
**Status**: ⚠️ Needs OAuth registration
**File**: `sources/cigna_fhir.py`
**Confidence**: HIGH (when working)
**Blocker**: Developer portal registration
**Expected**: 500-750 matches

### 4. Cigna MRF - PENDING
**Status**: ⚠️ Index parsing issues
**File**: `sources/cigna_mrf.py`
**Confidence**: HIGH (bulk data)
**Blocker**: File format discovery
**Expected**: 500-750 matches

### 5. Cigna Web Scraping - FALLBACK
**Status**: ⚠️ Complex, slow
**File**: `sources/cigna_web.py`
**Confidence**: MEDIUM
**Note**: Use only if API/MRF fail

---

## Project Structure

```
rei-provider-system/
├── data/
│   ├── providers.db              # Single unified database
│   ├── cache/                    # API response cache
│   └── logs/                     # Operation logs
├── sources/                      # Data source modules
│   ├── __init__.py
│   ├── base.py                   # Base class for all sources
│   ├── npi_registry.py          # CMS NPI Registry API
│   ├── healthgrades.py          # Healthgrades scraper
│   ├── cigna_fhir.py            # Cigna FHIR API
│   ├── cigna_mrf.py             # Cigna Machine-Readable Files
│   └── cigna_web.py             # Cigna web scraping fallback
├── enrichment/                   # NPI enrichment pipeline
│   ├── __init__.py
│   ├── matcher.py               # Cross-source matching
│   ├── confidence.py            # Confidence scoring
│   └── merger.py                # Data merging logic
├── api/                          # API layer
│   ├── __init__.py
│   ├── server.py                # FastAPI/Flask server
│   └── routes/
│       ├── providers.py
│       ├── search.py
│       └── admin.py
├── ui/                           # Web UI (optional)
│   ├── static/
│   ├── templates/
│   └── app.py
├── cli/                          # Command-line tools
│   ├── enrich.py                # Run enrichment
│   ├── search.py                # Search providers
│   ├── export.py                # Export data
│   └── stats.py                 # Show statistics
├── tests/
├── docs/                         # Documentation
│   ├── architecture/
│   ├── requirements/
│   └── decisions/
├── config.yaml                   # Configuration
├── requirements.txt
└── README.md
```

---

## Database Schema

```sql
-- Core provider table
CREATE TABLE providers (
    id INTEGER PRIMARY KEY,
    
    -- Identity (from multiple sources)
    npi TEXT UNIQUE,                    -- NPI number (10 digits)
    name TEXT,                          -- Full name
    first_name TEXT,
    last_name TEXT,
    credentials TEXT,                   -- MD, DO, etc.
    
    -- Specialty
    specialty TEXT,                     -- Reproductive Endocrinology
    taxonomy_code TEXT,                 -- 207VE0102X
    
    -- Location
    street TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    fax TEXT,
    
    -- Cigna-specific
    cigna_network_status TEXT,          -- in_network, out_of_network
    cigna_plans TEXT,                   -- JSON array of plans
    cigna_verified_date TEXT,
    
    -- Data source tracking
    source_priority INTEGER,            -- 1=Healthgrades, 2=NPI Registry, etc.
    
    -- Timestamps
    created_at TEXT,
    updated_at TEXT
);

-- Data sources tracking
CREATE TABLE provider_sources (
    id INTEGER PRIMARY KEY,
    provider_id INTEGER,
    source_name TEXT,                   -- healthgrades, npi_registry, cigna_fhir, etc.
    source_id TEXT,                     -- ID in source system
    source_url TEXT,
    raw_data TEXT,                      -- JSON blob
    confidence_score REAL,              -- 0.0 to 1.0
    match_type TEXT,                    -- exact, probable, fuzzy
    first_seen TEXT,
    last_verified TEXT,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- Confidence scores
CREATE TABLE provider_confidence (
    provider_id INTEGER PRIMARY KEY,
    overall_score REAL,                 -- Weighted average
    npi_confidence REAL,                -- How sure about NPI
    address_confidence REAL,
    phone_confidence REAL,
    specialty_confidence REAL,
    sources_count INTEGER,              -- Number of confirming sources
    last_calculated TEXT,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- Enrichment runs
CREATE TABLE enrichment_runs (
    id INTEGER PRIMARY KEY,
    source_name TEXT,
    started_at TEXT,
    completed_at TEXT,
    providers_processed INTEGER,
    providers_matched INTEGER,
    npis_found INTEGER,
    status TEXT                         -- running, completed, failed
);
```

---

## Confidence Scoring System

### Source Weights
| Source | Weight | Notes |
|--------|--------|-------|
| NPI Registry API | 1.0 | Official CMS source |
| Cigna FHIR API | 0.95 | Official payer data |
| Cigna MRF | 0.95 | Official bulk data |
| Healthgrades | 0.85 | Commercial directory |
| Cigna Web | 0.75 | Scraped data |

### Match Type Multipliers
| Match Type | Multiplier |
|------------|------------|
| NPI exact match | 1.0 |
| Name + State + Zip | 0.95 |
| Name + State + City | 0.90 |
| Name + State only | 0.80 |
| Fuzzy name match | 0.60-0.80 |

### Confidence Levels
| Score | Level | Action |
|-------|-------|--------|
| 0.95-1.0 | CERTAIN | Use as primary source |
| 0.85-0.94 | HIGH | Use with verification |
| 0.70-0.84 | MEDIUM | Flag for review |
| 0.50-0.69 | LOW | Manual verification needed |
| <0.50 | UNCERTAIN | Do not use |

---

## Implementation Phases

### Phase 1: Consolidation (Today)
- [ ] Merge databases into single structure
- [ ] Move all scripts to unified project
- [ ] Create base source class
- [ ] Set up logging and monitoring

### Phase 2: NPI Registry Enrichment (Today)
- [ ] Run NPI Registry API on all 1,297 unmatched
- [ ] Expected: 900+ new NPIs
- [ ] Calculate confidence scores

### Phase 3: Cigna Integration (This Week)
- [ ] Register for Cigna Developer Portal
- [ ] Implement FHIR API client
- [ ] Fix MRF downloader
- [ ] Run both, merge results

### Phase 4: UI & API (Next Week)
- [ ] Build REST API
- [ ] Create web UI
- [ ] Add search/filter
- [ ] Export functionality

### Phase 5: Continuous Enrichment (Ongoing)
- [ ] Weekly NPI Registry updates
- [ ] Monthly Cigna updates
- [ ] Confidence score recalculation
- [ ] Data quality monitoring

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Total REI providers | 1,595 | 2,000+ (with Cigna) |
| NPI coverage | 18.7% | 95%+ |
| Cigna network coverage | 0% | 100% of Cigna REI |
| Confidence >0.85 | 18.7% | 90%+ |
| Data sources per provider | 1 | 3+ |

---

## Next Actions

1. **Consolidate project structure** (me, now)
2. **Run NPI Registry enrichment** (me, today)
3. **Register Cigna Developer Portal** (you, this week)
4. **Implement Cigna FHIR** (me, once creds available)
5. **Build UI** (me, next week)

