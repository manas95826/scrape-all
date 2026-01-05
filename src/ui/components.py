"""
UI components for the Streamlit application.
"""

import streamlit as st
from typing import Dict, Any, Tuple, Optional

from ..config import Config, ScrapingMode, parse_exclude_patterns, parse_selectors


class UIComponents:
    """UI component utilities for the Streamlit app."""
    
    @staticmethod
    def setup_page_config():
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title="🕷️ Web Scraper",
            page_icon="🕷️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    @staticmethod
    def render_header():
        """Render application header."""
        st.title("🕷️ Universal Web Scraper")
        st.markdown("---")
    
    @staticmethod
    def render_sidebar() -> Tuple[str, str, Dict[str, Any]]:
        """Render sidebar configuration and return settings."""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # Scraping Mode
            scraping_mode = st.selectbox(
                "Scraping Mode",
                [ScrapingMode.BASIC, ScrapingMode.CUSTOM_SELECTORS, "PeptiPrices (Specialized)", "Pep-Pedia (Specialized)"]
            )
            
            # URL Input
            url = st.text_input(
                "🌐 Enter URL to scrape",
                placeholder="https://example.com",
                help="Enter the full URL including http:// or https://"
            )
            
            # Mode-specific configuration
            config = {}
            
            if scraping_mode == ScrapingMode.CUSTOM_SELECTORS:
                config = UIComponents._render_custom_selectors_config()
            elif scraping_mode == "PeptiPrices (Specialized)":
                config = UIComponents._render_pepti_prices_config()
            elif scraping_mode == "Pep-Pedia (Specialized)":
                config = UIComponents._render_pep_pedia_config()
            
            # Scrape Button
            scrape_button = st.button("🚀 Start Scraping", type="primary")
            
            return scraping_mode, url, config, scrape_button
    
    @staticmethod
    def _render_pepti_prices_config() -> Dict[str, Any]:
        """Render PeptiPrices specialized configuration."""
        st.subheader("💰 PeptiPrices Settings")
        
        st.info("🚀 This will automatically scrape all 60+ products from PeptiPrices.com")
        
        return {'bulk_scrape': True}
    
    @staticmethod
    def _render_pep_pedia_config() -> Dict[str, Any]:
        """Render Pep-Pedia specialized configuration."""
        st.subheader("📚 Pep-Pedia Settings")
        
        st.info("🚀 This will automatically scrape all 63 peptide research articles from Pep-Pedia.org")
        
        return {'bulk_scrape': True}
    
    @staticmethod
    def _render_custom_selectors_config() -> Dict[str, Any]:
        """Render custom selectors configuration."""
        st.subheader("🎯 Custom Selectors")
        
        selector_input = st.text_area(
            "Enter CSS selectors (one per line, format: key:selector)",
            placeholder="title:h1\nprice:.price\ndescription:.product-description",
            help="Example: title:h1 will extract text from h1 tags and store it as 'title'"
        )
        
        selectors = parse_selectors(selector_input)
        
        return {'selectors': selectors}
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL input."""
        if not url:
            st.error("⚠️ Please enter a URL to scrape!")
            return False
        
        if not url.startswith(('http://', 'https://')):
            st.error("⚠️ Please include http:// or https:// in the URL!")
            return False
        
        return True
    
    @staticmethod
    def render_instructions():
        """Render usage instructions."""
        st.markdown("""
        ## 🚀 How to Use
        
        1. **Enter URL**: Input the website URL you want to scrape (must include http:// or https://)
        2. **Choose Mode**: 
           - **Basic Content**: Extracts title, headings, paragraphs, links, and images from a single page
           - **Custom CSS Selectors**: Extract specific elements using CSS selectors from a single page
           - **PeptiPrices (Specialized)**: Automatically scrapes all 60+ peptide products from PeptiPrices.com
           - **Pep-Pedia (Specialized)**: Automatically scrapes all 63 peptide research articles from Pep-Pedia.org
        3. **Configure**: 
           - For custom mode, enter your CSS selectors
           - For PeptiPrices mode, just enter https://peptiprices.com/ and it will handle everything
           - For Pep-Pedia mode, just enter https://pep-pedia.org/browse and it will handle everything
        4. **Scrape**: Click the "Start Scraping" button
        5. **Download**: Choose from CSV and JSON output formats
        
        ## 📋 Features
        
        - **🧪 PeptiPrices Integration**: Bulk scrape all peptide products with pricing data
        - **📚 Pep-Pedia Integration**: Bulk scrape all peptide research articles with detailed information
        - **🎯 Output Formats**: JSON and CSV with organized compound/supplier data
        - **📊 Beautiful Visualizations**: Interactive charts and statistics
        - **🔍 Custom Selectors**: Extract specific data using CSS selectors
        - **💾 Easy Downloads**: One-click download in CSV or JSON format
        - **📱 Responsive Design**: Works on all devices
        - **⚡ Fast Processing**: Efficient scraping with proper headers
        - **📈 Progress Tracking**: Real-time progress bars for bulk operations
        """)
