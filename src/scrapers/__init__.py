"""
Scraper modules for different scraping modes.
"""

from .base import BaseScraper
from .basic import BasicScraper
from .crawler import WebsiteCrawler
from .sitemap import SitemapScraper
from .specialized import PepPediaScraper, PeptiPricesScraper
from .pep_pedia_bulk import PepPediaBulkScraper

__all__ = ['BaseScraper', 'BasicScraper', 'WebsiteCrawler', 'SitemapScraper', 'PepPediaScraper', 'PeptiPricesScraper', 'PepPediaBulkScraper']
