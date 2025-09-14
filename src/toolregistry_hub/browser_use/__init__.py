"""Browser-based web content fetching module using headless Firefox."""

from .browser_fetch import BrowserFetch, fetch_url_content

__all__ = [
    "BrowserFetch",
    "fetch_url_content",
]