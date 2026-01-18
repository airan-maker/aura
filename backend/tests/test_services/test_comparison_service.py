"""Tests for ComparisonService."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.comparison_service import ComparisonService
from app.models.analysis import AnalysisResult, AnalysisRequest, AnalysisStatus
from app.models.competitive import CompetitiveAnalysisBatch, CompetitiveAnalysisURL


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.add = Mock()
    return db


@pytest.fixture
def comparison_service(mock_db):
    """Create ComparisonService instance."""
    return ComparisonService(db=mock_db, openai_api_key="test-key")


def create_mock_result(url: str, seo_score: float, aeo_score: float):
    """Helper to create mock analysis result."""
    request = AnalysisRequest(
        id=uuid4(),
        url=url,
        status=AnalysisStatus.COMPLETED
    )
    result = AnalysisResult(
        id=uuid4(),
        request_id=request.id,
        seo_score=seo_score,
        aeo_score=aeo_score,
        seo_metrics={'category_scores': {}, 'issues': []},
        aeo_metrics={},
        recommendations=[]
    )
    result.request = request
    return result


@pytest.mark.asyncio
async def test_calculate_rankings_seo(comparison_service):
    """Test SEO rankings calculation."""
    results = [
        create_mock_result("https://competitor1.com", 85.5, 70),
        create_mock_result("https://competitor2.com", 92.3, 80),
        create_mock_result("https://competitor3.com", 78.1, 75),
    ]

    rankings = comparison_service._calculate_rankings(results, 'seo')

    # Should be sorted by score descending
    assert len(rankings) == 3
    assert rankings[0]['url'] == "https://competitor2.com"
    assert rankings[0]['score'] == 92.3
    assert rankings[0]['rank'] == 1
    assert rankings[0]['delta_from_leader'] == 0.0

    assert rankings[1]['url'] == "https://competitor1.com"
    assert rankings[1]['rank'] == 2
    assert rankings[1]['delta_from_leader'] < 0

    assert rankings[2]['url'] == "https://competitor3.com"
    assert rankings[2]['rank'] == 3


@pytest.mark.asyncio
async def test_calculate_rankings_aeo(comparison_service):
    """Test AEO rankings calculation."""
    results = [
        create_mock_result("https://competitor1.com", 85, 88.5),
        create_mock_result("https://competitor2.com", 90, 82.3),
        create_mock_result("https://competitor3.com", 75, 91.2),
    ]

    rankings = comparison_service._calculate_rankings(results, 'aeo')

    # Should be sorted by AEO score descending
    assert rankings[0]['url'] == "https://competitor3.com"
    assert rankings[0]['score'] == 91.2
    assert rankings[0]['rank'] == 1

    assert rankings[1]['url'] == "https://competitor1.com"
    assert rankings[1]['rank'] == 2


@pytest.mark.asyncio
async def test_identify_market_leader(comparison_service):
    """Test market leader identification."""
    seo_rankings = [
        {'url': 'https://leader.com', 'score': 95, 'rank': 1, 'label': 'Leader'},
        {'url': 'https://second.com', 'score': 85, 'rank': 2, 'label': 'Second'},
    ]
    aeo_rankings = [
        {'url': 'https://leader.com', 'score': 92, 'rank': 1, 'label': 'Leader'},
        {'url': 'https://second.com', 'score': 88, 'rank': 2, 'label': 'Second'},
    ]

    leader = comparison_service._identify_market_leader(seo_rankings, aeo_rankings)

    assert leader['seo']['url'] == 'https://leader.com'
    assert leader['seo']['score'] == 95
    assert leader['aeo']['url'] == 'https://leader.com'
    assert leader['aeo']['score'] == 92


@pytest.mark.asyncio
async def test_calculate_market_average(comparison_service):
    """Test market average calculation."""
    seo_rankings = [
        {'score': 90},
        {'score': 80},
        {'score': 70},
    ]
    aeo_rankings = [
        {'score': 85},
        {'score': 75},
        {'score': 65},
    ]

    averages = comparison_service._calculate_market_average(seo_rankings, aeo_rankings)

    assert averages['seo'] == 80.0  # (90 + 80 + 70) / 3
    assert averages['aeo'] == 75.0  # (85 + 75 + 65) / 3


@pytest.mark.asyncio
async def test_prepare_competitor_data(comparison_service):
    """Test competitor data preparation for LLM."""
    results = [
        create_mock_result("https://competitor1.com", 85, 80),
        create_mock_result("https://competitor2.com", 75, 70),
    ]

    seo_rankings = [
        {'url': 'https://competitor1.com', 'rank': 1},
        {'url': 'https://competitor2.com', 'rank': 2},
    ]
    aeo_rankings = [
        {'url': 'https://competitor1.com', 'rank': 1},
        {'url': 'https://competitor2.com', 'rank': 2},
    ]

    competitor_data = comparison_service._prepare_competitor_data(
        results,
        seo_rankings,
        aeo_rankings
    )

    assert len(competitor_data) == 2
    assert competitor_data[0]['url'] == "https://competitor1.com"
    assert competitor_data[0]['seo_score'] == 85
    assert competitor_data[0]['aeo_score'] == 80
    assert competitor_data[0]['seo_rank'] == 1
    assert competitor_data[0]['aeo_rank'] == 1


@pytest.mark.asyncio
async def test_extract_top_issues(comparison_service):
    """Test issue extraction from analysis result."""
    result = create_mock_result("https://test.com", 70, 60)
    result.seo_metrics = {
        'issues': ['Missing meta description', 'Slow load time']
    }
    result.recommendations = [
        {'priority': 'critical', 'description': 'Add title tag'},
        {'priority': 'high', 'description': 'Enable HTTPS'},
        {'priority': 'low', 'description': 'Minor improvement'},
    ]

    issues = comparison_service._extract_top_issues(result)

    assert len(issues) >= 2
    assert 'Missing meta description' in issues
    assert 'Slow load time' in issues


@pytest.mark.asyncio
async def test_extract_strengths(comparison_service):
    """Test strength extraction from analysis result."""
    result = create_mock_result("https://test.com", 90, 85)
    result.seo_metrics = {
        'category_scores': {
            'meta_tags': 95,
            'performance': 92,
            'mobile': 88
        },
        'metrics': {
            'ssl_enabled': True,
            'mobile_friendly': True,
            'structured_data': [{'@type': 'Organization'}]
        }
    }

    strengths = comparison_service._extract_strengths(result)

    assert len(strengths) > 0
    assert any('meta' in s.lower() for s in strengths)
    assert any('performance' in s.lower() for s in strengths)
    assert any('https' in s.lower() or 'security' in s.lower() for s in strengths)


@pytest.mark.asyncio
async def test_generate_comparison_success(comparison_service, mock_db):
    """Test successful comparison generation."""
    batch_id = uuid4()

    # Mock batch with URL entries
    batch = CompetitiveAnalysisBatch(id=batch_id, total_urls=2)
    url1 = CompetitiveAnalysisURL(
        id=uuid4(),
        batch_id=batch_id,
        request_id=uuid4()
    )
    url2 = CompetitiveAnalysisURL(
        id=uuid4(),
        batch_id=batch_id,
        request_id=uuid4()
    )
    batch.urls = [url1, url2]

    # Mock results
    result1 = create_mock_result("https://competitor1.com", 85, 80)
    result2 = create_mock_result("https://competitor2.com", 75, 70)

    # Mock database responses
    mock_batch_result = Mock()
    mock_batch_result.scalar_one_or_none.return_value = batch

    mock_results = Mock()
    mock_results.scalars.return_value.all.return_value = [result1, result2]

    mock_db.execute.side_effect = [mock_batch_result, mock_results]

    # Mock LLM analyzer
    with patch.object(comparison_service.llm_analyzer, 'analyze_competitive_landscape') as mock_llm:
        mock_llm.return_value = {
            'insights': 'Test insights',
            'opportunities': ['Opportunity 1', 'Opportunity 2'],
            'threats': ['Threat 1']
        }

        comparison = await comparison_service.generate_comparison(batch_id)

        assert comparison is not None
        assert comparison.batch_id == batch_id
        assert comparison.seo_comparison is not None
        assert comparison.aeo_comparison is not None
        assert comparison.market_leader is not None
        assert comparison.market_average is not None
        assert comparison.competitive_insights == 'Test insights'
        assert len(comparison.opportunities) == 2
        assert len(comparison.threats) == 1

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_generate_comparison_insufficient_results(comparison_service, mock_db):
    """Test comparison generation with insufficient results."""
    batch_id = uuid4()

    # Mock batch with only 1 URL
    batch = CompetitiveAnalysisBatch(id=batch_id, total_urls=1)
    url1 = CompetitiveAnalysisURL(
        id=uuid4(),
        batch_id=batch_id,
        request_id=uuid4()
    )
    batch.urls = [url1]

    result1 = create_mock_result("https://competitor1.com", 85, 80)

    mock_batch_result = Mock()
    mock_batch_result.scalar_one_or_none.return_value = batch

    mock_results = Mock()
    mock_results.scalars.return_value.all.return_value = [result1]

    mock_db.execute.side_effect = [mock_batch_result, mock_results]

    comparison = await comparison_service.generate_comparison(batch_id)

    # Should return None with < 2 results
    assert comparison is None
