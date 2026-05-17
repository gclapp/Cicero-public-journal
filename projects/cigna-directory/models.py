"""Data models for Cigna provider data."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Address(BaseModel):
    """Provider address."""
    street: str
    city: str
    state: str
    zip: str
    suite: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [self.street]
        if self.suite:
            parts.append(f"Suite {self.suite}")
        parts.append(f"{self.city}, {self.state} {self.zip}")
        return ", ".join(parts)


class Provider(BaseModel):
    """Healthcare provider from Cigna directory."""
    
    # Identification
    provider_id: Optional[str] = Field(None, description="Cigna's internal provider ID")
    npi: Optional[str] = Field(None, description="National Provider Identifier")
    
    # Basic info
    name: str = Field(..., description="Full provider name")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    credentials: Optional[str] = None  # MD, DO, NP, etc.
    
    # Professional
    specialties: List[str] = Field(default_factory=list)
    sub_specialties: List[str] = Field(default_factory=list)
    
    # Location
    address: Optional[Address] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    
    # Practice details
    accepting_new_patients: Optional[bool] = None
    languages: List[str] = Field(default_factory=list)
    
    # Additional info
    gender: Optional[str] = None
    years_in_practice: Optional[int] = None
    education: List[str] = Field(default_factory=list)
    hospital_affiliations: List[str] = Field(default_factory=list)
    
    # Insurance
    plans_accepted: List[str] = Field(default_factory=list)
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.now)
    search_zip: Optional[str] = None
    search_radius: Optional[int] = None
    search_specialty: Optional[str] = None
    
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
    accepting_new_patients: Optional[bool] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    per_page: int = Field(25, ge=1, le=100)


class SearchResult(BaseModel):
    """Result of a provider search."""
    
    criteria: SearchCriteria
    providers: List[Provider]
    total_count: Optional[int] = None
    page_count: Optional[int] = None
    has_more: bool = False
    scraped_at: datetime = Field(default_factory=datetime.now)
