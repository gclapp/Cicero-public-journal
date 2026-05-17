"""Data persistence for scraped provider data."""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models import Provider


class ProviderStorage:
    """Handles storage of provider data in multiple formats."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize SQLite
        self.db_path = self.data_dir / "providers.db"
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id TEXT,
                    npi TEXT,
                    name TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    credentials TEXT,
                    specialties TEXT,
                    sub_specialties TEXT,
                    gender TEXT,
                    years_in_practice INTEGER,
                    street TEXT,
                    city TEXT,
                    state TEXT,
                    zip TEXT,
                    suite TEXT,
                    phone TEXT,
                    fax TEXT,
                    accepting_new_patients INTEGER,
                    languages TEXT,
                    education TEXT,
                    hospital_affiliations TEXT,
                    plans_accepted TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    search_zip TEXT,
                    search_radius INTEGER,
                    search_specialty TEXT,
                    scraped_at TEXT,
                    UNIQUE(name, street, city, state, source)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON providers(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_zip ON providers(search_zip)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_specialty ON providers(search_specialty)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON providers(name)")
    
    def save_providers(self, providers: List[Provider]) -> int:
        """Save providers to SQLite. Returns count saved."""
        saved = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for provider in providers:
                try:
                    conn.execute("""
                        INSERT INTO providers (
                            provider_id, npi, name, first_name, last_name, credentials,
                            specialties, sub_specialties, gender, years_in_practice,
                            street, city, state, zip, suite, phone, fax,
                            accepting_new_patients, languages, education,
                            hospital_affiliations, plans_accepted, source, source_url,
                            search_zip, search_radius, search_specialty, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(name, street, city, state, source) DO UPDATE SET
                            scraped_at = excluded.scraped_at,
                            phone = excluded.phone,
                            specialties = excluded.specialties
                    """, (
                        provider.provider_id,
                        provider.npi,
                        provider.name,
                        provider.first_name,
                        provider.last_name,
                        provider.credentials,
                        json.dumps(provider.specialties),
                        json.dumps(provider.sub_specialties),
                        provider.gender,
                        provider.years_in_practice,
                        provider.address.street if provider.address else None,
                        provider.address.city if provider.address else None,
                        provider.address.state if provider.address else None,
                        provider.address.zip if provider.address else None,
                        provider.address.suite if provider.address else None,
                        provider.phone,
                        provider.fax,
                        1 if provider.accepting_new_patients else 0 if provider.accepting_new_patients is not None else None,
                        json.dumps(provider.languages),
                        json.dumps(provider.education),
                        json.dumps(provider.hospital_affiliations),
                        json.dumps(provider.plans_accepted),
                        provider.source,
                        provider.source_url,
                        provider.search_zip,
                        provider.search_radius,
                        provider.search_specialty,
                        provider.scraped_at.isoformat()
                    ))
                    saved += 1
                except Exception as e:
                    print(f"Error saving provider {provider.name}: {e}")
        
        return saved
    
    def export_to_json(self, filepath: Optional[Path] = None) -> Path:
        """Export all providers to JSON."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.data_dir / f"providers_{timestamp}.json"
        
        providers = self.get_all_providers()
        
        with open(filepath, 'w') as f:
            json.dump([p.model_dump() for p in providers], f, indent=2, default=str)
        
        return filepath
    
    def export_to_csv(self, filepath: Optional[Path] = None) -> Path:
        """Export all providers to CSV."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.data_dir / f"providers_{timestamp}.csv"
        
        providers = self.get_all_providers()
        
        if not providers:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'specialties', 'city', 'state', 'zip', 'phone', 'source'])
            return filepath
        
        rows = []
        for p in providers:
            rows.append({
                'name': p.name,
                'credentials': p.credentials or '',
                'specialties': '; '.join(p.specialties),
                'street': p.address.street if p.address else '',
                'city': p.address.city if p.address else '',
                'state': p.address.state if p.address else '',
                'zip': p.address.zip if p.address else '',
                'phone': p.phone or '',
                'accepting_new_patients': 'Yes' if p.accepting_new_patients else 'No' if p.accepting_new_patients is not None else 'Unknown',
                'languages': '; '.join(p.languages),
                'hospital_affiliations': '; '.join(p.hospital_affiliations),
                'source': p.source,
                'scraped_at': p.scraped_at.isoformat()
            })
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        return filepath
    
    def get_all_providers(self) -> List[Provider]:
        """Retrieve all providers from database."""
        from models import Address
        
        providers = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM providers ORDER BY scraped_at DESC")
            
            for row in cursor.fetchall():
                provider = Provider(
                    provider_id=row['provider_id'],
                    npi=row['npi'],
                    name=row['name'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    credentials=row['credentials'],
                    specialties=json.loads(row['specialties']) if row['specialties'] else [],
                    sub_specialties=json.loads(row['sub_specialties']) if row['sub_specialties'] else [],
                    gender=row['gender'],
                    years_in_practice=row['years_in_practice'],
                    address=Address(
                        street=row['street'] or '',
                        city=row['city'] or '',
                        state=row['state'] or '',
                        zip=row['zip'] or '',
                        suite=row['suite']
                    ) if row['street'] else None,
                    phone=row['phone'],
                    fax=row['fax'],
                    accepting_new_patients=bool(row['accepting_new_patients']) if row['accepting_new_patients'] is not None else None,
                    languages=json.loads(row['languages']) if row['languages'] else [],
                    education=json.loads(row['education']) if row['education'] else [],
                    hospital_affiliations=json.loads(row['hospital_affiliations']) if row['hospital_affiliations'] else [],
                    plans_accepted=json.loads(row['plans_accepted']) if row['plans_accepted'] else [],
                    source=row['source'],
                    source_url=row['source_url'],
                    search_zip=row['search_zip'],
                    search_radius=row['search_radius'],
                    search_specialty=row['search_specialty'],
                    scraped_at=datetime.fromisoformat(row['scraped_at'])
                )
                providers.append(provider)
        
        return providers
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
            
            by_source = conn.execute(
                "SELECT source, COUNT(*) as count FROM providers GROUP BY source"
            ).fetchall()
            
            by_zip = conn.execute(
                "SELECT search_zip, COUNT(*) as count FROM providers WHERE search_zip IS NOT NULL GROUP BY search_zip"
            ).fetchall()
            
            return {
                'total_providers': total,
                'by_source': {row[0]: row[1] for row in by_source},
                'by_zip': {row[0]: row[1] for row in by_zip},
                'database_path': str(self.db_path)
            }
