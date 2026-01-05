"""
Website crawler for discovering and scraping multiple pages.
"""

from collections import deque
from typing import List, Optional, Dict, Callable
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from ..config import Config
from ..models import ScrapedPage
from ..utils import extract_links, is_internal_link, should_skip_url, delay_request, extract_title_content_pairs, normalize_url, extract_custom_data
from .base import BaseScraper


class WebsiteCrawler(BaseScraper):
    """Crawler for discovering and scraping entire websites."""
    
    def scrape(
        self, 
        start_url: str, 
        max_pages: int = Config.DEFAULT_MAX_PAGES,
        max_depth: int = Config.DEFAULT_MAX_DEPTH,
        stay_on_domain: bool = True,
        exclude_patterns: Optional[List[str]] = None,
        use_sitemap: bool = True,
        selectors: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> List[ScrapedPage]:
        """Scrape entire website starting from a URL."""
        
        # Try sitemap first if enabled
        if use_sitemap:
            from .sitemap import SitemapScraper
            sitemap_scraper = SitemapScraper(delay=self.delay)
            
            if progress_callback:
                progress_callback(0.05, "Attempting to discover sitemap...")
            
            sitemap_urls = sitemap_scraper.discover_sitemap_urls(start_url, progress_callback)
            if sitemap_urls:
                urls_to_scrape = sitemap_urls[:max_pages]
                if progress_callback:
                    progress_callback(0.5, f"Found {len(urls_to_scrape)} URLs from sitemap")
                return self._scrape_urls(urls_to_scrape, selectors, progress_callback)
        
        # Fallback to crawling if no sitemap found
        if progress_callback:
            progress_callback(0.1, "Discovering pages via crawling...")
        
        urls_to_scrape = self._discover_pages(
            start_url, max_pages, max_depth, stay_on_domain, 
            exclude_patterns or Config.DEFAULT_EXCLUDE_PATTERNS, 
            progress_callback
        )
        
        return self._scrape_urls(urls_to_scrape, selectors, progress_callback)
    
    def _discover_pages(
        self, 
        start_url: str, 
        max_pages: int, 
        max_depth: int,
        stay_on_domain: bool,
        exclude_patterns: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Discover pages using breadth-first search."""
        base_domain = urlparse(start_url).netloc
        visited = set()
        queue = deque([(start_url, 0)])  # (url, depth)
        discovered_urls = set()
        
        while queue and len(discovered_urls) < max_pages:
            current_url, depth = queue.popleft()
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            
            # Skip URLs based on patterns
            if should_skip_url(current_url, exclude_patterns):
                continue
            
            if progress_callback:
                progress = min(len(discovered_urls) / max_pages, 0.95)
                progress_callback(progress, f"Discovering: {current_url} (depth: {depth}, found: {len(discovered_urls)} pages)")
            
            response = self.get_page(current_url)
            if response:
                discovered_urls.add(current_url)
                
                # Extract links and add to queue
                soup = BeautifulSoup(response.content, 'html.parser')
                links = extract_links(soup, current_url)
                
                for link in links:
                    if link not in visited:
                        # Stay on same domain if required
                        if stay_on_domain and not is_internal_link(link, start_url):
                            continue
                        
                        queue.append((link, depth + 1))
            
            delay_request(self.delay)
        
        return list(discovered_urls)
    
    def _scrape_urls(
        self, 
        urls: List[str], 
        selectors: Optional[Dict[str, str]],
        progress_callback: Optional[Callable] = None
    ) -> List[ScrapedPage]:
        """Scrape a list of URLs and extract backlinks."""
        results = []
        
        if progress_callback:
            progress_callback(0.5, f"Found {len(urls)} pages. Starting scraping...")
        
        for i, url in enumerate(urls, 1):
            if progress_callback:
                progress = 0.5 + (i / len(urls)) * 0.5
                progress_callback(progress, f"Scraping page {i}/{len(urls)}: {url}")
            
            page_data = self.scrape_single_page_with_backlinks(url, selectors)
            if page_data:
                results.append(page_data)
            
            if i < len(urls):
                delay_request(self.delay)
        
        return results
    
    def scrape_single_page_with_backlinks(self, url: str, selectors: Optional[Dict[str, str]] = None) -> Optional[ScrapedPage]:
        """Scrape a single page and extract backlink information."""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic content
        title_content_pairs = extract_title_content_pairs(soup)
        
        # Extract custom data if selectors provided
        custom_data = {}
        if selectors:
            custom_data = extract_custom_data(soup, selectors)
        
        # Extract backlink information
        backlinks = self._extract_backlinks(soup, url)
        custom_data['backlinks'] = backlinks
        
        # Create ScrapedPage
        page_data = {
            'scraped_url': response.url,
            'scraped_at': self._get_timestamp(),
            'title_content_pairs': title_content_pairs,
            'custom_data': custom_data
        }
        
        return ScrapedPage.from_dict(page_data)
    
    def _extract_backlinks(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Extract backlink information from a page."""
        backlinks = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            link_text = a_tag.get_text(strip=True)
            
            # Normalize the URL
            clean_url = normalize_url(href, page_url)
            if not clean_url:
                continue
            
            # Get additional link information
            link_info = {
                'url': clean_url,
                'link_text': link_text,
                'original_href': href,
                'is_internal': is_internal_link(clean_url, page_url),
                'title': a_tag.get('title', ''),
                'target': a_tag.get('target', '')
            }
            
            backlinks.append(link_info)
        
        return backlinks
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
