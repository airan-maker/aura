"""Tests for the web crawler service."""

import pytest
from app.services.crawler import WebCrawler, crawl_url
from app.core.exceptions import CrawlerException


@pytest.mark.asyncio
async def test_crawler_basic_functionality():
    """Test basic crawling functionality with example.com."""
    async with WebCrawler(timeout=30000) as crawler:
        data = await crawler.crawl("https://example.com")

        # Check basic fields
        assert data['url'] == "https://example.com"
        assert data['status_code'] == 200
        assert data['load_time'] > 0
        assert len(data['html']) > 0
        assert len(data['text']) > 0

        # Check SSL
        assert data['ssl_enabled'] is True


@pytest.mark.asyncio
async def test_crawler_meta_tags():
    """Test meta tag extraction."""
    async with WebCrawler() as crawler:
        data = await crawler.crawl("https://example.com")

        meta_tags = data['meta_tags']

        # Example.com should have a title
        assert 'title' in meta_tags
        assert len(meta_tags['title']) > 0


@pytest.mark.asyncio
async def test_crawler_headings():
    """Test heading extraction."""
    async with WebCrawler() as crawler:
        data = await crawler.crawl("https://example.com")

        headings = data['headings']

        # Check all heading levels exist
        for i in range(1, 7):
            assert f'h{i}' in headings
            assert isinstance(headings[f'h{i}'], list)


@pytest.mark.asyncio
async def test_crawler_screenshot():
    """Test screenshot capture."""
    async with WebCrawler() as crawler:
        data = await crawler.crawl("https://example.com")

        screenshot = data['screenshot']

        # Screenshot should be PNG bytes
        assert isinstance(screenshot, bytes)
        assert len(screenshot) > 0
        # PNG signature
        assert screenshot[:8] == b'\x89PNG\r\n\x1a\n'


@pytest.mark.asyncio
async def test_crawler_mobile_friendly():
    """Test mobile-friendly detection."""
    async with WebCrawler() as crawler:
        data = await crawler.crawl("https://example.com")

        # Mobile friendly should be a boolean
        assert isinstance(data['mobile_friendly'], bool)


@pytest.mark.asyncio
async def test_crawler_structured_data():
    """Test structured data extraction."""
    async with WebCrawler() as crawler:
        data = await crawler.crawl("https://example.com")

        structured_data = data['structured_data']

        # Should be a list (may be empty)
        assert isinstance(structured_data, list)


@pytest.mark.asyncio
async def test_crawler_timeout():
    """Test timeout handling."""
    async with WebCrawler(timeout=1) as crawler:  # 1ms timeout
        with pytest.raises(CrawlerException) as exc_info:
            await crawler.crawl("https://example.com")

        assert "Timeout" in str(exc_info.value) or "Failed to crawl" in str(exc_info.value)


@pytest.mark.asyncio
async def test_crawler_invalid_url():
    """Test handling of invalid URLs."""
    async with WebCrawler() as crawler:
        with pytest.raises(CrawlerException):
            await crawler.crawl("invalid-url")


@pytest.mark.asyncio
async def test_crawl_url_convenience_function():
    """Test the convenience function."""
    data = await crawl_url("https://example.com")

    assert data['url'] == "https://example.com"
    assert data['status_code'] == 200


@pytest.mark.asyncio
async def test_crawler_redirect_detection():
    """Test redirect detection via final_url."""
    async with WebCrawler() as crawler:
        # httpbin.org/redirect/1 redirects to /get
        data = await crawler.crawl("http://httpbin.org/redirect/1")

        # final_url should be different from original
        assert data['final_url'] != "http://httpbin.org/redirect/1"
        assert "/get" in data['final_url']


@pytest.mark.asyncio
async def test_crawler_context_manager_error():
    """Test that using crawler without context manager raises error."""
    crawler = WebCrawler()

    with pytest.raises(CrawlerException) as exc_info:
        await crawler.crawl("https://example.com")

    assert "not initialized" in str(exc_info.value).lower()
