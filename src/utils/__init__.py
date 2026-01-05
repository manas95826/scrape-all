"""
Utility modules for the web scraper.
"""

# Import from core.py
from .core import (
    safe_request,
    delay_request,
    create_progress_callback,
    extract_title_content_pairs,
    extract_custom_data,
    extract_links,
    is_valid_url,
    normalize_url,
    is_internal_link,
    should_skip_url,
    extract_element_text
)

# Import from content_categorizer.py
from .content_categorizer import ContentCategorizer

__all__ = [
    'safe_request',
    'delay_request', 
    'create_progress_callback',
    'extract_title_content_pairs',
    'extract_custom_data',
    'extract_links',
    'is_valid_url',
    'normalize_url',
    'is_internal_link',
    'should_skip_url',
    'extract_element_text',
    'ContentCategorizer'
]
