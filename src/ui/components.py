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
                [ScrapingMode.BASIC, ScrapingMode.CUSTOM_SELECTORS, 
                 ScrapingMode.WEBSITE_CRAWLER, ScrapingMode.SITEMAP_SCRAPER]
            )
            
            # URL Input
            url = st.text_input(
                "🌐 Enter URL to scrape",
                placeholder="https://example.com",
                help="Enter the full URL including http:// or https://"
            )
            
            # Mode-specific configuration
            config = {}
            
            if scraping_mode == ScrapingMode.WEBSITE_CRAWLER:
                config = UIComponents._render_crawler_config()
            elif scraping_mode == ScrapingMode.SITEMAP_SCRAPER:
                config = UIComponents._render_sitemap_config()
            elif scraping_mode == ScrapingMode.CUSTOM_SELECTORS:
                config = UIComponents._render_custom_selectors_config()
            
            # Scrape Button
            scrape_button = st.button("🚀 Start Scraping", type="primary")
            
            return scraping_mode, url, config, scrape_button
    
    @staticmethod
    def _render_crawler_config() -> Dict[str, Any]:
        """Render crawler-specific configuration."""
        st.subheader("🕷️ Crawler Settings")
        
        max_pages = st.number_input(
            "Max Pages to Scrape",
            min_value=1,
            max_value=Config.MAX_PAGES_LIMIT,
            value=Config.DEFAULT_MAX_PAGES,
            help="Maximum number of pages to discover and scrape"
        )
        
        max_depth = st.number_input(
            "Max Depth",
            min_value=1,
            max_value=Config.MAX_DEPTH_LIMIT,
            value=Config.DEFAULT_MAX_DEPTH,
            help="Maximum link depth to follow from the starting page"
        )
        
        stay_on_domain = st.checkbox(
            "Stay on Same Domain",
            value=True,
            help="Only scrape pages from the same domain as the starting URL"
        )
        
        use_sitemap = st.checkbox(
            "Use Sitemap (if available)",
            value=True,
            help="Try to discover and use XML sitemap for faster page discovery"
        )
        
        exclude_patterns = st.text_area(
            "Exclude Patterns (one per line)",
            placeholder=r"\.(pdf|jpg|jpeg|png|gif)$\n/admin\n/login",
            help="Regex patterns to exclude certain URLs (optional)"
        )
        
        exclude_list = parse_exclude_patterns(exclude_patterns)
        
        return {
            'max_pages': max_pages,
            'max_depth': max_depth,
            'stay_on_domain': stay_on_domain,
            'use_sitemap': use_sitemap,
            'exclude_patterns': exclude_list
        }
    
    @staticmethod
    def _render_sitemap_config() -> Dict[str, Any]:
        """Render sitemap-specific configuration."""
        st.subheader("🗺️ Sitemap Settings")
        
        sitemap_url = st.text_input(
            "🗺️ Sitemap URL (optional)",
            placeholder="https://example.com/sitemap.xml",
            help="Leave empty to auto-discover sitemap, or enter specific sitemap URL"
        )
        
        max_pages = st.number_input(
            "Max Pages to Scrape",
            min_value=1,
            max_value=Config.MAX_PAGES_LIMIT,
            value=100,
            help="Maximum number of pages to scrape from sitemap"
        )
        
        return {
            'sitemap_url': sitemap_url,
            'max_pages': max_pages
        }
    
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
           - **Website Crawler**: Discovers and scrapes all pages from an entire website
           - **Sitemap Scraper**: Uses XML sitemap to efficiently scrape all listed pages
        3. **Configure**: 
           - For custom mode, enter your CSS selectors
           - For crawler mode, set max pages, depth, and exclusion patterns
           - For sitemap mode, enter specific sitemap URL or let it auto-discover
        4. **Scrape**: Click the "Start Scraping" button
        5. **Download**: Choose from multiple output formats (JSON, CSV, HTML, TXT, XML)
        
        ## 📋 Features
        
        - **🕷️ Website Crawling**: Discover and scrape entire websites automatically
        - **🗺️ Sitemap Support**: Parse XML sitemaps for efficient page discovery
        - **🎯 Multiple Output Formats**: JSON, CSV, HTML, TXT, XML
        - **📊 Beautiful Visualizations**: Interactive charts and statistics
        - **🔍 Custom Selectors**: Extract specific data using CSS selectors
        - **💾 Easy Downloads**: One-click download in any format
        - **📱 Responsive Design**: Works on all devices
        - **⚡ Fast Processing**: Efficient scraping with proper headers
        - **🛡️ Smart Filtering**: Exclude unwanted URLs and stay on domain
        """)
