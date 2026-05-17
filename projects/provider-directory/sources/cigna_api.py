"""Cigna Official API source (pending approval)."""

from models import SearchCriteria, SearchResult, SourceInfo, Provider
from sources.base import ProviderSource


class CignaAPISource(ProviderSource):
    """Cigna Provider Directory API - NOT YET AVAILABLE.
    
    Waiting for developer portal approval from:
    https://developer.cigna.com/docs/service-apis/provider-directory
    """
    
    @property
    def info(self) -> SourceInfo:
        return SourceInfo(
            id="cigna-api",
            name="Cigna Provider Directory API",
            description="Official Cigna REST API for provider directory (pending approval)",
            status="pending",
            requires_auth=True,
            auth_type="oauth2",
            rate_limit="TBD",
            reliability="high",
            notes="Applied for access, waiting for approval"
        )
    
    async def authenticate(self, **kwargs) -> bool:
        """Cannot authenticate until API access is granted."""
        print("⚠️  Cigna API not yet available. Waiting for developer portal approval.")
        return False
    
    async def search(self, criteria: SearchCriteria) -> SearchResult:
        """Cannot search until API access is granted."""
        return SearchResult(
            source="cigna-api",
            criteria=criteria,
            providers=[],
            error="Cigna API access pending. Please use 'cigna-scraper' instead."
        )
    
    async def health_check(self) -> bool:
        """Check if API is available."""
        return False
