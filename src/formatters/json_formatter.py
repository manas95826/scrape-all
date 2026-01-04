"""
JSON formatter for scraped data.
"""

import json
from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Formatter for JSON output."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data as JSON."""
        if isinstance(data, ScrapedPage):
            return json.dumps(data.to_dict(), indent=2, ensure_ascii=False)
        elif isinstance(data, list):
            return json.dumps([page.to_dict() for page in data], indent=2, ensure_ascii=False)
        else:
            return json.dumps({}, indent=2, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        """Return JSON file extension."""
        return "json"
    
    def get_mime_type(self) -> str:
        """Return JSON MIME type."""
        return "application/json"
