"""Competitive analysis orchestrator for batch URL analysis."""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from app.models.competitive import (
    CompetitiveAnalysisBatch,
    CompetitiveAnalysisURL,
    ComparisonResult
)
from app.models.analysis import AnalysisRequest, AnalysisStatus
from app.services.orchestrator import AnalysisOrchestrator
from app.services.comparison_service import ComparisonService
from app.core.exceptions import AnalysisException

logger = logging.getLogger(__name__)


class CompetitiveOrchestrator:
    """
    Orchestrates competitive analysis for multiple URLs.

    Manages:
    - Concurrent crawling with semaphore limits
    - Individual URL analysis via AnalysisOrchestrator
    - Batch progress aggregation
    - Partial failure handling
    - Comparison result generation
    """

    def __init__(
        self,
        db: AsyncSession,
        anthropic_api_key: str,
        progress_callback: Optional[Callable] = None,
        max_concurrent: int = 3,
        crawler_timeout: int = 30000
    ):
        """
        Initialize competitive orchestrator.

        Args:
            db: Database session
            anthropic_api_key: Anthropic API key for LLM analysis
            progress_callback: Optional callback for progress updates
            max_concurrent: Maximum concurrent crawlers (default: 3)
            crawler_timeout: Crawler timeout in milliseconds
        """
        self.db = db
        self.anthropic_api_key = anthropic_api_key
        self.progress_callback = progress_callback
        self.crawler_timeout = crawler_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent

    async def run_competitive_analysis(self, batch_id: UUID) -> Dict[str, Any]:
        """
        Run complete competitive analysis for a batch.

        Workflow:
        1. Fetch batch and URLs from database
        2. Crawl all URLs concurrently (max concurrent limit)
        3. Analyze SEO/AEO for all URLs
        4. Generate comparison and insights
        5. Update batch status to COMPLETED

        Args:
            batch_id: UUID of the competitive analysis batch

        Returns:
            Dictionary containing:
            - batch_id: Batch UUID
            - status: Final status
            - total_urls: Total URL count
            - completed_count: Successfully completed URLs
            - failed_count: Failed URLs
            - comparison_id: ComparisonResult UUID

        Raises:
            AnalysisException: If batch not found or critical error
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting competitive analysis for batch {batch_id}")

        try:
            # 1. Fetch batch from database
            batch = await self._get_batch(batch_id)
            if not batch:
                raise AnalysisException(f"Batch {batch_id} not found")

            # Update status to PROCESSING
            await self._update_batch_status(
                batch,
                AnalysisStatus.PROCESSING,
                progress=0
            )

            # 2. Get all URLs in batch
            url_entries = await self._get_batch_urls(batch_id)
            if not url_entries:
                raise AnalysisException(f"No URLs found for batch {batch_id}")

            logger.info(f"Processing {len(url_entries)} URLs with max {self.max_concurrent} concurrent")

            # 3. Analyze all URLs concurrently with semaphore
            await self._analyze_all_urls_concurrently(batch, url_entries)

            # 4. Calculate final counts
            await self.db.refresh(batch)
            completed_count = sum(
                1 for entry in url_entries
                if entry.analysis_request.status == AnalysisStatus.COMPLETED
            )
            failed_count = len(url_entries) - completed_count

            # 5. Update batch counts
            batch.completed_count = completed_count
            batch.failed_count = failed_count

            # 6. Generate comparison if at least 2 succeeded
            comparison_id = None
            if completed_count >= 2:
                logger.info(f"Generating comparison for batch {batch_id}")
                comparison_service = ComparisonService(self.db, self.anthropic_api_key)
                comparison = await comparison_service.generate_comparison(batch_id)
                if comparison:
                    comparison_id = str(comparison.id)
                    logger.info(f"Comparison generated: {comparison_id}")

            # 7. Determine final status
            if completed_count == 0:
                # All failed
                final_status = AnalysisStatus.FAILED
                batch.error_message = "All URL analyses failed"
                batch.progress = 100
            elif completed_count >= 2:
                # At least 2 succeeded - mark as completed
                final_status = AnalysisStatus.COMPLETED
                batch.progress = 100
            else:
                # Only 1 succeeded - not enough for comparison
                final_status = AnalysisStatus.FAILED
                batch.error_message = "Insufficient successful analyses (minimum 2 required)"
                batch.progress = 100

            batch.status = final_status
            batch.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            # 8. Broadcast final progress
            if self.progress_callback:
                await self.progress_callback(str(batch_id), {
                    'status': final_status.value,
                    'progress': 100,
                    'completed_count': completed_count,
                    'failed_count': failed_count,
                    'total_urls': len(url_entries),
                    'comparison_id': comparison_id
                })

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Competitive analysis complete for batch {batch_id}. "
                f"Status: {final_status.value}, "
                f"Completed: {completed_count}/{len(url_entries)}, "
                f"Duration: {duration:.2f}s"
            )

            return {
                'batch_id': str(batch_id),
                'status': final_status.value,
                'total_urls': len(url_entries),
                'completed_count': completed_count,
                'failed_count': failed_count,
                'comparison_id': comparison_id,
                'duration': duration
            }

        except Exception as e:
            logger.error(f"Competitive analysis failed for batch {batch_id}: {str(e)}")
            await self._handle_batch_error(batch_id, e)
            raise

    async def _analyze_all_urls_concurrently(
        self,
        batch: CompetitiveAnalysisBatch,
        url_entries: List[CompetitiveAnalysisURL]
    ) -> None:
        """
        Analyze all URLs concurrently with semaphore limiting.

        Args:
            batch: CompetitiveAnalysisBatch instance
            url_entries: List of CompetitiveAnalysisURL entries
        """
        # Create tasks for all URLs
        tasks = [
            self._analyze_single_url(batch, entry, idx, len(url_entries))
            for idx, entry in enumerate(url_entries)
        ]

        # Run all tasks concurrently (semaphore limits actual concurrency)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _analyze_single_url(
        self,
        batch: CompetitiveAnalysisBatch,
        url_entry: CompetitiveAnalysisURL,
        index: int,
        total: int
    ) -> None:
        """
        Analyze a single URL within the batch.

        Uses semaphore to limit concurrent executions.

        Args:
            batch: CompetitiveAnalysisBatch instance
            url_entry: CompetitiveAnalysisURL entry
            index: URL index (0-based)
            total: Total number of URLs
        """
        async with self.semaphore:
            try:
                logger.info(
                    f"Starting analysis for URL {index + 1}/{total}: "
                    f"{url_entry.analysis_request.url}"
                )

                # Create individual progress callback that updates batch progress
                individual_callback = self._create_individual_progress_callback(
                    batch.id,
                    url_entry.request_id,
                    index,
                    total
                )

                # Run analysis using existing AnalysisOrchestrator
                orchestrator = AnalysisOrchestrator(
                    db=self.db,
                    anthropic_api_key=self.anthropic_api_key,
                    progress_callback=individual_callback,
                    crawler_timeout=self.crawler_timeout
                )

                await orchestrator.run_analysis(str(url_entry.request_id))

                logger.info(
                    f"Completed analysis for URL {index + 1}/{total}: "
                    f"{url_entry.analysis_request.url}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to analyze URL {index + 1}/{total} "
                    f"({url_entry.analysis_request.url}): {str(e)}"
                )
                # Error is already handled by AnalysisOrchestrator
                # Just log and continue with other URLs

    def _create_individual_progress_callback(
        self,
        batch_id: UUID,
        request_id: UUID,
        url_index: int,
        total_urls: int
    ) -> Optional[Callable]:
        """
        Create progress callback for individual URL that aggregates to batch.

        Args:
            batch_id: Batch UUID
            request_id: Individual request UUID
            url_index: URL index (0-based)
            total_urls: Total number of URLs

        Returns:
            Async callback function or None
        """
        if not self.progress_callback:
            return None

        async def individual_progress(req_id: str, progress_data: Dict[str, Any]) -> None:
            """Callback for individual URL progress."""
            # Calculate aggregate batch progress
            # Each URL contributes equally to total progress
            url_progress = progress_data.get('progress', 0)
            base_contribution = (url_index / total_urls) * 100
            current_contribution = (url_progress / 100) * (1 / total_urls) * 100
            aggregate_progress = int(base_contribution + current_contribution)

            # Broadcast batch-level progress
            await self.progress_callback(str(batch_id), {
                'status': 'processing',
                'progress': min(aggregate_progress, 99),  # Never reach 100 until complete
                'current_url': url_index + 1,
                'total_urls': total_urls,
                'current_step': f"URL {url_index + 1}/{total_urls}: {progress_data.get('step', '')}",
                'individual_statuses': {
                    str(request_id): {
                        'progress': url_progress,
                        'step': progress_data.get('step', ''),
                        'status': progress_data.get('status', 'processing')
                    }
                }
            })

        return individual_progress

    async def _get_batch(self, batch_id: UUID) -> Optional[CompetitiveAnalysisBatch]:
        """
        Fetch batch from database.

        Args:
            batch_id: Batch UUID

        Returns:
            CompetitiveAnalysisBatch or None
        """
        stmt = select(CompetitiveAnalysisBatch).where(
            CompetitiveAnalysisBatch.id == batch_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_batch_urls(self, batch_id: UUID) -> List[CompetitiveAnalysisURL]:
        """
        Fetch all URLs for a batch, ordered by order_index.

        Args:
            batch_id: Batch UUID

        Returns:
            List of CompetitiveAnalysisURL entries
        """
        stmt = (
            select(CompetitiveAnalysisURL)
            .where(CompetitiveAnalysisURL.batch_id == batch_id)
            .order_by(CompetitiveAnalysisURL.order_index)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _update_batch_status(
        self,
        batch: CompetitiveAnalysisBatch,
        status: AnalysisStatus,
        progress: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update batch status and timestamps.

        Args:
            batch: CompetitiveAnalysisBatch instance
            status: New status
            progress: Progress percentage (0-100)
            error_message: Optional error message
        """
        batch.status = status
        batch.progress = progress
        batch.updated_at = datetime.now(timezone.utc)

        if status == AnalysisStatus.PROCESSING and not batch.started_at:
            batch.started_at = datetime.now(timezone.utc)

        if status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            batch.completed_at = datetime.now(timezone.utc)

        if error_message:
            batch.error_message = error_message

        await self.db.commit()

        # Broadcast status update
        if self.progress_callback:
            await self.progress_callback(str(batch.id), {
                'status': status.value,
                'progress': progress
            })

    async def _handle_batch_error(self, batch_id: UUID, error: Exception) -> None:
        """
        Handle batch-level errors.

        Args:
            batch_id: Batch UUID
            error: Exception that occurred
        """
        try:
            batch = await self._get_batch(batch_id)
            if batch:
                batch.status = AnalysisStatus.FAILED
                batch.progress = 100
                batch.error_message = str(error)
                batch.completed_at = datetime.now(timezone.utc)
                batch.updated_at = datetime.now(timezone.utc)
                await self.db.commit()

                if self.progress_callback:
                    await self.progress_callback(str(batch_id), {
                        'status': 'failed',
                        'progress': 100,
                        'error': str(error)
                    })
        except Exception as e:
            logger.error(f"Failed to handle batch error: {e}")
