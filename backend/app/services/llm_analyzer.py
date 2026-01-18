"""LLM analyzer using Anthropic Claude for AEO (AI Engine Optimization) analysis."""

from anthropic import AsyncAnthropic
from typing import Dict, Any, List
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.core.exceptions import LLMAnalysisException

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    LLM-based AEO (AI Engine Optimization) Analyzer.

    Uses Anthropic Claude to evaluate:
    - Brand recognition and clarity
    - Content comprehensibility
    - Value proposition clarity
    - Target audience identification

    Generates AEO score (0-100) and recommendations.
    """

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        """
        Initialize LLM analyzer.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: claude-haiku-4-5-20251001)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_context_length = 2000  # Characters to send to Claude

    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def analyze_brand_recognition(
        self,
        url: str,
        page_text: str,
        meta_tags: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze brand recognition and content clarity using Claude.

        Args:
            url: Website URL
            page_text: Extracted page text content
            meta_tags: Meta tags dictionary

        Returns:
            Dictionary containing:
            - score: AEO score (0-100)
            - brand_recognition: Claude's analysis
            - llm_model: Model used
            - recommendations: List of recommendations

        Raises:
            LLMAnalysisException: If API call fails
        """
        logger.info(f"Starting LLM analysis for {url}")

        # Prepare context (limit length to avoid token limits)
        context = self._prepare_context(page_text, meta_tags)

        # Create prompt
        prompt = self._create_analysis_prompt(url, context)

        try:
            # Call Anthropic Claude API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=(
                    "You are an expert AI assistant evaluating website quality and clarity "
                    "for search engine and AI engine optimization (AEO). Your goal is to assess "
                    "how well an AI assistant like yourself would understand and recommend this website. "
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

            # Log the raw response for debugging
            logger.info(f"Claude raw response (first 500 chars): {response_text[:500]}")

            if not response_text or not response_text.strip():
                logger.error("Claude returned empty response")
                raise LLMAnalysisException("Claude returned empty response")

            # Try to extract JSON from markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]  # Remove ```
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]  # Remove closing ```
            cleaned_text = cleaned_text.strip()

            result = json.loads(cleaned_text)

            # Calculate AEO score
            clarity_score = result.get('clarity_score', 5)
            aeo_score = self._calculate_aeo_score(result, clarity_score)

            # Generate recommendations
            recommendations = self._generate_aeo_recommendations(result, clarity_score)

            logger.info(f"LLM analysis complete for {url}. AEO Score: {aeo_score}")

            return {
                'score': aeo_score,
                'brand_recognition': result,
                'llm_model': self.model,
                'recommendations': recommendations
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Raw response text: {response_text[:1000] if 'response_text' in locals() else 'N/A'}")
            raise LLMAnalysisException(f"Invalid JSON response from Claude: {str(e)}")
        except Exception as e:
            logger.error(f"Anthropic Claude API error: {e}")
            raise LLMAnalysisException(f"Anthropic Claude API error: {str(e)}")

    def _prepare_context(self, page_text: str, meta_tags: Dict[str, str]) -> str:
        """
        Prepare context to send to Claude, limiting length.

        Args:
            page_text: Full page text
            meta_tags: Meta tags dictionary

        Returns:
            Prepared context string
        """
        # Get key meta information
        title = meta_tags.get('title', '')
        description = meta_tags.get('description', '')

        # Limit body text length
        body_summary = page_text[:self.max_context_length] if len(page_text) > self.max_context_length else page_text

        # Remove excessive whitespace
        body_summary = ' '.join(body_summary.split())

        context = f"""
Title: {title}
Description: {description}

Content:
{body_summary}
"""
        return context.strip()

    def _create_analysis_prompt(self, url: str, context: str) -> str:
        """
        Create the analysis prompt for Claude.

        Args:
            url: Website URL
            context: Prepared context

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are analyzing a website for AI Engine Optimization (AEO).

Website URL: {url}

Website Content:
{context}

Please answer the following questions as if you were ChatGPT or another AI assistant responding to a user query about this website:

1. What does this website do? (Provide a clear, concise answer in 1-2 sentences)
2. What products or services does it offer? (Be specific)
3. Who is the target audience? (Be specific about demographics or user types)
4. What makes this brand unique or notable? (Identify unique value propositions)
5. Rate the clarity of the website's purpose on a scale of 1-10, where:
   - 1-3: Very unclear, confusing
   - 4-6: Somewhat clear but needs improvement
   - 7-8: Clear and understandable
   - 9-10: Exceptionally clear and compelling

6. Provide an overall impression of how well this website would be understood and recommended by an AI assistant.

Respond in JSON format with the following structure:
{{
    "what_it_does": "Clear description of what the website does",
    "products_services": "Specific products or services offered",
    "target_audience": "Specific target audience",
    "unique_value": "What makes this brand unique",
    "clarity_score": 8,
    "overall_impression": "Your overall assessment"
}}

Be honest and objective. If something is unclear or missing, say so."""

        return prompt

    def _calculate_aeo_score(self, llm_result: Dict[str, Any], clarity_score: int) -> float:
        """
        Calculate AEO score based on LLM analysis.

        Args:
            llm_result: Claude analysis result
            clarity_score: Clarity score (1-10)

        Returns:
            AEO score (0-100)
        """
        # Base score from clarity (70% weight)
        base_score = (clarity_score / 10) * 70

        # Completeness bonus (30% weight)
        completeness_score = 0
        required_fields = ['what_it_does', 'products_services', 'target_audience', 'unique_value']

        for field in required_fields:
            value = llm_result.get(field, '')
            if value and len(str(value)) > 20:  # Has substantial content
                completeness_score += 7.5  # 30 points total / 4 fields

        # Quality bonus - check for negative indicators
        penalty = 0
        overall_impression = llm_result.get('overall_impression', '').lower()

        if any(word in overall_impression for word in ['unclear', 'confusing', 'vague', 'difficult']):
            penalty = 10
        elif any(word in overall_impression for word in ['missing', 'lacking', 'insufficient']):
            penalty = 5

        final_score = base_score + completeness_score - penalty

        return round(min(max(final_score, 0), 100), 2)

    def _generate_aeo_recommendations(
        self,
        llm_result: Dict[str, Any],
        clarity_score: int
    ) -> List[Dict[str, Any]]:
        """
        Generate AEO improvement recommendations.

        Args:
            llm_result: Claude analysis result
            clarity_score: Clarity score (1-10)

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Low clarity score
        if clarity_score < 7:
            recommendations.append({
                'category': 'aeo',
                'priority': 'high',
                'title': 'Improve Content Clarity',
                'description': (
                    f'Your website purpose scored {clarity_score}/10 for clarity. AI engines struggle '
                    'to understand what you do. Add a clear value proposition and product descriptions '
                    'in the first paragraph of your homepage.'
                ),
                'impact': 'high'
            })

        # Check what_it_does field
        what_it_does = llm_result.get('what_it_does', '')
        if not what_it_does or len(what_it_does) < 30 or 'unclear' in what_it_does.lower():
            recommendations.append({
                'category': 'aeo',
                'priority': 'critical',
                'title': 'Define Your Value Proposition',
                'description': (
                    'AI engines cannot clearly determine what your website does. Add a prominent, '
                    'clear headline that explains your core offering in simple terms. Example: '
                    '"We help X do Y" or "The leading platform for Z".'
                ),
                'impact': 'critical'
            })

        # Check unique_value
        unique_value = llm_result.get('unique_value', '')
        if not unique_value or len(unique_value) < 20 or 'unclear' in unique_value.lower() or 'not clear' in unique_value.lower():
            recommendations.append({
                'category': 'aeo',
                'priority': 'medium',
                'title': 'Highlight Unique Selling Points',
                'description': (
                    'Your unique differentiators are not clear to AI engines. Add a section highlighting '
                    'what sets you apart from competitors. This helps AI assistants recommend you over alternatives.'
                ),
                'impact': 'medium'
            })

        # Check target_audience
        target_audience = llm_result.get('target_audience', '')
        if not target_audience or len(target_audience) < 20 or 'unclear' in target_audience.lower():
            recommendations.append({
                'category': 'aeo',
                'priority': 'medium',
                'title': 'Clarify Target Audience',
                'description': (
                    'Make it clearer who your product/service is for. AI engines need to understand '
                    'your target audience to recommend you to the right users. Add phrases like '
                    '"Perfect for..." or "Designed for..." in your content.'
                ),
                'impact': 'medium'
            })

        # Check products_services
        products_services = llm_result.get('products_services', '')
        if not products_services or len(products_services) < 30:
            recommendations.append({
                'category': 'aeo',
                'priority': 'high',
                'title': 'Detail Your Products/Services',
                'description': (
                    'Your products or services are not clearly described. Add detailed descriptions '
                    'of what you offer, including key features and benefits. This helps AI engines '
                    'match user queries to your offerings.'
                ),
                'impact': 'high'
            })

        # Overall impression check
        overall_impression = llm_result.get('overall_impression', '').lower()
        if any(word in overall_impression for word in ['poor', 'difficult', 'confusing', 'very unclear']):
            recommendations.append({
                'category': 'aeo',
                'priority': 'critical',
                'title': 'Comprehensive Content Overhaul Needed',
                'description': (
                    'AI engines find your website difficult to understand and recommend. Consider a '
                    'content audit focusing on: (1) Clear headline with value proposition, (2) Simple '
                    'language explaining what you do, (3) Prominent product/service descriptions, '
                    '(4) Customer benefits over features.'
                ),
                'impact': 'critical'
            })

        return recommendations


async def analyze_with_llm(
    url: str,
    page_text: str,
    meta_tags: Dict[str, str],
    api_key: str,
    model: str = "claude-3-5-sonnet-20241022"
) -> Dict[str, Any]:
    """
    Convenience function to analyze with LLM.

    Args:
        url: Website URL
        page_text: Page text content
        meta_tags: Meta tags dictionary
        api_key: Anthropic API key
        model: Model to use

    Returns:
        LLM analysis results

    Example:
        >>> from app.services.llm_analyzer import analyze_with_llm
        >>> result = await analyze_with_llm(
        ...     "https://example.com",
        ...     "Example content...",
        ...     {"title": "Example"},
        ...     "sk-ant-..."
        ... )
        >>> print(f"AEO Score: {result['score']}")
    """
    analyzer = LLMAnalyzer(api_key=api_key, model=model)
    return await analyzer.analyze_brand_recognition(url, page_text, meta_tags)
