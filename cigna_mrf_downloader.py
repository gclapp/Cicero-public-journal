#!/usr/bin/env python3
"""
Cigna MRF (Machine-Readable Files) Downloader and NPI Matcher

This script downloads Cigna's Machine-Readable Files, extracts REI providers,
and matches them against our database to find missing NPIs.

Usage:
    python cigna_mrf_downloader.py --discover          # Discover available files
    python cigna_mrf_downloader.py --download --parse  # Download and parse files
    python cigna_mrf_downloader.py --test-small        # Test with a small sample
"""

import argparse
import gzip
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse

import httpx
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
REI_TAXONOMY_CODES = ['207VE0102X', '207RE0101X', '207VG0400X']
CIGNA_MRF_BASE_URL = "https://www.cigna.com/legal/compliance/machine-readable-files"
CIGNA_MRF_LOOKUP_URL = "https://www.cigna.com/static/mrf/latest.json"
DATA_DIR = Path("data/cigna_mrf")
CHUNK_SIZE = 8192  # 8KB chunks for streaming


@dataclass
class MRFFile:
    """Represents an MRF file entry"""
    url: str
    file_name: str
    plan_name: str
    description: str
    last_updated: str
    file_size: Optional[str] = None
    downloaded: bool = False
    parsed: bool = False
    local_path: Optional[Path] = None
    priority: int = 0


@dataclass
class CignaProvider:
    """Represents a provider from Cigna MRF"""
    npi: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    taxonomy_codes: List[str] = field(default_factory=list)
    specialties: List[str] = field(default_factory=list)
    raw_data: Dict = field(default_factory=dict)


@dataclass
class MatchResult:
    """Represents a match between Cigna provider and our database"""
    cigna_provider: CignaProvider
    matched_provider_id: str
    match_score: float
    match_type: str  # 'npi_exact', 'name_state', 'fuzzy'
    confidence: str  # 'high', 'medium', 'low'


class MRFIndexParser:
    """Parse Cigna MRF table of contents/index files"""
    
    def __init__(self):
        self.client = httpx.Client(follow_redirects=True, timeout=60.0)
    
    def fetch_index(self) -> List[MRFFile]:
        """
        Fetch and parse Cigna MRF index.
        
        Cigna's MRF structure:
        1. Get latest.json from /static/mrf/latest.json
        2. That contains a TOC file URL
        3. The TOC file contains links to actual in-network rates files
        """
        logger.info(f"Fetching MRF index from {CIGNA_MRF_LOOKUP_URL}")
        
        try:
            # Step 1: Get the latest.json which contains the TOC URL
            response = self.client.get(CIGNA_MRF_LOOKUP_URL)
            response.raise_for_status()
            latest_data = response.json()
            
            # Step 2: Extract TOC file URL from latest.json
            toc_url = None
            if 'mrfs' in latest_data and len(latest_data['mrfs']) > 0:
                mrf_entry = latest_data['mrfs'][0]
                if 'files' in mrf_entry and len(mrf_entry['files']) > 0:
                    toc_url = mrf_entry['files'][0]['url']
                    logger.info(f"Found TOC URL: {toc_url[:100]}...")
            
            if not toc_url:
                logger.error("Could not find TOC URL in latest.json")
                return []
            
            # Step 3: Download and parse the TOC file
            return self._fetch_toc_file(toc_url)
            
        except Exception as e:
            logger.error(f"Failed to fetch MRF index: {e}")
            return []
    
    def _fetch_toc_file(self, toc_url: str) -> List[MRFFile]:
        """Fetch and parse the Table of Contents file"""
        logger.info(f"Fetching TOC file...")
        
        try:
            response = self.client.get(toc_url)
            response.raise_for_status()
            toc_data = response.json()
            
            files = []
            
            # Parse reporting_structure which contains the actual file links
            if 'reporting_structure' in toc_data:
                for structure in toc_data['reporting_structure']:
                    # Get plan info
                    plan_name = "Unknown"
                    if 'reporting_plans' in structure and len(structure['reporting_plans']) > 0:
                        plan_name = structure['reporting_plans'][0].get('plan_name', 'Unknown')
                    
                    # Get in-network files
                    if 'in_network_files' in structure:
                        for file_entry in structure['in_network_files']:
                            description = file_entry.get('description', '')
                            location = file_entry.get('location', '')
                            
                            if location:
                                # Extract file name from URL
                                parsed = urlparse(location)
                                file_name = os.path.basename(parsed.path)
                                if not file_name:
                                    file_name = description.replace('/', '_').replace(' ', '_') + '.json.gz'
                                
                                files.append(MRFFile(
                                    url=location,
                                    file_name=file_name,
                                    plan_name=plan_name,
                                    description=description,
                                    last_updated=datetime.now().isoformat()
                                ))
            
            logger.info(f"Found {len(files)} MRF files in TOC")
            return files
            
        except Exception as e:
            logger.error(f"Failed to fetch/parse TOC file: {e}")
            return []
    
    def filter_relevant_files(self, files: List[MRFFile]) -> List[MRFFile]:
        """
        Filter files most likely to contain REI providers.
        
        Strategy:
        1. Prioritize national PPO files (broadest coverage)
        2. Look for files with larger provider networks
        3. Skip supplemental/limited networks initially
        """
        relevant = []
        
        priority_keywords = [
            'national-ppo',
            'national_ppo',
            'sar-1',
            'open-access',
            'oap',
            'ppo',
            'cigna-health-life-insurance-company'
        ]
        
        skip_keywords = [
            'supplemental',
            'limited',
            'dental',
            'vision',
            'behavioral',
            'pharmacy'
        ]
        
        for file in files:
            file_lower = file.file_name.lower()
            desc_lower = file.description.lower()
            combined = file_lower + ' ' + desc_lower
            
            # Skip supplemental/limited networks
            if any(kw in combined for kw in skip_keywords):
                continue
            
            # Prioritize national PPO files
            priority = sum(1 for kw in priority_keywords if kw in combined)
            file.priority = priority
            
            if priority > 0:
                relevant.append(file)
        
        # Sort by priority (highest first)
        relevant.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Filtered to {len(relevant)} relevant files")
        for i, f in enumerate(relevant[:10]):
            logger.info(f"  {i+1}. {f.description[:60]}... (priority: {f.priority})")
        
        return relevant


class MRFDownloader:
    """Download MRF files with resume capability and progress tracking"""
    
    def __init__(self, download_dir: Path = DATA_DIR):
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(follow_redirects=True, timeout=300.0)
        
        # Track download state
        self.state_file = self.download_dir / "download_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load download state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_state(self):
        """Save download state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def download_file(self, mrf_file: MRFFile, force: bool = False) -> Optional[Path]:
        """
        Download a single MRF file with resume support.
        
        Args:
            mrf_file: MRFFile object with URL
            force: If True, re-download even if file exists
            
        Returns:
            Path to downloaded file or None if failed
        """
        local_path = self.download_dir / mrf_file.file_name
        mrf_file.local_path = local_path
        
        # Check if already downloaded
        if local_path.exists() and not force:
            if self._verify_file(local_path, mrf_file):
                logger.info(f"File already downloaded: {mrf_file.file_name}")
                mrf_file.downloaded = True
                return local_path
        
        logger.info(f"Downloading: {mrf_file.file_name}")
        logger.info(f"  From: {mrf_file.url[:80]}...")
        
        try:
            # Stream download with progress bar
            with self.client.stream('GET', mrf_file.url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                
                with open(local_path, 'wb') as f:
                    with tqdm(
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        desc=mrf_file.file_name[:30]
                    ) as pbar:
                        for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            # Verify download
            if self._verify_file(local_path, mrf_file):
                mrf_file.downloaded = True
                self.state[mrf_file.file_name] = {
                    'downloaded': True,
                    'timestamp': datetime.now().isoformat(),
                    'size': local_path.stat().st_size
                }
                self._save_state()
                
                logger.info(f"Successfully downloaded: {mrf_file.file_name}")
                return local_path
            else:
                logger.error(f"File verification failed: {mrf_file.file_name}")
                local_path.unlink(missing_ok=True)
                return None
                
        except Exception as e:
            logger.error(f"Download failed for {mrf_file.file_name}: {e}")
            local_path.unlink(missing_ok=True)
            return None
    
    def _verify_file(self, file_path: Path, mrf_file: MRFFile) -> bool:
        """Verify downloaded file integrity"""
        if not file_path.exists():
            return False
        
        if file_path.stat().st_size == 0:
            return False
        
        # Check if it's a valid gzip file (if .gz extension)
        if file_path.suffix == '.gz' or '.gz' in file_path.name:
            try:
                with gzip.open(file_path, 'rb') as f:
                    # Try to read first few bytes
                    f.read(1024)
                return True
            except Exception as e:
                logger.warning(f"File verification failed (not valid gzip): {e}")
                # Might be a zip file
                return True
        
        return True


class MRFStreamingParser:
    """Stream-parse large MRF JSON files to extract REI providers"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self.providers_extracted = 0
        self.rei_providers_found = 0
    
    def parse_providers(self, file_path: Path) -> Iterator[CignaProvider]:
        """
        Stream-parse MRF file and yield providers.
        
        Uses a memory-efficient approach suitable for multi-GB files.
        """
        logger.info(f"Parsing MRF file: {file_path}")
        
        # Determine file type
        is_gz = file_path.suffix == '.gz' or '.gz' in file_path.name
        is_zip = file_path.suffix == '.zip'
        
        try:
            if is_gz:
                yield from self._parse_gz_file(file_path)
            elif is_zip:
                yield from self._parse_zip_file(file_path)
            else:
                yield from self._parse_json_file(file_path)
                
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    def _parse_gz_file(self, file_path: Path) -> Iterator[CignaProvider]:
        """Parse a gzip-compressed JSON file"""
        with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            yield from self._extract_providers_from_data(data)
    
    def _parse_zip_file(self, file_path: Path) -> Iterator[CignaProvider]:
        """Parse a zip file containing JSON"""
        import zipfile
        
        with zipfile.ZipFile(file_path, 'r') as zf:
            # Find JSON files in the archive
            json_files = [name for name in zf.namelist() if name.endswith('.json')]
            
            for json_file in json_files:
                logger.info(f"Extracting from zip: {json_file}")
                with zf.open(json_file) as f:
                    data = json.load(f)
                    yield from self._extract_providers_from_data(data)
    
    def _parse_json_file(self, file_path: Path) -> Iterator[CignaProvider]:
        """Parse a plain JSON file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            yield from self._extract_providers_from_data(data)
    
    def _extract_providers_from_data(self, data: Dict) -> Iterator[CignaProvider]:
        """Extract providers from parsed JSON data"""
        # MRF files have provider_references at the top level
        provider_refs = data.get('provider_references', [])
        
        if not provider_refs:
            # Some files might have different structure
            logger.warning("No provider_references found in file")
            return
        
        logger.info(f"Found {len(provider_refs)} provider references")
        
        for ref in provider_refs:
            self.providers_extracted += 1
            
            provider = self._parse_provider_reference(ref)
            
            if provider and self._is_rei_provider(provider):
                self.rei_providers_found += 1
                yield provider
            
            # Progress update every 1000 providers
            if self.providers_extracted % 1000 == 0:
                logger.info(f"Processed {self.providers_extracted} providers, "
                          f"found {self.rei_providers_found} REI")
    
    def _parse_provider_reference(self, ref: Dict) -> Optional[CignaProvider]:
        """Parse a single provider reference into a CignaProvider object"""
        try:
            # Get NPI
            npi_list = ref.get('npi', [])
            if not npi_list:
                return None
            
            npi = str(npi_list[0]) if npi_list else None
            if not npi:
                return None
            
            # Get name
            first_name = ref.get('first_name', '')
            last_name = ref.get('last_name', '')
            
            # Some files use different field names
            if not first_name:
                first_name = ref.get('provider_first_name', '')
            if not last_name:
                last_name = ref.get('provider_last_name', '')
            
            name = f"{first_name} {last_name}".strip()
            
            # Get taxonomy codes
            taxonomy_codes = []
            specialties = []
            
            taxonomy_list = ref.get('taxonomy', [])
            for tax in taxonomy_list:
                code = tax.get('code', '')
                desc = tax.get('desc', '')
                if code:
                    taxonomy_codes.append(code)
                if desc:
                    specialties.append(desc)
            
            # Get location/address
            address = None
            city = None
            state = None
            zip_code = None
            phone = None
            
            locations = ref.get('location', [])
            if locations:
                loc = locations[0]
                address = loc.get('address', '')
                city = loc.get('city', '')
                state = loc.get('state', '')
                zip_code = loc.get('zip', '')
                phone = loc.get('phone', '')
            
            return CignaProvider(
                npi=npi,
                name=name,
                first_name=first_name or None,
                last_name=last_name or None,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                phone=phone,
                taxonomy_codes=taxonomy_codes,
                specialties=specialties,
                raw_data=ref
            )
            
        except Exception as e:
            logger.warning(f"Error parsing provider reference: {e}")
            return None
    
    def _is_rei_provider(self, provider: CignaProvider) -> bool:
        """Check if provider is a REI specialist based on taxonomy codes"""
        for code in provider.taxonomy_codes:
            if code in REI_TAXONOMY_CODES:
                return True
        
        # Also check specialties for REI-related terms
        rei_terms = ['reproductive', 'endocrinology', 'fertility', 'infertility']
        for specialty in provider.specialties:
            specialty_lower = specialty.lower()
            if any(term in specialty_lower for term in rei_terms):
                return True
        
        return False


class NPIMatcher:
    """Match Cigna providers against our database"""
    
    def __init__(self, db_path: str = "providers.db"):
        self.db_path = db_path
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.conn = None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def find_matches(self, provider: CignaProvider) -> List[MatchResult]:
        """Find matching providers in our database"""
        matches = []
        
        if not self.conn:
            return matches
        
        # Try NPI exact match first
        if provider.npi:
            cursor = self.conn.execute(
                "SELECT * FROM providers WHERE npi = ?",
                (provider.npi,)
            )
            row = cursor.fetchone()
            if row:
                matches.append(MatchResult(
                    cigna_provider=provider,
                    matched_provider_id=row['id'],
                    match_score=1.0,
                    match_type='npi_exact',
                    confidence='high'
                ))
                return matches
        
        # Try name + state match
        if provider.last_name and provider.state:
            cursor = self.conn.execute(
                """SELECT * FROM providers 
                   WHERE LOWER(last_name) = LOWER(?) AND state = ?""",
                (provider.last_name, provider.state)
            )
            rows = cursor.fetchall()
            for row in rows:
                matches.append(MatchResult(
                    cigna_provider=provider,
                    matched_provider_id=row['id'],
                    match_score=0.8,
                    match_type='name_state',
                    confidence='medium'
                ))
        
        return matches
    
    def update_provider_npi(self, match: MatchResult) -> bool:
        """Update our database with NPI from Cigna"""
        if not self.conn:
            return False
        
        try:
            self.conn.execute(
                "UPDATE providers SET npi = ? WHERE id = ?",
                (match.cigna_provider.npi, match.matched_provider_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update provider NPI: {e}")
            return False


class CignaMRFProcessor:
    """Main processor that orchestrates the download-parse-match pipeline"""
    
    def __init__(self):
        self.index_parser = MRFIndexParser()
        self.downloader = MRFDownloader()
        self.parser = MRFStreamingParser()
        self.matcher = None
        
        self.stats = {
            'files_discovered': 0,
            'files_downloaded': 0,
            'providers_extracted': 0,
            'rei_providers_found': 0,
            'matches_found': 0,
            'npis_updated': 0
        }
    
    def discover_files(self) -> List[MRFFile]:
        """Discover available MRF files from Cigna"""
        logger.info("=" * 60)
        logger.info("DISCOVERING CIGNA MRF FILES")
        logger.info("=" * 60)
        
        all_files = self.index_parser.fetch_index()
        self.stats['files_discovered'] = len(all_files)
        
        relevant_files = self.index_parser.filter_relevant_files(all_files)
        
        return relevant_files
    
    def download_files(self, files: List[MRFFile], max_files: Optional[int] = None) -> List[Path]:
        """Download MRF files"""
        logger.info("=" * 60)
        logger.info("DOWNLOADING MRF FILES")
        logger.info("=" * 60)
        
        downloaded = []
        
        files_to_download = files[:max_files] if max_files else files
        
        for mrf_file in files_to_download:
            path = self.downloader.download_file(mrf_file)
            if path:
                downloaded.append(path)
                self.stats['files_downloaded'] += 1
        
        logger.info(f"Downloaded {len(downloaded)} files")
        return downloaded
    
    def parse_and_match(self, file_paths: List[Path]):
        """Parse downloaded files and match providers"""
        logger.info("=" * 60)
        logger.info("PARSING AND MATCHING PROVIDERS")
        logger.info("=" * 60)
        
        self.matcher = NPIMatcher()
        
        for file_path in file_paths:
            self._process_file(file_path)
        
        self.matcher.close()
    
    def _process_file(self, file_path: Path):
        """Process a single MRF file"""
        logger.info(f"Processing: {file_path.name}")
        
        try:
            for provider in self.parser.parse_providers(file_path):
                self.stats['providers_extracted'] += 1
                self.stats['rei_providers_found'] += 1
                
                # Find matches
                matches = self.matcher.find_matches(provider)
                
                if matches:
                    self.stats['matches_found'] += 1
                    
                    # Update with best match
                    best_match = matches[0]
                    if best_match.confidence in ('high', 'medium'):
                        if self.matcher.update_provider_npi(best_match):
                            self.stats['npis_updated'] += 1
                            logger.info(f"Updated NPI for provider: {provider.name} "
                                      f"-> {provider.npi}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def run_full_pipeline(self, max_files: Optional[int] = None):
        """Run the complete pipeline"""
        # Step 1: Discover files
        files = self.discover_files()
        
        if not files:
            logger.error("No MRF files found!")
            return
        
        # Step 2: Download files
        downloaded = self.download_files(files, max_files=max_files)
        
        if not downloaded:
            logger.error("No files downloaded!")
            return
        
        # Step 3: Parse and match
        self.parse_and_match(downloaded)
        
        # Step 4: Print summary
        self._print_summary()
    
    def run_test_with_small_file(self):
        """Test the pipeline with a small MRF file"""
        logger.info("=" * 60)
        logger.info("RUNNING TEST WITH SMALL FILE")
        logger.info("=" * 60)
        
        # Create a small test MRF file
        test_data = {
            "provider_references": [
                {
                    "npi": ["1234567890"],
                    "first_name": "John",
                    "last_name": "Smith",
                    "taxonomy": [{"code": "207VE0102X", "desc": "Reproductive Endocrinology"}],
                    "location": [{"address": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"}]
                },
                {
                    "npi": ["9876543210"],
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "taxonomy": [{"code": "207RE0101X", "desc": "Endocrinology"}],
                    "location": [{"address": "456 Oak Ave", "city": "Los Angeles", "state": "CA", "zip": "90001"}]
                },
                {
                    "npi": ["5555555555"],
                    "first_name": "Bob",
                    "last_name": "Johnson",
                    "taxonomy": [{"code": "207Q00000X", "desc": "Family Medicine"}],
                    "location": [{"address": "789 Pine St", "city": "Chicago", "state": "IL", "zip": "60601"}]
                }
            ]
        }
        
        # Create test file
        test_file = DATA_DIR / "test_mrf.json.gz"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with gzip.open(test_file, 'wt') as f:
            json.dump(test_data, f)
        
        logger.info(f"Created test file: {test_file}")
        
        # Parse it
        logger.info("Parsing test file...")
        providers = list(self.parser.parse_providers(test_file))
        
        logger.info(f"Found {len(providers)} REI providers:")
        for p in providers:
            logger.info(f"  - {p.name} (NPI: {p.npi})")
            logger.info(f"    Taxonomy: {p.taxonomy_codes}")
            logger.info(f"    Location: {p.city}, {p.state}")
        
        # Verify we found the right providers
        assert len(providers) == 2, f"Expected 2 REI providers, found {len(providers)}"
        assert any(p.npi == "1234567890" for p in providers), "Missing John Smith"
        assert any(p.npi == "9876543210" for p in providers), "Missing Jane Doe"
        
        logger.info("✅ Test passed!")
        
        # Clean up
        test_file.unlink()
    
    def _print_summary(self):
        """Print processing summary"""
        logger.info("=" * 60)
        logger.info("CIGNA MRF PROCESSING SUMMARY")
        logger.info("=" * 60)
        for key, value in self.stats.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Cigna MRF Downloader and NPI Matcher"
    )
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Discover available MRF files from Cigna'
    )
    parser.add_argument(
        '--download',
        action='store_true',
        help='Download MRF files from Cigna'
    )
    parser.add_argument(
        '--parse',
        action='store_true',
        help='Parse downloaded MRF files'
    )
    parser.add_argument(
        '--match',
        action='store_true',
        help='Match providers against database'
    )
    parser.add_argument(
        '--full-pipeline',
        action='store_true',
        help='Run complete download-parse-match pipeline'
    )
    parser.add_argument(
        '--test-small',
        action='store_true',
        help='Test with a small sample file'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=1,
        help='Maximum number of files to process (default: 1)'
    )
    
    args = parser.parse_args()
    
    processor = CignaMRFProcessor()
    
    if args.test_small:
        processor.run_test_with_small_file()
    elif args.full_pipeline:
        processor.run_full_pipeline(max_files=args.max_files)
    elif args.discover:
        files = processor.discover_files()
        print(f"\nDiscovered {len(files)} relevant MRF files:")
        for i, f in enumerate(files[:20], 1):
            print(f"  {i}. {f.description[:60]}...")
            print(f"     URL: {f.url[:70]}...")
    elif args.download:
        files = processor.discover_files()
        processor.download_files(files, max_files=args.max_files)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
