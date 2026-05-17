"""Provider directory data sources."""

from sources.cigna_api import CignaAPISource
from sources.cigna_scraper import CignaScraperSource
from sources.healthgrades import HealthgradesSource
from sources.base import ProviderSource

__all__ = [
    'ProviderSource',
    'CignaAPISource',
    'CignaScraperSource',
    'HealthgradesSource',
]

# Registry of available sources
SOURCE_REGISTRY = {
    'cigna-api': CignaAPISource,
    'cigna-scraper': CignaScraperSource,
    'healthgrades': HealthgradesSource,
}


def get_source(source_id: str, **kwargs) -> ProviderSource:
    """Get a source instance by ID."""
    if source_id not in SOURCE_REGISTRY:
        raise ValueError(f"Unknown source: {source_id}. Available: {list(SOURCE_REGISTRY.keys())}")
    
    source_class = SOURCE_REGISTRY[source_id]
    return source_class(**kwargs)


def list_sources():
    """List all available sources with their info."""
    sources = []
    for source_id, source_class in SOURCE_REGISTRY.items():
        # Create temporary instance to get info
        try:
            instance = source_class()
            sources.append(instance.info)
        except Exception as e:
            # If we can't instantiate, create basic info
            from models import SourceInfo
            sources.append(SourceInfo(
                id=source_id,
                name=source_id,
                description="Error loading source info",
                status="disabled",
                requires_auth=True,
                reliability="low",
                notes=f"Error: {e}"
            ))
    return sources
