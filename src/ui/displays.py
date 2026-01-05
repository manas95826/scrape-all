"""
Data display components for the Streamlit application.
"""

import streamlit as st
import json
from typing import Union, List
from datetime import datetime

from ..models import ScrapedPage, ScrapingStats
from ..formatters import JSONFormatter


class DataDisplay:
    """Components for displaying scraped data."""
    
    @staticmethod
    def display_scraped_data(data: Union[ScrapedPage, List[ScrapedPage]]):
        """Display scraped data in a beautiful format."""
        if not data:
            st.error("No data to display!")
            return
        
        if isinstance(data, list):
            DataDisplay._display_multiple_pages(data)
        else:
            DataDisplay._display_single_page(data)
    
    @staticmethod
    def _display_single_page(page: ScrapedPage):
        """Display a single scraped page."""
        st.subheader("📊 Summary Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Title-Content Pairs", len(page.title_content_pairs))
        with col2:
            total_content_length = sum(len(pair.content) for pair in page.title_content_pairs)
            st.metric("Total Characters", total_content_length)
        
        # Basic Info
        st.subheader("🌍 Basic Information")
        st.info(f"""
        **URL:** {page.url}  
        **Scraped at:** {page.scraped_at}
        """)
        
        # Title-Content Pairs
        if page.title_content_pairs:
            st.subheader("📋 Title-Content Pairs")
            
            for i, pair in enumerate(page.title_content_pairs, 1):
                title = pair.title
                content = pair.content
                
                with st.expander(f"Section {i}: {title[:100]}{'...' if len(title) > 100 else ''}"):
                    st.write(f"**📌 Title:** {title}")
                    if content:
                        st.write(f"**📝 Content:** {content}")
                    else:
                        st.write("*No content found for this section*")
        
        # Custom data if present
        if page.custom_data:
            st.subheader("🎯 Custom Data")
            for key, value in page.custom_data.items():
                st.write(f"**{key}:** {value}")
    
    @staticmethod
    def _display_multiple_pages(pages: List[ScrapedPage]):
        """Display multiple scraped pages."""
        st.subheader("📊 Website Scraping Summary")
        
        # Calculate statistics
        stats = ScrapingStats.from_pages(pages, "Website Crawler", 0)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Pages", stats.total_pages)
        
        with col2:
            st.metric("Total Sections", stats.total_sections)
        
        with col3:
            st.metric("Total Characters", stats.total_characters)
        
        # Page selector
        page_titles = [
            f"Page {i+1}: {page.title_content_pairs[0].title[:50] if page.title_content_pairs else 'No title'}" 
            for i, page in enumerate(pages)
        ]
        selected_page = st.selectbox("📄 Select Page to View", range(len(page_titles)), format_func=lambda x: page_titles[x])
        
        # Display selected page
        page_data = pages[selected_page]
        st.markdown(f"### 🌐 Page URL: {page_data.url}")
        
        if page_data.title_content_pairs:
            st.subheader("📋 Title-Content Pairs")
            
            for i, pair in enumerate(page_data.title_content_pairs, 1):
                title = pair.title
                content = pair.content
                
                with st.expander(f"Section {i}: {title[:100]}{'...' if len(title) > 100 else ''}"):
                    st.write(f"**📌 Title:** {title}")
                    if content:
                        st.write(f"**📝 Content:** {content}")
                    else:
                        st.write("*No content found for this section*")
        
        # Custom data if present
        if page_data.custom_data:
            st.subheader("🎯 Custom Data")
            for key, value in page_data.custom_data.items():
                st.write(f"**{key}:** {value}")
    
    @staticmethod
    def display_raw_data_preview(data: Union[ScrapedPage, List[ScrapedPage]]):
        """Display raw data preview in JSON format."""
        st.markdown("---")
        st.subheader("🔍 Raw Data Preview")
        
        # Convert to dict for JSON display
        if isinstance(data, ScrapedPage):
            st.json(data.to_dict())
        else:
            st.json([page.to_dict() for page in data])
    
    @staticmethod
    def display_error(message: str):
        """Display error message."""
        st.error(f"❌ {message}")
    
    @staticmethod
    def display_success(message: str):
        """Display success message."""
        st.success(f"✅ {message}")
    
    @staticmethod
    def create_progress_components():
        """Create progress bar and status text components."""
        progress_bar = st.progress(0)
        status_text = st.empty()
        return progress_bar, status_text
    
    @staticmethod
    def update_progress(progress_bar, status_text, progress: float, status: str):
        """Update progress components."""
        progress_bar.progress(progress)
        status_text.text(status)
