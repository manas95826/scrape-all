"""
Configuration settings for the web scraper.
"""

from typing import List, Dict, Any
import re

class Config:
    """Configuration constants and settings."""
    
    # HTTP Settings
    DEFAULT_DELAY = 1
    TIMEOUT = 10
    MAX_RETRIES = 3
    
    # Default User Agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    # Default Exclude Patterns
    DEFAULT_EXCLUDE_PATTERNS = [
        r'\.(pdf|jpg|jpeg|png|gif|zip|tar|gz|exe)$',
        r'#',
        r'\?'
    ]
    
    # Sitemap URLs to check
    SITEMAP_LOCATIONS = [
        "/sitemap.xml",
        "/sitemap_index.xml", 
        "/sitemaps.xml",
        "/wp-sitemap.xml"
    ]
    
    # Crawler Limits
    DEFAULT_MAX_PAGES = 50
    DEFAULT_MAX_DEPTH = 3
    MAX_PAGES_LIMIT = 1000
    MAX_DEPTH_LIMIT = 10
    
    # Content Filters
    MIN_CONTENT_LENGTH = 10
    MIN_SECTION_CONTENT_LENGTH = 20

class ScrapingMode:
    """Enumeration of scraping modes."""
    BASIC = "Basic Content"
    CUSTOM_SELECTORS = "Custom CSS Selectors"
    WEBSITE_CRAWLER = "Website Crawler"
    SITEMAP_SCRAPER = "Sitemap Scraper"

class OutputFormat:
    """Enumeration of output formats."""
    JSON = "JSON"
    CSV = "CSV"
    HTML = "HTML"
    TXT = "TXT"
    XML = "XML"

def parse_exclude_patterns(patterns_text: str) -> List[str]:
    """Parse exclude patterns from text input."""
    if not patterns_text:
        return Config.DEFAULT_EXCLUDE_PATTERNS
    
    patterns = []
    for pattern in patterns_text.strip().split('\n'):
        pattern = pattern.strip()
        if pattern:
            try:
                re.compile(pattern)  # Validate regex
                patterns.append(pattern)
            except re.error:
                continue  # Skip invalid patterns
    
    return patterns if patterns else Config.DEFAULT_EXCLUDE_PATTERNS

def parse_selectors(selectors_text: str) -> Dict[str, str]:
    """Parse CSS selectors from text input."""
    selectors = {}
    if not selectors_text:
        return selectors
    
    for line in selectors_text.strip().split('\n'):
        if ':' in line:
            key, selector = line.split(':', 1)
            key = key.strip()
            selector = selector.strip()
            if key and selector:
                selectors[key] = selector
    
    return selectors
