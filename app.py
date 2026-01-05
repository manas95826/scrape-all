"""
Main Streamlit application for the Universal Web Scraper.
"""

import time
from typing import Union, List

import streamlit as st

from src.config import Config, ScrapingMode
from src.models import ScrapedPage
from src.scrapers import BasicScraper, PeptiPricesScraper
from src.ui import UIComponents, DataDisplay, DownloadManager
from src.utils import create_progress_callback


class WebScraperApp:
    """Main application class for the web scraper."""
    
    def __init__(self):
        self.download_manager = DownloadManager()
        self.scrapers = {
            ScrapingMode.BASIC: BasicScraper(),
            ScrapingMode.CUSTOM_SELECTORS: BasicScraper(),
            'PeptiPrices': PeptiPricesScraper()
        }
    
    def run(self):
        """Run the main application."""
        UIComponents.setup_page_config()
        UIComponents.render_header()
        
        # Render sidebar and get configuration
        scraping_mode, url, config, scrape_button = UIComponents.render_sidebar()
        
        # Main content area
        if scrape_button:
            self._handle_scraping_request(scraping_mode, url, config)
        else:
            UIComponents.render_instructions()
    
    def _handle_scraping_request(self, mode: str, url: str, config: dict):
        """Handle scraping request based on mode."""
        if not UIComponents.validate_url(url):
            return
        
        # Show loading spinner
        with st.spinner("🕷️ Scraping in progress..."):
            try:
                data = self._scrape_data(mode, url, config)
                
                if data:
                    DataDisplay.display_success("Scraping completed successfully!")
                    DataDisplay.display_scraped_data(data)
                    self.download_manager.render_download_section(data)
                    DataDisplay.display_raw_data_preview(data)
                else:
                    DataDisplay.display_error("Failed to scrape the URL. Please check if the URL is accessible and try again.")
            
            except Exception as e:
                DataDisplay.display_error(f"An error occurred during scraping: {str(e)}")
    
    def _scrape_data(self, mode: str, url: str, config: dict) -> Union[ScrapedPage, List[ScrapedPage]]:
        """Scrape data based on selected mode."""
        # Handle specialized scrapers (case-insensitive matching)
        mode_lower = mode.lower()
        if 'peptiprices' in mode_lower:
            scraper = self.scrapers['PeptiPrices']
            # Create progress components for bulk scraping
            progress_bar, status_text = DataDisplay.create_progress_components()
            progress_callback = create_progress_callback(progress_bar, status_text)
            
            try:
                data = scraper.scrape(url, bulk_scrape=True, progress_callback=progress_callback)
                return data
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                raise e
        
        # Handle standard modes - check if mode exists in scrapers dict
        if mode in self.scrapers:
            scraper = self.scrapers[mode]
            
            if mode == ScrapingMode.BASIC:
                return scraper.scrape(url)
            
            elif mode == ScrapingMode.CUSTOM_SELECTORS:
                selectors = config.get('selectors', {})
                return scraper.scrape(url, selectors=selectors)
        
        # If we get here, the mode is not recognized
        raise ValueError(f"Unknown scraping mode: {mode}")


def main():
    """Main entry point for the application."""
    app = WebScraperApp()
    app.run()


if __name__ == "__main__":
    main()