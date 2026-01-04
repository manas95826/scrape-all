"""
Base scraper class and common functionality.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, List
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from ..config import Config
from ..models import ScrapedPage
from ..utils import safe_request, delay_request


class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, delay: float = Config.DEFAULT_DELAY):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT
        })
    
    @abstractmethod
    def scrape(self, url: str, **kwargs) -> Optional[ScrapedPage]:
        """Scrape a single URL and return structured data."""
        pass
    
    def get_page(self, url: str) -> Optional[requests.Response]:
        """Fetch a webpage with error handling."""
        return safe_request(url, self.session)
    
    def parse_content(self, response: requests.Response, selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Parse content from HTTP response."""
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        
        if selectors:
            data = self._extract_custom_data(soup, selectors)
        else:
            data = self._extract_title_content(soup)
        
        data['scraped_url'] = response.url
        data['scraped_at'] = datetime.now().isoformat()
        
        return data
    
    def _extract_custom_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using custom CSS selectors."""
        from ..utils import extract_custom_data
        return extract_custom_data(soup, selectors)
    
    def _extract_title_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract title-content pairs from HTML."""
        from ..utils import extract_title_content_pairs
        return {'title_content_pairs': extract_title_content_pairs(soup)}
    
    def scrape_single_page(self, url: str, selectors: Optional[Dict[str, str]] = None) -> Optional[ScrapedPage]:
        """Scrape a single page and return ScrapedPage object."""
        response = self.get_page(url)
        if not response:
            return None
        
        data = self.parse_content(response, selectors)
        return ScrapedPage.from_dict(data)
    
    def __del__(self):
        """Cleanup session when scraper is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()
