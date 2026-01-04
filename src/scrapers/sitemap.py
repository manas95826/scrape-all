"""
Sitemap scraper for XML sitemap parsing and scraping.
"""

from typing import List, Optional, Callable
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from ..config import Config
from ..models import ScrapedPage
from ..utils import delay_request
from .base import BaseScraper


class SitemapScraper(BaseScraper):
    """Scraper for XML sitemaps."""
    
    def scrape(
        self,
        url: str,
        sitemap_url: Optional[str] = None,
        max_pages: int = Config.DEFAULT_MAX_PAGES,
        selectors: Optional[dict] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> List[ScrapedPage]:
        """Scrape pages using sitemap."""
        
        # Use provided sitemap URL or auto-discover
        target_sitemap_url = sitemap_url.strip() if sitemap_url and sitemap_url.strip() else None
        
        if target_sitemap_url:
            # Use provided sitemap URL
            urls_to_scrape = self.parse_sitemap(target_sitemap_url, progress_callback)
        else:
            # Auto-discover sitemap
            urls_to_scrape = self.discover_sitemap_urls(url, progress_callback)
        
        if not urls_to_scrape:
            if progress_callback:
                progress_callback(0, "No sitemap found or sitemap is empty.")
            return []
        
        # Limit to max_pages
        urls_to_scrape = urls_to_scrape[:max_pages]
        
        # Scrape all URLs from sitemap
        results = []
        for i, sitemap_url in enumerate(urls_to_scrape, 1):
            if progress_callback:
                progress = 0.5 + (i / len(urls_to_scrape)) * 0.5
                progress_callback(progress, f"Scraping page {i}/{len(urls_to_scrape)}: {sitemap_url}")
            
            page_data = self.scrape_single_page(sitemap_url, selectors)
            if page_data:
                results.append(page_data)
            
            if i < len(urls_to_scrape):
                delay_request(self.delay)
        
        return results
    
    def parse_sitemap(self, sitemap_url: str, progress_callback: Optional[Callable] = None) -> List[str]:
        """Parse XML sitemap and extract all URLs."""
        try:
            if progress_callback:
                progress_callback(0.1, f"Fetching sitemap: {sitemap_url}")
            
            response = self.get_page(sitemap_url)
            if not response:
                return []
            
            if progress_callback:
                progress_callback(0.3, "Parsing sitemap XML...")
            
            soup = BeautifulSoup(response.content, 'xml')
            urls = []
            
            # Find all URL elements
            url_elements = soup.find_all('url')
            
            if progress_callback:
                progress_callback(0.5, f"Found {len(url_elements)} URLs in sitemap")
            
            for url_elem in url_elements:
                loc_elem = url_elem.find('loc')
                if loc_elem and loc_elem.text:
                    urls.append(loc_elem.text.strip())
            
            # Also check for sitemap index (nested sitemaps)
            sitemap_elements = soup.find_all('sitemap')
            if sitemap_elements:
                if progress_callback:
                    progress_callback(0.7, f"Found {len(sitemap_elements)} nested sitemaps, processing...")
                
                for sitemap_elem in sitemap_elements:
                    loc_elem = sitemap_elem.find('loc')
                    if loc_elem and loc_elem.text:
                        nested_urls = self.parse_sitemap(loc_elem.text.strip(), progress_callback)
                        urls.extend(nested_urls)
            
            if progress_callback:
                progress_callback(1.0, f"Successfully parsed {len(urls)} URLs from sitemap")
            
            return list(set(urls))  # Remove duplicates
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error parsing sitemap: {str(e)}")
            return []
    
    def discover_sitemap_urls(self, base_url: str, progress_callback: Optional[Callable] = None) -> List[str]:
        """Try to discover and parse sitemap URLs for a website."""
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc
        
        # Common sitemap locations
        sitemap_urls = []
        for location in Config.SITEMAP_LOCATIONS:
            sitemap_urls.extend([
                f"https://{domain}{location}",
                f"https://www.{domain}{location}"
            ])
        
        for sitemap_url in sitemap_urls:
            if progress_callback:
                progress_callback(0.1, f"Trying sitemap: {sitemap_url}")
            
            urls = self.parse_sitemap(sitemap_url, progress_callback)
            if urls:
                return urls
        
        if progress_callback:
            progress_callback(0, "No sitemap found, falling back to crawling")
        
        return []
