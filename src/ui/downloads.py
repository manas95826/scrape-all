"""
Download management for the Streamlit application.
"""

import streamlit as st
from typing import Union, List
from datetime import datetime

from ..models import ScrapedPage
from ..formatters import (
    JSONFormatter, CSVFormatter, HTMLFormatter, 
    TextFormatter, XMLFormatter
)


class DownloadManager:
    """Manages download functionality for different formats."""
    
    def __init__(self):
        self.formatters = {
            'JSON': JSONFormatter(),
            'CSV': CSVFormatter(),
            'HTML': HTMLFormatter(),
            'TXT': TextFormatter(),
            'XML': XMLFormatter()
        }
    
    def render_download_section(self, data: Union[ScrapedPage, List[ScrapedPage]]):
        """Render download section with all format options."""
        st.markdown("---")
        st.subheader("💾 Download Results")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create columns for download buttons
        cols = st.columns(5)
        
        for i, (format_name, formatter) in enumerate(self.formatters.items()):
            with cols[i]:
                self._create_download_button(data, formatter, format_name, timestamp)
    
    def _create_download_button(self, data, formatter, format_name: str, timestamp: str):
        """Create a single download button."""
        try:
            formatted_data = formatter.format(data)
            filename = f"scraped_content_{timestamp}.{formatter.get_file_extension()}"
            
            st.download_button(
                label=f"📄 {format_name}",
                data=formatted_data,
                file_name=filename,
                mime=formatter.get_mime_type()
            )
        except Exception as e:
            st.error(f"Error generating {format_name}: {str(e)}")
    
    def get_download_data(self, data: Union[ScrapedPage, List[ScrapedPage]], format_name: str) -> str:
        """Get formatted data for a specific format."""
        if format_name not in self.formatters:
            raise ValueError(f"Unsupported format: {format_name}")
        
        formatter = self.formatters[format_name]
        return formatter.format(data)
