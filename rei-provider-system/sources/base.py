"""Base class for all data sources."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class ProviderData:
    """Standardized provider data structure."""
    npi: Optional[str]
    name: str
    first_name: Optional[str]
    last_name: Optional[str]
    credentials: Optional[str]
    specialty: Optional[str]
    taxonomy_code: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    phone: Optional[str]
    fax: Optional[str]
    
    # Source tracking
    source_name: str
    source_id: Optional[str]
    source_url: Optional[str]
    raw_data: Optional[Dict]
    
    # Confidence
    confidence_score: float = 0.0
    match_type: str = "unknown"  # exact, probable, fuzzy
    
    # Timestamps
    fetched_at: str = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now().isoformat()


class DataSource(ABC):
    """Abstract base class for all data sources."""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight  # For confidence scoring
        self.stats = {
            'searched': 0,
            'found': 0,
            'errors': 0
        }
    
    @abstractmethod
    def search_by_name(self, name: str, state: str, city: Optional[str] = None) -> List[ProviderData]:
        """Search for providers by name and location."""
        pass
    
    @abstractmethod
    def search_by_npi(self, npi: str) -> Optional[ProviderData]:
        """Search for provider by NPI."""
        pass
    
    def calculate_confidence(self, match_score: float) -> float:
        """Calculate confidence score based on source weight and match quality."""
        return min(1.0, match_score * self.weight)
