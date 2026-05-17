"""Abstract base class for all provider directory sources."""

from abc import ABC, abstractmethod
from typing import Optional

from models import SearchCriteria, SearchResult, SourceInfo


class ProviderSource(ABC):
    """Abstract base class for provider directory sources."""
    
    def __init__(self):
        self._authenticated = False
    
    @property
    @abstractmethod
    def info(self) -> SourceInfo:
        """Return information about this source."""
        pass
    
    @abstractmethod
    async def authenticate(self, **kwargs) -> bool:
        """Authenticate with the source. Returns success status."""
        pass
    
    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> SearchResult:
        """Search for providers."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source is accessible and working."""
        pass
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Clean up resources. Override if needed."""
        pass
