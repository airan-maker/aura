"""Comparison service for generating competitive analysis insights."""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timezone
import logging

from app.models.competitive import ComparisonResult, CompetitiveAnalysisBatch
from app.models.analysis import AnalysisResult, AnalysisStatus
from app.services.batch_llm_analyzer import BatchLLMAnalyzer

logger = logging.getLogger(__name__)


class ComparisonService:
    """
    Service for generating competitive comparison and insights.

    Generates:
    - SEO and AEO rankings
    - Market leader identification
    - Market averages and benchmarks
    - AI-generated competitive insights
    - Opportunities and threats
    """

    def __init__(self, db: AsyncSession, anthropic_api_key: str):
        """
        Initialize comparison service.

        Args:
            db: Database session
            anthropic_api_key: Anthropic API key for LLM analysis
        """
        self.db = db
        self.llm_analyzer = BatchLLMAnalyzer(api_key=anthropic_api_key)

    async def generate_comparison(
        self,
        batch_id: UUID
    ) -> Optional[ComparisonResult]:
        """
        Generate complete comparison analysis for a batch.

        Workflow:
        1. Fetch all completed analysis results for batch
        2. Calculate SEO and AEO rankings
        3. Compute market averages
        4. Identify market leaders
        5. Generate AI insights via BatchLLMAnalyzer
        6. Save ComparisonResult to database

        Args:
            batch_id: UUID of competitive analysis batch

        Returns:
            ComparisonResult instance or None if insufficient data

        Raises:
            Exception: If database operations fail
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Generating comparison for batch {batch_id}")

        try:
            # 1. Fetch completed analysis results
            results = await self._fetch_completed_results(batch_id)

            if len(results) < 2:
                logger.warning(
                    f"Insufficient results for batch {batch_id}: "
                    f"need at least 2, got {len(results)}"
                )
                return None

            # 2. Calculate rankings
            seo_rankings = self._calculate_rankings(results, 'seo')
            aeo_rankings = self._calculate_rankings(results, 'aeo')

            # 3. Compute market metrics
            market_leader = self._identify_market_leader(seo_rankings, aeo_rankings)
            market_average = self._calculate_market_average(seo_rankings, aeo_rankings)

            # 4. Prepare competitor data for LLM analysis
            competitor_data = self._prepare_competitor_data(results, seo_rankings, aeo_rankings)

            # 5. Generate AI insights
            llm_insights = await self.llm_analyzer.analyze_competitive_landscape(
                competitor_data
            )

            # 6. Create comparison result record
            comparison = ComparisonResult(
                batch_id=batch_id,
                seo_comparison={
                    'rankings': seo_rankings,
                    'average': market_average['seo'],
                    'leader': market_leader['seo']
                },
                aeo_comparison={
                    'rankings': aeo_rankings,
                    'average': market_average['aeo'],
                    'leader': market_leader['aeo']
                },
                market_leader=market_leader,
                market_average=market_average,
                competitive_insights=llm_insights.get('insights', ''),
                opportunities=llm_insights.get('opportunities', []),
                threats=llm_insights.get('threats', []),
                comparison_duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )

            # 7. Save to database
            self.db.add(comparison)
            await self.db.commit()
            await self.db.refresh(comparison)

            logger.info(
                f"Comparison generated for batch {batch_id}. "
                f"Duration: {comparison.comparison_duration:.2f}s"
            )

            return comparison

        except Exception as e:
            logger.error(f"Failed to generate comparison for batch {batch_id}: {e}")
            raise

    async def _fetch_completed_results(
        self,
        batch_id: UUID
    ) -> List[AnalysisResult]:
        """
        Fetch all completed analysis results for a batch.

        Args:
            batch_id: Batch UUID

        Returns:
            List of completed AnalysisResult objects
        """
        # Get batch to access URL entries
        batch_stmt = select(CompetitiveAnalysisBatch).where(
            CompetitiveAnalysisBatch.id == batch_id
        )
        batch_result = await self.db.execute(batch_stmt)
        batch = batch_result.scalar_one_or_none()

        if not batch:
            return []

        # Get all request IDs from batch URLs
        request_ids = [url_entry.request_id for url_entry in batch.urls]

        # Fetch completed results
        stmt = (
            select(AnalysisResult)
            .where(
                AnalysisResult.request_id.in_(request_ids)
            )
        )
        result = await self.db.execute(stmt)
        results = list(result.scalars().all())

        # Filter to only completed results
        completed = [r for r in results if r.request.status == AnalysisStatus.COMPLETED]

        logger.info(
            f"Fetched {len(completed)} completed results "
            f"out of {len(request_ids)} total for batch {batch_id}"
        )

        return completed

    def _calculate_rankings(
        self,
        results: List[AnalysisResult],
        metric_type: str  # 'seo' or 'aeo'
    ) -> List[Dict[str, Any]]:
        """
        Calculate rankings for SEO or AEO scores.

        Args:
            results: List of AnalysisResult objects
            metric_type: 'seo' or 'aeo'

        Returns:
            List of ranking entries sorted by score (descending)
            Each entry: {url, score, rank, delta_from_leader, delta_from_average}
        """
        # Extract scores
        scores = []
        for result in results:
            url = result.request.url
            score = result.seo_score if metric_type == 'seo' else result.aeo_score

            scores.append({
                'url': url,
                'score': round(score, 2),
                'label': self._get_url_label(result)
            })

        # Sort by score descending
        scores.sort(key=lambda x: x['score'], reverse=True)

        # Calculate average
        avg_score = sum(s['score'] for s in scores) / len(scores) if scores else 0

        # Assign ranks and calculate deltas
        rankings = []
        leader_score = scores[0]['score'] if scores else 0

        for idx, item in enumerate(scores):
            rankings.append({
                'url': item['url'],
                'label': item['label'],
                'score': item['score'],
                'rank': idx + 1,
                'delta_from_leader': round(item['score'] - leader_score, 2),
                'delta_from_average': round(item['score'] - avg_score, 2)
            })

        return rankings

    def _identify_market_leader(
        self,
        seo_rankings: List[Dict[str, Any]],
        aeo_rankings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify market leaders for SEO and AEO.

        Args:
            seo_rankings: SEO rankings list
            aeo_rankings: AEO rankings list

        Returns:
            Dictionary: {
                'seo': {url, score, label},
                'aeo': {url, score, label}
            }
        """
        seo_leader = seo_rankings[0] if seo_rankings else None
        aeo_leader = aeo_rankings[0] if aeo_rankings else None

        return {
            'seo': {
                'url': seo_leader['url'],
                'score': seo_leader['score'],
                'label': seo_leader.get('label')
            } if seo_leader else None,
            'aeo': {
                'url': aeo_leader['url'],
                'score': aeo_leader['score'],
                'label': aeo_leader.get('label')
            } if aeo_leader else None
        }

    def _calculate_market_average(
        self,
        seo_rankings: List[Dict[str, Any]],
        aeo_rankings: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate market average scores.

        Args:
            seo_rankings: SEO rankings list
            aeo_rankings: AEO rankings list

        Returns:
            Dictionary: {'seo': avg_score, 'aeo': avg_score}
        """
        seo_avg = (
            sum(r['score'] for r in seo_rankings) / len(seo_rankings)
            if seo_rankings else 0
        )
        aeo_avg = (
            sum(r['score'] for r in aeo_rankings) / len(aeo_rankings)
            if aeo_rankings else 0
        )

        return {
            'seo': round(seo_avg, 2),
            'aeo': round(aeo_avg, 2)
        }

    def _prepare_competitor_data(
        self,
        results: List[AnalysisResult],
        seo_rankings: List[Dict[str, Any]],
        aeo_rankings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prepare competitor data for LLM analysis.

        Args:
            results: List of AnalysisResult objects
            seo_rankings: SEO rankings
            aeo_rankings: AEO rankings

        Returns:
            List of competitor summaries for LLM
        """
        competitor_data = []

        # Create lookup maps for rankings
        seo_rank_map = {r['url']: r['rank'] for r in seo_rankings}
        aeo_rank_map = {r['url']: r['rank'] for r in aeo_rankings}

        for result in results:
            url = result.request.url
            label = self._get_url_label(result)

            # Extract top issues and strengths
            issues = self._extract_top_issues(result)
            strengths = self._extract_strengths(result)

            competitor_data.append({
                'url': url,
                'label': label,
                'seo_score': round(result.seo_score, 2),
                'aeo_score': round(result.aeo_score, 2),
                'seo_rank': seo_rank_map.get(url, 0),
                'aeo_rank': aeo_rank_map.get(url, 0),
                'issues': issues[:5],  # Top 5 issues
                'strengths': strengths[:3]  # Top 3 strengths
            })

        return competitor_data

    def _get_url_label(self, result: AnalysisResult) -> Optional[str]:
        """
        Get label for a result's URL from CompetitiveAnalysisURL.

        Args:
            result: AnalysisResult object

        Returns:
            Label string or None
        """
        # In a real implementation, we'd query CompetitiveAnalysisURL
        # For now, return None and handle it in the calling code
        return None

    def _extract_top_issues(self, result: AnalysisResult) -> List[str]:
        """
        Extract top issues from analysis result.

        Args:
            result: AnalysisResult object

        Returns:
            List of issue descriptions
        """
        issues = []

        # SEO issues
        if result.seo_metrics:
            issues.extend(result.seo_metrics.get('issues', []))

        # AEO issues from recommendations
        if result.recommendations:
            for rec in result.recommendations[:5]:
                if rec.get('priority') in ['critical', 'high']:
                    issues.append(rec.get('description', ''))

        return issues

    def _extract_strengths(self, result: AnalysisResult) -> List[str]:
        """
        Extract strengths from analysis result.

        Args:
            result: AnalysisResult object

        Returns:
            List of strength descriptions
        """
        strengths = []

        # Check high category scores
        if result.seo_metrics and 'category_scores' in result.seo_metrics:
            category_scores = result.seo_metrics['category_scores']
            for category, score in category_scores.items():
                if score >= 90:
                    strengths.append(f"Excellent {category.replace('_', ' ')} ({score}/100)")

        # Check for structured data
        if result.seo_metrics and result.seo_metrics.get('metrics', {}).get('structured_data'):
            strengths.append("Has structured data (Schema.org)")

        # Check security
        if result.seo_metrics and result.seo_metrics.get('metrics', {}).get('ssl_enabled'):
            strengths.append("HTTPS enabled")

        # Check mobile friendly
        if result.seo_metrics and result.seo_metrics.get('metrics', {}).get('mobile_friendly'):
            strengths.append("Mobile-friendly")

        return strengths


async def generate_comparison(
    batch_id: UUID,
    db: AsyncSession,
    anthropic_api_key: str
) -> Optional[ComparisonResult]:
    """
    Convenience function to generate comparison.

    Args:
        batch_id: Competitive analysis batch UUID
        db: Database session
        anthropic_api_key: Anthropic API key

    Returns:
        ComparisonResult instance or None

    Example:
        >>> from app.services.comparison_service import generate_comparison
        >>> comparison = await generate_comparison(batch_id, db, api_key)
        >>> print(f"SEO Leader: {comparison.market_leader['seo']['url']}")
    """
    service = ComparisonService(db, anthropic_api_key)
    return await service.generate_comparison(batch_id)
