"""Enhanced Google search with advanced anti-bot detection techniques using Playwright."""

import asyncio
import random
import time
from typing import Dict, List, Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import stealth_async

from .filter import filter_search_results
from .websearch import WebSearchGeneral


class WebSearchGoogleEnhanced(WebSearchGeneral):
    """Enhanced Google search using Playwright with advanced anti-bot detection techniques.
    
    This implementation uses techniques from the blog post:
    https://dev.to/hasdata_com/simple-google-maps-scraper-using-playwright-e72
    
    Features:
    - Stealth mode with playwright-stealth
    - Real browser automation with Chromium
    - Human-like behavior simulation
    - Enhanced user agent and headers
    - Cookie management
    - Random delays and realistic browsing patterns
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30.0,
        proxy: Optional[str] = None,
    ):
        """Initialize the enhanced Google searcher.
        
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
        """Start the browser instance with anti-detection settings."""
        try:
            self.playwright = await async_playwright().start()

            # Launch Chromium with anti-detection settings (as suggested in the blog)
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
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
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

            logger.info("Enhanced Google searcher started with Chromium and stealth mode")

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

    def search(
        self,
        query: str,
        number_results: int = 5,
        threshold: float = 0.2,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, str]]:
        """Perform search and return results (sync wrapper).
        
        Args:
            query: The search query
            number_results: Maximum number of results to return
            threshold: Not used in this implementation
            timeout: Optional timeout override in seconds
            
        Returns:
            List of search results with title, url, content, and excerpt
        """
        return asyncio.run(self.search_async(query, number_results, timeout))

    async def search_async(
        self,
        query: str,
        number_results: int = 5,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, str]]:
        """Perform async search and return results.
        
        Args:
            query: The search query
            number_results: Maximum number of results to return
            timeout: Optional timeout override in seconds
            
        Returns:
            List of search results with title, url, content, and excerpt
        """
        if not self.context:
            await self.start()

        page = None
        try:
            page = await self.context.new_page()
            
            # Apply stealth mode to the page
            await stealth_async(page)
            
            # Human-like behavior: random delay before starting
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            # Navigate to Google homepage first (more human-like)
            logger.info("Navigating to Google homepage")
            await page.goto("https://www.google.com", timeout=(timeout or self.timeout) * 1000)
            
            # Set Google cookies for better compatibility
            await page.context.add_cookies([
                {
                    "name": "CONSENT",
                    "value": "PENDING+987",
                    "domain": ".google.com",
                    "path": "/",
                },
                {
                    "name": "SOCS",
                    "value": "CAESHAgBEhIaAB",
                    "domain": ".google.com", 
                    "path": "/",
                }
            ])
            
            # Wait for page to load
            await page.wait_for_timeout(random.randint(2000, 4000))
            
            # Find and fill search box
            search_box = await page.wait_for_selector('input[name="q"]', timeout=10000)
            
            # Human-like typing with delays
            await search_box.click()
            await page.wait_for_timeout(random.randint(500, 1500))
            
            # Type query character by character with random delays
            for char in query:
                await search_box.type(char)
                await page.wait_for_timeout(random.randint(50, 200))
            
            # Random delay before pressing Enter
            await page.wait_for_timeout(random.randint(1000, 2000))
            
            # Press Enter to search
            await search_box.press("Enter")
            
            # Wait for search results to load
            await page.wait_for_selector('div[data-sokoban-container]', timeout=15000)
            await page.wait_for_timeout(random.randint(2000, 4000))
            
            # Extract search results
            results = await self._extract_search_results(page, number_results)
            
            logger.info(f"Successfully extracted {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
        finally:
            if page:
                await page.close()

    async def _extract_search_results(self, page: Page, max_results: int) -> List[Dict[str, str]]:
        """Extract search results from the page."""
        results = []
        
        try:
            # Wait for search results to be present
            await page.wait_for_selector('div[data-sokoban-container] h3', timeout=10000)
            
            # Extract search result elements
            search_results = await page.query_selector_all('div[data-sokoban-container]')
            
            for i, result_element in enumerate(search_results[:max_results]):
                try:
                    # Extract title
                    title_element = await result_element.query_selector('h3')
                    title = await title_element.inner_text() if title_element else ""
                    
                    # Extract URL
                    link_element = await result_element.query_selector('a[href]')
                    url = await link_element.get_attribute('href') if link_element else ""
                    
                    # Clean URL (remove Google redirect)
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    # Extract description/snippet
                    desc_selectors = [
                        '[data-sncf="1"]',
                        '.VwiC3b',
                        '.s3v9rd',
                        '.st'
                    ]
                    
                    description = ""
                    for selector in desc_selectors:
                        desc_element = await result_element.query_selector(selector)
                        if desc_element:
                            description = await desc_element.inner_text()
                            break
                    
                    if title and url and not url.startswith('http://') and not url.startswith('https://'):
                        continue
                        
                    if title and url:
                        results.append({
                            "title": title.strip(),
                            "url": url.strip(),
                            "content": description.strip(),
                            "excerpt": description.strip(),  # For compatibility
                        })
                        
                except Exception as e:
                    logger.debug(f"Error extracting result {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
            
        return results


# Convenience function for simple usage
async def search_google_enhanced(
    query: str,
    number_results: int = 5,
    headless: bool = True,
    timeout: float = 30.0,
    proxy: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Convenience function to perform a Google search.
    
    Args:
        query: The search query
        number_results: Maximum number of results to return
        headless: Whether to run browser in headless mode
        timeout: Timeout for operations in seconds
        proxy: Optional proxy server URL
        
    Returns:
        List of search results with title, url, content, and excerpt
    """
    async with WebSearchGoogleEnhanced(headless=headless, timeout=timeout, proxy=proxy) as searcher:
        return await searcher.search_async(query, number_results, timeout)


if __name__ == "__main__":
    import json
    
    async def test_search():
        results = await search_google_enhanced("python tutorial", 3)
        for result in results:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_search())