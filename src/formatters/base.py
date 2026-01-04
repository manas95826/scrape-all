"""
Base formatter class.
"""

from abc import ABC, abstractmethod
from typing import Union, List
from ..models import ScrapedPage


class BaseFormatter(ABC):
    """Base class for all output formatters."""
    
    @abstractmethod
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data into specific output format."""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format."""
        pass
    
    @abstractmethod
    def get_mime_type(self) -> str:
        """Get MIME type for this format."""
        pass
