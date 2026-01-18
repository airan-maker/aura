# Pydantic Schemas

from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisResultResponse,
    SEOMetrics,
    AEOMetrics,
    Recommendation,
    HealthResponse
)

from app.schemas.competitive import (
    CompetitiveAnalysisCreate,
    CompetitiveBatchResponse,
    CompetitiveURLStatus,
    ComparisonResponse,
    CompetitiveResultResponse,
    RankingEntry,
    ComparisonMetrics,
    MarketLeader,
    MarketAverage,
    CompetitiveInsight,
    BatchProgress
)

__all__ = [
    # Analysis schemas
    "AnalysisCreate",
    "AnalysisResponse",
    "AnalysisResultResponse",
    "SEOMetrics",
    "AEOMetrics",
    "Recommendation",
    "HealthResponse",
    # Competitive schemas
    "CompetitiveAnalysisCreate",
    "CompetitiveBatchResponse",
    "CompetitiveURLStatus",
    "ComparisonResponse",
    "CompetitiveResultResponse",
    "RankingEntry",
    "ComparisonMetrics",
    "MarketLeader",
    "MarketAverage",
    "CompetitiveInsight",
    "BatchProgress",
]
