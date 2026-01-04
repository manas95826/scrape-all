"""
Data models for the web scraper.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class TitleContentPair:
    """Represents a title-content pair from a webpage."""
    title: str
    content: str
    section_number: int = 0

@dataclass
class ScrapedPage:
    """Represents a scraped webpage with its metadata."""
    url: str
    scraped_at: str
    title_content_pairs: List[TitleContentPair]
    custom_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.custom_data is None:
            self.custom_data = {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScrapedPage':
        """Create ScrapedPage from dictionary."""
        pairs = []
        for i, pair_data in enumerate(data.get('title_content_pairs', [])):
            pairs.append(TitleContentPair(
                title=pair_data.get('title', ''),
                content=pair_data.get('content', ''),
                section_number=i + 1
            ))
        
        return cls(
            url=data.get('scraped_url', ''),
            scraped_at=data.get('scraped_at', datetime.now().isoformat()),
            title_content_pairs=pairs,
            custom_data={k: v for k, v in data.items() 
                        if k not in ['scraped_url', 'scraped_at', 'title_content_pairs']}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ScrapedPage to dictionary."""
        return {
            'scraped_url': self.url,
            'scraped_at': self.scraped_at,
            'title_content_pairs': [
                {
                    'title': pair.title,
                    'content': pair.content
                } for pair in self.title_content_pairs
            ],
            **self.custom_data
        }

@dataclass
class ScrapingStats:
    """Statistics for a scraping operation."""
    total_pages: int
    total_sections: int
    total_characters: int
    scraping_mode: str
    duration_seconds: float
    
    @classmethod
    def from_pages(cls, pages: List[ScrapedPage], mode: str, duration: float) -> 'ScrapingStats':
        """Create stats from scraped pages."""
        total_sections = sum(len(page.title_content_pairs) for page in pages)
        total_characters = sum(
            len(pair.content) for page in pages 
            for pair in page.title_content_pairs
        )
        
        return cls(
            total_pages=len(pages),
            total_sections=total_sections,
            total_characters=total_characters,
            scraping_mode=mode,
            duration_seconds=duration
        )

@dataclass
class SitemapInfo:
    """Information about a discovered sitemap."""
    url: str
    page_count: int
    is_nested: bool = False
    parent_sitemap: Optional[str] = None
