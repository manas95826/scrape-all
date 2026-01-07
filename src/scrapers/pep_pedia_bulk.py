"""
Specialized scrapers for specific peptide websites.
"""

from typing import Dict, List, Optional, Callable
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base import BaseScraper
from ..models import ScrapedPage


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
    
    def __init__(self, delay: float = 1.0):
        super().__init__(delay)
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver with headless Chrome."""
        if self.driver:
            return self.driver
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            # Fallback to requests-based scraping
            return None
    
    def __del__(self):
        """Cleanup WebDriver when scraper is destroyed."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
        super().__del__()
    
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
    
    def scrape_with_toggles(self, url: str, **kwargs) -> Optional[ScrapedPage]:
        """Scrape Pep-Pedia with JavaScript toggle handling for multiple administration routes."""
        driver = self._init_driver()
        if not driver:
            print("⚠️  WebDriver initialization failed, falling back to regular scraping")
            return self.scrape(url, **kwargs)
        
        try:
            print(f"🌐 Loading page: {url}")
            driver.get(url)
            
            # Wait for page to fully load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # Additional wait for dynamic content
            
            route_content = {}
            
            # Define all possible routes to check
            all_routes = ['oral', 'injectable', 'nasal', 'topical']
            
            # Step 1: Get initial content (detect what's currently active)
            print("📄 Extracting initial content...")
            initial_source = driver.page_source
            initial_soup = BeautifulSoup(initial_source, 'html.parser')
            initial_content = self._extract_title_content_pairs(initial_soup)
            
            # Step 2: Detect what type of content this is
            detected_route = self._detect_content_route(initial_content)
            print(f"🔍 Initial content appears to be: {detected_route.upper()}")
            
            if detected_route in all_routes:
                route_content[detected_route] = initial_content
                print(f"✅ Found {len(initial_content)} {detected_route} content sections")
            else:
                # Default to injectable if detection fails
                route_content['injectable'] = initial_content
                print(f"✅ Found {len(initial_content)} injectable content sections (default)")
            
            # Step 3: Try to toggle to all other available routes
            print("🔄 Checking for additional administration routes...")
            
            for target_route in all_routes:
                if target_route == detected_route:
                    continue  # Skip the route we already have
                
                print(f"🔄 Attempting to toggle to {target_route}...")
                toggle_success = self._toggle_to_route(driver, target_route)
                
                if toggle_success:
                    time.sleep(3)  # Wait for content to fully load
                    print(f"✅ Toggle successful, extracting {target_route} content...")
                    
                    alternate_source = driver.page_source
                    alternate_soup = BeautifulSoup(alternate_source, 'html.parser')
                    alternate_content = self._extract_title_content_pairs(alternate_soup)
                    
                    # Check if content actually changed
                    if self._content_is_different(initial_content, alternate_content):
                        route_content[target_route] = alternate_content
                        print(f"✅ Found {len(alternate_content)} {target_route} content sections")
                        initial_content = alternate_content  # Update for next comparison
                        detected_route = target_route
                    else:
                        print(f"⚠️  {target_route} toggle didn't change content - skipping")
                else:
                    print(f"⚠️  No {target_route} toggle found - skipping")
            
            # Step 4: If we only have one route, try intelligent separation
            if len(route_content) == 1:
                print("⚠️  Only one route found, attempting intelligent content separation...")
                existing_route = list(route_content.keys())[0]
                existing_content = route_content[existing_route]
                
                separated_content = self._intelligently_separate_content_multi_route(existing_content)
                if separated_content:
                    route_content.update(separated_content)
                    print(f"✅ Separated content into multiple routes")
                else:
                    print(f"🔄 Keeping single route: {existing_route}")
            
            # Ensure all routes exist (even if empty)
            for route in all_routes:
                if route not in route_content:
                    route_content[route] = []
            
            # Extract peptide info per route
            peptide_info = {}
            for route, content in route_content.items():
                if content:
                    route_soup = BeautifulSoup(
                        "".join([c["content"] for c in content]),
                        "html.parser"
                    )
                    peptide_info[route] = self._extract_peptide_info(route_soup)
                    print(f"🧪 Extracted peptide info for {route} route")
            
            # Create final page data (no AI categorization)
            page_data = {
                'scraped_url': url,
                'scraped_at': self._get_timestamp(),
                'content_by_route': route_content,
                'peptide_info': peptide_info,
                'categorized_content': {}  # Empty - will be filled during CSV processing
            }
            
            # Print summary
            print(f"📊 Summary:")
            for route in all_routes:
                count = len(route_content.get(route, []))
                if count > 0:
                    print(f"   {route.capitalize()}: {count} sections")
            
            return ScrapedPage.from_dict(page_data)
            
        except Exception as e:
            print(f"❌ Error during scraping with toggles: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to regular scraping
            print("🔄 Falling back to regular scraping...")
            return self.scrape(url, **kwargs)
    
    def _toggle_to_route(self, driver, target_route: str) -> bool:
        """Try to toggle to the specified route (oral/injectable/nasal/topical) with enhanced detection."""
        try:
            # Wait for page to be fully loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Multiple strategies to find toggle elements for all routes
            toggle_selectors = [
                # Strategy 1: Direct button text matching (case-insensitive)
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//input[contains(@value, '{target_route}')]",
                f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                
                # Strategy 2: Class-based detection
                f"//*[contains(@class, '{target_route}') and (self::button or self::a or self::div)]",
                f"//*[contains(@data-route, '{target_route}')]",
                f"//*[contains(@data-tab, '{target_route}')]",
                
                # Strategy 3: Common toggle patterns
                f"//button[contains(@class, 'tab') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//div[contains(@class, 'toggle') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//span[contains(@class, 'tab') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                
                # Strategy 4: Radio button groups
                f"//input[@type='radio' and @value='{target_route}']/..",
                f"//input[@type='radio' and contains(@name, 'route') and @value='{target_route}']/..",
                
                # Strategy 5: Select dropdown options
                f"//select[contains(@name, 'route')]//option[@value='{target_route}']",
                f"//select[contains(@id, 'route')]//option[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                
                # Strategy 6: Navigation elements
                f"//nav//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//div[contains(@class, 'nav')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                
                # Strategy 7: Generic clickable elements
                f"//*[contains(@class, 'btn') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//*[contains(@class, 'button') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                f"//*[contains(@role, 'tab') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_route}')]",
                
                # Strategy 8: Form elements
                f"//input[contains(@id, '{target_route}')]",
                f"//button[contains(@id, '{target_route}')]",
                f"//div[contains(@id, '{target_route}') and (self::button or self::a or @onclick)]"
            ]
            
            for selector in toggle_selectors:
                try:
                    elements = driver.find_elements("xpath", selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            # Scroll into view and click
                            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                            time.sleep(0.5)
                            
                            # Try different click methods
                            try:
                                elem.click()
                            except Exception:
                                try:
                                    driver.execute_script("arguments[0].click();", elem)
                                except Exception:
                                    continue
                            
                            print(f"✅ Successfully clicked {target_route} toggle using: {selector}")
                            return True
                except Exception:
                    continue
            
            print(f"⚠️  No {target_route} toggle found")
            return False
            
        except Exception as e:
            print(f"❌ Error toggling to {target_route}: {e}")
            return False
    
    def _extract_title_content_pairs(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract title-content pairs with comprehensive strategies."""
        pairs = []
        
        # Strategy 1: Extract by headings
        pairs.extend(self._extract_by_headings(soup))
        
        # Strategy 2: Extract by containers
        pairs.extend(self._extract_by_containers(soup))
        
        # Strategy 3: Extract all meaningful content
        pairs.extend(self._extract_all_content_sections(soup))
        
        # Deduplicate and return
        seen_titles = set()
        unique_pairs = []
        
        for pair in pairs:
            title = pair.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_pairs.append(pair)
        
        return unique_pairs
    
    def _extract_by_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract content using heading-based structure."""
        pairs = []
        
        # Find all heading tags
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            title = heading.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Get content until next heading
            content_elements = []
            next_element = heading.next_sibling
            
            while next_element:
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                if next_element.name and next_element.get_text(strip=True):
                    content_elements.append(next_element)
                next_element = next_element.next_sibling
            
            if content_elements:
                content = '\n'.join([elem.get_text(strip=True) for elem in content_elements])
                if content and len(content) > 20:
                    pairs.append({
                        'title': title,
                        'content': content
                    })
        
        return pairs
    
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
                # Scrape individual product page with toggle handling
                scraped_page = self.scrape_with_toggles(product_url)
                if scraped_page:
                    # Add the searched product name to the data
                    page_data = scraped_page.to_dict()
                    page_data['searched_product'] = product_name
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
        """Extract title-content pairs from HTML with comprehensive content capture."""
        pairs = []
        
        # Method 1: Extract all meaningful content sections
        all_content = self._extract_all_content_sections(soup)
        
        # Method 2: Extract by headings (traditional approach)
        heading_content = self._extract_by_headings(soup)
        
        # Method 3: Extract by common content containers
        container_content = self._extract_by_containers(soup)
        
        # Merge and deduplicate all content
        all_pairs = all_content + heading_content + container_content
        
        # Remove duplicates while preserving order
        seen_titles = set()
        unique_pairs = []
        for pair in all_pairs:
            title = pair.get('title', '').strip()
            content = pair.get('content', '').strip()
            
            if title and content and len(content) > 20:  # Filter out very short content
                title_key = title.lower().replace(' ', '').replace('\n', '').replace('\t', '')
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_pairs.append(pair)
        
        return unique_pairs
    
    def _extract_all_content_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all content sections from the page."""
        pairs = []
        
        # Extract all text content with structure
        for element in soup.find_all(['div', 'section', 'article', 'main']):
            # Skip if element is too small or contains mostly navigation
            text = element.get_text(strip=True)
            if len(text) < 50:
                continue
                
            # Skip navigation, footer, header elements
            classes = element.get('class', [])
            if any(cls in ['nav', 'navigation', 'menu', 'footer', 'header', 'sidebar'] for cls in classes):
                continue
            
            # Try to find a title within this element
            title = ""
            
            # Look for heading inside this element
            heading = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                title = heading.get_text(strip=True)
            else:
                # Look for strong/bold text that could be a title
                bold = element.find(['strong', 'b'])
                if bold:
                    bold_text = bold.get_text(strip=True)
                    if len(bold_text) < 200 and len(bold_text) > 5:  # Reasonable title length
                        title = bold_text
            
            # If no title found, use first 50 chars as title
            if not title:
                title = text[:50] + "..." if len(text) > 50 else text
            
            pairs.append({
                'title': title,
                'content': text
            })
        
        return pairs
    
    def _extract_by_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract content using heading-based structure."""
        pairs = []
        
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            title = heading.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Get all content until next heading of same or higher level
            content_parts = []
            current_level = int(heading.name[1])  # h1 -> 1, h2 -> 2, etc.
            current_element = heading.next_sibling
            
            while current_element:
                # Stop if we hit a heading of same or higher level
                if (current_element.name and 
                    current_element.name.startswith('h') and 
                    int(current_element.name[1]) <= current_level):
                    break
                
                # Extract text content
                if hasattr(current_element, 'get_text'):
                    text = current_element.get_text(strip=True)
                    if text and len(text) > 10:  # Filter out very short content
                        content_parts.append(text)
                
                current_element = current_element.next_sibling
            
            # Also look for nested content within the same section
            if content_parts:
                # Look for content in descendants of the heading's parent
                parent = heading.parent
                if parent:
                    # Find all elements after the heading within the same parent
                    after_heading = False
                    for child in parent.find_all():
                        if child == heading:
                            after_heading = True
                            continue
                        if after_heading and child.name and child.name.startswith('h'):
                            break
                        if after_heading and hasattr(child, 'get_text'):
                            text = child.get_text(strip=True)
                            if text and len(text) > 10 and text not in content_parts:
                                content_parts.append(text)
            
            content = ' '.join(content_parts).strip()
            if content:
                pairs.append({
                    'title': title,
                    'content': content
                })
        
        return pairs
    
    def _extract_by_containers(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract content from common container elements."""
        pairs = []
        
        # Common content container selectors
        container_selectors = [
            '.content', '.section', '.article-content', '.post-content',
            '[class*="content"]', '[class*="section"]', '[class*="article"]',
            'main', 'article', 'section',
            '.card', '.info-box', '.description', '.details'
        ]
        
        for selector in container_selectors:
            try:
                containers = soup.select(selector)
                for container in containers:
                    text = container.get_text(strip=True)
                    if len(text) < 100:  # Skip very short content
                        continue
                    
                    # Try to find a title
                    title = ""
                    
                    # Look for data-title attribute
                    if container.get('data-title'):
                        title = container.get('data-title')
                    
                    # Look for heading inside
                    if not title:
                        heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        if heading:
                            title = heading.get_text(strip=True)
                    
                    # Look for title in class
                    if not title:
                        classes = container.get('class', [])
                        title_classes = [cls for cls in classes if 'title' in cls.lower()]
                        if title_classes:
                            title = title_classes[0].replace('-', ' ').title()
                    
                    # Use first part of text as title
                    if not title:
                        words = text.split()[:10]
                        title = ' '.join(words) + "..."
                    
                    pairs.append({
                        'title': title,
                        'content': text
                    })
            except:
                continue
        
        return pairs
    
    def _detect_content_route(self, content: List[Dict[str, str]]) -> str:
        """Detect which administration route the content belongs to."""
        if not content:
            return 'injectable'  # Default
        
        # Combine all content text for analysis
        all_text = " ".join([c.get('content', '').lower() for c in content])
        all_titles = " ".join([c.get('title', '').lower() for c in content])
        
        # Route-specific indicators
        route_indicators = {
            'injectable': [
                'inject', 'injection', 'subcutaneous', 'subq', 'intramuscular',
                'reconstitute', 'bacteriostatic water', 'syringe', 'needle',
                'injection site', 'belly thigh arm', 'near injury',
                'rotate injection sites', 'sterile injection'
            ],
            'oral': [
                'oral', 'capsule', 'tablet', 'sublingual', 'buccal',
                'swallow', 'with food', 'without food', 'gastric absorption',
                'bioavailability oral', 'first pass metabolism', 'digestive'
            ],
            'nasal': [
                'nasal', 'nose', 'spray', 'intranasal', 'nasal spray',
                'nasal administration', 'nasal delivery', 'nasal mucosa',
                'nasal absorption', 'nose drops'
            ],
            'topical': [
                'topical', 'cream', 'gel', 'lotion', 'ointment', 'patch',
                'skin', 'dermal', 'transdermal', 'apply to skin',
                'topical application', 'skin absorption', 'surface'
            ]
        }
        
        # Score each route
        route_scores = {}
        for route, indicators in route_indicators.items():
            content_score = sum(1 for indicator in indicators if indicator in all_text)
            title_score = sum(1 for indicator in indicators if indicator in all_titles)
            route_scores[route] = content_score + (title_score * 2)
        
        print(f"  📊 Route scores: {route_scores}")
        
        # Return the route with highest score
        if route_scores:
            best_route = max(route_scores, key=route_scores.get)
            if route_scores[best_route] > 0:
                return best_route
        
        return 'injectable'  # Default if no indicators found
    
    def _intelligently_separate_content_multi_route(self, content: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Intelligently separate content into multiple administration routes."""
        if not content:
            return {'oral': [], 'injectable': [], 'nasal': [], 'topical': []}
        
        route_content = {
            'oral': [],
            'injectable': [],
            'nasal': [],
            'topical': []
        }
        
        for item in content:
            title = item.get('title', '').lower()
            content_text = item.get('content', '').lower()
            
            # Route-specific classification
            classified_route = self._classify_content_route(title, content_text)
            route_content[classified_route].append(item)
        
        return route_content
    
    def _classify_content_route(self, title: str, content: str) -> str:
        """Classify content into a specific administration route."""
        combined_text = f"{title} {content}"
        
        # Check each route in order of specificity
        if self._is_nasal_section(title, content):
            return 'nasal'
        elif self._is_topical_section(title, content):
            return 'topical'
        elif self._is_injectable_section(title, content):
            return 'injectable'
        elif self._is_oral_section(title, content):
            return 'oral'
        else:
            # Default to injectable for ambiguous content
            return 'injectable'
    
    def _is_nasal_section(self, title: str, content: str) -> bool:
        """Determine if a section is nasal-specific."""
        nasal_keywords = [
            'nasal', 'nose', 'spray', 'intranasal', 'nasal spray',
            'nasal administration', 'nasal delivery', 'nasal mucosa',
            'nasal absorption', 'nose drops'
        ]
        
        combined_text = f"{title} {content}"
        return any(keyword in combined_text for keyword in nasal_keywords)
    
    def _is_topical_section(self, title: str, content: str) -> bool:
        """Determine if a section is topical-specific."""
        topical_keywords = [
            'topical', 'cream', 'gel', 'lotion', 'ointment', 'patch',
            'skin', 'dermal', 'transdermal', 'apply to skin',
            'topical application', 'skin absorption', 'surface'
        ]
        
        combined_text = f"{title} {content}"
        return any(keyword in combined_text for keyword in topical_keywords)
    
    def _content_is_different(self, content1: List[Dict[str, str]], content2: List[Dict[str, str]]) -> bool:
        """Check if two content lists are actually different."""
        if len(content1) != len(content2):
            return True
        
        # Compare content hashes
        titles1 = set(c.get('title', '') for c in content1)
        titles2 = set(c.get('title', '') for c in content2)
        
        if titles1 != titles2:
            return True
        
        # Compare content text (more thorough)
        text1 = " ".join(sorted(c.get('content', '') for c in content1))
        text2 = " ".join(sorted(c.get('content', '') for c in content2))
        
        return text1 != text2
    
    def _intelligently_separate_content(self, content: List[Dict[str, str]], is_injectable: bool) -> Dict[str, List[Dict[str, str]]]:
        """Intelligently separate content into oral and injectable sections."""
        if not content:
            return {'oral': [], 'injectable': []}
        
        oral_content = []
        injectable_content = []
        
        for item in content:
            title = item.get('title', '').lower()
            content_text = item.get('content', '').lower()
            
            # Route-specific classification
            if self._is_injectable_section(title, content_text):
                injectable_content.append(item)
            elif self._is_oral_section(title, content_text):
                oral_content.append(item)
            else:
                # Ambiguous content - assign based on overall content type
                if is_injectable:
                    injectable_content.append(item)
                else:
                    oral_content.append(item)
        
        return {'oral': oral_content, 'injectable': injectable_content}
    
    def _is_injectable_section(self, title: str, content: str) -> bool:
        """Determine if a section is injectable-specific."""
        injectable_keywords = [
            'inject', 'injection', 'subcutaneous', 'subq', 'intramuscular',
            'reconstitute', 'bacteriostatic', 'syringe', 'needle',
            'injection site', 'rotate injection', 'sterile technique'
        ]
        
        combined_text = f"{title} {content}"
        return any(keyword in combined_text for keyword in injectable_keywords)
    
    def _is_oral_section(self, title: str, content: str) -> bool:
        """Determine if a section is oral-specific."""
        oral_keywords = [
            'oral', 'capsule', 'tablet', 'sublingual', 'buccal',
            'swallow', 'with food', 'without food', 'gastric absorption',
            'bioavailability oral', 'first pass', 'digestive'
        ]
        
        combined_text = f"{title} {content}"
        return any(keyword in combined_text for keyword in oral_keywords)
    
    def _filter_content_by_route(self, content: List[Dict[str, str]], is_injectable: bool) -> Dict[str, List[Dict[str, str]]]:
        """Filter content by removing route-specific inappropriate content."""
        if is_injectable:
            # Remove clearly oral-specific content if we have injectable content
            filtered = [item for item in content if not self._is_oral_section(item.get('title', ''), item.get('content', ''))]
            return {'oral': [], 'injectable': filtered}
        else:
            # Remove clearly injectable-specific content if we have oral content
            filtered = [item for item in content if not self._is_injectable_section(item.get('title', ''), item.get('content', ''))]
            return {'oral': filtered, 'injectable': []}
