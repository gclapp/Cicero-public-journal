

---

## 10. MRF Implementation Details

### 10.1 MRF Downloader (`cigna_mrf_downloader.py`)

The MRF downloader is the primary component for extracting NPIs from Cigna's Machine-Readable Files.

#### Key Classes

**MRFIndexParser**
```python
class MRFIndexParser:
    """Parse Cigna MRF table of contents/index files"""
    
    def fetch_index(self) -> List[MRFFile]:
        """Fetch and parse Cigna MRF index from HTML page"""
        
    def filter_relevant_files(self, files: List[MRFFile]) -> List[MRFFile]:
        """Filter to files most likely to contain REI providers"""
```

**MRFDownloader**
```python
class MRFDownloader:
    """Download MRF files with resume capability"""
    
    def download_file(self, mrf_file: MRFFile, force: bool = False) -> Optional[Path]:
        """Download a single MRF file with progress tracking"""
        
    def _verify_file(self, file_path: Path, mrf_file: MRFFile) -> bool:
        """Verify downloaded gzip file integrity"""
```

**MRFStreamingParser**
```python
class MRFStreamingParser:
    """Stream-parse large MRF JSON files"""
    
    REI_TAXONOMY_CODES = ['207VE0102X', '207RE0101X', '207VG0400X']
    
    def parse_providers(self, file_path: Path) -> Iterator[CignaProvider]:
        """Yield REI providers from MRF file"""
        
    def _is_rei_provider(self, provider: CignaProvider) -> bool:
        """Check if provider has REI taxonomy codes"""
```

**NPIMatcher**
```python
class NPIMatcher:
    """Match Cigna providers against our database"""
    
    def find_matches(self, cigna_provider: CignaProvider) -> List[MatchResult]:
        """Find matching providers using NPI or name+state"""
        
    def update_provider_npi(self, match: MatchResult) -> bool:
        """Update database with matched NPI"""
```

#### Usage

```bash
# Run full pipeline
python cigna_mrf_downloader.py --full-pipeline

# Test with small sample
python cigna_mrf_downloader.py --test-small

# Process limited files
python cigna_mrf_downloader.py --full-pipeline --max-files 5
```

### 10.2 MRF Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    MRF PROCESSING PIPELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                           │
│  │ Cigna MRF    │                                           │
│  │ Index Page   │                                           │
│  └──────┬───────┘                                           │
│         │ 1. Parse HTML for file URLs                       │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Filter Files │───▶│ Download     │───▶│ Stream Parse │  │
│  │ (REI likely) │    │ (resume)     │    │ (extract)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                   │         │
│                                                   ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Update DB    │◀───│ Match Engine │◀───│ REI Filter   │  │
│  │ (NPIs)       │    │ (fuzzy)      │    │ (taxonomy)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 File Structure

```
rei-provider-scraper/
├── cigna_mrf_downloader.py      # Main implementation
├── cigna_mrf_requirements.txt   # Dependencies
├── test_cigna_mrf.py            # Unit tests
├── data/cigna_mrf/              # Downloaded files
│   ├── download_state.json      # Resume state
│   └── *.json.gz                # MRF files
└── logs/cigna_mrf.log           # Processing logs
```

### 10.4 Testing

Run unit tests:
```bash
python test_cigna_mrf.py
```

Test components:
- MRFStreamingParser: Parse test file with sample providers
- NPIMatcher: Test name matching and database updates
- MatchResult: Verify confidence scoring

---

## 11. Conclusion

This architecture provides a robust, scalable foundation for integrating Cigna provider data into our REI Provider Scraper system. The multi-source approach with fallback strategies ensures high availability and maximizes match rates while maintaining compliance and data quality.

**Implementation Status:**
- ✅ MRF Downloader: Implemented (`cigna_mrf_downloader.py`)
- ✅ NPI Matcher: Implemented with fuzzy matching
- ✅ ADR-003: Documented
- ✅ Architecture: Updated with MRF section
- ⏳ Testing: Unit tests created, integration test pending
- ⏳ Deployment: Ready for staging

**Next Steps:**
1. Run test with small MRF file
2. Validate match rates on sample data
3. Deploy to production for full processing
4. Monitor and optimize based on results

---

*Document Version: 1.1*  
*Last Updated: May 24, 2026*
