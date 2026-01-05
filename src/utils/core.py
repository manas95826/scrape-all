"""
Core utility functions for the web scraper.
"""

import re
import time
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional, Callable
from bs4 import BeautifulSoup
import requests

from ..config import Config


def is_valid_url(url: str) -> bool:
    """Check if URL is valid and accessible."""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False


def normalize_url(url: str, base_url: str) -> str:
    """Normalize and join URL with base URL."""
    full_url = urljoin(base_url, url)
    parsed = urlparse(full_url)
    
    # Only include HTTP/HTTPS links
    if parsed.scheme not in ['http', 'https']:
        return ""
    
    # Remove fragment and query parameters for consistency
    clean_url = parsed._replace(fragment='', params='', query='').geturl()
    return clean_url


def is_internal_link(url: str, base_domain: str) -> bool:
    """Check if URL belongs to the same domain."""
    try:
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_domain)
        return parsed_url.netloc == parsed_base.netloc
    except:
        return False


def should_skip_url(url: str, exclude_patterns: List[str]) -> bool:
    """Check if URL should be skipped based on patterns."""
    for pattern in exclude_patterns:
        if re.search(pattern, url):
            return True
    return False


def extract_links(soup: BeautifulSoup, base_url: str) -> Set[str]:
    """Extract all links from a BeautifulSoup object."""
    links = set()
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href')
        clean_url = normalize_url(href, base_url)
        if clean_url:
            links.add(clean_url)
    
    return links


def extract_title_content_pairs(soup: BeautifulSoup) -> List[dict]:
    """Extract title-content pairs from HTML content."""
    pairs = []
    
    # Get main title as first title
    main_title = soup.title.string.strip() if soup.title else ''
    if main_title:
        pairs.append({'title': main_title, 'content': ''})
    
    # Find all headings and their following content
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    for heading in headings:
        title = heading.get_text(strip=True)
        if not title:
            continue
        
        # Get content after this heading until next heading
        content_parts = []
        next_element = heading.next_sibling
        
        while next_element:
            # Stop if we hit another heading
            if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break
            
            # Extract text from this element
            text = extract_element_text(next_element)
            if text:
                content_parts.append(text)
            
            next_element = next_element.next_sibling
        
        content = ' '.join(content_parts)
        pairs.append({'title': title, 'content': content})
    
    # If no headings found, get all paragraphs as content with main title
    if not headings and main_title:
        paragraphs = soup.find_all('p')
        content_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > Config.MIN_CONTENT_LENGTH:
                content_parts.append(text)
        
        if content_parts and pairs:
            pairs[0]['content'] = ' '.join(content_parts)
    
    return pairs


def extract_element_text(element) -> Optional[str]:
    """Extract text from an element based on its type."""
    if element.name == 'p':
        text = element.get_text(strip=True)
        return text if len(text) > Config.MIN_CONTENT_LENGTH else None
    elif element.name in ['div', 'section', 'article']:
        text = element.get_text(strip=True)
        return text if len(text) > Config.MIN_SECTION_CONTENT_LENGTH else None
    elif hasattr(element, 'get_text'):
        text = element.get_text(strip=True)
        return text if len(text) > Config.MIN_CONTENT_LENGTH else None
    
    return None


def extract_custom_data(soup: BeautifulSoup, selectors: dict) -> dict:
    """Extract data using custom CSS selectors."""
    data = {}
    
    for key, selector in selectors.items():
        elements = soup.select(selector)
        if elements:
            if len(elements) == 1:
                data[key] = elements[0].get_text(strip=True)
            else:
                data[key] = [elem.get_text(strip=True) for elem in elements]
    
    return data


def create_progress_callback(progress_bar, status_text) -> Callable:
    """Create a progress callback function for Streamlit."""
    def callback(progress: float, status: str):
        progress_bar.progress(progress)
        status_text.text(status)
    
    return callback


def safe_request(url: str, session: requests.Session, timeout: int = Config.TIMEOUT) -> Optional[requests.Response]:
    """Make a safe HTTP request with error handling."""
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException:
        return None


def delay_request(delay: float = Config.DEFAULT_DELAY):
    """Add delay between requests to be respectful."""
    if delay > 0:
        time.sleep(delay)
