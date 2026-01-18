"""Pydantic schemas for analysis requests and responses."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AnalysisCreate(BaseModel):
    """Schema for creating a new analysis request."""
    url: str = Field(..., description="URL to analyze", min_length=1, max_length=2048)


class AnalysisResponse(BaseModel):
    """Schema for analysis request status response."""
    id: UUID
    url: str
    status: str
    progress: int = Field(..., ge=0, le=100)
    current_step: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class SEOMetrics(BaseModel):
    """Schema for SEO metrics."""
    meta_tags: Dict[str, Any]
    headings: Dict[str, List[str]]
    load_time: float
    mobile_friendly: bool
    ssl_enabled: bool
    structured_data: List[Dict[str, Any]]


class AEOMetrics(BaseModel):
    """Schema for AEO (AI Engine Optimization) metrics."""
    what_it_does: str
    products_services: str
    target_audience: str
    unique_value: str
    clarity_score: int
    overall_impression: str


class Recommendation(BaseModel):
    """Schema for a single recommendation."""
    category: str  # 'seo' or 'aeo'
    priority: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'


class AnalysisResultResponse(BaseModel):
    """Schema for complete analysis results."""
    id: UUID
    request_id: UUID
    url: str
    seo_score: float
    seo_metrics: Dict[str, Any]
    aeo_score: float
    aeo_metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    analysis_duration: float
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    environment: str
