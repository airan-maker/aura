"""Analysis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import uuid
import logging

from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisResultResponse
)
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisStatus
from app.database import get_db
from app.workers.analysis_worker_sync import run_analysis_sync
from app.utils.validators import validate_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


# WebSocket Manager
class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, request_id: str, websocket: WebSocket):
        """
        Accept a new WebSocket connection.

        Args:
            request_id: Analysis request ID
            websocket: WebSocket connection
        """
        await websocket.accept()
        if request_id not in self.active_connections:
            self.active_connections[request_id] = []
        self.active_connections[request_id].append(websocket)
        logger.info(f"WebSocket connected for analysis {request_id}")

    def disconnect(self, request_id: str, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            request_id: Analysis request ID
            websocket: WebSocket connection
        """
        if request_id in self.active_connections:
            if websocket in self.active_connections[request_id]:
                self.active_connections[request_id].remove(websocket)
            if not self.active_connections[request_id]:
                del self.active_connections[request_id]
        logger.info(f"WebSocket disconnected for analysis {request_id}")

    async def send_update(self, request_id: str, data: dict):
        """
        Send update to all connected clients for a request.

        Args:
            request_id: Analysis request ID
            data: Data to send
        """
        if request_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[request_id]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket update: {e}")
                    disconnected.append(connection)

            # Clean up disconnected sockets
            for conn in disconnected:
                self.disconnect(request_id, conn)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    data: AnalysisCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new analysis request.

    Args:
        data: Analysis creation data (URL)
        db: Database session

    Returns:
        Created analysis request with ID and status
    """
    # Validate URL
    if not validate_url(data.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format or potentially unsafe URL"
        )

    # Create analysis request
    request = AnalysisRequest(
        url=data.url,
        status=AnalysisStatus.PENDING,
        progress=0
    )

    db.add(request)
    await db.commit()
    await db.refresh(request)

    logger.info(f"Created analysis request {request.id} for {data.url}")

    # Submit to background worker (synchronous, non-blocking)
    run_analysis_sync(str(request.id), websocket_manager)

    return AnalysisResponse(
        id=request.id,
        url=request.url,
        status=request.status.value,
        progress=request.progress,
        created_at=request.created_at
    )


@router.get("/{request_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get analysis request status.

    Args:
        request_id: Analysis request UUID
        db: Database session

    Returns:
        Analysis request with current status and progress
    """
    result = await db.execute(
        select(AnalysisRequest).where(AnalysisRequest.id == request_id)
    )
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis request {request_id} not found"
        )

    return AnalysisResponse(
        id=request.id,
        url=request.url,
        status=request.status.value,
        progress=request.progress,
        current_step=request.current_step,
        created_at=request.created_at,
        started_at=request.started_at,
        completed_at=request.completed_at,
        error_message=request.error_message
    )


@router.get("/{request_id}/results", response_model=AnalysisResultResponse)
async def get_analysis_results(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete analysis results.

    Args:
        request_id: Analysis request UUID
        db: Database session

    Returns:
        Complete analysis results including SEO and AEO scores

    Raises:
        404: If results not found or analysis not completed
    """
    # Get the request first
    request_result = await db.execute(
        select(AnalysisRequest).where(AnalysisRequest.id == request_id)
    )
    request = request_result.scalar_one_or_none()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis request {request_id} not found"
        )

    # Check if completed
    if request.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed yet. Current status: {request.status.value}"
        )

    # Get results
    result_query = await db.execute(
        select(AnalysisResult).where(AnalysisResult.request_id == request_id)
    )
    analysis_result = result_query.scalar_one_or_none()

    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis results not found"
        )

    return AnalysisResultResponse(
        id=analysis_result.id,
        request_id=analysis_result.request_id,
        url=request.url,
        seo_score=analysis_result.seo_score,
        seo_metrics=analysis_result.seo_metrics,
        aeo_score=analysis_result.aeo_score,
        aeo_metrics=analysis_result.aeo_metrics,
        recommendations=analysis_result.recommendations,
        analysis_duration=analysis_result.analysis_duration,
        created_at=analysis_result.created_at
    )


@router.get("", response_model=List[AnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    List analysis requests with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of analysis requests
    """
    result = await db.execute(
        select(AnalysisRequest)
        .order_by(AnalysisRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    requests = result.scalars().all()

    return [
        AnalysisResponse(
            id=req.id,
            url=req.url,
            status=req.status.value,
            progress=req.progress,
            current_step=req.current_step,
            created_at=req.created_at,
            started_at=req.started_at,
            completed_at=req.completed_at,
            error_message=req.error_message
        )
        for req in requests
    ]


@router.websocket("/{request_id}/ws")
async def websocket_endpoint(
    request_id: str,
    websocket: WebSocket
):
    """
    WebSocket endpoint for real-time progress updates.

    Args:
        request_id: Analysis request UUID
        websocket: WebSocket connection
    """
    await websocket_manager.connect(request_id, websocket)

    try:
        # Keep connection alive and listen for any client messages
        while True:
            # Wait for client ping or close
            data = await websocket.receive_text()
            # Echo back to keep alive
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        websocket_manager.disconnect(request_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {request_id}: {e}")
        websocket_manager.disconnect(request_id, websocket)
