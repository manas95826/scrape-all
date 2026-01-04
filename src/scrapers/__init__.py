"""
Scraper modules for different scraping modes.
"""

from .base import BaseScraper
from .basic import BasicScraper
from .crawler import WebsiteCrawler
from .sitemap import SitemapScraper

__all__ = ['BaseScraper', 'BasicScraper', 'WebsiteCrawler', 'SitemapScraper']
