"""
XML formatter for scraped data.
"""

from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class XMLFormatter(BaseFormatter):
    """Formatter for XML output."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data as XML."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return '<?xml version="1.0" encoding="UTF-8"?><scraped_content></scraped_content>'
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single page as XML."""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<scraped_content>\n'
        xml += f'  <url>{page.url}</url>\n'
        xml += f'  <scraped_at>{page.scraped_at}</scraped_at>\n'
        
        xml += '  <title_content_pairs>\n'
        for i, pair in enumerate(page.title_content_pairs, 1):
            xml += f'    <pair id="{i}">\n'
            xml += f'      <title>{self._escape_xml(pair.title)}</title>\n'
            xml += f'      <content>{self._escape_xml(pair.content)}</content>\n'
            xml += f'    </pair>\n'
        xml += '  </title_content_pairs>\n'
        
        # Add custom data if present
        if page.custom_data:
            xml += '  <custom_data>\n'
            for key, value in page.custom_data.items():
                xml += f'    <{key}>{self._escape_xml(str(value))}</{key}>\n'
            xml += '  </custom_data>\n'
        
        xml += '</scraped_content>\n'
        return xml
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages as XML."""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<website_scraping_report>\n'
        xml += f'  <summary>\n'
        xml += f'    <total_pages>{len(pages)}</total_pages>\n'
        xml += f'    <total_sections>{sum(len(page.title_content_pairs) for page in pages)}</total_sections>\n'
        xml += f'    <total_characters>{sum(sum(len(pair.content) for pair in page.title_content_pairs) for page in pages)}</total_characters>\n'
        xml += f'  </summary>\n'
        xml += f'  <pages>\n'
        
        for i, page in enumerate(pages, 1):
            xml += f'    <page id="{i}">\n'
            xml += f'      <url>{page.url}</url>\n'
            xml += f'      <scraped_at>{page.scraped_at}</scraped_at>\n'
            
            xml += f'      <title_content_pairs>\n'
            for j, pair in enumerate(page.title_content_pairs, 1):
                xml += f'        <pair id="{j}">\n'
                xml += f'          <title>{self._escape_xml(pair.title)}</title>\n'
                xml += f'          <content>{self._escape_xml(pair.content)}</content>\n'
                xml += f'        </pair>\n'
            xml += f'      </title_content_pairs>\n'
            
            # Add custom data if present
            if page.custom_data:
                xml += f'      <custom_data>\n'
                for key, value in page.custom_data.items():
                    xml += f'        <{key}>{self._escape_xml(str(value))}</{key}>\n'
                xml += f'      </custom_data>\n'
            
            xml += f'    </page>\n'
        
        xml += f'  </pages>\n'
        xml += f'</website_scraping_report>\n'
        return xml
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        if not text:
            return ""
        
        # Basic XML escaping
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        return text
    
    def get_file_extension(self) -> str:
        """Return XML file extension."""
        return "xml"
    
    def get_mime_type(self) -> str:
        """Return XML MIME type."""
        return "application/xml"
