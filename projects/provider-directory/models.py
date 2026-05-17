"""Shared data models for all provider directory sources."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


SourceType = Literal["cigna-api", "cigna-scraper", "healthgrades", "healthgrades_v2"]


class Address(BaseModel):
    """Provider address."""
    street: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    suite: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [self.street]
        if self.suite:
            parts.append(f"Suite {self.suite}")
        parts.append(f"{self.city}, {self.state} {self.zip}")
        return ", ".join(parts)


class Provider(BaseModel):
    """Healthcare provider from any source."""
    
    # Identification
    provider_id: Optional[str] = Field(None, description="Source's internal provider ID")
    npi: Optional[str] = Field(None, description="National Provider Identifier")
    
    # Basic info
    name: str = Field(..., description="Full provider name")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    credentials: Optional[str] = None  # MD, DO, NP, etc.
    gender: Optional[str] = None
    
    # Professional
    specialties: List[str] = Field(default_factory=list)
    sub_specialties: List[str] = Field(default_factory=list)
    years_in_practice: Optional[int] = None
    
    # Location
    address: Optional[Address] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    
    # Practice details
    accepting_new_patients: Optional[bool] = None
    languages: List[str] = Field(default_factory=list)
    
    # Additional info
    education: List[str] = Field(default_factory=list)
    hospital_affiliations: List[str] = Field(default_factory=list)
    
    # Insurance
    plans_accepted: List[str] = Field(default_factory=list)
    
    # Source metadata
    source: SourceType = Field(..., description="Which data source found this provider")
    source_url: Optional[str] = None
    
    # Search context
    search_zip: Optional[str] = None
    search_radius: Optional[int] = None
    search_specialty: Optional[str] = None
    
    # Timestamps
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchCriteria(BaseModel):
    """Search parameters for provider lookup."""
    
    zip_code: str
    radius_miles: int = Field(10, ge=1, le=100)
    specialty: Optional[str] = None
    provider_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    accepting_new_patients_only: bool = False
    
    # Pagination
    page: int = Field(1, ge=1)
    per_page: int = Field(25, ge=1, le=100)
    max_pages: int = Field(10, ge=1, le=100)  # Safety limit - increased to 100


class SearchResult(BaseModel):
    """Result of a provider search."""
    
    source: SourceType
    criteria: SearchCriteria
    providers: List[Provider] = Field(default_factory=list)
    total_count: Optional[int] = None
    page_count: Optional[int] = None
    has_more: bool = False
    search_time_ms: Optional[int] = None
    error: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class SourceInfo(BaseModel):
    """Information about a data source."""
    
    id: SourceType
    name: str
    description: str
    status: Literal["active", "beta", "pending", "disabled"]
    requires_auth: bool
    auth_type: Optional[str] = None  # oauth, api_key, credentials
    rate_limit: Optional[str] = None
    reliability: Literal["high", "medium", "low"]
    notes: Optional[str] = None
