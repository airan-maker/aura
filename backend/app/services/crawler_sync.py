"""Synchronous web crawler using Playwright for analyzing websites."""

from playwright.sync_api import sync_playwright, Page, Browser
from typing import Dict, Any, Optional, List
import logging
import time

from app.core.exceptions import CrawlerException

logger = logging.getLogger(__name__)


class WebCrawlerSync:
    """
    Playwright-based synchronous web crawler for extracting SEO/AEO data.

    Extracts:
    - HTML and text content
    - Meta tags (title, description, OG tags)
    - Heading structure (H1-H6)
    - JSON-LD Structured Data
    - Screenshots
    - Performance metrics
    - Mobile friendliness indicators
    """

    def __init__(self, timeout: int = 30000, headless: bool = True):
        """
        Initialize the web crawler.

        Args:
            timeout: Page load timeout in milliseconds (default: 30000)
            headless: Run browser in headless mode (default: True)
        """
        self.timeout = timeout
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None

    def __enter__(self):
        """Context manager entry - initialize Playwright."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def crawl(self, url: str) -> Dict[str, Any]:
        """
        Crawl a URL and extract all relevant data.

        Args:
            url: The URL to crawl

        Returns:
            Dictionary containing all extracted data

        Raises:
            CrawlerException: If crawling fails
        """
        if not self.browser:
            raise CrawlerException("Browser not initialized. Use 'with' context manager.")

        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AuraBot/1.0'
        )

        page = context.new_page()

        try:
            logger.info(f"Starting crawl of {url}")

            # Measure page load time
            start_time = time.time()

            # Navigate to the URL
            response = page.goto(
                url,
                wait_until='networkidle',
                timeout=self.timeout
            )

            load_time = time.time() - start_time

            if not response:
                raise CrawlerException(f"Failed to load {url} - no response")

            # Wait for any dynamic content
            page.wait_for_timeout(1000)

            # Extract data
            data = {
                'url': url,
                'status_code': response.status,
                'load_time': load_time,
                'html': page.content(),
                'text': page.inner_text('body'),
                'title': page.title(),
                'meta_tags': self._extract_meta_tags(page),
                'headings': self._extract_headings(page),
                'structured_data': self._extract_structured_data(page),
                'mobile_viewport': self._check_mobile_viewport(page),
                'ssl_enabled': url.startswith('https://'),
                'final_url': page.url,
                'screenshot': None  # Skip screenshots for now
            }

            logger.info(f"Successfully crawled {url} (status: {response.status}, time: {load_time:.2f}s)")

            return data

        except Exception as e:
            logger.error(f"Failed to crawl {url}: {str(e)}")
            raise CrawlerException(f"Failed to crawl {url}: {str(e)}")

        finally:
            context.close()

    def _extract_meta_tags(self, page: Page) -> Dict[str, str]:
        """Extract meta tags from page."""
        meta_tags = {}
        
        # Title
        meta_tags['title'] = page.title()
        
        # Meta tags
        metas = page.locator('meta').all()
        for meta in metas:
            name = meta.get_attribute('name') or meta.get_attribute('property')
            content = meta.get_attribute('content')
            if name and content:
                meta_tags[name] = content
        
        return meta_tags

    def _extract_headings(self, page: Page) -> Dict[str, List[str]]:
        """Extract heading structure."""
        headings = {}
        
        for level in range(1, 7):
            h_tags = page.locator(f'h{level}').all()
            headings[f'h{level}'] = [h.inner_text() for h in h_tags]
        
        return headings

    def _extract_structured_data(self, page: Page) -> List[Dict]:
        """Extract JSON-LD structured data."""
        structured_data = []
        
        try:
            scripts = page.locator('script[type="application/ld+json"]').all()
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.inner_text())
                    structured_data.append(data)
                except:
                    pass
        except:
            pass
        
        return structured_data

    def _check_mobile_viewport(self, page: Page) -> bool:
        """Check if mobile viewport meta tag is present."""
        viewport = page.locator('meta[name="viewport"]').first
        return viewport.count() > 0
