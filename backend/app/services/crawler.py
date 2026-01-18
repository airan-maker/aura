"""Web crawler using Playwright for analyzing websites."""

from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, Any, Optional, List
import asyncio
import logging

from app.core.exceptions import CrawlerException

logger = logging.getLogger(__name__)


class WebCrawler:
    """
    Playwright-based web crawler for extracting SEO/AEO data.

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

    async def __aenter__(self):
        """Async context manager entry - initialize Playwright."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def crawl(self, url: str) -> Dict[str, Any]:
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
            raise CrawlerException("Browser not initialized. Use 'async with' context manager.")

        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AuraBot/1.0'
        )

        page = await context.new_page()

        try:
            logger.info(f"Starting crawl of {url}")

            # Measure page load time
            start_time = asyncio.get_event_loop().time()

            # Navigate to the URL
            response = await page.goto(
                url,
                wait_until='networkidle',
                timeout=self.timeout
            )

            load_time = asyncio.get_event_loop().time() - start_time

            if not response:
                raise CrawlerException(f"Failed to load {url} - no response")

            # Wait for any dynamic content
            await page.wait_for_timeout(1000)

            # Extract data in parallel for better performance
            html_task = page.content()
            text_task = self._extract_text(page)
            meta_task = self._extract_meta_tags(page)
            headings_task = self._extract_headings(page)
            structured_data_task = self._extract_structured_data(page)
            screenshot_task = page.screenshot(full_page=True, type='png')
            mobile_task = self._check_mobile_friendly(page)

            # Await all tasks
            html_content, text_content, meta_tags, headings, structured_data, screenshot, mobile_friendly = await asyncio.gather(
                html_task,
                text_task,
                meta_task,
                headings_task,
                structured_data_task,
                screenshot_task,
                mobile_task
            )

            logger.info(f"Successfully crawled {url} in {load_time:.2f}s")

            return {
                'url': url,
                'status_code': response.status,
                'load_time': round(load_time, 2),
                'html': html_content,
                'text': text_content,
                'meta_tags': meta_tags,
                'headings': headings,
                'structured_data': structured_data,
                'screenshot': screenshot,
                'mobile_friendly': mobile_friendly,
                'ssl_enabled': url.startswith('https://'),
                'final_url': page.url,  # Check for redirects
            }

        except asyncio.TimeoutError:
            raise CrawlerException(f"Timeout while loading {url} (timeout: {self.timeout}ms)")
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            raise CrawlerException(f"Failed to crawl {url}: {str(e)}")
        finally:
            await context.close()

    async def _extract_text(self, page: Page) -> str:
        """
        Extract visible text content from the page.

        Args:
            page: Playwright page object

        Returns:
            Extracted text content
        """
        try:
            text = await page.evaluate('''() => {
                // Remove script, style, and hidden elements
                const clone = document.body.cloneNode(true);
                const elementsToRemove = clone.querySelectorAll('script, style, noscript, [hidden]');
                elementsToRemove.forEach(el => el.remove());
                return clone.innerText || clone.textContent || '';
            }''')
            return text.strip()
        except Exception as e:
            logger.warning(f"Failed to extract text: {e}")
            return ""

    async def _extract_meta_tags(self, page: Page) -> Dict[str, str]:
        """
        Extract meta tags from the page.

        Extracts:
        - title
        - description
        - keywords
        - Open Graph tags (og:*)
        - Twitter Card tags (twitter:*)
        - canonical URL

        Args:
            page: Playwright page object

        Returns:
            Dictionary of meta tags
        """
        try:
            meta_tags = await page.evaluate('''() => {
                const tags = {};

                // Title tag
                tags['title'] = document.title || '';

                // Meta tags
                document.querySelectorAll('meta').forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name && content) {
                        tags[name.toLowerCase()] = content;
                    }
                });

                // Canonical URL
                const canonical = document.querySelector('link[rel="canonical"]');
                if (canonical) {
                    tags['canonical'] = canonical.href;
                }

                // Robots meta
                const robots = document.querySelector('meta[name="robots"]');
                if (robots) {
                    tags['robots'] = robots.getAttribute('content');
                }

                return tags;
            }''')
            return meta_tags
        except Exception as e:
            logger.warning(f"Failed to extract meta tags: {e}")
            return {}

    async def _extract_headings(self, page: Page) -> Dict[str, List[str]]:
        """
        Extract heading structure (H1-H6) from the page.

        Args:
            page: Playwright page object

        Returns:
            Dictionary with h1-h6 keys and lists of heading texts
        """
        try:
            headings = await page.evaluate('''() => {
                const result = {};
                for (let i = 1; i <= 6; i++) {
                    const tags = Array.from(document.querySelectorAll(`h${i}`));
                    result[`h${i}`] = tags
                        .map(tag => tag.textContent.trim())
                        .filter(text => text.length > 0);
                }
                return result;
            }''')
            return headings
        except Exception as e:
            logger.warning(f"Failed to extract headings: {e}")
            return {f'h{i}': [] for i in range(1, 7)}

    async def _extract_structured_data(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract JSON-LD structured data from the page.

        Args:
            page: Playwright page object

        Returns:
            List of structured data objects
        """
        try:
            structured_data = await page.evaluate('''() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                const data = [];

                scripts.forEach(script => {
                    try {
                        const json = JSON.parse(script.textContent);
                        data.push(json);
                    } catch (e) {
                        // Skip invalid JSON
                    }
                });

                return data;
            }''')
            return structured_data
        except Exception as e:
            logger.warning(f"Failed to extract structured data: {e}")
            return []

    async def _check_mobile_friendly(self, page: Page) -> bool:
        """
        Check if the page has mobile-friendly indicators.

        Checks for:
        - viewport meta tag
        - responsive meta tags

        Args:
            page: Playwright page object

        Returns:
            True if mobile-friendly indicators are present
        """
        try:
            has_viewport = await page.evaluate('''() => {
                const viewport = document.querySelector('meta[name="viewport"]');
                return viewport !== null;
            }''')
            return has_viewport
        except Exception as e:
            logger.warning(f"Failed to check mobile friendliness: {e}")
            return False


async def crawl_url(url: str, timeout: int = 30000) -> Dict[str, Any]:
    """
    Convenience function to crawl a single URL.

    Args:
        url: URL to crawl
        timeout: Timeout in milliseconds

    Returns:
        Crawled data dictionary

    Example:
        >>> data = await crawl_url("https://example.com")
        >>> print(data['meta_tags']['title'])
    """
    async with WebCrawler(timeout=timeout) as crawler:
        return await crawler.crawl(url)
