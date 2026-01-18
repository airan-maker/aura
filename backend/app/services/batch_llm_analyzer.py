"""Batch LLM analyzer for competitive landscape insights."""

from anthropic import AsyncAnthropic
from typing import Dict, Any, List
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.core.exceptions import LLMAnalysisException

logger = logging.getLogger(__name__)


class BatchLLMAnalyzer:
    """
    Batch LLM analyzer for competitive analysis.

    Optimizes API costs by making a single Claude call to analyze
    all competitors together, rather than individual calls.

    Cost savings: ~80% vs. individual analysis
    """

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        """
        Initialize batch LLM analyzer.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-haiku-4-5-20251001)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens_per_competitor = 750  # Limit context per competitor

    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def analyze_competitive_landscape(
        self,
        competitor_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze competitive landscape using single Claude call.

        Args:
            competitor_data: List of competitor summaries, each containing:
                - url: Website URL
                - label: Optional label (e.g., "Competitor A")
                - seo_score: SEO score (0-100)
                - aeo_score: AEO score (0-100)
                - seo_rank: Rank in SEO rankings
                - aeo_rank: Rank in AEO rankings
                - issues: List of top issues
                - strengths: List of strengths
                - brand_summary: Brief brand description

        Returns:
            Dictionary containing:
            - insights: AI-generated competitive landscape overview (string)
            - opportunities: List of improvement opportunities (List[str])
            - threats: List of competitive threats (List[str])
            - overall_winner: URL and reason for overall winner (Dict)

        Raises:
            LLMAnalysisException: If API call fails
        """
        logger.info(f"Starting batch LLM analysis for {len(competitor_data)} competitors")

        if not competitor_data:
            raise LLMAnalysisException("No competitor data provided")

        # Create competitive analysis prompt
        prompt = self._create_competitive_prompt(competitor_data)

        try:
            # Call Anthropic Claude API with all competitor data
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.5,
                system=(
                    "You are a competitive analysis expert specializing in SEO and AI Engine "
                    "Optimization (AEO). Your goal is to provide actionable insights by comparing "
                    "multiple websites and identifying opportunities and threats. "
                    "Always respond with valid JSON only, no additional text."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response from Claude
            response_text = response.content[0].text
            result = json.loads(response_text)

            logger.info(
                f"Batch LLM analysis complete. "
                f"Generated {len(result.get('opportunities', []))} opportunities, "
                f"{len(result.get('threats', []))} threats"
            )

            return {
                'insights': result.get('insights', ''),
                'opportunities': result.get('opportunities', []),
                'threats': result.get('threats', []),
                'overall_winner': result.get('overall_winner', {})
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            raise LLMAnalysisException(f"Invalid JSON response from GPT: {str(e)}")
        except Exception as e:
            logger.error(f"OpenAI API error during batch analysis: {e}")
            raise LLMAnalysisException(f"OpenAI API error: {str(e)}")

    def _create_competitive_prompt(
        self,
        competitor_data: List[Dict[str, Any]]
    ) -> str:
        """
        Create competitive analysis prompt for GPT.

        Args:
            competitor_data: List of competitor summaries

        Returns:
            Formatted prompt string
        """
        # Build competitor summaries
        competitor_summaries = []
        for idx, competitor in enumerate(competitor_data, 1):
            label = competitor.get('label') or f"Competitor {idx}"
            url = competitor.get('url', '')
            seo_score = competitor.get('seo_score', 0)
            aeo_score = competitor.get('aeo_score', 0)
            seo_rank = competitor.get('seo_rank', idx)
            aeo_rank = competitor.get('aeo_rank', idx)
            brand_summary = competitor.get('brand_summary', 'Not available')
            issues = competitor.get('issues', [])
            strengths = competitor.get('strengths', [])

            summary = f"""
{label} ({url})
  • SEO Score: {seo_score}/100 (Rank #{seo_rank})
  • AEO Score: {aeo_score}/100 (Rank #{aeo_rank})
  • Description: {brand_summary[:200]}

  Strengths:
{self._format_list(strengths) if strengths else '  - None identified'}

  Weaknesses:
{self._format_list(issues[:3]) if issues else '  - None identified'}
"""
            competitor_summaries.append(summary.strip())

        # Create full prompt
        prompt = f"""You are analyzing a competitive landscape of {len(competitor_data)} websites for SEO and AEO optimization.

COMPETITORS:
{'=' * 80}
{chr(10).join(competitor_summaries)}
{'=' * 80}

Please provide a comprehensive competitive analysis with the following:

1. **Competitive Landscape Overview** (3-5 sentences):
   - Summarize the overall competitive dynamics
   - Identify any clear patterns (e.g., "All competitors lack structured data")
   - Note any standout performers and why

2. **Top 5 Opportunities for Improvement**:
   - Actionable opportunities based on competitive gaps
   - Focus on areas where multiple competitors are weak
   - Prioritize high-impact, achievable improvements
   - Format: Clear, specific actions (e.g., "Add structured data - only 1/3 competitors have it")

3. **Top 3 Competitive Threats**:
   - What are the strongest competitors doing well?
   - What advantages do they have?
   - What risks do weaker competitors face?
   - Format: Specific competitive advantages to watch

4. **Overall Winner**:
   - Which competitor performs best overall?
   - Consider both SEO and AEO scores
   - Provide specific reasons why they lead

Respond in JSON format:
{{
    "insights": "3-5 sentence competitive landscape overview",
    "opportunities": [
        "Specific opportunity 1",
        "Specific opportunity 2",
        "Specific opportunity 3",
        "Specific opportunity 4",
        "Specific opportunity 5"
    ],
    "threats": [
        "Specific competitive threat 1",
        "Specific competitive threat 2",
        "Specific competitive threat 3"
    ],
    "overall_winner": {{
        "url": "winning competitor URL",
        "label": "competitor label",
        "reason": "1-2 sentence explanation of why they win"
    }}
}}

Be specific, actionable, and data-driven. Focus on insights that help improve SEO/AEO performance."""

        return prompt

    def _format_list(self, items: List[str], max_items: int = 5) -> str:
        """
        Format list of items as bullet points.

        Args:
            items: List of strings
            max_items: Maximum items to include

        Returns:
            Formatted string with bullet points
        """
        if not items:
            return "  - None"

        formatted = []
        for item in items[:max_items]:
            # Truncate long items
            item_text = item[:150] if len(item) > 150 else item
            formatted.append(f"  - {item_text}")

        return '\n'.join(formatted)


async def analyze_competitive_landscape(
    competitor_data: List[Dict[str, Any]],
    api_key: str,
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Convenience function for batch competitive analysis.

    Args:
        competitor_data: List of competitor summaries
        api_key: OpenAI API key
        model: Model to use

    Returns:
        Competitive analysis results

    Example:
        >>> from app.services.batch_llm_analyzer import analyze_competitive_landscape
        >>> competitors = [
        ...     {'url': 'https://example.com', 'seo_score': 85, 'aeo_score': 78, ...},
        ...     {'url': 'https://competitor.com', 'seo_score': 72, 'aeo_score': 81, ...}
        ... ]
        >>> results = await analyze_competitive_landscape(competitors, "sk-...")
        >>> print(results['insights'])
    """
    analyzer = BatchLLMAnalyzer(api_key=api_key, model=model)
    return await analyzer.analyze_competitive_landscape(competitor_data)
