"""Tests for SEO analyzer service."""

import pytest
from app.services.seo_analyzer import SEOAnalyzer, analyze_seo


def test_seo_analyzer_perfect_score():
    """Test SEO analyzer with perfect data."""
    analyzer = SEOAnalyzer()

    perfect_data = {
        'url': 'https://example.com',
        'meta_tags': {
            'title': 'Perfect SEO Title - Example Domain',  # 38 chars - perfect
            'description': 'This is a perfect meta description that is between 120 and 160 characters long, providing valuable information about the page content.',  # 147 chars
            'og:title': 'Open Graph Title',
            'og:description': 'OG Description',
            'og:image': 'https://example.com/image.jpg',
            'og:url': 'https://example.com',
            'canonical': 'https://example.com'
        },
        'headings': {
            'h1': ['Main Heading'],
            'h2': ['Subheading 1', 'Subheading 2'],
            'h3': ['Detail 1', 'Detail 2'],
            'h4': [],
            'h5': [],
            'h6': []
        },
        'load_time': 1.5,  # Excellent
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': [
            {
                '@context': 'https://schema.org',
                '@type': 'Organization',
                'name': 'Example'
            }
        ]
    }

    result = analyzer.analyze(perfect_data)

    # Should have high score (close to 100)
    assert result['score'] >= 95
    assert result['score'] <= 100

    # All category scores should be high
    assert result['category_scores']['meta_tags'] >= 90
    assert result['category_scores']['headings'] == 100
    assert result['category_scores']['performance'] == 100
    assert result['category_scores']['mobile'] == 100
    assert result['category_scores']['security'] == 100
    assert result['category_scores']['structured_data'] == 100

    # Should have minimal issues
    assert len(result['issues']) == 0


def test_seo_analyzer_missing_title():
    """Test analyzer detects missing title."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {},
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have lower score due to missing title
    assert result['category_scores']['meta_tags'] < 50

    # Should have issue about missing title
    assert any('title' in issue.lower() for issue in result['issues'])

    # Should have recommendation to add title
    assert any(
        rec['title'] == 'Add Title Tag'
        for rec in result['recommendations']
    )


def test_seo_analyzer_title_too_short():
    """Test analyzer detects title that's too short."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Short'  # Only 5 chars
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have issue about short title
    assert any('too short' in issue.lower() for issue in result['issues'])

    # Should have recommendation to expand title
    assert any(
        'expand' in rec['title'].lower() and 'title' in rec['title'].lower()
        for rec in result['recommendations']
    )


def test_seo_analyzer_title_too_long():
    """Test analyzer detects title that's too long."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'This is a very long title that exceeds the recommended maximum length of 60 characters for SEO purposes'  # 104 chars
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have issue about long title
    assert any('too long' in issue.lower() for issue in result['issues'])


def test_seo_analyzer_missing_meta_description():
    """Test analyzer detects missing meta description."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title Length Here - Example'
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have issue about missing description
    assert any('description' in issue.lower() for issue in result['issues'])

    # Should have recommendation
    assert any(
        rec['title'] == 'Add Meta Description'
        for rec in result['recommendations']
    )


def test_seo_analyzer_missing_h1():
    """Test analyzer detects missing H1 tag."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users searching for this content.'
        },
        'headings': {
            'h1': [],  # No H1
            'h2': ['Subheading'],
            'h3': [], 'h4': [], 'h5': [], 'h6': []
        },
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have low headings score
    assert result['category_scores']['headings'] <= 50

    # Should have issue about missing H1
    assert any('h1' in issue.lower() for issue in result['issues'])

    # Should have critical recommendation
    assert any(
        rec['priority'] == 'critical' and 'h1' in rec['title'].lower()
        for rec in result['recommendations']
    )


def test_seo_analyzer_multiple_h1():
    """Test analyzer detects multiple H1 tags."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users.'
        },
        'headings': {
            'h1': ['First H1', 'Second H1', 'Third H1'],  # Multiple H1s
            'h2': ['Subheading'],
            'h3': [], 'h4': [], 'h5': [], 'h6': []
        },
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have issue about multiple H1s
    assert any('multiple' in issue.lower() and 'h1' in issue.lower() for issue in result['issues'])


def test_seo_analyzer_slow_performance():
    """Test analyzer detects slow page load."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users.'
        },
        'headings': {'h1': ['Test'], 'h2': ['Sub'], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 8.5,  # Very slow
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have low performance score
    assert result['category_scores']['performance'] < 30

    # Should have issue about slow load time
    assert any('slow' in issue.lower() for issue in result['issues'])

    # Should have critical recommendation
    assert any(
        'speed' in rec['title'].lower() and rec['priority'] in ['critical', 'high']
        for rec in result['recommendations']
    )


def test_seo_analyzer_not_mobile_friendly():
    """Test analyzer detects missing mobile optimization."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users.'
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': False,  # Not mobile friendly
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have 0 mobile score
    assert result['category_scores']['mobile'] == 0

    # Should have critical recommendation about viewport
    assert any(
        'viewport' in rec['description'].lower() and rec['priority'] == 'critical'
        for rec in result['recommendations']
    )


def test_seo_analyzer_no_https():
    """Test analyzer detects missing HTTPS."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users.'
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': False,  # No HTTPS
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have 0 security score
    assert result['category_scores']['security'] == 0

    # Should have critical recommendation about HTTPS
    assert any(
        'https' in rec['description'].lower() and rec['priority'] == 'critical'
        for rec in result['recommendations']
    )


def test_seo_analyzer_no_structured_data():
    """Test analyzer detects missing structured data."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users.'
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []  # No structured data
    }

    result = analyzer.analyze(data)

    # Should have 0 structured data score
    assert result['category_scores']['structured_data'] == 0

    # Should have recommendation about structured data
    assert any(
        'structured data' in rec['title'].lower()
        for rec in result['recommendations']
    )


def test_seo_analyzer_open_graph_partial():
    """Test analyzer with partial Open Graph tags."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {
            'title': 'Good Title - Example',
            'description': 'Good description with enough length to pass validation checks and provide value to users.',
            'og:title': 'OG Title',
            'og:description': 'OG Description'
            # Missing og:image and og:url
        },
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have recommendation to complete OG tags
    assert any(
        'open graph' in rec['title'].lower()
        for rec in result['recommendations']
    )


def test_analyze_seo_convenience_function():
    """Test the convenience function."""
    crawl_data = {
        'url': 'https://example.com',
        'meta_tags': {
            'title': 'Example Domain - Test Site',
            'description': 'This is an example domain used for testing and documentation purposes with sufficient length for SEO.'
        },
        'headings': {'h1': ['Example'], 'h2': ['More Info'], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 1.8,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyze_seo(crawl_data)

    # Should return valid result
    assert 'score' in result
    assert 'category_scores' in result
    assert 'issues' in result
    assert 'recommendations' in result
    assert 'metrics' in result

    # Score should be between 0 and 100
    assert 0 <= result['score'] <= 100


def test_seo_analyzer_metrics_included():
    """Test that metrics are included in the result."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {'title': 'Test'},
        'headings': {'h1': ['Test'], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 2.0,
        'mobile_friendly': True,
        'ssl_enabled': True,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Metrics should be included
    assert 'metrics' in result
    assert 'meta_tags' in result['metrics']
    assert 'headings' in result['metrics']
    assert 'load_time' in result['metrics']
    assert 'mobile_friendly' in result['metrics']
    assert 'ssl_enabled' in result['metrics']
    assert 'structured_data' in result['metrics']


def test_seo_analyzer_recommendation_structure():
    """Test that recommendations have proper structure."""
    analyzer = SEOAnalyzer()

    data = {
        'meta_tags': {},  # Missing everything to generate recommendations
        'headings': {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'load_time': 10.0,
        'mobile_friendly': False,
        'ssl_enabled': False,
        'structured_data': []
    }

    result = analyzer.analyze(data)

    # Should have many recommendations
    assert len(result['recommendations']) > 0

    # Each recommendation should have required fields
    for rec in result['recommendations']:
        assert 'category' in rec
        assert 'priority' in rec
        assert 'title' in rec
        assert 'description' in rec
        assert 'impact' in rec

        # Priority should be valid
        assert rec['priority'] in ['critical', 'high', 'medium', 'low']

        # Category should be 'seo'
        assert rec['category'] == 'seo'
