"""Google search using Patchright (anti-detection Playwright fork) with enhanced stealth."""

import asyncio
import random
import time
from typing import Dict, List, Optional

from loguru import logger

try:
    from patchright.async_api import async_playwright
    PATCHRIGHT_AVAILABLE = True
except ImportError:
    from playwright.async_api import async_playwright
    PATCHRIGHT_AVAILABLE = False
    logger.warning("Patchright not available, falling back to regular Playwright")

from .filter import filter_search_results
from .websearch import WebSearchGeneral


class WebSearchGooglePatchright(WebSearchGeneral):
    """Google search using Patchright with maximum stealth capabilities.
    
    Patchright is a fork of Playwright specifically designed to avoid bot detection.
    It includes built-in patches to bypass common detection methods.
    
    Features:
    - Patchright for maximum stealth
    - Human-like interaction patterns
    - Advanced fingerprint masking
    - Realistic browsing behavior
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30.0,
        proxy: Optional[str] = None,
    ):
        """Initialize the Patchright Google searcher.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in seconds
            proxy: Optional proxy server URL
        """
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.browser = None
        self.context = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser instance with maximum stealth."""
        try:
            self.playwright = await async_playwright().start()

            # Enhanced launch arguments for maximum stealth
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
                "--disable-extensions",
                "--disable-plugins",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-zygote",
                "--disable-accelerated-2d-canvas",
                "--disable-accelerated-jpeg-decoding",
                "--disable-accelerated-mjpeg-decode",
                "--disable-accelerated-video-decode",
                "--disable-gpu",
                "--disable-gpu-sandbox",
            ]

            if self.proxy:
                launch_args.append(f"--proxy-server={self.proxy}")

            # Use Chromium for better compatibility
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args,
            )

            # Create context with realistic fingerprint
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},  # Common resolution
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
                color_scheme="light",
                reduced_motion="no-preference",
                forced_colors="none",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                },
            )

            # Add advanced stealth script
            await self.context.add_init_script("""
                // Hide webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: ""},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Override platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
                
                // Override hardwareConcurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });
                
                // Override deviceMemory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });
            """)

            stealth_status = "🎭 Patchright" if PATCHRIGHT_AVAILABLE else "🎪 Playwright"
            logger.info(f"{stealth_status} Google searcher started with maximum stealth")

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
            if self.playwright:
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
        """Perform async search with maximum stealth.
        
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
            
            # Simulate human behavior: random delay before starting
            await page.wait_for_timeout(random.randint(2000, 5000))
            
            # Navigate to Google homepage first (more human-like)
            logger.info("🔍 Navigating to Google homepage with stealth")
            await page.goto("https://www.google.com", 
                          timeout=(timeout or self.timeout) * 1000,
                          wait_until="domcontentloaded")
            
            # Handle potential cookie consent
            try:
                # Wait for potential cookie banner and accept
                cookie_button = await page.wait_for_selector(
                    'button:has-text("Accept all"), button:has-text("I agree"), #L2AGLb',
                    timeout=3000
                )
                if cookie_button:
                    await cookie_button.click()
                    await page.wait_for_timeout(random.randint(1000, 2000))
            except:
                pass  # No cookie banner found
            
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
            
            # Wait for page to fully load
            await page.wait_for_timeout(random.randint(3000, 6000))
            
            # Find search box with multiple selectors
            search_selectors = [
                'input[name="q"]',
                'textarea[name="q"]',
                '#APjFqb',
                '.gLFyf'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await page.wait_for_selector(selector, timeout=5000)
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                raise Exception("Could not find search box")
            
            # Human-like interaction with search box
            await search_box.click()
            await page.wait_for_timeout(random.randint(500, 1500))
            
            # Clear any existing text
            await search_box.fill("")
            await page.wait_for_timeout(random.randint(200, 500))
            
            # Type query with human-like delays
            for i, char in enumerate(query):
                await search_box.type(char)
                # Vary typing speed
                if i % 3 == 0:
                    await page.wait_for_timeout(random.randint(100, 300))
                else:
                    await page.wait_for_timeout(random.randint(50, 150))
            
            # Random pause before submitting
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            # Submit search
            await search_box.press("Enter")
            
            # Wait for search results with multiple strategies
            try:
                await page.wait_for_selector('div[data-sokoban-container]', timeout=15000)
            except:
                try:
                    await page.wait_for_selector('#search', timeout=10000)
                except:
                    await page.wait_for_selector('.g', timeout=10000)
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(random.randint(3000, 6000))
            
            # Extract search results
            results = await self._extract_search_results(page, number_results)
            
            logger.info(f"🎯 Successfully extracted {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during search: {e}")
            return []
        finally:
            if page:
                await page.close()

    async def _extract_search_results(self, page, max_results: int) -> List[Dict[str, str]]:
        """Extract search results with multiple fallback strategies."""
        results = []
        
        try:
            # Multiple strategies for finding results
            result_selectors = [
                'div[data-sokoban-container]',
                '.g',
                '.tF2Cxc',
                '.yuRUbf'
            ]
            
            search_results = []
            for selector in result_selectors:
                search_results = await page.query_selector_all(selector)
                if search_results:
                    break
            
            if not search_results:
                logger.warning("No search results found with any selector")
                return []
            
            for i, result_element in enumerate(search_results[:max_results * 2]):  # Get more to filter
                try:
                    # Extract title with multiple selectors
                    title_selectors = ['h3', '.LC20lb', '.DKV0Md']
                    title = ""
                    for selector in title_selectors:
                        title_element = await result_element.query_selector(selector)
                        if title_element:
                            title = await title_element.inner_text()
                            break
                    
                    # Extract URL with multiple selectors
                    link_selectors = ['a[href]', '.yuRUbf a', 'h3 a']
                    url = ""
                    for selector in link_selectors:
                        link_element = await result_element.query_selector(selector)
                        if link_element:
                            url = await link_element.get_attribute('href')
                            break
                    
                    # Clean URL (remove Google redirect)
                    if url and url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    # Extract description with multiple selectors
                    desc_selectors = [
                        '[data-sncf="1"]',
                        '.VwiC3b',
                        '.s3v9rd', 
                        '.st',
                        '.IsZvec'
                    ]
                    
                    description = ""
                    for selector in desc_selectors:
                        desc_element = await result_element.query_selector(selector)
                        if desc_element:
                            description = await desc_element.inner_text()
                            break
                    
                    # Validate result
                    if (title and url and 
                        (url.startswith('http://') or url.startswith('https://')) and
                        not url.startswith('https://www.google.com')):
                        
                        results.append({
                            "title": title.strip(),
                            "url": url.strip(),
                            "content": description.strip(),
                            "excerpt": description.strip(),  # For compatibility
                        })
                        
                        if len(results) >= max_results:
                            break
                        
                except Exception as e:
                    logger.debug(f"Error extracting result {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
            
        return results


# Convenience function
async def search_google_patchright(
    query: str,
    number_results: int = 5,
    headless: bool = True,
    timeout: float = 30.0,
    proxy: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Convenience function to perform a Google search with Patchright.
    
    Args:
        query: The search query
        number_results: Maximum number of results to return
        headless: Whether to run browser in headless mode
        timeout: Timeout for operations in seconds
        proxy: Optional proxy server URL
        
    Returns:
        List of search results with title, url, content, and excerpt
    """
    async with WebSearchGooglePatchright(headless=headless, timeout=timeout, proxy=proxy) as searcher:
        return await searcher.search_async(query, number_results, timeout)


if __name__ == "__main__":
    import json
    
    async def test_search():
        results = await search_google_patchright("python tutorial", 3)
        for result in results:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_search())