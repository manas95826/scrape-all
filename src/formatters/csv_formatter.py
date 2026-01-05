"""
CSV formatter for scraped data.
"""

import pandas as pd
from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class CSVFormatter(BaseFormatter):
    """Formatter for CSV output."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format data as CSV."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return ""
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single page as CSV."""
        rows = []
        
        # Check for specialized data first
        if 'product_pricing' in page.custom_data:
            return self._format_pepti_prices_csv(page)
        elif 'backlinks' in page.custom_data:
            return self._format_backlinks_csv(page)
        
        # Default formatting for title-content pairs
        for i, pair in enumerate(page.title_content_pairs, 1):
            rows.append({
                'section_number': i,
                'title': pair.title,
                'content': pair.content,
                'content_length': len(pair.content)
            })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return ""
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages as CSV."""
        rows = []
        
        # Check if any pages have specialized data
        has_product_pricing = any('product_pricing' in page.custom_data for page in pages)
        has_backlinks = any('backlinks' in page.custom_data for page in pages)
        
        if has_product_pricing:
            return self._format_pepti_prices_csv_multiple(pages)
        elif has_backlinks:
            return self._format_backlinks_csv_multiple(pages)
        
        # Default formatting for title-content pairs
        for i, page in enumerate(pages, 1):
            for j, pair in enumerate(page.title_content_pairs, 1):
                rows.append({
                    'page_number': i,
                    'page_url': page.url,
                    'section_number': j,
                    'title': pair.title,
                    'content': pair.content,
                    'content_length': len(pair.content)
                })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return ""
    
    def _format_pepti_prices_csv(self, page: ScrapedPage) -> str:
        """Format PeptiPrices data as CSV."""
        products = page.custom_data.get("product_pricing", [])
        rows = []
        
        # Extract compound name from the page URL or from searched_product
        compound_name = page.custom_data.get("searched_product", "")
        if not compound_name:
            # Try to extract from URL
            if "/products/" in page.url:
                compound_name = page.url.split("/products/")[-1].replace("-", " ").replace("_", " ").title()
            else:
                compound_name = "Unknown"
        
        for product in products:
            for supplier in product.get("suppliers", []):
                rows.append({
                    "compound_name": compound_name,
                    "source_url": page.url,
                    "supplier": supplier.get("supplier", ""),
                    "price_current": supplier.get("price_current", ""),
                    "price_original": supplier.get("price_original", ""),
                    "stock_status": supplier.get("stock_status", ""),
                    "supplier_url": supplier.get("url", ""),
                    "full_text": supplier.get("full_text", "")
                })
        
        if rows:
            df = pd.DataFrame(rows)
            # Sort by supplier for better organization
            df = df.sort_values(['supplier'])
            return df.to_csv(index=False)
        return ""
    
    def _format_pepti_prices_csv_multiple(self, pages: List[ScrapedPage]) -> str:
        """Format multiple PeptiPrices pages as CSV."""
        all_rows = []
        
        for page in pages:
            # Extract compound name from the page URL or from searched_product
            compound_name = page.custom_data.get("searched_product", "")
            if not compound_name:
                # Try to extract from URL
                if "/products/" in page.url:
                    compound_name = page.url.split("/products/")[-1].replace("-", " ").replace("_", " ").title()
                else:
                    compound_name = "Unknown"
            
            products = page.custom_data.get("product_pricing", [])
            for product in products:
                for supplier in product.get("suppliers", []):
                    all_rows.append({
                        "compound_name": compound_name,
                        "source_url": page.url,
                        "supplier": supplier.get("supplier", ""),
                        "price_current": supplier.get("price_current", ""),
                        "price_original": supplier.get("price_original", ""),
                        "stock_status": supplier.get("stock_status", ""),
                        "supplier_url": supplier.get("url", ""),
                        "full_text": supplier.get("full_text", "")
                    })
        
        if all_rows:
            df = pd.DataFrame(all_rows)
            # Sort by compound name for better organization
            df = df.sort_values(['compound_name', 'supplier'])
            return df.to_csv(index=False)
        return ""
    
    def _format_backlinks_csv(self, page: ScrapedPage) -> str:
        """Format backlinks data as CSV."""
        backlinks = page.custom_data.get("backlinks", [])
        rows = []
        
        for backlink in backlinks:
            rows.append({
                "page_url": page.url,
                "link_url": backlink.get("url", ""),
                "link_text": backlink.get("link_text", ""),
                "is_internal": backlink.get("is_internal", ""),
                "title": backlink.get("title", ""),
                "target": backlink.get("target", ""),
                "original_href": backlink.get("original_href", "")
            })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return ""
    
    def _format_backlinks_csv_multiple(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages' backlinks as CSV."""
        all_rows = []
        
        for page in pages:
            backlinks = page.custom_data.get("backlinks", [])
            for backlink in backlinks:
                all_rows.append({
                    "page_url": page.url,
                    "link_url": backlink.get("url", ""),
                    "link_text": backlink.get("link_text", ""),
                    "is_internal": backlink.get("is_internal", ""),
                    "title": backlink.get("title", ""),
                    "target": backlink.get("target", ""),
                    "original_href": backlink.get("original_href", "")
                })
        
        if all_rows:
            df = pd.DataFrame(all_rows)
            return df.to_csv(index=False)
        return ""
    
    def get_file_extension(self) -> str:
        """Return CSV file extension."""
        return "csv"
    
    def get_mime_type(self) -> str:
        """Return CSV MIME type."""
        return "text/csv"
