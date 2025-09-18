"""Enhanced browser-based web content fetching using Playwright and Chromium with stealth mode."""

import asyncio
from typing import Any, Dict, Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import stealth_async


class BrowserFetch:
    """Enhanced browser-based web content fetcher using Chromium with anti-bot detection."""

    def __init__(self, headless: bool = True, timeout: float = 30.0, proxy: Optional[str] = None):
        """Initialize the browser fetcher.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in seconds
            proxy: Optional proxy server URL
        """
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
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
        """Start the browser instance with enhanced anti-detection."""
        try:
            self.playwright = await async_playwright().start()

            # Launch Chromium with enhanced anti-detection settings (based on blog post)
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-field-trial-config",
                "--disable-back-forward-cache",
                "--disable-ipc-flooding-protection",
            ]

            if self.proxy:
                launch_args.append(f"--proxy-server={self.proxy}")

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args,
            )

            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

            logger.info("Browser started successfully with Chromium and stealth mode")

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

            # Apply stealth mode to the page
            await stealth_async(page)

            # Navigate to the URL with human-like behavior
            logger.info(f"Navigating to: {url}")
            
            # Add random delay before navigation (simulate human behavior)
            import random
            await page.wait_for_timeout(random.randint(1000, 3000))
            
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

            # Wait with random delay for dynamic content to load (human-like)
            await page.wait_for_timeout(random.randint(2000, 4000))

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
    proxy: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to fetch content from a single URL.

    Args:
        url: The URL to fetch content from
        headless: Whether to run browser in headless mode
        timeout: Timeout for operations in seconds
        wait_for_selector: Optional CSS selector to wait for
        proxy: Optional proxy server URL

    Returns:
        Dictionary containing the extracted content and metadata
    """
    async with BrowserFetch(headless=headless, timeout=timeout, proxy=proxy) as fetcher:
        return await fetcher.fetch_content(url, wait_for_selector)
