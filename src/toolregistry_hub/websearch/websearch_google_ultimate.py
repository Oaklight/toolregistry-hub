"""Ultimate Google search implementation inspired by the TypeScript version with comprehensive anti-bot detection."""

import asyncio
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .filter import filter_search_results
from .websearch import WebSearchGeneral


class FingerprintConfig:
    """Browser fingerprint configuration."""
    
    def __init__(self, device_name: str, locale: str, timezone_id: str, 
                 color_scheme: str, reduced_motion: str, forced_colors: str):
        self.device_name = device_name
        self.locale = locale
        self.timezone_id = timezone_id
        self.color_scheme = color_scheme
        self.reduced_motion = reduced_motion
        self.forced_colors = forced_colors


class SavedState:
    """Saved browser state."""
    
    def __init__(self):
        self.fingerprint: Optional[FingerprintConfig] = None
        self.google_domain: Optional[str] = None


class WebSearchGoogleUltimate(WebSearchGeneral):
    """Ultimate Google search with comprehensive anti-bot detection inspired by TypeScript implementation.
    
    Features:
    - Host machine fingerprint generation
    - Browser state persistence
    - Intelligent CAPTCHA handling
    - WebGL fingerprint randomization
    - Multiple result extraction strategies
    - Automatic headless/headed mode switching
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 60.0,
        proxy: Optional[str] = None,
        state_file: str = "./browser-state.json",
        no_save_state: bool = False,
        locale: str = "zh-CN",
    ):
        """Initialize the ultimate Google searcher.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in seconds
            proxy: Optional proxy server URL
            state_file: Path to save browser state
            no_save_state: Whether to disable state saving
            locale: Browser locale
        """
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.state_file = state_file
        self.no_save_state = no_save_state
        self.locale = locale
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.saved_state = SavedState()
        
        # Device and domain lists
        self.device_list = [
            "Desktop Chrome",
            "Desktop Edge", 
            "Desktop Firefox",
            "Desktop Safari",
        ]
        
        self.google_domains = [
            "https://www.google.com",
            "https://www.google.co.uk", 
            "https://www.google.ca",
            "https://www.google.com.au",
        ]
        
        self.sorry_patterns = [
            "google.com/sorry/index",
            "google.com/sorry",
            "recaptcha",
            "captcha", 
            "unusual traffic",
        ]

    def get_host_machine_config(self) -> FingerprintConfig:
        """Get host machine configuration for fingerprint."""
        # Get system timezone
        timezone_offset = time.timezone / 3600
        timezone_id = "Asia/Shanghai"  # Default
        
        if -8 <= timezone_offset <= -7:
            timezone_id = "Asia/Shanghai"
        elif timezone_offset == -9:
            timezone_id = "Asia/Tokyo"
        elif timezone_offset == 0:
            timezone_id = "Europe/London"
        elif timezone_offset == 5:
            timezone_id = "America/New_York"
            
        # Detect color scheme based on time
        hour = time.localtime().tm_hour
        color_scheme = "dark" if 19 <= hour or hour < 7 else "light"
        
        return FingerprintConfig(
            device_name="Desktop Chrome",
            locale=self.locale,
            timezone_id=timezone_id,
            color_scheme=color_scheme,
            reduced_motion="no-preference",
            forced_colors="none"
        )

    def load_saved_state(self):
        """Load saved browser state and fingerprint."""
        fingerprint_file = self.state_file.replace(".json", "-fingerprint.json")
        
        if os.path.exists(self.state_file):
            logger.info(f"Found browser state file: {self.state_file}")
            
            if os.path.exists(fingerprint_file):
                try:
                    with open(fingerprint_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'fingerprint' in data:
                            fp_data = data['fingerprint']
                            self.saved_state.fingerprint = FingerprintConfig(**fp_data)
                        if 'google_domain' in data:
                            self.saved_state.google_domain = data['google_domain']
                    logger.info("Loaded saved fingerprint configuration")
                except Exception as e:
                    logger.warning(f"Failed to load fingerprint config: {e}")

    def save_state(self):
        """Save browser state and fingerprint."""
        if self.no_save_state:
            return
            
        fingerprint_file = self.state_file.replace(".json", "-fingerprint.json")
        
        try:
            # Save fingerprint config
            state_data = {}
            if self.saved_state.fingerprint:
                state_data['fingerprint'] = {
                    'device_name': self.saved_state.fingerprint.device_name,
                    'locale': self.saved_state.fingerprint.locale,
                    'timezone_id': self.saved_state.fingerprint.timezone_id,
                    'color_scheme': self.saved_state.fingerprint.color_scheme,
                    'reduced_motion': self.saved_state.fingerprint.reduced_motion,
                    'forced_colors': self.saved_state.fingerprint.forced_colors,
                }
            if self.saved_state.google_domain:
                state_data['google_domain'] = self.saved_state.google_domain
                
            os.makedirs(os.path.dirname(fingerprint_file), exist_ok=True)
            with open(fingerprint_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved fingerprint configuration to {fingerprint_file}")
        except Exception as e:
            logger.error(f"Failed to save fingerprint config: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser with comprehensive anti-detection."""
        try:
            self.load_saved_state()
            self.playwright = await async_playwright().start()

            # Enhanced launch arguments
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--disable-web-security",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--hide-scrollbars",
                "--mute-audio",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-component-extensions-with-background-pages",
                "--disable-extensions",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-renderer-backgrounding",
                "--enable-features=NetworkService,NetworkServiceInProcess",
                "--force-color-profile=srgb",
                "--metrics-recording-only",
            ]

            if self.proxy:
                launch_args.append(f"--proxy-server={self.proxy}")

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=launch_args,
                timeout=self.timeout * 2000,
            )

            # Create context with fingerprint
            fingerprint = self.saved_state.fingerprint or self.get_host_machine_config()
            if not self.saved_state.fingerprint:
                self.saved_state.fingerprint = fingerprint

            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "locale": fingerprint.locale,
                "timezone_id": fingerprint.timezone_id,
                "color_scheme": fingerprint.color_scheme,
                "reduced_motion": fingerprint.reduced_motion,
                "forced_colors": fingerprint.forced_colors,
                "permissions": ["geolocation", "notifications"],
                "accept_downloads": True,
                "is_mobile": False,
                "has_touch": False,
                "java_script_enabled": True,
                "extra_http_headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
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
            }

            # Add storage state if exists
            if os.path.exists(self.state_file):
                context_options["storage_state"] = self.state_file

            self.context = await self.browser.new_context(**context_options)

            # Add comprehensive stealth script
            await self.context.add_init_script("""
                // Hide webdriver property
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ["en-US", "en", "zh-CN"],
                });
                
                // Add chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function () {},
                    csi: function () {},
                    app: {},
                };
                
                // WebGL fingerprint randomization
                if (typeof WebGLRenderingContext !== "undefined") {
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function (parameter) {
                        if (parameter === 37445) {
                            return "Intel Inc.";
                        }
                        if (parameter === 37446) {
                            return "Intel Iris OpenGL Engine";
                        }
                        return getParameter.call(this, parameter);
                    };
                }
                
                // Screen properties
                Object.defineProperty(window.screen, "width", { get: () => 1920 });
                Object.defineProperty(window.screen, "height", { get: () => 1080 });
                Object.defineProperty(window.screen, "colorDepth", { get: () => 24 });
                Object.defineProperty(window.screen, "pixelDepth", { get: () => 24 });
            """)

            logger.info("🚀 Ultimate Google searcher started with comprehensive stealth")

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    async def close(self):
        """Close the browser and save state."""
        try:
            if self.context and not self.no_save_state:
                await self.context.storage_state(path=self.state_file)
                self.save_state()
                
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
        """Perform search and return results (sync wrapper)."""
        return asyncio.run(self.search_async(query, number_results, timeout))

    async def search_async(
        self,
        query: str,
        number_results: int = 5,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, str]]:
        """Perform async search with ultimate stealth."""
        if not self.context:
            await self.start()

        return await self._perform_search(query, number_results, timeout, self.headless)

    async def _perform_search(
        self, 
        query: str, 
        number_results: int, 
        timeout: Optional[float], 
        headless: bool
    ) -> List[Dict[str, str]]:
        """Internal search implementation with CAPTCHA handling."""
        page = None
        try:
            page = await self.context.new_page()
            
            # Random delay before starting
            await page.wait_for_timeout(random.randint(2000, 5000))
            
            # Select Google domain
            selected_domain = (self.saved_state.google_domain or 
                             random.choice(self.google_domains))
            if not self.saved_state.google_domain:
                self.saved_state.google_domain = selected_domain
            
            logger.info(f"🔍 Navigating to {selected_domain}")
            
            # Navigate to Google
            response = await page.goto(
                selected_domain,
                timeout=(timeout or self.timeout) * 1000,
                wait_until="networkidle"
            )
            
            # Check for CAPTCHA
            current_url = page.url()
            is_blocked = any(pattern in current_url for pattern in self.sorry_patterns)
            
            if is_blocked:
                if headless:
                    logger.warning("🤖 CAPTCHA detected, switching to headed mode...")
                    await page.close()
                    return await self._perform_search(query, number_results, timeout, False)
                else:
                    logger.warning("🤖 CAPTCHA detected, please complete verification...")
                    await page.wait_for_navigation(
                        timeout=(timeout or self.timeout) * 2000,
                        url=lambda url: not any(pattern in str(url) for pattern in self.sorry_patterns)
                    )
            
            # Find and interact with search box
            search_selectors = [
                "textarea[name='q']",
                "input[name='q']", 
                "textarea[title='Search']",
                "input[title='Search']",
                "textarea[aria-label='Search']",
                "input[aria-label='Search']",
                "textarea",
            ]
            
            search_input = None
            for selector in search_selectors:
                search_input = await page.query_selector(selector)
                if search_input:
                    logger.info(f"Found search box: {selector}")
                    break
                    
            if not search_input:
                raise Exception("Could not find search box")
            
            # Human-like interaction
            await search_input.click()
            await page.wait_for_timeout(random.randint(500, 1500))
            
            # Type query with human-like delays
            for char in query:
                await search_input.type(char)
                await page.wait_for_timeout(random.randint(50, 200))
            
            await page.wait_for_timeout(random.randint(1000, 2000))
            await page.keyboard.press("Enter")
            
            # Wait for results
            await page.wait_for_load_state("networkidle", timeout=(timeout or self.timeout) * 1000)
            
            # Check for CAPTCHA after search
            search_url = page.url()
            is_blocked_after = any(pattern in search_url for pattern in self.sorry_patterns)
            
            if is_blocked_after:
                if headless:
                    logger.warning("🤖 CAPTCHA after search, switching to headed mode...")
                    await page.close()
                    return await self._perform_search(query, number_results, timeout, False)
                else:
                    logger.warning("🤖 CAPTCHA after search, please complete verification...")
                    await page.wait_for_navigation(
                        timeout=(timeout or self.timeout) * 2000,
                        url=lambda url: not any(pattern in str(url) for pattern in self.sorry_patterns)
                    )
            
            # Extract results using multiple strategies
            results = await self._extract_results(page, number_results)
            
            logger.info(f"🎯 Successfully extracted {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
        finally:
            if page:
                await page.close()

    async def _extract_results(self, page: Page, max_results: int) -> List[Dict[str, str]]:
        """Extract search results using multiple strategies."""
        results = await page.evaluate("""
            (maxResults) => {
                const results = [];
                const seenUrls = new Set();
                
                // Multiple selector strategies
                const selectorSets = [
                    { container: '#search div[data-hveid]', title: 'h3', snippet: '.VwiC3b' },
                    { container: '#rso div[data-hveid]', title: 'h3', snippet: '[data-sncf="1"]' },
                    { container: '.g', title: 'h3', snippet: 'div[style*="webkit-line-clamp"]' },
                    { container: 'div[jscontroller][data-hveid]', title: 'h3', snippet: 'div[role="text"]' }
                ];
                
                const alternativeSnippetSelectors = [
                    '.VwiC3b',
                    '[data-sncf="1"]',
                    'div[style*="webkit-line-clamp"]',
                    'div[role="text"]'
                ];
                
                // Try each selector set
                for (const selectors of selectorSets) {
                    if (results.length >= maxResults) break;
                    
                    const containers = document.querySelectorAll(selectors.container);
                    
                    for (const container of containers) {
                        if (results.length >= maxResults) break;
                        
                        const titleElement = container.querySelector(selectors.title);
                        if (!titleElement) continue;
                        
                        const title = (titleElement.textContent || "").trim();
                        
                        // Find link
                        let link = '';
                        const linkInTitle = titleElement.querySelector('a');
                        if (linkInTitle) {
                            link = linkInTitle.href;
                        } else {
                            let current = titleElement;
                            while (current && current.tagName !== 'A') {
                                current = current.parentElement;
                            }
                            if (current && current instanceof HTMLAnchorElement) {
                                link = current.href;
                            } else {
                                const containerLink = container.querySelector('a');
                                if (containerLink) {
                                    link = containerLink.href;
                                }
                            }
                        }
                        
                        // Filter invalid or duplicate links
                        if (!link || !link.startsWith('http') || seenUrls.has(link)) continue;
                        
                        // Find snippet
                        let snippet = '';
                        const snippetElement = container.querySelector(selectors.snippet);
                        if (snippetElement) {
                            snippet = (snippetElement.textContent || "").trim();
                        } else {
                            // Try alternative selectors
                            for (const altSelector of alternativeSnippetSelectors) {
                                const element = container.querySelector(altSelector);
                                if (element) {
                                    snippet = (element.textContent || "").trim();
                                    break;
                                }
                            }
                        }
                        
                        if (title && link) {
                            results.push({ title, link, snippet });
                            seenUrls.add(link);
                        }
                    }
                }
                
                return results.slice(0, maxResults);
            }
        """, max_results)
        
        # Convert to expected format
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result["title"],
                "url": result["link"],
                "content": result["snippet"],
                "excerpt": result["snippet"],  # For compatibility
            })
        
        return formatted_results


# Convenience function
async def search_google_ultimate(
    query: str,
    number_results: int = 5,
    headless: bool = True,
    timeout: float = 60.0,
    proxy: Optional[str] = None,
    state_file: str = "./browser-state.json",
) -> List[Dict[str, str]]:
    """Convenience function for ultimate Google search."""
    async with WebSearchGoogleUltimate(
        headless=headless,
        timeout=timeout,
        proxy=proxy,
        state_file=state_file,
    ) as searcher:
        return await searcher.search_async(query, number_results, timeout)


if __name__ == "__main__":
    import json
    
    async def test_search():
        results = await search_google_ultimate("python tutorial", 3)
        for result in results:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_search())