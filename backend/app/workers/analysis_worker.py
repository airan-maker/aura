"""Background worker for processing analysis tasks."""

import asyncio
from typing import Dict, Optional
import logging

from app.services.orchestrator import AnalysisOrchestrator
from app.database import AsyncSessionLocal
from app.config import settings

logger = logging.getLogger(__name__)


class AnalysisWorker:
    """
    Background worker for managing analysis tasks.

    Uses asyncio.create_task to run analyses in the background.
    Tracks running tasks and provides status information.
    """

    def __init__(self):
        """Initialize the worker."""
        self.tasks: Dict[str, asyncio.Task] = {}
        self.websocket_manager = None  # Set by main app

    def set_websocket_manager(self, manager):
        """
        Set the WebSocket manager for progress updates.

        Args:
            manager: WebSocketManager instance
        """
        self.websocket_manager = manager

    async def submit_analysis(self, request_id: str) -> None:
        """
        Submit an analysis task to run in the background.

        Args:
            request_id: UUID of the analysis request
        """
        # Check if already running
        if request_id in self.tasks and not self.tasks[request_id].done():
            logger.warning(f"Analysis {request_id} is already running")
            return

        # Create background task
        logger.info(f"Submitting analysis task for {request_id}")
        task = asyncio.create_task(self._run_analysis(request_id))
        self.tasks[request_id] = task

    async def _run_analysis(self, request_id: str):
        """
        Execute the analysis in the background.

        Args:
            request_id: UUID of the analysis request
        """
        async with AsyncSessionLocal() as db:
            orchestrator = AnalysisOrchestrator(
                db=db,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                progress_callback=self._broadcast_progress,
                crawler_timeout=settings.CRAWLER_TIMEOUT
            )

            try:
                await orchestrator.run_analysis(request_id)
                logger.info(f"Analysis completed successfully for {request_id}")
            except Exception as e:
                logger.error(f"Analysis failed for {request_id}: {str(e)}")
            finally:
                # Clean up task
                if request_id in self.tasks:
                    del self.tasks[request_id]

    async def _broadcast_progress(self, request_id: str, data: Dict):
        """
        Broadcast progress update via WebSocket.

        Args:
            request_id: Analysis request ID
            data: Progress data
        """
        if self.websocket_manager:
            await self.websocket_manager.send_update(request_id, data)

    def get_task_status(self, request_id: str) -> Optional[str]:
        """
        Get the status of a background task.

        Args:
            request_id: Analysis request ID

        Returns:
            'processing', 'completed', 'failed', or None if not found
        """
        if request_id not in self.tasks:
            return None

        task = self.tasks[request_id]
        if task.done():
            if task.exception() is not None:
                return 'failed'
            return 'completed'
        return 'processing'

    async def cancel_analysis(self, request_id: str) -> bool:
        """
        Cancel a running analysis.

        Args:
            request_id: Analysis request ID

        Returns:
            True if cancelled, False if not running
        """
        if request_id not in self.tasks:
            return False

        task = self.tasks[request_id]
        if not task.done():
            task.cancel()
            logger.info(f"Cancelled analysis {request_id}")
            return True

        return False

    def get_active_tasks(self) -> int:
        """
        Get the number of currently active tasks.

        Returns:
            Number of active tasks
        """
        return sum(1 for task in self.tasks.values() if not task.done())


# Global worker instance
analysis_worker = AnalysisWorker()
