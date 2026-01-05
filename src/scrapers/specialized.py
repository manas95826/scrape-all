"""
Specialized scrapers for specific peptide websites.
"""

from typing import Dict, List, Optional, Callable
from bs4 import BeautifulSoup
import re
import json
import os

from .base import BaseScraper
from ..models import ScrapedPage


class PepPediaScraper(BaseScraper):
    """Specialized scraper for Pep-Pedia.org."""
    
    def scrape(self, url: str, **kwargs) -> Optional[ScrapedPage]:
        """Scrape Pep-Pedia with structured data extraction."""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract structured data
        structured_data = self._extract_peptide_info(soup)
        
        # Create ScrapedPage with custom data
        page_data = {
            'scraped_url': response.url,
            'scraped_at': self._get_timestamp(),
            'title_content_pairs': self._extract_title_content_pairs(soup),
            'peptide_info': structured_data
        }
        
        return ScrapedPage.from_dict(page_data)
    
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
                        
                        # Standardize keys
                        if 'weight' in key.lower():
                            molecular_info['weight'] = value
                        elif 'length' in key.lower():
                            molecular_info['length'] = value
                        elif 'type' in key.lower():
                            molecular_info['type'] = value
                        elif 'sequence' in key.lower():
                            molecular_info['amino_acid_sequence'] = value
                
                break
        
        return molecular_info if molecular_info else None
    
    def _extract_benefits(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract key benefits."""
        benefits = []
        
        # Look for benefits section
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if 'benefit' in heading.get_text().lower():
                # Get next sibling elements
                next_elem = heading.next_sibling
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 20:
                            benefits.append(text)
                    next_elem = next_elem.next_sibling
                break
        
        return benefits if benefits else None
    
    def _extract_mechanism(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract mechanism of action."""
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if 'mechanism' in heading.get_text().lower():
                next_elem = heading.next_sibling
                mechanism_text = ""
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 50:
                            mechanism_text += text + " "
                    next_elem = next_elem.next_sibling
                
                return mechanism_text.strip() if mechanism_text else None
        
        return None
    
    def _extract_research_indications(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extract research indications."""
        indications = []
        
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if 'indication' in heading.get_text().lower() or 'effective' in heading.get_text().lower():
                next_elem = heading.next_sibling
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 20:
                            indications.append({
                                'indication': heading.get_text(strip=True),
                                'description': text
                            })
                    next_elem = next_elem.next_sibling
                break
        
        return indications if indications else None
    
    def _extract_quality_indicators(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extract quality indicators."""
        indicators = []
        
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            if 'quality' in heading.get_text().lower():
                next_elem = heading.next_sibling
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 10:
                            indicators.append({
                                'indicator': heading.get_text(strip=True),
                                'description': text
                            })
                    next_elem = next_elem.next_sibling
                break
        
        return indicators if indicators else None
    
    def _extract_protocols(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract research protocols."""
        protocol_info = {}
        
        # Look for protocol sections
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            heading_text = heading.get_text().lower()
            if any(keyword in heading_text for keyword in ['protocol', 'dose', 'reconstitute']):
                next_elem = heading.next_sibling
                protocol_text = ""
                
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if hasattr(next_elem, 'get_text'):
                        text = next_elem.get_text(strip=True)
                        protocol_text += text + " "
                    next_elem = next_elem.next_sibling
                
                if 'dose' in heading_text:
                    protocol_info['dosing'] = protocol_text.strip()
                elif 'reconstitute' in heading_text:
                    protocol_info['reconstitution'] = protocol_text.strip()
                else:
                    protocol_info['general'] = protocol_text.strip()
        
        return protocol_info if protocol_info else None
    
    def _extract_title_content_pairs(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract title-content pairs with improved logic."""
        pairs = []
        
        # Get main title
        main_title = soup.title.string.strip() if soup.title else ''
        if main_title:
            pairs.append({'title': main_title, 'content': ''})
        
        # Find all headings and extract content properly
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            title = heading.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Extract content after this heading
            content_parts = []
            next_element = heading.next_sibling
            
            while next_element:
                # Stop at next heading
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                # Extract meaningful content
                content = self._extract_element_content(next_element)
                if content:
                    content_parts.append(content)
                
                next_element = next_element.next_sibling
            
            content = ' '.join(content_parts).strip()
            if content and len(content) > 10:
                pairs.append({'title': title, 'content': content})
        
        return pairs
    
    def _extract_element_content(self, element) -> Optional[str]:
        """Extract content from an element with better filtering."""
        if not element:
            return None
        
        if element.name == 'p':
            text = element.get_text(strip=True)
            return text if len(text) > 10 else None
        elif element.name in ['div', 'section', 'article']:
            text = element.get_text(strip=True)
            return text if len(text) > 20 else None
        elif hasattr(element, 'get_text'):
            text = element.get_text(strip=True)
            return text if len(text) > 10 else None
        
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


class PeptiPricesScraper(BaseScraper):
    """Specialized scraper for PeptiPrices.com."""
    
    # Product list with URL mappings
    PRODUCT_LIST = [
        "Retatrutide",
        "Tirzepatide", 
        "Tesamorelin",
        "KLOW",
        "GHK-Cu",
        "BPC-157/TB-500",
        "MOTS-c",
        "GLOW",
        "BPC-157",
        "Ipamorelin/CJC-1295 (No DAC)",
        "Semaglutide",
        "TB-500",
        "Bacteriostatic Water",
        "Ipamorelin",
        "Cagrilintide",
        "PT-141",
        "Epithalon",
        "KPV",
        "Selank",
        "NAD+",
        "Glutathione",
        "Semax",
        "AOD-9604",
        "DSIP",
        "Melanotan-2",
        "Sermorelin",
        "IGF-1 LR3",
        "5-Amino-1MQ",
        "CJC-1295 (No DAC)",
        "Melanotan-1",
        "SS-31",
        "Thymosin Alpha-1",
        "ARA-290",
        "Oxytocin",
        "SNAP-8",
        "Acetic Acid",
        "Tesamorelin/Ipamorelin",
        "CJC-1295 (with DAC)",
        "LL-37",
        "MGF",
        "VIP",
        "GHRP-2",
        "Mazdutide",
        "GHRP-6",
        "FOXO4-DRI",
        "Hexarelin",
        "Kisspeptin",
        "HCG",
        "Dihexa",
        "Selank/Semax",
        "Survodutide",
        "Tesofensine",
        "Gonadorelin",
        "Thymalin",
        "Humanin",
        "Retatrutide/Cagrilintide",
        "Semaglutide/Cagrilintide",
        "IGF-1 DES"
    ]
    
    def __init__(self, delay: float = 1.0):
        super().__init__(delay)
        self.dosage_data = self._load_dosage_data()
    
    def _load_dosage_data(self) -> Dict:
        """Load dosage data from JSON file."""
        try:
            # Get the project root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            dosage_file_path = os.path.join(project_root, 'dosage_data.json')
            
            with open(dosage_file_path, 'r') as f:
                data = json.load(f)
                return data.get('dosage_data', {})
        except Exception as e:
            print(f"Error loading dosage data: {e}")
            return {}
    
    def scrape(self, url: str, **kwargs) -> Optional[ScrapedPage]:
        """Scrape PeptiPrices with structured product data."""
        # Check if this is a bulk scrape request
        if kwargs.get('bulk_scrape'):
            progress_callback = kwargs.get('progress_callback')
            return self._bulk_scrape(progress_callback)
        
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product pricing data
        products = self._extract_product_data(soup)
        
        page_data = {
            'scraped_url': response.url,
            'scraped_at': self._get_timestamp(),
            'title_content_pairs': self._extract_title_content_pairs(soup),
            'product_pricing': products
        }
        
        return ScrapedPage.from_dict(page_data)
    
    def _bulk_scrape(self, progress_callback: Optional[Callable] = None) -> List[ScrapedPage]:
        """Scrape all products from the product list with dosage support."""
        all_results = []
        base_url = "https://peptiprices.com/products/"
        
        # Calculate total URLs (base products + dosage-specific URLs)
        total_urls = 0
        urls_to_scrape = []
        
        for product_name in self.PRODUCT_LIST:
            product_base_url = base_url + self._product_name_to_url(product_name)
            urls_to_scrape.append((product_name, product_base_url, None))
            total_urls += 1
            
            # Check if this product has dosage data
            if product_name in self.dosage_data:
                dosages = self.dosage_data[product_name]
                for dosage in dosages.keys():
                    dosage_url = f"{product_base_url}?dosage={dosage}"
                    urls_to_scrape.append((product_name, dosage_url, dosage))
                    total_urls += 1
        
        # Scrape all URLs
        for index, (product_name, url, dosage) in enumerate(urls_to_scrape):
            # Update progress
            if progress_callback:
                progress = index / total_urls
                if dosage:
                    progress_callback(progress, f"Scraping {product_name} - {dosage} ({index + 1}/{total_urls})")
                else:
                    progress_callback(progress, f"Scraping {product_name} ({index + 1}/{total_urls})")
            
            try:
                # Scrape the URL
                response = self.get_page(url)
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    products = self._extract_product_data(soup)
                    
                    page_data = {
                        'scraped_url': response.url,
                        'scraped_at': self._get_timestamp(),
                        'title_content_pairs': self._extract_title_content_pairs(soup),
                        'product_pricing': products,
                        'searched_product': product_name,
                        'dosage': dosage
                    }
                    
                    all_results.append(ScrapedPage.from_dict(page_data))
                
                # Add delay to avoid overwhelming the server
                import time
                time.sleep(1)  # 1 second delay between requests
                
            except Exception as e:
                # Log error but continue with other URLs
                print(f"Error scraping {product_name} - {dosage or 'base'}: {str(e)}")
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(1.0, f"Completed! Scraped {len(all_results)} pages.")
        
        return all_results
    
    def _product_name_to_url(self, product_name: str) -> str:
        """Convert product name to URL-friendly format."""
        import re
        
        # Handle special cases based on examples
        url = product_name.lower()
        
        # Replace spaces and special characters with hyphens
        url = re.sub(r'[^\w\-/]', '-', url)
        url = re.sub(r'-+', '-', url)  # Multiple hyphens to single
        url = url.strip('-')  # Remove leading/trailing hyphens
        
        # Handle specific conversions based on examples
        if url == 'igf-1-des':
            return 'igf-1-des'
        elif url == 'retatrutide-cagrilintide':
            return 'retatrutide_cagrilintide'  # Use underscore instead of hyphen
        elif url == 'cjc-1295-with-dac':
            return 'cjc-1295-with-dac'
        elif url == 'cjc-1295-no-dac':
            return 'cjc-1295-no-dac'
        elif url == 'ipamorelin-cjc-1295-no-dac':
            return 'ipamorelin-cjc-1295-no-dac'
        elif url == 'tesamorelin-ipamorelin':
            return 'tesamorelin-ipamorelin'
        elif url == 'bpc-157-tb-500':
            return 'bpc-157-tb-500'
        elif url == 'selank-semax':
            return 'selank-semax'
        elif url == 'semaglutide-cagrilintide':
            return 'semaglutide_cagrilintide'  # Use underscore instead of hyphen
        elif url == 'ara-290':
            return 'ara-290'
        elif url == '5-amino-1mq':
            return '5-amino-1mq'
        elif url == 'foxo4-dri':
            return 'foxo4-dri'
        elif url == 'ss-31':
            return 'ss-31'
        elif url == 'nad-':  # Handle NAD+ case
            return 'nad'
        elif url == 'ghk-cu':
            return 'ghk-cu'
        elif url == 'melanotan-1':
            return 'melanotan-1'
        elif url == 'melanotan-2':
            return 'melanotan-2'
        elif url == 'bacteriostatic-water':
            return 'bacteriostatic-water'
        elif url == 'acetic-acid':
            return 'acetic-acid'
        elif url == 'glutathione':
            return 'glutathione'
        elif url == 'snap-8':
            return 'snap-8'
        elif url == 'll-37':
            return 'll-37'
        elif url == 'mgf':
            return 'mgf'
        elif url == 'vip':
            return 'vip'
        elif url == 'ghrp-2':
            return 'ghrp-2'
        elif url == 'ghrp-6':
            return 'ghrp-6'
        elif url == 'hcg':
            return 'hcg'
        elif url == 'kpv':
            return 'kpv'
        elif url == 'dsip':
            return 'dsip'
        elif url == 'igf-1-lr3':
            return 'igf-1-lr3'
        
        # Default: just return the cleaned URL
        return url
    
    def _extract_product_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract product pricing information."""
        products = []
        
        # Look for product sections - try multiple approaches
        product_sections = soup.find_all(['h2', 'h3'])
        
        for section in product_sections:
            section_text = section.get_text(strip=True).lower()
            
            # Skip non-product sections
            if any(skip in section_text for skip in ['results', 'find the best', 'search', 'about']):
                continue
            
            # Get product name
            product_name = section.get_text(strip=True)
            
            # Find all product links after this section
            product_links = []
            
            # Look for links in the next few elements
            next_elem = section.next_sibling
            elements_checked = 0
            max_elements = 20  # Limit search to avoid going too far
            
            while next_elem and elements_checked < max_elements:
                elements_checked += 1
                
                # Stop at next major heading
                if next_elem.name in ['h1', 'h2', 'h3']:
                    break
                
                # Find all links in this element
                if next_elem.name == 'a' and next_elem.get('href'):
                    link_text = next_elem.get_text(strip=True)
                    href = next_elem.get('href')
                    
                    # Extract price and supplier info
                    price_info = self._extract_price_info(link_text)
                    if price_info:
                        price_info.update({
                            'supplier': self._extract_supplier_name(href),
                            'url': href,
                            'product_name': product_name
                        })
                        product_links.append(price_info)
                
                # Also look for links within this element
                elif hasattr(next_elem, 'find_all'):
                    links = next_elem.find_all('a', href=True)
                    for link in links:
                        link_text = link.get_text(strip=True)
                        href = link.get('href')
                        
                        price_info = self._extract_price_info(link_text)
                        if price_info:
                            price_info.update({
                                'supplier': self._extract_supplier_name(href),
                                'url': href,
                                'product_name': product_name
                            })
                            product_links.append(price_info)
                
                next_elem = next_elem.next_sibling
            
            if product_links:
                products.append({
                    'product_name': product_name,
                    'suppliers': product_links
                })
        
        # If no products found with headings, try alternative approach
        if not products:
            products = self._extract_products_fallback(soup)
        
        return products
    
    def _extract_products_fallback(self, soup: BeautifulSoup) -> List[Dict]:
        """Fallback method to extract products when heading-based approach fails."""
        products = []
        
        # Look for all links that might be products
        all_links = soup.find_all('a', href=True)
        
        # Group links by potential product names
        link_groups = {}
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip non-product links
            if any(skip in href.lower() for skip in ['mailto:', 'tel:', '#', 'javascript']):
                continue
            
            # Extract price info
            price_info = self._extract_price_info(text)
            if price_info:
                # Try to determine product name from context
                product_name = self._guess_product_name_from_context(link)
                
                if product_name not in link_groups:
                    link_groups[product_name] = []
                
                price_info.update({
                    'supplier': self._extract_supplier_name(href),
                    'url': href,
                    'product_name': product_name
                })
                link_groups[product_name].append(price_info)
        
        # Convert groups to product format
        for product_name, suppliers in link_groups.items():
            products.append({
                'product_name': product_name,
                'suppliers': suppliers
            })
        
        return products
    
    def _guess_product_name_from_context(self, link_element) -> str:
        """Try to guess product name from surrounding context."""
        # Look at previous headings
        prev_elements = []
        current = link_element.previous_sibling
        
        while current and len(prev_elements) < 5:
            if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading_text = current.get_text(strip=True)
                if heading_text and len(heading_text) < 50:
                    return heading_text
            prev_elements.append(current)
            current = current.previous_sibling
        
        return "Unknown Product"
    
    def _extract_price_info(self, link_text: str) -> Optional[Dict]:
        """Extract price information from link text."""
        # Pattern: "SupplierName In Stock PEPTI $42.75*$95.00"
        price_pattern = r'\$(\d+\.?\d*)\*?\$?(\d+\.?\d*)'
        match = re.search(price_pattern, link_text)
        
        if match:
            return {
                'price_current': float(match.group(1)),
                'price_original': float(match.group(2)) if match.group(2) else None,
                'stock_status': 'In Stock' if 'In Stock' in link_text else 'Out of Stock',
                'full_text': link_text
            }
        
        return None
    
    def _extract_supplier_name(self, url: str) -> str:
        """Extract supplier name from URL."""
        # Extract domain name
        import re
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Clean up domain name
        supplier = domain.replace('.com', '').replace('.shop', '').replace('.is', '')
        return supplier.title() if supplier else 'Unknown'
    
    def _extract_title_content_pairs(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract title-content pairs for pricing site."""
        pairs = []
        
        # Get main title
        main_title = soup.title.string.strip() if soup.title else ''
        if main_title:
            pairs.append({'title': main_title, 'content': ''})
        
        # Find all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            title = heading.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Extract content after heading
            content_parts = []
            next_element = heading.next_sibling
            
            while next_element:
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                content = self._extract_element_content(next_element)
                if content:
                    content_parts.append(content)
                
                next_element = next_element.next_sibling
            
            content = ' '.join(content_parts).strip()
            if content and len(content) > 10:
                pairs.append({'title': title, 'content': content})
        
        return pairs
    
    def _extract_element_content(self, element) -> Optional[str]:
        """Extract content from an element."""
        if not element:
            return None
        
        if element.name == 'p':
            text = element.get_text(strip=True)
            return text if len(text) > 10 else None
        elif element.name in ['div', 'section', 'article']:
            text = element.get_text(strip=True)
            return text if len(text) > 20 else None
        elif hasattr(element, 'get_text'):
            text = element.get_text(strip=True)
            return text if len(text) > 10 else None
        
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
