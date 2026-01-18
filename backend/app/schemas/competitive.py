"""Pydantic schemas for competitive analysis."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class CompetitiveAnalysisCreate(BaseModel):
    """Schema for creating a new competitive analysis batch."""
    urls: List[str] = Field(
        ...,
        description="List of competitor URLs to analyze",
        min_length=2,
        max_length=5
    )
    labels: Optional[List[str]] = Field(
        None,
        description="Optional labels for each URL (e.g., 'Competitor A', 'Our Site')"
    )
    name: Optional[str] = Field(
        None,
        description="Optional name for this competitive analysis",
        max_length=255
    )


class CompetitiveURLStatus(BaseModel):
    """Schema for individual URL status in a batch."""
    url: str
    label: Optional[str] = None
    status: str
    progress: int = Field(..., ge=0, le=100)
    request_id: UUID
    is_primary: bool = False
    order_index: int

    class Config:
        from_attributes = True


class CompetitiveBatchResponse(BaseModel):
    """Schema for competitive analysis batch status response."""
    id: UUID
    name: Optional[str] = None
    status: str
    progress: int = Field(..., ge=0, le=100)
    total_urls: int
    completed_count: int
    failed_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    urls: List[CompetitiveURLStatus] = []

    class Config:
        from_attributes = True


class RankingEntry(BaseModel):
    """Schema for a single competitor ranking entry."""
    url: str
    score: float
    rank: int
    delta_from_leader: Optional[float] = None
    delta_from_average: Optional[float] = None


class ComparisonMetrics(BaseModel):
    """Schema for comparison metrics (SEO or AEO)."""
    rankings: List[RankingEntry]
    average_score: float
    leader: RankingEntry
    laggard: RankingEntry


class MarketLeader(BaseModel):
    """Schema for market leader identification."""
    seo: Dict[str, Any]  # {url, score}
    aeo: Dict[str, Any]  # {url, score}


class MarketAverage(BaseModel):
    """Schema for market averages."""
    seo: float
    aeo: float


class CompetitiveInsight(BaseModel):
    """Schema for a single competitive insight."""
    category: str  # 'insight', 'opportunity', 'threat'
    content: str
    priority: Optional[str] = 'medium'  # 'critical', 'high', 'medium', 'low'


class ComparisonResponse(BaseModel):
    """Schema for comparison-only response."""
    seo_rankings: List[RankingEntry]
    aeo_rankings: List[RankingEntry]
    market_leader: Dict[str, Any]
    market_average: Dict[str, Any]
    insights: str  # AI-generated narrative
    opportunities: List[str]
    threats: List[str]

    class Config:
        from_attributes = True


class CompetitiveResultResponse(BaseModel):
    """Schema for complete competitive analysis results."""
    batch: CompetitiveBatchResponse
    individual_results: List[Dict[str, Any]]  # List of AnalysisResultResponse
    comparison: ComparisonResponse

    class Config:
        from_attributes = True


class BatchProgress(BaseModel):
    """Schema for WebSocket progress updates."""
    batch_id: UUID
    progress: int = Field(..., ge=0, le=100)
    status: str
    current_step: str
    completed_count: int
    total_urls: int
    individual_statuses: Dict[str, Dict[str, Any]]  # {url: {status, progress}}
