"""
Specialized formatters for structured peptide data.
"""

import json
import csv
from io import StringIO
from typing import Union, List
from ..models import ScrapedPage
from .base import BaseFormatter


class PeptideInfoFormatter(BaseFormatter):
    """Formatter for structured peptide information."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format peptide data with structured information."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return json.dumps({"error": "No data available"}, indent=2)
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single peptide page."""
        output = {
            "peptide_info": page.custom_data.get("peptide_info", {}),
            "basic_info": {
                "url": page.url,
                "scraped_at": page.scraped_at,
                "title": page.title_content_pairs[0].title if page.title_content_pairs else ""
            },
            "content_sections": [
                {
                    "title": pair.title,
                    "content": pair.content
                } for pair in page.title_content_pairs
            ]
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple peptide pages."""
        peptides = []
        
        for page in pages:
            peptide_data = {
                "name": page.custom_data.get("peptide_info", {}).get("name", "Unknown"),
                "url": page.url,
                "scraped_at": page.scraped_at,
                "molecular_info": page.custom_data.get("peptide_info", {}).get("molecular_info", {}),
                "benefits": page.custom_data.get("peptide_info", {}).get("benefits", []),
                "mechanism_of_action": page.custom_data.get("peptide_info", {}).get("mechanism_of_action", ""),
                "research_indications": page.custom_data.get("peptide_info", {}).get("research_indications", []),
                "quality_indicators": page.custom_data.get("peptide_info", {}).get("quality_indicators", []),
                "protocols": page.custom_data.get("peptide_info", {}).get("protocols", {}),
                "content_sections": [
                    {
                        "title": pair.title,
                        "content": pair.content
                    } for pair in page.title_content_pairs
                ]
            }
            peptides.append(peptide_data)
        
        return json.dumps({
            "peptides": peptides,
            "total_count": len(peptides),
            "scraped_at": pages[0].scraped_at if pages else ""
        }, indent=2, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        return "json"
    
    def get_mime_type(self) -> str:
        return "application/json"


class PricingDataFormatter(BaseFormatter):
    """Formatter for pricing comparison data."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format pricing data with structured comparison."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page(data)
        elif isinstance(data, list):
            return self._format_multiple_pages(data)
        else:
            return json.dumps({"error": "No data available"}, indent=2)
    
    def _format_single_page(self, page: ScrapedPage) -> str:
        """Format a single pricing page."""
        products = page.custom_data.get("product_pricing", [])
        
        output = {
            "page_info": {
                "url": page.url,
                "scraped_at": page.scraped_at,
                "title": page.title_content_pairs[0].title if page.title_content_pairs else ""
            },
            "products": products
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def _format_multiple_pages(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pricing pages."""
        all_products = []
        
        for page in pages:
            products = page.custom_data.get("product_pricing", [])
            all_products.extend(products)
        
        return json.dumps({
            "pricing_comparison": {
                "products": all_products,
                "total_products": len(all_products),
                "unique_suppliers": self._count_unique_suppliers(all_products),
                "last_updated": pages[0].scraped_at if pages else ""
            }
        }, indent=2, ensure_ascii=False)
    
    def _count_unique_suppliers(self, products: List[dict]) -> int:
        """Count unique suppliers across all products."""
        suppliers = set()
        for product in products:
            for supplier in product.get("suppliers", []):
                suppliers.add(supplier.get("supplier", "Unknown"))
        return len(suppliers)
    
    def get_file_extension(self) -> str:
        return "json"
    
    def get_mime_type(self) -> str:
        return "application/json"


class PricingCSVFormatter(BaseFormatter):
    """CSV formatter for pricing data with proper structure."""
    
    def format(self, data: Union[ScrapedPage, List[ScrapedPage]]) -> str:
        """Format pricing data as CSV."""
        if isinstance(data, ScrapedPage):
            return self._format_single_page_csv(data)
        elif isinstance(data, list):
            return self._format_multiple_pages_csv(data)
        else:
            return ""
    
    def _format_single_page_csv(self, page: ScrapedPage) -> str:
        """Format single page as CSV."""
        products = page.custom_data.get("product_pricing", [])
        rows = []
        
        for product in products:
            product_name = product.get("product_name", "")
            for supplier in product.get("suppliers", []):
                rows.append({
                    "product_name": product_name,
                    "supplier": supplier.get("supplier", ""),
                    "price_current": supplier.get("price_current", ""),
                    "price_original": supplier.get("price_original", ""),
                    "stock_status": supplier.get("stock_status", ""),
                    "url": supplier.get("url", ""),
                    "full_text": supplier.get("full_text", "")
                })
        
        if rows:
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "product_name", "supplier", "price_current", "price_original", 
                "stock_status", "url", "full_text"
            ])
            writer.writeheader()
            writer.writerows(rows)
            return output.getvalue()
        
        return ""
    
    def _format_multiple_pages_csv(self, pages: List[ScrapedPage]) -> str:
        """Format multiple pages as CSV."""
        all_rows = []
        
        for page in pages:
            products = page.custom_data.get("product_pricing", [])
            for product in products:
                product_name = product.get("product_name", "")
                for supplier in product.get("suppliers", []):
                    all_rows.append({
                        "product_name": product_name,
                        "supplier": supplier.get("supplier", ""),
                        "price_current": supplier.get("price_current", ""),
                        "price_original": supplier.get("price_original", ""),
                        "stock_status": supplier.get("stock_status", ""),
                        "url": supplier.get("url", ""),
                        "full_text": supplier.get("full_text", "")
                    })
        
        if all_rows:
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "product_name", "supplier", "price_current", "price_original", 
                "stock_status", "url", "full_text"
            ])
            writer.writeheader()
            writer.writerows(all_rows)
            return output.getvalue()
        
        return ""
    
    def get_file_extension(self) -> str:
        return "csv"
    
    def get_mime_type(self) -> str:
        return "text/csv"
