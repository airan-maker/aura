"""Analysis orchestrator coordinating the entire analysis pipeline."""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import logging
import aiofiles
from pathlib import Path

from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisStatus
from app.services.crawler import WebCrawler
from app.services.seo_analyzer import SEOAnalyzer
from app.services.llm_analyzer import LLMAnalyzer
from app.core.exceptions import AnalysisException, CrawlerException, LLMAnalysisException

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orchestrates the entire analysis pipeline.

    Pipeline:
    1. Crawl website (Playwright)
    2. Analyze SEO metrics
    3. Analyze with LLM (GPT-4)
    4. Save results to database
    5. Update progress throughout

    Supports progress callbacks for real-time updates.
    """

    def __init__(
        self,
        db: AsyncSession,
        anthropic_api_key: str,
        progress_callback: Optional[Callable] = None,
        crawler_timeout: int = 30000
    ):
        """
        Initialize the orchestrator.

        Args:
            db: Database session
            anthropic_api_key: Anthropic API key
            progress_callback: Optional callback for progress updates
            crawler_timeout: Crawler timeout in milliseconds
        """
        self.db = db
        self.anthropic_api_key = anthropic_api_key
        self.progress_callback = progress_callback
        self.crawler_timeout = crawler_timeout

    async def run_analysis(self, request_id: str) -> Dict[str, Any]:
        """
        Execute the complete analysis pipeline.

        Args:
            request_id: UUID of the analysis request

        Returns:
            Dictionary with analysis results

        Raises:
            AnalysisException: If analysis fails
        """
        start_time = datetime.utcnow()

        try:
            # 1. Get request from database
            logger.info(f"Starting analysis for request {request_id}")
            request = await self._get_request(request_id)
            await self._update_status(
                request,
                AnalysisStatus.PROCESSING,
                "Starting analysis",
                0
            )

            # 2. Crawl website (Progress: 0% → 30%)
            await self._update_progress(request, "Crawling website", 10)
            crawl_data = await self._crawl_website(request.url)
            await self._update_progress(request, "Crawl completed", 30)

            # 3. SEO Analysis (Progress: 30% → 60%)
            await self._update_progress(request, "Analyzing SEO metrics", 35)
            seo_results = await self._analyze_seo(crawl_data)
            await self._update_progress(request, "SEO analysis completed", 60)

            # 4. LLM Analysis (Progress: 60% → 90%)
            await self._update_progress(request, "Running AI analysis", 65)
            aeo_results = await self._analyze_with_llm(
                request.url,
                crawl_data['text'],
                crawl_data['meta_tags']
            )
            await self._update_progress(request, "AI analysis completed", 90)

            # 5. Save results (Progress: 90% → 100%)
            await self._update_progress(request, "Saving results", 95)
            result = await self._save_results(
                request,
                crawl_data,
                seo_results,
                aeo_results,
                start_time
            )

            # 6. Mark as completed
            await self._update_status(
                request,
                AnalysisStatus.COMPLETED,
                "Analysis completed",
                100
            )

            logger.info(f"Analysis completed for request {request_id}")

            return {
                'request_id': str(request.id),
                'status': 'completed',
                'url': request.url,
                'seo_score': result.seo_score,
                'aeo_score': result.aeo_score,
                'duration': result.analysis_duration
            }

        except Exception as e:
            logger.error(f"Analysis failed for request {request_id}: {str(e)}")
            await self._handle_error(request, e)
            raise

    async def _crawl_website(self, url: str) -> Dict[str, Any]:
        """
        Crawl the website.

        Args:
            url: URL to crawl

        Returns:
            Crawled data dictionary

        Raises:
            CrawlerException: If crawling fails
        """
        try:
            async with WebCrawler(timeout=self.crawler_timeout) as crawler:
                return await crawler.crawl(url)
        except Exception as e:
            raise CrawlerException(f"Failed to crawl {url}: {str(e)}")

    async def _analyze_seo(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform SEO analysis.

        Args:
            crawl_data: Crawled website data

        Returns:
            SEO analysis results
        """
        analyzer = SEOAnalyzer()
        return analyzer.analyze(crawl_data)

    async def _analyze_with_llm(
        self,
        url: str,
        page_text: str,
        meta_tags: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Perform LLM-based AEO analysis.

        Args:
            url: Website URL
            page_text: Page text content
            meta_tags: Meta tags dictionary

        Returns:
            AEO analysis results

        Raises:
            LLMAnalysisException: If LLM analysis fails
        """
        analyzer = LLMAnalyzer(api_key=self.anthropic_api_key)
        return await analyzer.analyze_brand_recognition(url, page_text, meta_tags)

    async def _save_results(
        self,
        request: AnalysisRequest,
        crawl_data: Dict[str, Any],
        seo_results: Dict[str, Any],
        aeo_results: Dict[str, Any],
        start_time: datetime
    ) -> AnalysisResult:
        """
        Save analysis results to database.

        Args:
            request: Analysis request object
            crawl_data: Crawled data
            seo_results: SEO analysis results
            aeo_results: AEO analysis results
            start_time: Analysis start time

        Returns:
            Created AnalysisResult object
        """
        # Save screenshot to filesystem
        screenshot_path = await self._save_screenshot(
            request.id,
            crawl_data['screenshot']
        )

        # Combine all recommendations
        all_recommendations = (
            seo_results.get('recommendations', []) +
            aeo_results.get('recommendations', [])
        )

        # Sort recommendations by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_recommendations.sort(
            key=lambda x: priority_order.get(x.get('priority', 'low'), 3)
        )

        # Create result object
        result = AnalysisResult(
            request_id=request.id,
            page_html=crawl_data['html'][:50000],  # Limit size
            page_text=crawl_data['text'][:50000],  # Limit size
            screenshot_path=screenshot_path,
            seo_score=seo_results['score'],
            seo_metrics=seo_results['metrics'],
            aeo_score=aeo_results['score'],
            aeo_metrics=aeo_results['brand_recognition'],
            recommendations=all_recommendations,
            analysis_duration=(datetime.utcnow() - start_time).total_seconds()
        )

        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        return result

    async def _save_screenshot(self, request_id: str, screenshot_bytes: bytes) -> str:
        """
        Save screenshot to filesystem.

        Args:
            request_id: Analysis request ID
            screenshot_bytes: Screenshot PNG bytes

        Returns:
            Path to saved screenshot
        """
        # Create storage directory
        screenshot_dir = Path("storage/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{request_id}.png"
        filepath = screenshot_dir / filename

        # Save file asynchronously
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(screenshot_bytes)

        return str(filepath)

    async def _update_progress(
        self,
        request: AnalysisRequest,
        step: str,
        progress: int
    ):
        """
        Update analysis progress.

        Args:
            request: Analysis request object
            step: Current step description
            progress: Progress percentage (0-100)
        """
        request.current_step = step
        request.progress = progress
        request.updated_at = datetime.utcnow()
        await self.db.commit()

        # Send progress update via callback (WebSocket)
        if self.progress_callback:
            try:
                await self.progress_callback(str(request.id), {
                    'status': 'processing',
                    'step': step,
                    'progress': progress
                })
            except Exception as e:
                logger.warning(f"Failed to send progress update: {e}")

    async def _update_status(
        self,
        request: AnalysisRequest,
        status: AnalysisStatus,
        step: str,
        progress: int
    ):
        """
        Update analysis status.

        Args:
            request: Analysis request object
            status: New status
            step: Current step description
            progress: Progress percentage
        """
        request.status = status
        request.current_step = step
        request.progress = progress
        request.updated_at = datetime.utcnow()

        if status == AnalysisStatus.PROCESSING and not request.started_at:
            request.started_at = datetime.utcnow()
        elif status == AnalysisStatus.COMPLETED:
            request.completed_at = datetime.utcnow()

        await self.db.commit()

    async def _handle_error(self, request: AnalysisRequest, error: Exception):
        """
        Handle analysis error.

        Args:
            request: Analysis request object
            error: Exception that occurred
        """
        request.status = AnalysisStatus.FAILED
        request.error_message = str(error)
        request.error_details = {
            'type': type(error).__name__,
            'step': request.current_step,
            'progress': request.progress
        }
        request.updated_at = datetime.utcnow()
        await self.db.commit()

        # Notify via callback
        if self.progress_callback:
            try:
                await self.progress_callback(str(request.id), {
                    'status': 'failed',
                    'error': str(error)
                })
            except Exception as e:
                logger.warning(f"Failed to send error notification: {e}")

    async def _get_request(self, request_id: str) -> AnalysisRequest:
        """
        Retrieve analysis request from database.

        Args:
            request_id: Request UUID

        Returns:
            AnalysisRequest object

        Raises:
            AnalysisException: If request not found
        """
        result = await self.db.execute(
            select(AnalysisRequest).where(AnalysisRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            raise AnalysisException(f"Analysis request {request_id} not found")

        return request
