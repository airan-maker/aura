"""Database models for competitive analysis."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, Index, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base
from app.models.analysis import AnalysisStatus


class CompetitiveAnalysisBatch(Base):
    """Competitive analysis batch containing multiple competitor URLs."""

    __tablename__ = "competitive_analysis_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))  # Optional user-provided name

    # Status and progress
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0)  # 0-100 aggregate progress

    # Counts
    total_urls = Column(Integer, nullable=False)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Error tracking
    error_message = Column(Text)

    # Relationships
    urls = relationship(
        "CompetitiveAnalysisURL",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="CompetitiveAnalysisURL.order_index"
    )
    comparison_result = relationship(
        "ComparisonResult",
        back_populates="batch",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_batch_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<CompetitiveAnalysisBatch(id={self.id}, name={self.name}, status={self.status}, total_urls={self.total_urls})>"


class CompetitiveAnalysisURL(Base):
    """Links individual analysis requests to competitive batches."""

    __tablename__ = "competitive_analysis_urls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("competitive_analysis_batches.id"), nullable=False)
    request_id = Column(UUID(as_uuid=True), ForeignKey("analysis_requests.id"), nullable=False, unique=True)

    # URL metadata
    url_label = Column(String(255))  # e.g., "Competitor 1", "Our Site"
    is_primary = Column(Boolean, default=False)  # Mark user's own site
    order_index = Column(Integer, default=0)  # Display order

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    batch = relationship("CompetitiveAnalysisBatch", back_populates="urls")
    analysis_request = relationship("AnalysisRequest")

    __table_args__ = (
        Index('idx_batch_urls', 'batch_id', 'order_index'),
    )

    def __repr__(self):
        return f"<CompetitiveAnalysisURL(id={self.id}, batch_id={self.batch_id}, request_id={self.request_id})>"


class ComparisonResult(Base):
    """Stores aggregated comparison insights and benchmarking data."""

    __tablename__ = "comparison_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("competitive_analysis_batches.id"), unique=True, nullable=False)

    # Comparative metrics (JSON for flexibility)
    seo_comparison = Column(JSON)  # {rankings: [{url, score, rank}], average, leader}
    aeo_comparison = Column(JSON)  # {rankings: [{url, score, rank}], average, leader}

    # Benchmarking
    market_leader = Column(JSON)  # {seo: {url, score}, aeo: {url, score}}
    market_average = Column(JSON)  # {seo: avg_score, aeo: avg_score}

    # AI-generated insights
    competitive_insights = Column(JSON)  # AI analysis of competitive landscape
    opportunities = Column(JSON)  # Identified gaps/opportunities (array)
    threats = Column(JSON)  # Competitive threats (array)

    # Performance
    comparison_duration = Column(Float)  # Duration in seconds

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship
    batch = relationship("CompetitiveAnalysisBatch", back_populates="comparison_result")

    def __repr__(self):
        return f"<ComparisonResult(id={self.id}, batch_id={self.batch_id})>"
