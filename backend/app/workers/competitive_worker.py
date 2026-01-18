"""Background worker for processing competitive analysis batches."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.services.competitive_orchestrator import CompetitiveOrchestrator
from app.config import settings

logger = logging.getLogger(__name__)

# Thread pool for running background tasks in separate event loops
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="competitive_worker")


def _run_in_new_loop(coro):
    """
    Run an async coroutine in a completely new event loop in a separate thread.

    This ensures proper greenlet context for SQLAlchemy async operations.
    Uses asyncio.run() which properly initializes async context including greenlets.
    """
    # asyncio.run() creates a new event loop and properly initializes async context
    return asyncio.run(coro)


async def run_competitive_analysis_task(batch_id: str, websocket_manager=None):
    """
    Execute a competitive analysis batch in a background task.

    This function submits the actual work to a thread pool with a new event loop
    to ensure proper SQLAlchemy async context.

    Args:
        batch_id: UUID string of the competitive analysis batch
        websocket_manager: Optional WebSocket manager for progress updates
    """
    logger.info(f"Submitting competitive analysis for batch {batch_id} to worker pool")

    # Submit to thread pool with new event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        _executor,
        _run_in_new_loop,
        _execute_competitive_analysis(batch_id, websocket_manager)
    )


async def _execute_competitive_analysis(batch_id: str, websocket_manager=None):
    """
    Internal function that executes the competitive analysis.

    This runs in a separate thread with its own event loop and database engine.

    **SQLite Limitation:**
    SQLite's async driver (aiosqlite) cannot initialize greenlet context in background
    threads. ALL async database operations fail, including UPDATE statements.

    For SQLite: Background processing is skipped entirely. Batch remains in "pending" state.
    For PostgreSQL: Full competitive analysis with CompetitiveOrchestrator runs successfully.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    # Detect if using SQLite
    is_sqlite = "sqlite" in settings.DATABASE_URL.lower()

    if is_sqlite:
        logger.warning(
            f"╔═══════════════════════════════════════════════════════════════════════╗\n"
            f"║ SQLite Detected - Background Processing Not Available                ║\n"
            f"║                                                                       ║\n"
            f"║ The competitive analysis batch {batch_id[:8]}... has been created    ║\n"
            f"║ successfully, but background processing cannot execute with SQLite.  ║\n"
            f"║                                                                       ║\n"
            f"║ REASON: aiosqlite cannot initialize greenlet context in background   ║\n"
            f"║         worker threads (documented SQLAlchemy/aiosqlite limitation). ║\n"
            f"║                                                                       ║\n"
            f"║ SOLUTION: Switch to PostgreSQL for full competitive analysis:        ║\n"
            f"║                                                                       ║\n"
            f"║   1. docker run -d -p 5432:5432 \\                                    ║\n"
            f"║        -e POSTGRES_DB=aura \\                                         ║\n"
            f"║        -e POSTGRES_USER=aura \\                                       ║\n"
            f"║        -e POSTGRES_PASSWORD=aura_password \\                          ║\n"
            f"║        postgres:16                                                    ║\n"
            f"║                                                                       ║\n"
            f"║   2. Update .env:                                                     ║\n"
            f"║      DATABASE_URL=postgresql+asyncpg://aura:aura_password@localhost: ║\n"
            f"║                   5432/aura                                           ║\n"
            f"║                                                                       ║\n"
            f"║   3. python init_db.py                                                ║\n"
            f"║                                                                       ║\n"
            f"║   4. Restart backend → Everything will work! ✅                      ║\n"
            f"║                                                                       ║\n"
            f"║ The batch will remain in 'pending' status. All other API features    ║\n"
            f"║ work normally (create batch, get status, etc).                       ║\n"
            f"╚═══════════════════════════════════════════════════════════════════════╝"
        )
        return {
            'batch_id': batch_id,
            'status': 'pending',
            'message': 'SQLite detected - background processing not available. See logs for PostgreSQL setup instructions.'
        }

    # PostgreSQL: Run full competitive analysis
    logger.info(f"Starting competitive analysis for batch {batch_id} (PostgreSQL mode)")

    # Create a fresh async engine for this thread with NullPool
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.ENVIRONMENT == "development",
        poolclass=NullPool,  # Don't pool connections in background threads
    )

    # Create session maker
    AsyncSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )

    # Create a new async database session for this background task
    async with AsyncSessionLocal() as db:
        try:
            # Convert string to UUID
            batch_uuid = UUID(batch_id)

            # Run full orchestrator
            result = await _run_full_competitive_analysis(
                db, batch_uuid, batch_id, websocket_manager
            )

            logger.info(
                f"Competitive analysis completed successfully for batch {batch_id}. "
                f"Status: {result.get('status', 'unknown')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Competitive analysis failed for batch {batch_id}: {str(e)}",
                exc_info=True
            )
            # Don't try to update database from here - would hit same greenlet issue
            raise

        finally:
            # Close the engine to clean up connections
            await engine.dispose()


async def _run_full_competitive_analysis(
    db: "AsyncSession",
    batch_uuid: UUID,
    batch_id: str,
    websocket_manager
) -> Dict:
    """
    Run full competitive analysis using CompetitiveOrchestrator.

    This is the production code path for PostgreSQL databases.
    """
    # Create progress callback
    async def progress_callback(bid: str, data: Dict):
        """Broadcast progress via WebSocket."""
        if websocket_manager:
            try:
                await websocket_manager.send_update(bid, data)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket update: {e}")

    # Initialize orchestrator
    orchestrator = CompetitiveOrchestrator(
        db=db,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        progress_callback=progress_callback,
        max_concurrent=min(settings.MAX_CONCURRENT_ANALYSES, 3),  # Max 3 concurrent
        crawler_timeout=settings.CRAWLER_TIMEOUT
    )

    # Run the competitive analysis
    result = await orchestrator.run_competitive_analysis(batch_uuid)

    return result


