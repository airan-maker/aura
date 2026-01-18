"""Competitive analysis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import uuid
import logging

from app.schemas.competitive import (
    CompetitiveAnalysisCreate,
    CompetitiveBatchResponse,
    CompetitiveURLStatus,
    ComparisonResponse,
    CompetitiveResultResponse
)
from app.models.competitive import (
    CompetitiveAnalysisBatch,
    CompetitiveAnalysisURL,
    ComparisonResult
)
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisStatus
from app.database import get_db
from app.workers.competitive_worker_sync import run_competitive_analysis_sync
from app.utils.validators import validate_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/competitive", tags=["competitive"])


# WebSocket Manager for Competitive Analysis
class CompetitiveWebSocketManager:
    """Manages WebSocket connections for competitive analysis real-time updates."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, batch_id: str, websocket: WebSocket):
        """
        Accept a new WebSocket connection.

        Args:
            batch_id: Competitive analysis batch ID
            websocket: WebSocket connection
        """
        await websocket.accept()
        if batch_id not in self.active_connections:
            self.active_connections[batch_id] = []
        self.active_connections[batch_id].append(websocket)
        logger.info(f"WebSocket connected for batch {batch_id}")

    def disconnect(self, batch_id: str, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            batch_id: Competitive analysis batch ID
            websocket: WebSocket connection
        """
        if batch_id in self.active_connections:
            if websocket in self.active_connections[batch_id]:
                self.active_connections[batch_id].remove(websocket)
            if not self.active_connections[batch_id]:
                del self.active_connections[batch_id]
        logger.info(f"WebSocket disconnected for batch {batch_id}")

    async def send_update(self, batch_id: str, data: dict):
        """
        Send update to all connected clients for a batch.

        Args:
            batch_id: Competitive analysis batch ID
            data: Data to send
        """
        if batch_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[batch_id]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket update: {e}")
                    disconnected.append(connection)

            # Clean up disconnected sockets
            for conn in disconnected:
                self.disconnect(batch_id, conn)


# Global WebSocket manager instance
websocket_manager = CompetitiveWebSocketManager()


@router.post("", response_model=CompetitiveBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_competitive_analysis(
    data: CompetitiveAnalysisCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new competitive analysis batch.

    Args:
        data: Competitive analysis creation data (2-5 URLs with optional labels)
        db: Database session

    Returns:
        Created competitive analysis batch with ID and status

    Raises:
        400: If invalid URLs or labels mismatch
    """
    # Validate URLs
    for url in data.urls:
        if not validate_url(url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL format or potentially unsafe URL: {url}"
            )

    # Validate labels length matches URLs if provided
    if data.labels and len(data.labels) != len(data.urls):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Labels count ({len(data.labels)}) must match URLs count ({len(data.urls)})"
        )

    # Create batch record
    batch = CompetitiveAnalysisBatch(
        name=data.name,
        status=AnalysisStatus.PENDING,
        progress=0,
        total_urls=len(data.urls),
        completed_count=0,
        failed_count=0
    )

    db.add(batch)
    await db.flush()  # Get batch ID before creating URLs

    # Create individual analysis requests for each URL
    url_entries = []
    for idx, url in enumerate(data.urls):
        # Create individual analysis request
        analysis_request = AnalysisRequest(
            url=url,
            status=AnalysisStatus.PENDING,
            progress=0
        )
        db.add(analysis_request)
        await db.flush()  # Get request ID

        # Create competitive analysis URL entry
        label = data.labels[idx] if data.labels else None
        url_entry = CompetitiveAnalysisURL(
            batch_id=batch.id,
            request_id=analysis_request.id,
            url_label=label,
            is_primary=(idx == 0),  # First URL is primary by default
            order_index=idx
        )
        db.add(url_entry)
        url_entries.append(url_entry)

    await db.commit()
    await db.refresh(batch)

    logger.info(
        f"Created competitive analysis batch {batch.id} "
        f"with {len(data.urls)} URLs"
    )

    # Submit to background task using synchronous worker
    # This uses ThreadPoolExecutor which returns immediately (non-blocking)
    # and runs in a background thread with synchronous SQLAlchemy (no greenlet issues)
    run_competitive_analysis_sync(
        str(batch.id),
        websocket_manager
    )

    # Build response with URL statuses
    # Refresh batch to get relationships
    await db.refresh(batch, ['urls'])

    url_statuses = []
    for url_entry in batch.urls:
        # Eagerly load the analysis_request relationship
        await db.refresh(url_entry, ['analysis_request'])
        url_statuses.append(CompetitiveURLStatus(
            url=url_entry.analysis_request.url,
            label=url_entry.url_label,
            status=url_entry.analysis_request.status.value,
            progress=url_entry.analysis_request.progress,
            request_id=str(url_entry.request_id),
            is_primary=url_entry.is_primary,
            order_index=url_entry.order_index
        ))

    return CompetitiveBatchResponse(
        id=batch.id,
        name=batch.name,
        status=batch.status.value,
        progress=batch.progress,
        total_urls=batch.total_urls,
        completed_count=batch.completed_count,
        failed_count=batch.failed_count,
        created_at=batch.created_at,
        urls=url_statuses
    )


@router.get("/{batch_id}", response_model=CompetitiveBatchResponse)
async def get_batch_status(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get competitive analysis batch status with individual URL progress.

    Args:
        batch_id: Batch UUID
        db: Database session

    Returns:
        Batch status with individual URL statuses

    Raises:
        404: If batch not found
    """
    # Get batch
    result = await db.execute(
        select(CompetitiveAnalysisBatch).where(
            CompetitiveAnalysisBatch.id == batch_id
        )
    )
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitive analysis batch {batch_id} not found"
        )

    # Get URL entries with analysis requests
    url_result = await db.execute(
        select(CompetitiveAnalysisURL)
        .where(CompetitiveAnalysisURL.batch_id == batch_id)
        .order_by(CompetitiveAnalysisURL.order_index)
    )
    url_entries = url_result.scalars().all()

    # Build URL statuses
    url_statuses = []
    for url_entry in url_entries:
        # Eagerly load the analysis_request relationship
        await db.refresh(url_entry, ['analysis_request'])
        url_statuses.append(CompetitiveURLStatus(
            url=url_entry.analysis_request.url,
            label=url_entry.url_label,
            status=url_entry.analysis_request.status.value,
            progress=url_entry.analysis_request.progress,
            request_id=str(url_entry.request_id),
            is_primary=url_entry.is_primary,
            order_index=url_entry.order_index
        ))

    return CompetitiveBatchResponse(
        id=batch.id,
        name=batch.name,
        status=batch.status.value,
        progress=batch.progress,
        total_urls=batch.total_urls,
        completed_count=batch.completed_count,
        failed_count=batch.failed_count,
        created_at=batch.created_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        error_message=batch.error_message,
        urls=url_statuses
    )


@router.get("/{batch_id}/results", response_model=CompetitiveResultResponse)
async def get_competitive_results(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete competitive analysis results including comparison.

    Args:
        batch_id: Batch UUID
        db: Database session

    Returns:
        Complete results: batch status, individual results, and comparison

    Raises:
        404: If batch or results not found
        400: If analysis not completed
    """
    # Get batch
    batch_result = await db.execute(
        select(CompetitiveAnalysisBatch).where(
            CompetitiveAnalysisBatch.id == batch_id
        )
    )
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitive analysis batch {batch_id} not found"
        )

    # Check if completed
    if batch.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed yet. Current status: {batch.status.value}"
        )

    # Get individual analysis results
    url_entries = await db.execute(
        select(CompetitiveAnalysisURL)
        .where(CompetitiveAnalysisURL.batch_id == batch_id)
        .order_by(CompetitiveAnalysisURL.order_index)
    )
    url_list = url_entries.scalars().all()

    individual_results = []
    for url_entry in url_list:
        # Eagerly load the analysis_request relationship
        await db.refresh(url_entry, ['analysis_request'])

        # Get analysis result for this URL
        result_query = await db.execute(
            select(AnalysisResult).where(
                AnalysisResult.request_id == url_entry.request_id
            )
        )
        result = result_query.scalar_one_or_none()

        if result:
            individual_results.append({
                'url': url_entry.analysis_request.url,
                'label': url_entry.url_label,
                'seo_score': result.seo_score,
                'aeo_score': result.aeo_score,
                'seo_metrics': result.seo_metrics,
                'aeo_metrics': result.aeo_metrics,
                'recommendations': result.recommendations
            })

    # Get comparison result
    comparison_query = await db.execute(
        select(ComparisonResult).where(
            ComparisonResult.batch_id == batch_id
        )
    )
    comparison = comparison_query.scalar_one_or_none()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison results not found"
        )

    # Build batch response (must use loop for eager loading)
    url_statuses = []
    for entry in url_list:
        # Eagerly load the analysis_request relationship
        await db.refresh(entry, ['analysis_request'])
        url_statuses.append(CompetitiveURLStatus(
            url=entry.analysis_request.url,
            label=entry.url_label,
            status=entry.analysis_request.status.value,
            progress=entry.analysis_request.progress,
            request_id=str(entry.request_id),
            is_primary=entry.is_primary,
            order_index=entry.order_index
        ))

    batch_response = CompetitiveBatchResponse(
        id=batch.id,
        name=batch.name,
        status=batch.status.value,
        progress=batch.progress,
        total_urls=batch.total_urls,
        completed_count=batch.completed_count,
        failed_count=batch.failed_count,
        created_at=batch.created_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        urls=url_statuses
    )

    # Build comparison response
    comparison_response = ComparisonResponse(
        seo_rankings=comparison.seo_comparison.get('rankings', []),
        aeo_rankings=comparison.aeo_comparison.get('rankings', []),
        market_leader=comparison.market_leader,
        market_average=comparison.market_average,
        insights=comparison.competitive_insights,
        opportunities=comparison.opportunities,
        threats=comparison.threats
    )

    return CompetitiveResultResponse(
        batch=batch_response,
        individual_results=individual_results,
        comparison=comparison_response
    )


@router.get("/{batch_id}/comparison", response_model=ComparisonResponse)
async def get_comparison_only(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comparison results only (summary view).

    Args:
        batch_id: Batch UUID
        db: Database session

    Returns:
        Comparison with rankings, insights, opportunities, and threats

    Raises:
        404: If comparison not found
    """
    # Get comparison result
    result = await db.execute(
        select(ComparisonResult).where(
            ComparisonResult.batch_id == batch_id
        )
    )
    comparison = result.scalar_one_or_none()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison results not found for batch {batch_id}"
        )

    return ComparisonResponse(
        seo_rankings=comparison.seo_comparison.get('rankings', []),
        aeo_rankings=comparison.aeo_comparison.get('rankings', []),
        market_leader=comparison.market_leader,
        market_average=comparison.market_average,
        insights=comparison.competitive_insights,
        opportunities=comparison.opportunities,
        threats=comparison.threats
    )


@router.websocket("/{batch_id}/ws")
async def websocket_endpoint(
    batch_id: str,
    websocket: WebSocket
):
    """
    WebSocket endpoint for real-time batch progress updates.

    Args:
        batch_id: Competitive analysis batch UUID
        websocket: WebSocket connection
    """
    await websocket_manager.connect(batch_id, websocket)

    try:
        # Keep connection alive and listen for any client messages
        while True:
            # Wait for client ping or close
            data = await websocket.receive_text()
            # Echo back to keep alive
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        websocket_manager.disconnect(batch_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for batch {batch_id}: {e}")
        websocket_manager.disconnect(batch_id, websocket)
