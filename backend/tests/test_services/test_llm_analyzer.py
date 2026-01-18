"""Tests for LLM analyzer service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.llm_analyzer import LLMAnalyzer, analyze_with_llm
from app.core.exceptions import LLMAnalysisException


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    def _create_response(clarity_score=8, what_it_does="A website for testing",
                        products_services="Testing services",
                        target_audience="Developers",
                        unique_value="Fast and reliable testing"):
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = json.dumps({
            "what_it_does": what_it_does,
            "products_services": products_services,
            "target_audience": target_audience,
            "unique_value": unique_value,
            "clarity_score": clarity_score,
            "overall_impression": "Clear and well-structured website"
        })
        return response
    return _create_response


@pytest.mark.asyncio
async def test_llm_analyzer_high_clarity(mock_openai_response):
    """Test LLM analyzer with high clarity score."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    # Mock the OpenAI client
    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_openai_response(clarity_score=9)

        result = await analyzer.analyze_brand_recognition(
            url="https://example.com",
            page_text="This is a test website content",
            meta_tags={"title": "Test Site", "description": "Test description"}
        )

        # Should have high AEO score
        assert result['score'] >= 85
        assert result['score'] <= 100

        # Should have brand recognition data
        assert 'brand_recognition' in result
        assert result['brand_recognition']['clarity_score'] == 9

        # Should have minimal recommendations for high score
        assert len(result['recommendations']) <= 2


@pytest.mark.asyncio
async def test_llm_analyzer_low_clarity(mock_openai_response):
    """Test LLM analyzer with low clarity score."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_openai_response(
            clarity_score=3,
            what_it_does="Unclear",
            products_services="Not clear",
            target_audience="Unknown",
            unique_value="Not specified"
        )

        result = await analyzer.analyze_brand_recognition(
            url="https://example.com",
            page_text="Test content",
            meta_tags={"title": "Test"}
        )

        # Should have low AEO score
        assert result['score'] < 50

        # Should have many recommendations
        assert len(result['recommendations']) >= 3

        # Should have critical priority recommendations
        assert any(
            rec['priority'] == 'critical'
            for rec in result['recommendations']
        )


@pytest.mark.asyncio
async def test_llm_analyzer_unclear_value_proposition(mock_openai_response):
    """Test detection of unclear value proposition."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_openai_response(
            clarity_score=5,
            what_it_does="It's unclear what this site does",
            products_services="Some products",
            target_audience="General users",
            unique_value="Nothing particularly unique"
        )

        result = await analyzer.analyze_brand_recognition(
            url="https://example.com",
            page_text="Test content",
            meta_tags={"title": "Test"}
        )

        # Should recommend defining value proposition
        assert any(
            'value proposition' in rec['title'].lower() or 'what your website does' in rec['description'].lower()
            for rec in result['recommendations']
        )


@pytest.mark.asyncio
async def test_llm_analyzer_context_preparation():
    """Test context preparation with long text."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    # Create very long text (> 2000 chars)
    long_text = "Lorem ipsum " * 200  # ~2400 chars

    context = analyzer._prepare_context(
        page_text=long_text,
        meta_tags={
            "title": "Test Title",
            "description": "Test Description"
        }
    )

    # Should be limited to max length
    assert len(context) <= 2200  # Some extra for title/description
    assert "Test Title" in context
    assert "Test Description" in context


@pytest.mark.asyncio
async def test_llm_analyzer_aeo_score_calculation():
    """Test AEO score calculation logic."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    # Perfect result
    perfect_result = {
        "what_it_does": "A comprehensive testing platform for developers",
        "products_services": "Automated testing tools and continuous integration services",
        "target_audience": "Software development teams and QA professionals",
        "unique_value": "Industry-leading speed and reliability with 99.9% uptime",
        "clarity_score": 10,
        "overall_impression": "Exceptionally clear and well-presented"
    }

    score = analyzer._calculate_aeo_score(perfect_result, 10)

    # Should be close to 100
    assert score >= 95
    assert score <= 100


@pytest.mark.asyncio
async def test_llm_analyzer_aeo_score_with_penalty():
    """Test AEO score with penalties for negative indicators."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    # Result with negative impression
    negative_result = {
        "what_it_does": "Some kind of service",
        "products_services": "Various products",
        "target_audience": "People",
        "unique_value": "Nothing special",
        "clarity_score": 5,
        "overall_impression": "The website is very unclear and confusing to understand"
    }

    score = analyzer._calculate_aeo_score(negative_result, 5)

    # Should have penalty applied
    assert score < 50  # Base would be 35 (5/10 * 70), but penalties apply


@pytest.mark.asyncio
async def test_llm_analyzer_recommendations_for_unclear_audience():
    """Test recommendations for unclear target audience."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    result = {
        "what_it_does": "A good service",
        "products_services": "Quality products",
        "target_audience": "Unclear",
        "unique_value": "Good quality",
        "clarity_score": 6,
        "overall_impression": "Decent but could be clearer"
    }

    recommendations = analyzer._generate_aeo_recommendations(result, 6)

    # Should recommend clarifying target audience
    assert any(
        'target audience' in rec['title'].lower()
        for rec in recommendations
    )


@pytest.mark.asyncio
async def test_llm_analyzer_recommendations_for_missing_products():
    """Test recommendations for missing product descriptions."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    result = {
        "what_it_does": "A platform",
        "products_services": "Products",  # Too short
        "target_audience": "Users",
        "unique_value": "Good",
        "clarity_score": 6,
        "overall_impression": "Basic information"
    }

    recommendations = analyzer._generate_aeo_recommendations(result, 6)

    # Should recommend detailing products
    assert any(
        'products' in rec['title'].lower() or 'services' in rec['title'].lower()
        for rec in recommendations
    )


@pytest.mark.asyncio
async def test_llm_analyzer_api_error_handling(mock_openai_response):
    """Test handling of API errors."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        # Simulate API error
        mock_create.side_effect = Exception("API rate limit exceeded")

        with pytest.raises(LLMAnalysisException) as exc_info:
            await analyzer.analyze_brand_recognition(
                url="https://example.com",
                page_text="Test",
                meta_tags={"title": "Test"}
            )

        assert "OpenAI API error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_llm_analyzer_invalid_json_response():
    """Test handling of invalid JSON response."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        # Return invalid JSON
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Not valid JSON"
        mock_create.return_value = response

        with pytest.raises(LLMAnalysisException) as exc_info:
            await analyzer.analyze_brand_recognition(
                url="https://example.com",
                page_text="Test",
                meta_tags={"title": "Test"}
            )

        assert "Invalid JSON" in str(exc_info.value)


@pytest.mark.asyncio
async def test_llm_analyzer_prompt_includes_url():
    """Test that prompt includes the URL."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    url = "https://example.com"
    context = "Test context"

    prompt = analyzer._create_analysis_prompt(url, context)

    # URL should be in prompt
    assert url in prompt

    # Context should be in prompt
    assert context in prompt

    # Should ask for JSON response
    assert "JSON" in prompt


@pytest.mark.asyncio
async def test_llm_analyzer_retry_on_failure(mock_openai_response):
    """Test retry logic on temporary failures."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        # Fail twice, then succeed
        mock_create.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            mock_openai_response(clarity_score=8)
        ]

        result = await analyzer.analyze_brand_recognition(
            url="https://example.com",
            page_text="Test",
            meta_tags={"title": "Test"}
        )

        # Should eventually succeed
        assert result['score'] > 0

        # Should have been called 3 times (2 failures + 1 success)
        assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_analyze_with_llm_convenience_function(mock_openai_response):
    """Test the convenience function."""
    with patch('app.services.llm_analyzer.AsyncOpenAI') as mock_openai_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response(clarity_score=7)
        )
        mock_openai_class.return_value = mock_client

        result = await analyze_with_llm(
            url="https://example.com",
            page_text="Test content",
            meta_tags={"title": "Test"},
            api_key="test-key"
        )

        # Should return valid result
        assert 'score' in result
        assert 'brand_recognition' in result
        assert 'recommendations' in result


@pytest.mark.asyncio
async def test_llm_analyzer_completeness_scoring():
    """Test completeness affects scoring."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    # Complete result
    complete_result = {
        "what_it_does": "A comprehensive platform for managing business operations and workflows",
        "products_services": "Cloud-based project management software with collaboration tools",
        "target_audience": "Small to medium-sized businesses and enterprise teams",
        "unique_value": "Integrated AI-powered automation and real-time analytics",
        "clarity_score": 8
    }

    # Incomplete result (short answers)
    incomplete_result = {
        "what_it_does": "A platform",
        "products_services": "Software",
        "target_audience": "Users",
        "unique_value": "Good",
        "clarity_score": 8
    }

    complete_score = analyzer._calculate_aeo_score(complete_result, 8)
    incomplete_score = analyzer._calculate_aeo_score(incomplete_result, 8)

    # Complete should score higher
    assert complete_score > incomplete_score
    assert complete_score >= 85
    assert incomplete_score < 75


@pytest.mark.asyncio
async def test_llm_analyzer_result_structure(mock_openai_response):
    """Test that result has correct structure."""
    analyzer = LLMAnalyzer(api_key="test-key", model="gpt-4")

    with patch.object(analyzer.client.chat.completions, 'create',
                     new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_openai_response(clarity_score=8)

        result = await analyzer.analyze_brand_recognition(
            url="https://example.com",
            page_text="Test",
            meta_tags={"title": "Test"}
        )

        # Check required fields
        assert 'score' in result
        assert 'brand_recognition' in result
        assert 'llm_model' in result
        assert 'recommendations' in result

        # Score should be 0-100
        assert 0 <= result['score'] <= 100

        # Model should be specified
        assert result['llm_model'] == 'gpt-4'

        # Recommendations should be a list
        assert isinstance(result['recommendations'], list)

        # Each recommendation should have required fields
        for rec in result['recommendations']:
            assert 'category' in rec
            assert 'priority' in rec
            assert 'title' in rec
            assert 'description' in rec
            assert 'impact' in rec
