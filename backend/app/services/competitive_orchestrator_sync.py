"""Synchronous competitive analysis orchestrator for batch URL analysis.

Uses synchronous SQLAlchemy to avoid greenlet issues in background threads.
This orchestrator runs in ThreadPoolExecutor and manages the full competitive analysis workflow.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.competitive import CompetitiveAnalysisBatch, CompetitiveAnalysisURL
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisStatus

logger = logging.getLogger(__name__)


class CompetitiveOrchestratorSync:
    """
    Synchronous orchestrator for competitive analysis.

    Manages concurrent analysis of multiple competitor URLs using sync SQLAlchemy.
    Designed to run in ThreadPoolExecutor without greenlet issues.
    """

    def __init__(
        self,
        db: Session,
        batch_id: UUID,
        max_concurrent: int = 3
    ):
        """
        Initialize synchronous competitive orchestrator.

        Args:
            db: Synchronous database session
            batch_id: Competitive analysis batch UUID
            max_concurrent: Maximum concurrent analyses (default: 3)
        """
        self.db = db
        self.batch_id = batch_id
        self.max_concurrent = max_concurrent

    def run_analysis(self) -> Dict:
        """
        Execute complete competitive analysis workflow synchronously.

        Returns:
            Dict with analysis results and status

        Workflow:
            1. Fetch batch and URLs (0-5%)
            2. Analyze all URLs concurrently (5-80%)
            3. Generate comparison (80-95%)
            4. Save results (95-100%)
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting synchronous competitive analysis for batch {self.batch_id}")

        try:
            # Step 1: Fetch batch and URLs (0-5%)
            self._update_batch_progress(5, "Fetching batch data")

            batch = self._get_batch()
            if not batch:
                raise Exception(f"Batch {self.batch_id} not found")

            url_entries = self._get_url_entries()
            if not url_entries:
                raise Exception(f"No URLs found for batch {self.batch_id}")

            logger.info(f"Found {len(url_entries)} URLs to analyze")

            # Step 2: Mark batch as PROCESSING
            batch.status = AnalysisStatus.PROCESSING
            batch.progress = 10
            batch.started_at = datetime.now(timezone.utc)
            batch.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            # Step 3: Analyze all URLs concurrently (10-80%)
            results = self._run_concurrent_analyses(url_entries)

            # Step 4: Generate comparison (80-95%)
            self._update_batch_progress(80, "Generating comparison")

            completed_results = [r for r in results if r.get('status') == 'completed']
            comparison = None

            if len(completed_results) >= 2:
                comparison = self._generate_comparison_sync(completed_results)

            # Step 5: Update final batch status (95-100%)
            self._update_batch_progress(95, "Finalizing results")

            completed_count = len(completed_results)
            failed_count = len(results) - completed_count

            # Determine final status
            if completed_count == 0:
                final_status = AnalysisStatus.FAILED
                error_message = "All URL analyses failed"
            elif completed_count >= 2:
                final_status = AnalysisStatus.COMPLETED
                error_message = None
            else:
                final_status = AnalysisStatus.FAILED
                error_message = "Insufficient successful analyses (minimum 2 required)"

            self._finalize_batch(
                status=final_status,
                completed_count=completed_count,
                failed_count=failed_count,
                error_message=error_message
            )

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"Competitive analysis completed for batch {self.batch_id}: "
                f"{final_status.value}, {completed_count}/{len(url_entries)} succeeded, "
                f"duration: {duration:.2f}s"
            )

            return {
                'batch_id': str(self.batch_id),
                'status': final_status.value,
                'total_urls': len(url_entries),
                'completed_count': completed_count,
                'failed_count': failed_count,
                'comparison_id': str(comparison.id) if comparison else None,
                'duration': duration
            }

        except Exception as e:
            logger.error(
                f"Synchronous competitive analysis failed for batch {self.batch_id}: {e}",
                exc_info=True
            )
            self._finalize_batch(
                status=AnalysisStatus.FAILED,
                error_message=str(e)[:500]
            )
            raise

    def _run_concurrent_analyses(
        self,
        url_entries: List[CompetitiveAnalysisURL]
    ) -> List[Dict]:
        """
        Run analyses for all URLs with concurrency control.

        Since we're in a background thread, we can create a new event loop
        to run async individual analyses concurrently.

        Args:
            url_entries: List of CompetitiveAnalysisURL entries

        Returns:
            List of analysis results
        """
        results = []
        total_urls = len(url_entries)
        progress_per_url = 70.0 / total_urls  # 10-80% range

        logger.info(f"Analyzing {total_urls} URLs with max {self.max_concurrent} concurrent")

        # Create new event loop for async operations in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Extract data from sync context before passing to async
            url_data = []
            for url_entry in url_entries:
                url_data.append({
                    'request_id': url_entry.request_id,
                    'url': url_entry.analysis_request.url,
                    'label': url_entry.url_label
                })

            # Create async tasks for all URLs
            async def analyze_all():
                semaphore = asyncio.Semaphore(self.max_concurrent)
                tasks = []

                for idx, data in enumerate(url_data):
                    task = self._analyze_single_url_async(
                        semaphore,
                        data,
                        idx,
                        total_urls,
                        progress_per_url
                    )
                    tasks.append(task)

                return await asyncio.gather(*tasks, return_exceptions=True)

            # Run all analyses
            results = loop.run_until_complete(analyze_all())

        finally:
            loop.close()

        return results

    async def _analyze_single_url_async(
        self,
        semaphore: asyncio.Semaphore,
        url_data: Dict,
        index: int,
        total: int,
        progress_per_url: float
    ) -> Dict:
        """
        Analyze a single URL within semaphore limit.

        Args:
            semaphore: Asyncio semaphore for concurrency control
            url_data: Dict with request_id, url, label
            index: URL index (0-based)
            total: Total number of URLs
            progress_per_url: Progress contribution per URL

        Returns:
            Dict with analysis result or error
        """
        async with semaphore:
            try:
                request_id = url_data['request_id']
                request_url = url_data['url']
                url_label = url_data['label']

                logger.info(f"Starting analysis for {request_url} ({index + 1}/{total})")

                # Run individual URL analysis using AnalysisOrchestrator
                result = await self._run_single_analysis_async(request_id)

                if result:
                    logger.info(f"Completed analysis for {request_url}")
                    return {
                        'request_id': str(request_id),
                        'url': request_url,
                        'label': url_label,
                        'status': 'completed',
                        'result': result
                    }
                else:
                    raise Exception("Analysis returned None")

            except Exception as e:
                logger.error(f"Failed to analyze URL {url_label}: {e}")
                return {
                    'request_id': str(url_data['request_id']),
                    'url': url_data['url'],
                    'label': url_data['label'],
                    'status': 'failed',
                    'error': str(e)
                }

    async def _run_single_analysis_async(self, request_id: UUID) -> Optional[AnalysisResult]:
        """
        Run single URL analysis using async AnalysisOrchestrator.

        Creates a new async database session for the orchestrator.

        Args:
            request_id: Analysis request UUID

        Returns:
            AnalysisResult or None
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.services.orchestrator import AnalysisOrchestrator

        # Create async engine for this analysis
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
            async with AsyncSessionLocal() as async_db:
                orchestrator = AnalysisOrchestrator(
                    db=async_db,
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    progress_callback=None,  # No individual progress callbacks
                    crawler_timeout=30000
                )

                await orchestrator.run_analysis(str(request_id))

                # Get the result
                result = await async_db.execute(
                    select(AnalysisResult).where(
                        AnalysisResult.request_id == request_id
                    )
                )
                return result.scalar_one_or_none()

        finally:
            await async_engine.dispose()

    def _generate_comparison_sync(self, results: List[Dict]) -> Optional['ComparisonResult']:
        """
        Generate comparison using async ComparisonService in sync context.

        Args:
            results: List of completed analysis results

        Returns:
            ComparisonResult or None
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.services.comparison_service import ComparisonService

        logger.info(f"Generating comparison for {len(results)} completed analyses")

        # Create new event loop for async comparison generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            async def generate():
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
                    async with AsyncSessionLocal() as async_db:
                        service = ComparisonService(async_db, settings.ANTHROPIC_API_KEY)
                        comparison = await service.generate_comparison(self.batch_id)
                        return comparison
                finally:
                    await async_engine.dispose()

            return loop.run_until_complete(generate())

        finally:
            loop.close()

    def _get_batch(self) -> Optional[CompetitiveAnalysisBatch]:
        """Fetch batch from database."""
        return self.db.execute(
            select(CompetitiveAnalysisBatch).where(
                CompetitiveAnalysisBatch.id == self.batch_id
            )
        ).scalar_one_or_none()

    def _get_url_entries(self) -> List[CompetitiveAnalysisURL]:
        """Fetch URL entries for batch with eager loading of analysis_request."""
        from sqlalchemy.orm import joinedload

        result = self.db.execute(
            select(CompetitiveAnalysisURL)
            .options(joinedload(CompetitiveAnalysisURL.analysis_request))
            .where(CompetitiveAnalysisURL.batch_id == self.batch_id)
            .order_by(CompetitiveAnalysisURL.order_index)
        )
        return list(result.scalars().all())

    def _update_batch_progress(self, progress: int, message: str = ""):
        """Update batch progress and log message."""
        batch = self._get_batch()
        if batch:
            batch.progress = progress
            batch.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            if message:
                logger.info(f"Batch {self.batch_id}: {message} ({progress}%)")

    def _finalize_batch(
        self,
        status: AnalysisStatus,
        completed_count: int = 0,
        failed_count: int = 0,
        error_message: Optional[str] = None
    ):
        """Update batch to final status."""
        batch = self._get_batch()
        if batch:
            batch.status = status
            batch.progress = 100
            batch.completed_count = completed_count
            batch.failed_count = failed_count
            batch.completed_at = datetime.now(timezone.utc)
            batch.updated_at = datetime.now(timezone.utc)

            if error_message:
                batch.error_message = error_message

            self.db.commit()
