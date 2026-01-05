"""
Specialized scrapers for specific peptide websites.
"""

from typing import Dict, List, Optional, Callable
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

from .base import BaseScraper
from ..models import ScrapedPage
from ..utils.content_categorizer import ContentCategorizer


class PepPediaBulkScraper(BaseScraper):
    """Specialized bulk scraper for Pep-Pedia.org."""
    
    # Product list with URL mappings
    PRODUCT_LIST = [
        "5-Amino-1MQ",
        "Adalank",
        "Adamax",
        "Adipotide (Prohibitin-TP01)",
        "AHK-Cu",
        "AOD-9604",
        "Ara 290",
        "BPC-157",
        "Cagrilintide",
        "Cartalax",
        "Cerebrolysin",
        "CJC-1295 (without DAC)",
        "CJC-1295 (with DAC)",
        "CJC/IPA Protocol",
        "Cyclic Glycine-Proline (cGP)",
        "Dihexa",
        "DSIP (Delta Sleep-Inducing Peptide)",
        "Epitalon",
        "Fat Blaster",
        "GHK-Cu",
        "Glow Protocol",
        "Glutathione",
        "HCG (Human Chorionic Gonadotropin)",
        "HGH (Somatropin)",
        "IGF-1 LR3",
        "Ipamorelin",
        "Kisspeptin",
        "KLOW Protocol",
        "KPV",
        "Lipo-C",
        "LL-37",
        "Mazdutide",
        "Melanotan I",
        "Melanotan II",
        "MK-677",
        "MOTS-c",
        "NA Semax Amidate",
        "NAD+",
        "Omberacetam (Noopept)",
        "Orforglipron",
        "Oxytocin",
        "PE-22-28 (Mini-Spadin)",
        "PEG-MGF",
        "Pinealon",
        "Prostamax",
        "PT-141",
        "Retatrutide",
        "Selank",
        "Semaglutide",
        "Semax",
        "Sermorelin",
        "SLU-PP-332",
        "SNAP-8",
        "SS-31 (Elamipretide)",
        "Survodutide",
        "TB-500",
        "Tesamorelin",
        "Tesofensine",
        "Thymosin Alpha 1",
        "Thymosin Beta-4",
        "Tirzepatide",
        "TRT (Testosterone Replacement Therapy)",
        "Wolverine Stack"
    ]
    
    def __init__(self, delay: float = 1.0, openai_api_key: Optional[str] = None):
        super().__init__(delay)
        self.categorizer = ContentCategorizer(openai_api_key) if openai_api_key else None
    
    def scrape(self, url: str, **kwargs) -> Optional[ScrapedPage]:
        """Scrape Pep-Pedia with structured product data."""
        # Check if this is a bulk scrape request
        if kwargs.get('bulk_scrape'):
            progress_callback = kwargs.get('progress_callback')
            return self._bulk_scrape(progress_callback)
        
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract content by route (oral/injectable)
        route_content = self._extract_by_route(soup)
        
        # Extract peptide info per route
        peptide_info = {}
        for route, content in route_content.items():
            route_soup = BeautifulSoup(
                "".join([c["content"] for c in content]),
                "html.parser"
            )
            peptide_info[route] = self._extract_peptide_info(route_soup)
        
        # Categorize content if OpenAI is available
        categorized_content = {}
        if self.categorizer and route_content:
            # Combine all route content into single content
            all_content = []
            for route, content in route_content.items():
                route_content_text = "\n\n".join([f"{pair['title']}\n{pair['content']}" for pair in content])
                all_content.append(f"=== {route.upper()} ===\n{route_content_text}")
            
            full_content = "\n\n".join(all_content)
            page_title = soup.find('h1')
            page_title_text = page_title.get_text(strip=True) if page_title else ""
            
            categorized_content = self.categorizer.categorize_content(
                title=page_title_text,
                content=full_content,
                url=response.url
            )
        
        page_data = {
            'scraped_url': response.url,
            'scraped_at': self._get_timestamp(),
            'content_by_route': {
                'oral': route_content.get('oral', []),
                'injectable': route_content.get('injectable', [])
            },
            'peptide_info': peptide_info,
            'categorized_content': categorized_content
        }
        
        return ScrapedPage.from_dict(page_data)
    
    def _bulk_scrape(self, progress_callback: Optional[Callable] = None) -> List[ScrapedPage]:
        """Scrape all products from the product list."""
        all_results = []
        base_url = "https://pep-pedia.org/peptides/"
        total_products = len(self.PRODUCT_LIST)
        
        for index, product_name in enumerate(self.PRODUCT_LIST):
            # Update progress
            if progress_callback:
                progress = index / total_products
                progress_callback(progress, f"Scraping {product_name} ({index + 1}/{total_products})")
            
            # Convert product name to URL format
            product_url = base_url + self._product_name_to_url(product_name)
            
            try:
                # Scrape individual product page
                response = self.get_page(product_url)
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract content by route (oral/injectable)
                    route_content = self._extract_by_route(soup)
                    
                    # Extract peptide info per route
                    peptide_info = {}
                    for route, content in route_content.items():
                        route_soup = BeautifulSoup(
                            "".join([c["content"] for c in content]),
                            "html.parser"
                        )
                        peptide_info[route] = self._extract_peptide_info(route_soup)
                    
                    # Categorize content if OpenAI is available
                    categorized_content = {}
                    if self.categorizer and route_content:
                        # Combine all route content into single content
                        all_content = []
                        for route, content in route_content.items():
                            route_content_text = "\n\n".join([f"{pair['title']}\n{pair['content']}" for pair in content])
                            all_content.append(f"=== {route.upper()} ===\n{route_content_text}")
                        
                        full_content = "\n\n".join(all_content)
                        page_title = soup.find('h1')
                        page_title_text = page_title.get_text(strip=True) if page_title else ""
                        
                        categorized_content = self.categorizer.categorize_content(
                            title=page_title_text,
                            content=full_content,
                            url=response.url
                        )
                    
                    page_data = {
                        'scraped_url': response.url,
                        'scraped_at': self._get_timestamp(),
                        'content_by_route': {
                            'oral': route_content.get('oral', []),
                            'injectable': route_content.get('injectable', [])
                        },
                        'peptide_info': peptide_info,
                        'searched_product': product_name,
                        'categorized_content': categorized_content
                    }
                    
                    all_results.append(ScrapedPage.from_dict(page_data))
                
                # Add delay to avoid overwhelming the server
                import time
                time.sleep(1)  # 1 second delay between requests
                
            except Exception as e:
                # Log error but continue with other products
                print(f"Error scraping {product_name}: {str(e)}")
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(1.0, f"Completed! Scraped {len(all_results)} products.")
        
        return all_results
    
    def _product_name_to_url(self, product_name: str) -> str:
        """Convert product name to URL-friendly format."""
        import re
        
        # Handle special cases based on examples
        url = product_name.lower()
        
        # Handle HCG special case - remove bracket content
        if "hcg" in url.lower():
            url = "hcg"
        # Handle other special cases with brackets
        elif "(" in url and ")" in url:
            # Remove content in brackets for URL
            url = re.sub(r'\s*\([^)]*\)', '', url)
        
        # Replace spaces and special characters with hyphens
        url = re.sub(r'[^\w\-]', '-', url)
        url = re.sub(r'-+', '-', url)  # Multiple hyphens to single
        url = url.strip('-')  # Remove leading/trailing hyphens
        
        # Handle specific conversions
        special_cases = {
            "5-amino-1mq": "5-amino-1mq",
            "adalank": "adalank",
            "adamax": "adamax",
            "adipotide-prohibitin-tp01": "adipotide",
            "ahk-cu": "ahk-cu",
            "aod-9604": "aod-9604",
            "ara-290": "ara-290",
            "bpc-157": "bpc-157",
            "cagrilintide": "cagrilintide",
            "cartalax": "cartalax",
            "cerebrolysin": "cerebrolysin",
            "cjc-1295-without-dac": "cjc-1295-without-dac",
            "cjc-1295-with-dac": "cjc-1295-with-dac",
            "cjc-ipa-protocol": "cjc-ipa-protocol",
            "cyclic-glycine-proline-cgp": "cyclic-glycine-proline-cgp",
            "dihexa": "dihexa",
            "dsip-delta-sleep-inducing-peptide": "dsip",
            "epitalon": "epitalon",
            "fat-blaster": "fat-blaster",
            "ghk-cu": "ghk-cu",
            "glow-protocol": "glow-protocol",
            "glutathione": "glutathione",
            "hgh-somatropin": "hgh",
            "igf-1-lr3": "igf-1-lr3",
            "ipamorelin": "ipamorelin",
            "kisspeptin": "kisspeptin",
            "klow-protocol": "klow-protocol",
            "kpv": "kpv",
            "lipo-c": "lipo-c",
            "ll-37": "ll-37",
            "mazdutide": "mazdutide",
            "melanotan-i": "melanotan-i",
            "melanotan-ii": "melanotan-ii",
            "mk-677": "mk-677",
            "mots-c": "mots-c",
            "na-semax-amidate": "na-semax-amidate",
            "nad": "nad",
            "omberacetam-noopept": "omberacetam-noopept",
            "orforglipron": "orforglipron",
            "oxytocin": "oxytocin",
            "pe-22-28-mini-spadin": "pe-22-28-mini-spadin",
            "peg-mgf": "peg-mgf",
            "pinealon": "pinealon",
            "prostamax": "prostamax",
            "pt-141": "pt-141",
            "retatrutide": "retatrutide",
            "selank": "selank",
            "semaglutide": "semaglutide",
            "semax": "semax",
        }
        
        # Check if we have a special case
        for key, value in special_cases.items():
            if url == key or url.replace('-', '') == key.replace('-', ''):
                return value
        
        # Default: return the cleaned URL
        return url
    
    def _extract_peptide_info(self, soup: BeautifulSoup) -> Dict:
        """Extract structured peptide information."""
        info = {}
        
        # Extract peptide name from URL or title
        peptide_name = self._extract_peptide_name(soup)
        if peptide_name:
            info['name'] = peptide_name
        
        # Extract molecular information
        molecular_info = self._extract_molecular_info(soup)
        if molecular_info:
            info['molecular_info'] = molecular_info
        
        # Extract benefits
        benefits = self._extract_benefits(soup)
        if benefits:
            info['benefits'] = benefits
        
        # Extract mechanism of action
        mechanism = self._extract_mechanism(soup)
        if mechanism:
            info['mechanism_of_action'] = mechanism
        
        # Extract research indications
        indications = self._extract_research_indications(soup)
        if indications:
            info['research_indications'] = indications
        
        # Extract quality indicators
        quality = self._extract_quality_indicators(soup)
        if quality:
            info['quality_indicators'] = quality
        
        # Extract research protocols
        protocols = self._extract_protocols(soup)
        if protocols:
            info['protocols'] = protocols
        
        return info
    
    def _extract_peptide_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract peptide name from page."""
        # Try to get from h1 title
        h1 = soup.find('h1')
        if h1:
            text = h1.get_text(strip=True)
            # Remove common suffixes
            for suffix in [' - Research, Dosing & Protocols | Pep-Pedia', ' | Pep-Pedia']:
                text = text.replace(suffix, '')
            return text.strip()
        return None
    
    def _extract_molecular_info(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract molecular information."""
        molecular_info = {}
        
        # Look for molecular information section
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if 'molecular' in heading.get_text().lower():
                # Get next sibling elements
                next_elem = heading.next_sibling
                info_text = ""
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        info_text += next_elem.get_text() + " "
                    next_elem = next_elem.next_sibling
                
                # Parse molecular data
                lines = info_text.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        molecular_info[key] = value
        
        return molecular_info if molecular_info else None
    
    def _extract_benefits(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract benefits information."""
        benefits = []
        
        # Look for benefits section
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if any(keyword in heading.get_text().lower() for keyword in ['benefit', 'advantage', 'effect']):
                # Get list items or paragraphs
                next_elem = heading.next_sibling
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if next_elem.name == 'ul' or next_elem.name == 'ol':
                        items = next_elem.find_all('li')
                        for item in items:
                            benefit_text = item.get_text(strip=True)
                            if benefit_text:
                                benefits.append(benefit_text)
                    elif hasattr(next_elem, 'get_text') and len(next_elem.get_text(strip=True)) > 10:
                        benefits.append(next_elem.get_text(strip=True))
                    next_elem = next_elem.next_sibling
        
        return benefits if benefits else None
    
    def _extract_mechanism(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract mechanism of action."""
        # Look for mechanism section
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if any(keyword in heading.get_text().lower() for keyword in ['mechanism', 'action', 'how it works']):
                # Get next sibling elements
                next_elem = heading.next_sibling
                mechanism_text = ""
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        mechanism_text += next_elem.get_text() + " "
                    next_elem = next_elem.next_sibling
                
                return mechanism_text.strip() if mechanism_text.strip() else None
        
        return None
    
    def _extract_research_indications(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract research indications."""
        indications = []
        
        # Look for research/indications section
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if any(keyword in heading.get_text().lower() for keyword in ['research', 'indication', 'study', 'clinical']):
                # Get list items or paragraphs
                next_elem = heading.next_sibling
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if next_elem.name == 'ul' or next_elem.name == 'ol':
                        items = next_elem.find_all('li')
                        for item in items:
                            indication_text = item.get_text(strip=True)
                            if indication_text:
                                indications.append(indication_text)
                    elif hasattr(next_elem, 'get_text') and len(next_elem.get_text(strip=True)) > 10:
                        indications.append(next_elem.get_text(strip=True))
                    next_elem = next_elem.next_sibling
        
        return indications if indications else None
    
    def _extract_quality_indicators(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract quality indicators."""
        quality = {}
        
        # Look for quality/purity information
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if any(keyword in heading.get_text().lower() for keyword in ['quality', 'purity', 'grade']):
                # Get next sibling elements
                next_elem = heading.next_sibling
                info_text = ""
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        info_text += next_elem.get_text() + " "
                    next_elem = next_elem.next_sibling
                
                # Parse quality data
                lines = info_text.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        quality[key] = value
        
        return quality if quality else None
    
    def _extract_protocols(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extract research protocols."""
        protocols = []
        
        # Look for protocol/dosing section
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if any(keyword in heading.get_text().lower() for keyword in ['protocol', 'dosing', 'dosage', 'administration']):
                # Get next sibling elements
                next_elem = heading.next_sibling
                protocol_info = {}
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        if len(text) > 10:
                            if 'description' not in protocol_info:
                                protocol_info['description'] = text
                            else:
                                protocol_info['details'] = text
                    next_elem = next_elem.next_sibling
                
                if protocol_info:
                    protocols.append(protocol_info)
        
        return protocols if protocols else None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def _extract_by_route(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """Extract content by route (oral/injectable) from toggle-based layouts."""
        routes = {}
        
        for route in ["oral", "injectable"]:
            # Try different selector patterns for route containers
            container = soup.select_one(
                f'[data-tab="{route}"], [data-route="{route}"], .{route}-content, #{route}-content, .{route}.tab-panel'
            )
            
            if not container:
                # Try to find by class name containing the route
                container = soup.find(lambda tag: tag.has_attr('class') and 
                                     any(route in str(cls).lower() for cls in tag.get('class', [])) and
                                     any('tab' in str(cls).lower() or 'panel' in str(cls).lower() or 'content' in str(cls).lower() 
                                         for cls in tag.get('class', [])))
            
            if container:
                routes[route] = self._extract_title_content_pairs(container)
        
        # If no route-specific containers found, fall back to extracting all content
        if not routes:
            # Try to identify route sections by looking for route indicators in text
            all_content = self._extract_title_content_pairs(soup)
            oral_content = []
            injectable_content = []
            current_route = None
            
            for pair in all_content:
                title_lower = pair['title'].lower()
                content_lower = pair['content'].lower()
                
                # Check if this title indicates a route section
                if any(keyword in title_lower for keyword in ['oral', 'injectable', 'injection']):
                    if 'oral' in title_lower:
                        current_route = 'oral'
                    elif 'injectable' in title_lower or 'injection' in title_lower:
                        current_route = 'injectable'
                
                # Assign content to appropriate route
                if current_route == 'oral':
                    oral_content.append(pair)
                elif current_route == 'injectable':
                    injectable_content.append(pair)
                else:
                    # If no route identified, check content for route indicators
                    if any(keyword in content_lower for keyword in ['oral', 'injectable', 'injection']):
                        if 'oral' in content_lower and 'injectable' not in content_lower:
                            oral_content.append(pair)
                        elif 'injectable' in content_lower or 'injection' in content_lower:
                            injectable_content.append(pair)
                        else:
                            # Content mentions both routes, add to both
                            oral_content.append(pair)
                            injectable_content.append(pair)
                    else:
                        # Default to oral if no route indicators
                        oral_content.append(pair)
            
            if oral_content:
                routes['oral'] = oral_content
            if injectable_content:
                routes['injectable'] = injectable_content
        
        return routes
    
    def _extract_title_content_pairs(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract title-content pairs from HTML."""
        pairs = []
        
        # Look for headings and their following content
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            title = heading.get_text(strip=True)
            if not title:
                continue
                
            # Get content after this heading
            content_elements = []
            next_elem = heading.next_sibling
            
            # Collect content until next heading
            while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if hasattr(next_elem, 'get_text') and next_elem.get_text(strip=True):
                    content_elements.append(next_elem.get_text(strip=True))
                next_elem = next_elem.next_sibling
            
            # Join content
            content = ' '.join(content_elements).strip()
            if content:
                pairs.append({
                    'title': title,
                    'content': content
                })
        
        return pairs
