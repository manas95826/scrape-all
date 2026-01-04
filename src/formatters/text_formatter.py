"""
Text formatter for scraped data.
"""

from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class TextFormatter(BaseFormatter):
    """Formatter for plain text output."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data as plain text."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return "No data available"
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single page as text."""
        text = f"""╔══════════════════════════════════════════════════════════════╗
║                    🕷️ WEB SCRAPING REPORT                    ║
╚══════════════════════════════════════════════════════════════╝

📊 BASIC INFORMATION
────────────────────────────────────────────────────────────────
URL: {page.url}
Scraped at: {page.scraped_at}

📈 CONTENT STATISTICS
────────────────────────────────────────────────────────────────
Title-Content Pairs: {len(page.title_content_pairs)}
Total Characters: {sum(len(pair.content) for pair in page.title_content_pairs)}

"""
        
        # Title-Content Pairs
        if page.title_content_pairs:
            text += "📋 TITLE-CONTENT PAIRS\n────────────────────────────────────────────────────────────────\n"
            for i, pair in enumerate(page.title_content_pairs, 1):
                title = pair.title
                content = pair.content
                
                text += f"\n{'='*80}\n"
                text += f"SECTION {i}\n"
                text += f"{'='*80}\n"
                text += f"TITLE: {title}\n"
                text += f"{'─'*80}\n"
                if content:
                    text += f"CONTENT:\n{content}\n"
                else:
                    text += f"CONTENT:\nNo content found for this section\n"
                text += f"\n"
        
        text += "╔══════════════════════════════════════════════════════════════╗\n"
        text += "║                        END OF REPORT                        ║\n"
        text += "╚══════════════════════════════════════════════════════════════╝\n"
        
        return text
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages as text."""
        total_pairs = sum(len(page.title_content_pairs) for page in pages)
        total_chars = sum(sum(len(pair.content) for pair in page.title_content_pairs) for page in pages)
        
        text = f"""╔══════════════════════════════════════════════════════════════╗
║                🕷️ WEBSITE SCRAPING REPORT                ║
╚══════════════════════════════════════════════════════════════╝

📊 SUMMARY STATISTICS
────────────────────────────────────────────────────────────────
Total Pages: {len(pages)}
Total Sections: {total_pairs}
Total Characters: {total_chars}

"""
        
        for i, page in enumerate(pages, 1):
            text += f"\n{'='*100}\n"
            text += f"PAGE {i}\n"
            text += f"{'='*100}\n"
            text += f"URL: {page.url}\n"
            text += f"Scraped at: {page.scraped_at}\n"
            text += f"Sections: {len(page.title_content_pairs)}\n"
            text += f"{'─'*100}\n"
            
            if page.title_content_pairs:
                for j, pair in enumerate(page.title_content_pairs, 1):
                    title = pair.title
                    content = pair.content
                    
                    text += f"\n  {'─'*80}\n"
                    text += f"  SECTION {j}\n"
                    text += f"  {'─'*80}\n"
                    text += f"  TITLE: {title}\n"
                    text += f"  {'─'*80}\n"
                    if content:
                        text += f"  CONTENT:\n  {content}\n"
                    else:
                        text += f"  CONTENT:\n  No content found for this section\n"
                    text += f"\n"
        
        text += "\n╔══════════════════════════════════════════════════════════════╗\n"
        text += "║                        END OF REPORT                        ║\n"
        text += "╚══════════════════════════════════════════════════════════════╝\n"
        
        return text
    
    def get_file_extension(self) -> str:
        """Return text file extension."""
        return "txt"
    
    def get_mime_type(self) -> str:
        """Return text MIME type."""
        return "text/plain"
