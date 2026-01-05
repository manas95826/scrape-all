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
        elif 'categorized_content' in page.custom_data:
            return self._format_pep_pedia_csv(page)
        
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
        has_categorized_content = any('categorized_content' in page.custom_data for page in pages)
        
        if has_product_pricing:
            return self._format_pepti_prices_csv_multiple(pages)
        elif has_backlinks:
            return self._format_backlinks_csv_multiple(pages)
        elif has_categorized_content:
            return self._format_pep_pedia_csv_multiple(pages)
        
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
                compound_name = page.url.split("/products/")[-1].split("?")[0].replace("-", " ").replace("_", " ").title()
            else:
                compound_name = "Unknown"
        
        # Extract dosage information
        dosage = page.custom_data.get("dosage", "")
        
        for product in products:
            for supplier in product.get("suppliers", []):
                rows.append({
                    "compound_name": compound_name,
                    "dosage": dosage if dosage else "Standard",
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
                    compound_name = page.url.split("/products/")[-1].split("?")[0].replace("-", " ").replace("_", " ").title()
                else:
                    compound_name = "Unknown"
            
            # Extract dosage information
            dosage = page.custom_data.get("dosage", "")
            
            products = page.custom_data.get("product_pricing", [])
            for product in products:
                for supplier in product.get("suppliers", []):
                    all_rows.append({
                        "compound_name": compound_name,
                        "dosage": dosage if dosage else "Standard",
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
            # Sort by compound name, then dosage, then supplier for better organization
            df = df.sort_values(['compound_name', 'dosage', 'supplier'])
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
    
    def _format_pep_pedia_csv(self, page: ScrapedPage) -> str:
        """Format Pep-Pedia categorized content as CSV with route separation."""
        categorized_content = page.custom_data.get("categorized_content", {})
        peptide_name = page.custom_data.get("searched_product", "")
        content_by_route = page.custom_data.get("content_by_route", {})
        peptide_info = page.custom_data.get("peptide_info", {})
        
        rows = []
        
        # Get all available routes
        routes = content_by_route.keys() if content_by_route else ['oral']  # Default to oral if no route data
        
        for route in routes:
            # Create a row for each route
            row = {
                'peptide_name': peptide_name,
                'route': route,
                'source_url': page.url,
                'scraped_at': page.scraped_at
            }
            
            # Add all categorized fields
            categorized_fields = [
                "Overview", "Key Benefits", "Mechanism of Action", "Molecular Information",
                "Research Indications", "Research Protocols", "Peptide Interactions",
                "How to Reconstitute", "Quality Indicators", "What to Expect",
                "Side Effects & Safety", "References", "Quick Start Guide",
                "Storage", "Cycle Length", "Break Between"
            ]
            
            for field in categorized_fields:
                row[field] = categorized_content.get(field, "")
            
            # Add route-specific peptide info if available
            if peptide_info and route in peptide_info:
                route_peptide_info = peptide_info[route]
                
                # Add specific peptide info fields
                if 'name' in route_peptide_info:
                    row['peptide_display_name'] = route_peptide_info['name']
                
                # Add molecular info
                if 'molecular_info' in route_peptide_info:
                    mol_info = route_peptide_info['molecular_info']
                    for key, value in mol_info.items():
                        row[f'molecular_{key.lower().replace(" ", "_")}'] = value
                
                # Add benefits
                if 'benefits' in route_peptide_info:
                    benefits = route_peptide_info['benefits']
                    if isinstance(benefits, list):
                        row['benefits'] = '; '.join(benefits)
                    else:
                        row['benefits'] = str(benefits)
                
                # Add mechanism
                if 'mechanism_of_action' in route_peptide_info:
                    row['route_mechanism'] = route_peptide_info['mechanism_of_action']
                
                # Add research indications
                if 'research_indications' in route_peptide_info:
                    indications = route_peptide_info['research_indications']
                    if isinstance(indications, list):
                        row['route_indications'] = '; '.join(indications)
                    else:
                        row['route_indications'] = str(indications)
                
                # Add protocols
                if 'protocols' in route_peptide_info:
                    protocols = route_peptide_info['protocols']
                    if isinstance(protocols, list):
                        protocol_texts = []
                        for protocol in protocols:
                            if isinstance(protocol, dict):
                                protocol_text = protocol.get('description', '')
                                if 'details' in protocol:
                                    protocol_text += f" - {protocol['details']}"
                                protocol_texts.append(protocol_text)
                            else:
                                protocol_texts.append(str(protocol))
                        row['route_protocols'] = '; '.join(protocol_texts)
                    else:
                        row['route_protocols'] = str(protocols)
            
            # Add content sections for this route
            if content_by_route and route in content_by_route:
                route_content = content_by_route[route]
                if route_content:
                    # Combine all content for this route
                    all_titles = []
                    all_contents = []
                    for content_pair in route_content:
                        if isinstance(content_pair, dict):
                            all_titles.append(content_pair.get('title', ''))
                            all_contents.append(content_pair.get('content', ''))
                    
                    row['route_content_titles'] = ' | '.join(all_titles)
                    row['route_content'] = ' \n\n '.join(all_contents)
            
            rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        return ""
    
    def _format_pep_pedia_csv_multiple(self, pages: List[ScrapedPage]) -> str:
        """Format multiple Pep-Pedia pages with categorized content as CSV with route separation."""
        all_rows = []
        
        for page in pages:
            categorized_content = page.custom_data.get("categorized_content", {})
            peptide_name = page.custom_data.get("searched_product", "")
            content_by_route = page.custom_data.get("content_by_route", {})
            peptide_info = page.custom_data.get("peptide_info", {})
            
            # Get all available routes
            routes = content_by_route.keys() if content_by_route else ['oral']  # Default to oral if no route data
            
            for route in routes:
                # Create a row for each route
                row = {
                    'peptide_name': peptide_name,
                    'route': route,
                    'source_url': page.url,
                    'scraped_at': page.scraped_at
                }
                
                # Add all categorized fields
                categorized_fields = [
                    "Overview", "Key Benefits", "Mechanism of Action", "Molecular Information",
                    "Research Indications", "Research Protocols", "Peptide Interactions",
                    "How to Reconstitute", "Quality Indicators", "What to Expect",
                    "Side Effects & Safety", "References", "Quick Start Guide",
                    "Storage", "Cycle Length", "Break Between"
                ]
                
                for field in categorized_fields:
                    row[field] = categorized_content.get(field, "")
                
                # Add route-specific peptide info if available
                if peptide_info and route in peptide_info:
                    route_peptide_info = peptide_info[route]
                    
                    # Add specific peptide info fields
                    if 'name' in route_peptide_info:
                        row['peptide_display_name'] = route_peptide_info['name']
                    
                    # Add molecular info
                    if 'molecular_info' in route_peptide_info:
                        mol_info = route_peptide_info['molecular_info']
                        for key, value in mol_info.items():
                            row[f'molecular_{key.lower().replace(" ", "_")}'] = value
                    
                    # Add benefits
                    if 'benefits' in route_peptide_info:
                        benefits = route_peptide_info['benefits']
                        if isinstance(benefits, list):
                            row['benefits'] = '; '.join(benefits)
                        else:
                            row['benefits'] = str(benefits)
                    
                    # Add mechanism
                    if 'mechanism_of_action' in route_peptide_info:
                        row['route_mechanism'] = route_peptide_info['mechanism_of_action']
                    
                    # Add research indications
                    if 'research_indications' in route_peptide_info:
                        indications = route_peptide_info['research_indications']
                        if isinstance(indications, list):
                            row['route_indications'] = '; '.join(indications)
                        else:
                            row['route_indications'] = str(indications)
                    
                    # Add protocols
                    if 'protocols' in route_peptide_info:
                        protocols = route_peptide_info['protocols']
                        if isinstance(protocols, list):
                            protocol_texts = []
                            for protocol in protocols:
                                if isinstance(protocol, dict):
                                    protocol_text = protocol.get('description', '')
                                    if 'details' in protocol:
                                        protocol_text += f" - {protocol['details']}"
                                    protocol_texts.append(protocol_text)
                                else:
                                    protocol_texts.append(str(protocol))
                            row['route_protocols'] = '; '.join(protocol_texts)
                        else:
                            row['route_protocols'] = str(protocols)
                
                # Add content sections for this route
                if content_by_route and route in content_by_route:
                    route_content = content_by_route[route]
                    if route_content:
                        # Combine all content for this route
                        all_titles = []
                        all_contents = []
                        for content_pair in route_content:
                            if isinstance(content_pair, dict):
                                all_titles.append(content_pair.get('title', ''))
                                all_contents.append(content_pair.get('content', ''))
                        
                        row['route_content_titles'] = ' | '.join(all_titles)
                        row['route_content'] = ' \n\n '.join(all_contents)
                
                all_rows.append(row)
        
        if all_rows:
            df = pd.DataFrame(all_rows)
            # Sort by peptide name, then route for better organization
            df = df.sort_values(['peptide_name', 'route'])
            return df.to_csv(index=False)
        return ""
    
    def get_file_extension(self) -> str:
        """Return CSV file extension."""
        return "csv"
    
    def get_mime_type(self) -> str:
        """Return CSV MIME type."""
        return "text/csv"
