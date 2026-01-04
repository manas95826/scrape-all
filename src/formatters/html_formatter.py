"""
HTML formatter for scraped data.
"""

from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class HTMLFormatter(BaseFormatter):
    """Formatter for HTML output."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data as HTML."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return self._empty_html()
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single page as HTML."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scraped Content Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; background: #f9f9f; }}
        .section h2 {{ color: #007cba; margin-top: 0; }}
        .title-content-pair {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
        .title {{ background: #007cba; color: white; padding: 15px; font-weight: bold; font-size: 18px; }}
        .content {{ background: #f0f8ff; padding: 15px; }}
        .meta-info {{ background: #f0f0f0; padding: 10px; border-radius: 3px; margin: 10px 0; }}
        .stats {{ display: flex; gap: 20px; margin: 10px 0; flex-wrap: wrap; }}
        .stat {{ background: #007cba; color: white; padding: 10px; border-radius: 3px; text-align: center; min-width: 80px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ Web Scraping Report</h1>
        <div class="meta-info">
            <p><strong>URL:</strong> <a href="{page.url}" target="_blank">{page.url}</a></p>
            <p><strong>Scraped at:</strong> {page.scraped_at}</p>
        </div>
        <div class="stats">
            <div class="stat">
                <h3>{len(page.title_content_pairs)}</h3>
                <p>Title-Content Pairs</p>
            </div>
            <div class="stat">
                <h3>{sum(len(pair.content) for pair in page.title_content_pairs)}</h3>
                <p>Total Characters</p>
            </div>
        </div>
    </div>"""
        
        # Title-Content Pairs Section
        if page.title_content_pairs:
            html += '<div class="section"><h2>📋 Title-Content Pairs</h2>'
            for i, pair in enumerate(page.title_content_pairs, 1):
                title = pair.title
                content = pair.content
                
                html += f'<div class="title-content-pair">'
                html += f'<div class="title">{i}. {title}</div>'
                if content:
                    html += f'<div class="content">{content}</div>'
                else:
                    html += f'<div class="content"><em>No content found for this section</em></div>'
                html += '</div>'
            html += '</div>'
        
        html += '</body></html>'
        return html
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages as HTML."""
        total_pairs = sum(len(page.title_content_pairs) for page in pages)
        total_chars = sum(sum(len(pair.content) for pair in page.title_content_pairs) for page in pages)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Scraping Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .page-section {{ margin: 30px 0; padding: 20px; border: 2px solid #ddd; border-radius: 8px; background: #fafafa; }}
        .page-header {{ background: #007cba; color: white; padding: 15px; margin: -20px -20px 20px -20px; border-radius: 6px 6px 0 0; }}
        .title-content-pair {{ margin: 15px 0; border: 1px solid #ccc; border-radius: 5px; overflow: hidden; }}
        .title {{ background: #2c3e50; color: white; padding: 12px; font-weight: bold; }}
        .content {{ background: #ecf0f1; padding: 12px; }}
        .stats {{ display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap; }}
        .stat {{ background: #27ae60; color: white; padding: 10px; border-radius: 3px; text-align: center; min-width: 80px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ Website Scraping Report</h1>
        <div class="stats">
            <div class="stat">
                <h3>{len(pages)}</h3>
                <p>Total Pages</p>
            </div>
            <div class="stat">
                <h3>{total_pairs}</h3>
                <p>Total Sections</p>
            </div>
            <div class="stat">
                <h3>{total_chars}</h3>
                <p>Total Characters</p>
            </div>
        </div>
    </div>"""
        
        for i, page in enumerate(pages, 1):
            html += f'<div class="page-section">'
            html += f'<div class="page-header">'
            html += f'<h2>Page {i}: {page.url}</h2>'
            html += f'<p>Scraped at: {page.scraped_at}</p>'
            html += f'</div>'
            
            if page.title_content_pairs:
                for j, pair in enumerate(page.title_content_pairs, 1):
                    title = pair.title
                    content = pair.content
                    
                    html += f'<div class="title-content-pair">'
                    html += f'<div class="title">{j}. {title}</div>'
                    if content:
                        html += f'<div class="content">{content}</div>'
                    else:
                        html += f'<div class="content"><em>No content found for this section</em></div>'
                    html += '</div>'
            
            html += '</div>'
        
        html += '</body></html>'
        return html
    
    def _empty_html(self) -> str:
        """Return empty HTML template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>No Data</title>
</head>
<body>
    <h1>No data available</h1>
</body>
</html>"""
    
    def get_file_extension(self) -> str:
        """Return HTML file extension."""
        return "html"
    
    def get_mime_type(self) -> str:
        """Return HTML MIME type."""
        return "text/html"
