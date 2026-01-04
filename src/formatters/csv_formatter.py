"""
CSV formatter for scraped data.
"""

import pandas as pd
from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class CSVFormatter(BaseFormatter):
    """Formatter for CSV output."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data as CSV."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return ""
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single page as CSV."""
        rows = []
        for i, pair in enumerate(page.title_content_pairs, 1):
            rows.append({
                'section_number': i,
                'title': pair.title,
                'content': pair.content,
                'content_length': len(pair.content)
            })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return ""
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages as CSV."""
        rows = []
        for i, page in enumerate(pages, 1):
            for j, pair in enumerate(page.title_content_pairs, 1):
                rows.append({
                    'page_number': i,
                    'page_url': page.url,
                    'section_number': j,
                    'title': pair.title,
                    'content': pair.content,
                    'content_length': len(pair.content)
                })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return ""
    
    def get_file_extension(self) -> str:
        """Return CSV file extension."""
        return "csv"
    
    def get_mime_type(self) -> str:
        """Return CSV MIME type."""
        return "text/csv"
