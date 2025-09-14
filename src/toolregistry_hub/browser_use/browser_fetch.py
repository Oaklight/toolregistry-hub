"""Simple browser-based web content fetching using Playwright and Firefox."""

import asyncio
from typing import Any, Dict, Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class BrowserFetch:
    """Simple browser-based web content fetcher using headless Firefox."""

    def __init__(self, headless: bool = True, timeout: float = 30.0):
        """Initialize the browser fetcher.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser instance."""
        try:
            self.playwright = await async_playwright().start()

            # Launch Firefox with anti-detection settings
            self.browser = await self.playwright.firefox.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
                firefox_user_prefs={
                    "dom.webdriver.enabled": False,
                    "useAutomationExtension": False,
                    "general.platform.override": "Linux x86_64",
                    "general.useragent.override": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
                },
            )

            # Create a new context with additional stealth settings
            self.context = await self.browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            )

            # Add stealth script to all pages
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)

            logger.info("Browser started successfully")

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    async def close(self):
        """Close the browser instance."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, "playwright"):
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def fetch_content(
        self, url: str, wait_for_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch content from a URL using the browser.

        Args:
            url: The URL to fetch content from
            wait_for_selector: Optional CSS selector to wait for before extracting content

        Returns:
            Dictionary containing the extracted content and metadata
        """
        if not self.context:
            raise RuntimeError(
                "Browser not started. Call start() first or use as context manager."
            )

        page = None
        try:
            page = await self.context.new_page()

            # Navigate to the URL
            logger.info(f"Navigating to: {url}")
            response = await page.goto(
                url, timeout=self.timeout * 1000, wait_until="networkidle"
            )

            if not response:
                raise RuntimeError(f"Failed to load page: {url}")

            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}: {url}")

            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(
                    wait_for_selector, timeout=self.timeout * 1000
                )

            # Wait a bit for dynamic content to load
            await page.wait_for_timeout(2000)

            # Extract content using JavaScript
            content_data = await page.evaluate("""
                () => {
                    // Remove unwanted elements
                    const unwantedSelectors = [
                        'script', 'style', 'nav', 'footer', 'header',
                        '.advertisement', '.ads', '.sidebar', '.popup',
                        '[class*="cookie"]', '[class*="banner"]'
                    ];
                    
                    unwantedSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => el.remove());
                    });
                    
                    // Find main content area
                    const contentSelectors = [
                        'main', 'article', '[role="main"]',
                        '.content', '.post-content', '.entry-content',
                        '.article-body', '.story-body'
                    ];
                    
                    let mainContent = null;
                    for (const selector of contentSelectors) {
                        mainContent = document.querySelector(selector);
                        if (mainContent) break;
                    }
                    
                    // Fallback to body if no main content found
                    const source = mainContent || document.body;
                    
                    // Extract metadata
                    const title = document.title || '';
                    const description = document.querySelector('meta[name="description"]')?.content || '';
                    const ogTitle = document.querySelector('meta[property="og:title"]')?.content || '';
                    const ogDescription = document.querySelector('meta[property="og:description"]')?.content || '';
                    
                    // Extract text content
                    const textContent = source ? source.innerText.trim() : '';
                    
                    // Count elements
                    const wordCount = textContent.split(/\\s+/).filter(word => word.length > 0).length;
                    const linkCount = document.querySelectorAll('a[href]').length;
                    const imageCount = document.querySelectorAll('img').length;
                    
                    return {
                        title: title,
                        content: textContent,
                        description: description,
                        og_title: ogTitle,
                        og_description: ogDescription,
                        word_count: wordCount,
                        link_count: linkCount,
                        image_count: imageCount,
                        url: window.location.href
                    };
                }
            """)

            logger.info(
                f"Successfully extracted content from {url} ({content_data['word_count']} words)"
            )

            return {
                "success": True,
                "url": url,
                "status_code": response.status,
                "title": content_data["title"],
                "content": content_data["content"],
                "metadata": {
                    "description": content_data["description"],
                    "og_title": content_data["og_title"],
                    "og_description": content_data["og_description"],
                    "word_count": content_data["word_count"],
                    "link_count": content_data["link_count"],
                    "image_count": content_data["image_count"],
                    "final_url": content_data["url"],
                },
            }

        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "title": "",
                "content": "",
                "metadata": {},
            }

        finally:
            if page:
                await page.close()


# Convenience function for simple usage
async def fetch_url_content(
    url: str,
    headless: bool = True,
    timeout: float = 30.0,
    wait_for_selector: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to fetch content from a single URL.

    Args:
        url: The URL to fetch content from
        headless: Whether to run browser in headless mode
        timeout: Timeout for operations in seconds
        wait_for_selector: Optional CSS selector to wait for

    Returns:
        Dictionary containing the extracted content and metadata
    """
    async with BrowserFetch(headless=headless, timeout=timeout) as fetcher:
        return await fetcher.fetch_content(url, wait_for_selector)
