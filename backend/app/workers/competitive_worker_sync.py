"""Synchronous background worker for competitive analysis.

Uses ThreadPoolExecutor with synchronous orchestrator to avoid all greenlet issues.
This is the production-ready solution for background competitive analysis.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

logger = logging.getLogger(__name__)

# Thread pool for running background tasks
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="competitive_worker")


def run_competitive_analysis_sync(batch_id: str, websocket_manager=None):
    """
    Submit competitive analysis to background thread pool.

    Uses synchronous orchestrator with sync SQLAlchemy - no greenlet issues.

    Args:
        batch_id: Batch UUID as string
        websocket_manager: Optional WebSocket manager (currently not used in sync version)

    Returns:
        Future object
    """
    logger.info(f"Submitting competitive analysis for batch {batch_id} to worker pool")

    # Submit to thread pool (returns immediately, runs in background)
    future = _executor.submit(_execute_competitive_analysis, batch_id)

    return future


def _execute_competitive_analysis(batch_id: str) -> Dict:
    """
    Execute competitive analysis using synchronous orchestrator.

    Runs in a background thread from ThreadPoolExecutor.

    Args:
        batch_id: Batch UUID as string

    Returns:
        Dict with analysis results
    """
    from app.models.competitive import CompetitiveAnalysisBatch
    from app.models.analysis import AnalysisStatus
    from app.services.competitive_orchestrator_sync import CompetitiveOrchestratorSync

    logger.info(f"Starting synchronous competitive analysis for batch {batch_id}")

    # Create synchronous database engine
    # Convert async URL to sync URL for psycopg2
    sync_db_url = settings.DATABASE_URL.replace('+asyncpg', '').replace('+aiosqlite', '')

    engine = create_engine(
        sync_db_url,
        poolclass=NullPool,
        echo=settings.ENVIRONMENT == "development"
    )

    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        try:
            # Convert to UUID
            batch_uuid = UUID(batch_id)

            # Create orchestrator and run analysis
            orchestrator = CompetitiveOrchestratorSync(
                db=db,
                batch_id=batch_uuid,
                max_concurrent=3
            )

            result = orchestrator.run_analysis()

            logger.info(
                f"Competitive analysis completed for batch {batch_id}: "
                f"{result.get('status')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Synchronous competitive analysis failed for batch {batch_id}: {e}",
                exc_info=True
            )

            # Mark batch as failed
            try:
                db.execute(
                    update(CompetitiveAnalysisBatch)
                    .where(CompetitiveAnalysisBatch.id == UUID(batch_id))
                    .values(
                        status=AnalysisStatus.FAILED,
                        progress=100,
                        error_message=str(e)[:500],
                        completed_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                db.commit()
                logger.info(f"Marked batch {batch_id} as FAILED")
            except Exception as update_error:
                logger.error(f"Failed to update batch status: {update_error}")

            return {
                'batch_id': batch_id,
                'status': 'failed',
                'error': str(e)
            }
