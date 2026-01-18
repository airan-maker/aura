"""Database models for analysis requests and results."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class AnalysisStatus(enum.Enum):
    """Status of an analysis request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRequest(Base):
    """Analysis request initiated by a user."""

    __tablename__ = "analysis_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False, index=True)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)

    # Relationship
    result = relationship("AnalysisResult", back_populates="request", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisRequest(id={self.id}, url={self.url}, status={self.status})>"


class AnalysisResult(Base):
    """Analysis results including SEO and AEO metrics."""

    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("analysis_requests.id"), unique=True, nullable=False)

    # Crawled data
    page_html = Column(Text)
    page_text = Column(Text)
    screenshot_path = Column(String(512))

    # SEO metrics
    seo_score = Column(Float)  # 0-100
    seo_metrics = Column(JSON)  # Detailed SEO analysis

    # AEO (AI Engine Optimization) metrics
    aeo_score = Column(Float)  # 0-100
    aeo_metrics = Column(JSON)  # Detailed AEO analysis

    # Recommendations
    recommendations = Column(JSON)  # List of actionable recommendations

    # Performance
    analysis_duration = Column(Float)  # Duration in seconds

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship
    request = relationship("AnalysisRequest", back_populates="result")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, seo_score={self.seo_score}, aeo_score={self.aeo_score})>"
