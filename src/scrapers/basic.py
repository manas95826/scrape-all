"""
Basic content scraper for single pages.
"""

from typing import Optional, Dict
from ..models import ScrapedPage
from .base import BaseScraper


class BasicScraper(BaseScraper):
    """Scraper for basic content extraction from single pages."""
    
    def scrape(self, url: str, selectors: Optional[Dict[str, str]] = None, **kwargs) -> Optional[ScrapedPage]:
        """Scrape a single page for basic content."""
        return self.scrape_single_page(url, selectors)
