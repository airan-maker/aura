"""Synchronous background worker for processing analysis tasks."""

import logging
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.config import settings

logger = logging.getLogger(__name__)

# Thread pool for running background tasks
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="analysis_worker")


def run_analysis_sync(request_id: str, websocket_manager=None):
    """
    Submit analysis to background thread pool.

    Args:
        request_id: Analysis request UUID
        websocket_manager: Optional WebSocket manager for progress updates

    Returns:
        Future object
    """
    logger.info(f"Submitting analysis for request {request_id} to worker pool")
    future = _executor.submit(_execute_analysis, request_id, websocket_manager)
    return future


def _execute_analysis(request_id: str, websocket_manager=None):
    """
    Execute analysis using synchronous SQLAlchemy.

    This runs in a background thread with synchronous database operations.

    Args:
        request_id: Analysis request UUID
        websocket_manager: Optional WebSocket manager

    Returns:
        Dict with analysis results
    """
    import asyncio
    from uuid import UUID
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    logger.info(f"Executing analysis for request {request_id} in background thread")

    # Create new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        async def run_async_analysis():
            """Run analysis with async orchestrator in new event loop."""
            from app.services.orchestrator import AnalysisOrchestrator

            # Create async engine for this thread
            async_engine = create_async_engine(
                settings.DATABASE_URL,
                poolclass=NullPool,
                echo=False
            )

            AsyncSessionLocal = async_sessionmaker(
                async_engine,
                expire_on_commit=False
            )

            try:
                async with AsyncSessionLocal() as db:
                    # Create progress callback
                    async def progress_callback(req_id: str, data: dict):
                        """Broadcast progress via WebSocket."""
                        if websocket_manager:
                            try:
                                await websocket_manager.send_update(req_id, data)
                            except Exception as e:
                                logger.warning(f"Failed to send WebSocket update: {e}")

                    # Initialize orchestrator
                    orchestrator = AnalysisOrchestrator(
                        db=db,
                        anthropic_api_key=settings.ANTHROPIC_API_KEY,
                        progress_callback=progress_callback,
                        crawler_timeout=settings.CRAWLER_TIMEOUT
                    )

                    # Run the analysis
                    result = await orchestrator.run_analysis(request_id)

                    logger.info(
                        f"Analysis completed successfully for {request_id}. "
                        f"Status: {result.get('status', 'unknown')}"
                    )

                    return result

            finally:
                await async_engine.dispose()

        # Run async analysis in this thread's event loop
        result = loop.run_until_complete(run_async_analysis())
        return result

    except Exception as e:
        logger.error(
            f"Analysis failed for request {request_id}: {str(e)}",
            exc_info=True
        )
        raise

    finally:
        loop.close()
