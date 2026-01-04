import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
import pandas as pd
from io import StringIO, BytesIO
import base64
import re
from collections import deque

class WebScraper:
    def __init__(self, delay=1):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_page(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            return None
    
    def parse_content(self, response, selectors=None):
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {}
        
        if selectors:
            for key, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        data[key] = elements[0].get_text(strip=True)
                    else:
                        data[key] = [elem.get_text(strip=True) for elem in elements]
        else:
            # Extract title-content pairs in order
            title_content_pairs = []
            
            # Get main title as first title
            main_title = soup.title.string.strip() if soup.title else ''
            if main_title:
                title_content_pairs.append({'title': main_title, 'content': ''})
            
            # Find all headings and their following content
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            for i, heading in enumerate(headings):
                title = heading.get_text(strip=True)
                if not title:
                    continue
                
                # Get content after this heading until next heading
                content_parts = []
                next_element = heading.next_sibling
                
                while next_element:
                    # Stop if we hit another heading
                    if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    
                    # Extract text from this element
                    if next_element.name == 'p':
                        text = next_element.get_text(strip=True)
                        if text and len(text) > 10:
                            content_parts.append(text)
                    elif next_element.name in ['div', 'section', 'article']:
                        text = next_element.get_text(strip=True)
                        if text and len(text) > 20:
                            content_parts.append(text)
                    elif hasattr(next_element, 'get_text'):
                        text = next_element.get_text(strip=True)
                        if text and len(text) > 10:
                            content_parts.append(text)
                    
                    next_element = next_element.next_sibling
                
                content = ' '.join(content_parts)
                title_content_pairs.append({'title': title, 'content': content})
            
            # If no headings found, get all paragraphs as content with main title
            if not headings and main_title:
                paragraphs = soup.find_all('p')
                content_parts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:
                        content_parts.append(text)
                
                if content_parts:
                    title_content_pairs[0]['content'] = ' '.join(content_parts)
            
            data = {
                'title_content_pairs': title_content_pairs
            }
        
        return data
    
    def scrape_single_page(self, url, selectors=None):
        response = self.get_page(url)
        if response:
            data = self.parse_content(response, selectors)
            data['scraped_url'] = url
            data['scraped_at'] = datetime.now().isoformat()
            return data
        return None
    
    def extract_links(self, response, base_url):
        """Extract all links from a page and normalize them"""
        if not response:
            return set()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            full_url = urljoin(base_url, href)
            
            # Parse and normalize URL
            parsed = urlparse(full_url)
            
            # Only include HTTP/HTTPS links
            if parsed.scheme not in ['http', 'https']:
                continue
            
            # Remove fragment and query parameters for consistency
            clean_url = parsed._replace(fragment='', params='', query='').geturl()
            
            links.add(clean_url)
        
        return links
    
    def is_internal_link(self, url, base_domain):
        """Check if URL belongs to the same domain"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            return parsed_url.netloc == parsed_base.netloc
        except:
            return False
    
    def should_skip_url(self, url, exclude_patterns=None):
        """Check if URL should be skipped based on patterns"""
        if not exclude_patterns:
            return False
        
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def discover_website_pages(self, start_url, max_pages=50, max_depth=3, stay_on_domain=True, exclude_patterns=None, progress_callback=None):
        """Discover all pages on a website using breadth-first search"""
        if exclude_patterns is None:
            exclude_patterns = [r'\.(pdf|jpg|jpeg|png|gif|zip|tar|gz|exe)$', r'#', r'\?']
        
        base_domain = urlparse(start_url).netloc
        visited = set()
        queue = deque([(start_url, 0)])  # (url, depth)
        discovered_urls = set()
        total_processed = 0
        
        while queue and len(discovered_urls) < max_pages:
            current_url, depth = queue.popleft()
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            
            # Skip URLs based on patterns
            if self.should_skip_url(current_url, exclude_patterns):
                continue
            
            if progress_callback:
                progress = min(len(discovered_urls) / max_pages, 0.95)  # Cap at 95% during discovery
                progress_callback(progress, f"Discovering: {current_url} (depth: {depth}, found: {len(discovered_urls)} pages)")
            
            response = self.get_page(current_url)
            if response:
                discovered_urls.add(current_url)
                total_processed += 1
                
                # Extract links and add to queue
                links = self.extract_links(response, current_url)
                for link in links:
                    if link not in visited:
                        # Stay on same domain if required
                        if stay_on_domain and not self.is_internal_link(link, start_url):
                            continue
                        
                        queue.append((link, depth + 1))
            
            # Add delay to be respectful
            time.sleep(self.delay)
        
        return list(discovered_urls)
    
    def parse_sitemap(self, sitemap_url, progress_callback=None):
        """Parse XML sitemap and extract all URLs"""
        try:
            if progress_callback:
                progress_callback(0.1, f"Fetching sitemap: {sitemap_url}")
            
            response = self.get_page(sitemap_url)
            if not response:
                return []
            
            if progress_callback:
                progress_callback(0.3, "Parsing sitemap XML...")
            
            soup = BeautifulSoup(response.content, 'xml')
            urls = []
            
            # Find all URL elements
            url_elements = soup.find_all('url')
            
            if progress_callback:
                progress_callback(0.5, f"Found {len(url_elements)} URLs in sitemap")
            
            for url_elem in url_elements:
                loc_elem = url_elem.find('loc')
                if loc_elem and loc_elem.text:
                    urls.append(loc_elem.text.strip())
            
            # Also check for sitemap index (nested sitemaps)
            sitemap_elements = soup.find_all('sitemap')
            if sitemap_elements:
                if progress_callback:
                    progress_callback(0.7, f"Found {len(sitemap_elements)} nested sitemaps, processing...")
                
                for sitemap_elem in sitemap_elements:
                    loc_elem = sitemap_elem.find('loc')
                    if loc_elem and loc_elem.text:
                        nested_urls = self.parse_sitemap(loc_elem.text.strip(), progress_callback)
                        urls.extend(nested_urls)
            
            if progress_callback:
                progress_callback(1.0, f"Successfully parsed {len(urls)} URLs from sitemap")
            
            return list(set(urls))  # Remove duplicates
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error parsing sitemap: {str(e)}")
            return []
    
    def discover_sitemap_urls(self, base_url, progress_callback=None):
        """Try to discover and parse sitemap URLs for a website"""
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc
        
        # Common sitemap locations
        sitemap_urls = [
            f"https://{domain}/sitemap.xml",
            f"https://{domain}/sitemap_index.xml",
            f"https://{domain}/sitemaps.xml",
            f"https://www.{domain}/sitemap.xml",
            f"https://www.{domain}/sitemap_index.xml",
            f"https://{domain}/wp-sitemap.xml",  # WordPress
        ]
        
        for sitemap_url in sitemap_urls:
            if progress_callback:
                progress_callback(0.1, f"Trying sitemap: {sitemap_url}")
            
            urls = self.parse_sitemap(sitemap_url, progress_callback)
            if urls:
                return urls
        
        if progress_callback:
            progress_callback(0, "No sitemap found, falling back to crawling")
        
        return []

    def scrape_entire_website(self, start_url, max_pages=50, max_depth=3, stay_on_domain=True, selectors=None, exclude_patterns=None, progress_callback=None, use_sitemap=True):
        """Scrape entire website starting from a URL"""
        urls_to_scrape = []
        
        # Try sitemap first if enabled
        if use_sitemap:
            if progress_callback:
                progress_callback(0.05, "Attempting to discover sitemap...")
            
            sitemap_urls = self.discover_sitemap_urls(start_url, progress_callback)
            if sitemap_urls:
                urls_to_scrape = sitemap_urls[:max_pages]  # Limit to max_pages
                if progress_callback:
                    progress_callback(0.5, f"Found {len(urls_to_scrape)} URLs from sitemap")
        
        # Fallback to crawling if no sitemap found
        if not urls_to_scrape:
            if progress_callback:
                progress_callback(0.1, "Discovering pages via crawling...")
            
            urls_to_scrape = self.discover_website_pages(
                start_url, max_pages, max_depth, stay_on_domain, exclude_patterns, progress_callback
            )
        
        if progress_callback:
            progress_callback(0.5, f"Found {len(urls_to_scrape)} pages. Starting scraping...")
        
        # Scrape all discovered pages
        results = []
        for i, url in enumerate(urls_to_scrape, 1):
            if progress_callback:
                progress = 0.5 + (i / len(urls_to_scrape)) * 0.5
                progress_callback(progress, f"Scraping page {i}/{len(urls_to_scrape)}: {url}")
            
            data = self.scrape_single_page(url, selectors)
            if data:
                results.append(data)
            
            if i < len(urls_to_scrape):
                time.sleep(self.delay)
        
        return results
    
    def generate_html_report(self, data):
        if isinstance(data, list):
            data = data[0] if data else {}
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scraped Content Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; background: #f9f9f; }}
        .section h2 {{ color: #007cba; margin-top: 0; }}
        .title-content-pair {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
        .title {{ background: #007cba; color: white; padding: 15px; font-weight: bold; font-size: 18px; }}
        .content {{ background: #f0f8ff; padding: 15px; }}
        .meta-info {{ background: #f0f0f0; padding: 10px; border-radius: 3px; margin: 10px 0; }}
        .stats {{ display: flex; gap: 20px; margin: 10px 0; flex-wrap: wrap; }}
        .stat {{ background: #007cba; color: white; padding: 10px; border-radius: 3px; text-align: center; min-width: 80px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ Web Scraping Report</h1>
        <div class="meta-info">
            <p><strong>URL:</strong> <a href="{data.get('scraped_url', '#')}" target="_blank">{data.get('scraped_url', 'Unknown')}</a></p>
            <p><strong>Scraped at:</strong> {data.get('scraped_at', 'Unknown')}</p>
        </div>
        <div class="stats">
            <div class="stat">
                <h3>{len(data.get('title_content_pairs', []))}</h3>
                <p>Title-Content Pairs</p>
            </div>
            <div class="stat">
                <h3>{sum(len(pair.get('content', '')) for pair in data.get('title_content_pairs', []))}</h3>
                <p>Total Characters</p>
            </div>
        </div>
    </div>"""
        
        # Title-Content Pairs Section
        if data.get('title_content_pairs'):
            html += '<div class="section"><h2>📋 Title-Content Pairs</h2>'
            for i, pair in enumerate(data['title_content_pairs'], 1):
                title = pair.get('title', '')
                content = pair.get('content', '')
                
                html += f'<div class="title-content-pair">'
                html += f'<div class="title">{i}. {title}</div>'
                if content:
                    html += f'<div class="content">{content}</div>'
                else:
                    html += f'<div class="content"><em>No content found for this section</em></div>'
                html += '</div>'
            html += '</div>'
        
        html += '</body></html>'
        return html
    
    def generate_formatted_text(self, data):
        if isinstance(data, list):
            data = data[0] if data else {}
        
        text = f"""╔══════════════════════════════════════════════════════════════╗
║                    🕷️ WEB SCRAPING REPORT                    ║
╚══════════════════════════════════════════════════════════════╝

📊 BASIC INFORMATION
────────────────────────────────────────────────────────────────
URL: {data.get('scraped_url', 'Unknown')}
Scraped at: {data.get('scraped_at', 'Unknown')}

📈 CONTENT STATISTICS
────────────────────────────────────────────────────────────────
Title-Content Pairs: {len(data.get('title_content_pairs', []))}
Total Characters: {sum(len(pair.get('content', '')) for pair in data.get('title_content_pairs', []))}

"""
        
        # Title-Content Pairs
        if data.get('title_content_pairs'):
            text += "📋 TITLE-CONTENT PAIRS\n────────────────────────────────────────────────────────────────\n"
            for i, pair in enumerate(data['title_content_pairs'], 1):
                title = pair.get('title', '')
                content = pair.get('content', '')
                
                text += f"\n{'='*80}\n"
                text += f"SECTION {i}\n"
                text += f"{'='*80}\n"
                text += f"TITLE: {title}\n"
                text += f"{'─'*80}\n"
                if content:
                    text += f"CONTENT:\n{content}\n"
                else:
                    text += f"CONTENT:\nNo content found for this section\n"
                text += f"\n"
        
        text += "╔══════════════════════════════════════════════════════════════╗\n"
        text += "║                        END OF REPORT                        ║\n"
        text += "╚══════════════════════════════════════════════════════════════╝\n"
        
        return text
    
    def generate_xml(self, data):
        if isinstance(data, list):
            data = data[0] if data else {}
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<scraped_content>\n'
        xml += f'  <url>{data.get("scraped_url", "")}</url>\n'
        xml += f'  <scraped_at>{data.get("scraped_at", "")}</scraped_at>\n'
        
        xml += '  <title_content_pairs>\n'
        for i, pair in enumerate(data.get('title_content_pairs', []), 1):
            xml += f'    <pair id="{i}">\n'
            xml += f'      <title>{pair.get("title", "")}</title>\n'
            xml += f'      <content>{pair.get("content", "")}</content>\n'
            xml += f'    </pair>\n'
        xml += '  </title_content_pairs>\n'
        
        xml += '</scraped_content>\n'
        return xml

def create_download_buttons(data, timestamp):
    """Create download buttons for different formats"""
    
    # JSON Download
    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    st.download_button(
        label="📄 Download JSON",
        data=json_data,
        file_name=f"scraped_content_{timestamp}.json",
        mime="application/json"
    )
    
    # CSV Download - Create rows for each title-content pair
    if isinstance(data, dict) and data.get('title_content_pairs'):
        csv_rows = []
        for i, pair in enumerate(data['title_content_pairs'], 1):
            csv_rows.append({
                'section_number': i,
                'title': pair.get('title', ''),
                'content': pair.get('content', ''),
                'content_length': len(pair.get('content', ''))
            })
        
        df = pd.DataFrame(csv_rows)
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv_data,
            file_name=f"scraped_content_{timestamp}.csv",
            mime="text/csv"
        )
    
    # HTML Download
    html_data = WebScraper().generate_html_report(data)
    st.download_button(
        label="🌐 Download HTML",
        data=html_data,
        file_name=f"scraped_content_{timestamp}.html",
        mime="text/html"
    )
    
    # Text Download
    text_data = WebScraper().generate_formatted_text(data)
    st.download_button(
        label="📝 Download TXT",
        data=text_data,
        file_name=f"scraped_content_{timestamp}.txt",
        mime="text/plain"
    )
    
    # XML Download
    xml_data = WebScraper().generate_xml(data)
    st.download_button(
        label="📋 Download XML",
        data=xml_data,
        file_name=f"scraped_content_{timestamp}.xml",
        mime="application/xml"
    )

def display_scraped_data(data):
    """Display scraped data in a beautiful format"""
    if not data:
        st.error("No data to display!")
        return
    
    # Handle single page vs multiple pages
    if isinstance(data, list):
        st.subheader("📊 Website Scraping Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Pages", len(data))
        
        with col2:
            total_pairs = sum(len(page.get('title_content_pairs', [])) for page in data)
            st.metric("Total Sections", total_pairs)
        
        with col3:
            total_content = sum(sum(len(pair.get('content', '')) for pair in page.get('title_content_pairs', [])) for page in data)
            st.metric("Total Characters", total_content)
        
        # Page selector
        page_titles = [f"Page {i+1}: {page.get('title_content_pairs', [{}])[0].get('title', 'No title')[:50]}" for i, page in enumerate(data)]
        selected_page = st.selectbox("📄 Select Page to View", range(len(page_titles)), format_func=lambda x: page_titles[x])
        
        # Display selected page
        page_data = data[selected_page]
        st.markdown(f"### 🌐 Page URL: {page_data.get('scraped_url', 'Unknown')}")
        
        if page_data.get('title_content_pairs'):
            st.subheader("📋 Title-Content Pairs")
            
            for i, pair in enumerate(page_data['title_content_pairs'], 1):
                title = pair.get('title', '')
                content = pair.get('content', '')
                
                with st.expander(f"Section {i}: {title[:100]}{'...' if len(title) > 100 else ''}"):
                    st.write(f"**📌 Title:** {title}")
                    if content:
                        st.write(f"**📝 Content:** {content}")
                    else:
                        st.write("*No content found for this section*")
    else:
        # Single page display (existing code)
        st.subheader("📊 Summary Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Title-Content Pairs", len(data.get('title_content_pairs', [])))
        with col2:
            total_content_length = sum(len(pair.get('content', '')) for pair in data.get('title_content_pairs', []))
            st.metric("Total Characters", total_content_length)
        
        # Basic Info
        st.subheader("🌍 Basic Information")
        st.info(f"""
        **URL:** {data.get('scraped_url', 'Unknown')}  
        **Scraped at:** {data.get('scraped_at', 'Unknown')}
        """)
        
        # Title-Content Pairs
        if data.get('title_content_pairs'):
            st.subheader("📋 Title-Content Pairs")
            
            for i, pair in enumerate(data['title_content_pairs'], 1):
                title = pair.get('title', '')
                content = pair.get('content', '')
                
                with st.expander(f"Section {i}: {title[:100]}{'...' if len(title) > 100 else ''}"):
                    st.write(f"**📌 Title:** {title}")
                    if content:
                        st.write(f"**📝 Content:** {content}")
                    else:
                        st.write("*No content found for this section*")

def main():
    st.set_page_config(
        page_title="🕷️ Web Scraper",
        page_icon="🕷️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🕷️ Universal Web Scraper")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Scraping Mode
        scraping_mode = st.selectbox(
            "Scraping Mode",
            ["Basic Content", "Custom CSS Selectors", "Website Crawler", "Sitemap Scraper"]
        )
        
        # URL Input
        url = st.text_input(
            "🌐 Enter URL to scrape",
            placeholder="https://example.com",
            help="Enter the full URL including http:// or https://"
        )
        
        # Website Crawler Configuration
        if scraping_mode == "Website Crawler":
            st.subheader("🕷️ Crawler Settings")
            max_pages = st.number_input(
                "Max Pages to Scrape",
                min_value=1,
                max_value=500,
                value=50,
                help="Maximum number of pages to discover and scrape"
            )
            
            max_depth = st.number_input(
                "Max Depth",
                min_value=1,
                max_value=10,
                value=3,
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
            
            # Parse exclude patterns
            exclude_list = []
            if exclude_patterns:
                exclude_list = [pattern.strip() for pattern in exclude_patterns.strip().split('\n') if pattern.strip()]
        
        # Sitemap Scraper Configuration
        elif scraping_mode == "Sitemap Scraper":
            st.subheader("🗺️ Sitemap Settings")
            sitemap_url = st.text_input(
                "🗺️ Sitemap URL (optional)",
                placeholder="https://example.com/sitemap.xml",
                help="Leave empty to auto-discover sitemap, or enter specific sitemap URL"
            )
            
            max_pages = st.number_input(
                "Max Pages to Scrape",
                min_value=1,
                max_value=1000,
                value=100,
                help="Maximum number of pages to scrape from sitemap"
            )
        
        # Custom Selectors
        selectors = {}
        if scraping_mode == "Custom CSS Selectors":
            st.subheader("🎯 Custom Selectors")
            selector_input = st.text_area(
                "Enter CSS selectors (one per line, format: key:selector)",
                placeholder="title:h1\nprice:.price\ndescription:.product-description",
                help="Example: title:h1 will extract text from h1 tags and store it as 'title'"
            )
            
            # Parse selectors
            if selector_input:
                for line in selector_input.strip().split('\n'):
                    if ':' in line:
                        key, selector = line.split(':', 1)
                        selectors[key.strip()] = selector.strip()
        
        # Scrape Button
        scrape_button = st.button("🚀 Start Scraping", type="primary")
    
    # Main content area
    if scrape_button:
        if not url:
            st.error("⚠️ Please enter a URL to scrape!")
            return
        
        if not url.startswith(('http://', 'https://')):
            st.error("⚠️ Please include http:// or https:// in the URL!")
            return
        
        # Show loading spinner
        with st.spinner("🕷️ Scraping in progress..."):
            scraper = WebScraper()
            
            if scraping_mode == "Basic Content":
                data = scraper.scrape_single_page(url)
            elif scraping_mode == "Custom CSS Selectors":
                data = scraper.scrape_single_page(url, selectors)
            elif scraping_mode == "Website Crawler":
                # Create progress bar for website crawling
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Define progress callback function
                def update_progress(progress, status):
                    progress_bar.progress(progress)
                    status_text.text(status)
                
                try:
                    data = scraper.scrape_entire_website(
                        url, 
                        max_pages=max_pages, 
                        max_depth=max_depth, 
                        stay_on_domain=stay_on_domain, 
                        selectors=selectors, 
                        exclude_patterns=exclude_list if exclude_list else None,
                        use_sitemap=use_sitemap,
                        progress_callback=update_progress
                    )
                    
                    # Update progress to completion
                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Completed! Scraped {len(data)} pages.")
                    
                except Exception as e:
                    st.error(f"❌ Error during crawling: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
            elif scraping_mode == "Sitemap Scraper":
                # Create progress bar for sitemap scraping
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Define progress callback function
                def update_progress(progress, status):
                    progress_bar.progress(progress)
                    status_text.text(status)
                
                try:
                    # Use provided sitemap URL or auto-discover
                    target_sitemap_url = sitemap_url.strip() if sitemap_url and sitemap_url.strip() else None
                    
                    if target_sitemap_url:
                        # Use provided sitemap URL
                        urls_to_scrape = scraper.parse_sitemap(target_sitemap_url, update_progress)
                    else:
                        # Auto-discover sitemap
                        urls_to_scrape = scraper.discover_sitemap_urls(url, update_progress)
                    
                    if not urls_to_scrape:
                        st.error("❌ No sitemap found or sitemap is empty.")
                        progress_bar.empty()
                        status_text.empty()
                        data = None
                    else:
                        # Limit to max_pages
                        urls_to_scrape = urls_to_scrape[:max_pages]
                        
                        # Scrape all URLs from sitemap
                        results = []
                        for i, sitemap_url in enumerate(urls_to_scrape, 1):
                            progress = 0.5 + (i / len(urls_to_scrape)) * 0.5
                            update_progress(progress, f"Scraping page {i}/{len(urls_to_scrape)}: {sitemap_url}")
                            
                            page_data = scraper.scrape_single_page(sitemap_url, selectors)
                            if page_data:
                                results.append(page_data)
                            
                            if i < len(urls_to_scrape):
                                time.sleep(scraper.delay)
                        
                        data = results
                        progress_bar.progress(1.0)
                        status_text.text(f"✅ Completed! Scraped {len(data)} pages from sitemap.")
                
                except Exception as e:
                    st.error(f"❌ Error during sitemap scraping: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
                    data = None
        
        if data:
            st.success("✅ Scraping completed successfully!")
            
            # Display the data
            display_scraped_data(data)
            
            # Download section
            st.markdown("---")
            st.subheader("💾 Download Results")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create columns for download buttons
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                json_data = json.dumps(data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📄 JSON",
                    data=json_data,
                    file_name=f"scraped_content_{timestamp}.json",
                    mime="application/json"
                )
            
            with col2:
                # CSV - Handle both single page and multiple pages
                csv_data = ""
                if isinstance(data, list):
                    # Multiple pages - create summary CSV
                    csv_rows = []
                    for i, page in enumerate(data, 1):
                        for j, pair in enumerate(page.get('title_content_pairs', []), 1):
                            csv_rows.append({
                                'page_number': i,
                                'page_url': page.get('scraped_url', ''),
                                'section_number': j,
                                'title': pair.get('title', ''),
                                'content': pair.get('content', ''),
                                'content_length': len(pair.get('content', ''))
                            })
                    
                    if csv_rows:
                        df = pd.DataFrame(csv_rows)
                        csv_data = df.to_csv(index=False)
                else:
                    # Single page
                    if data.get('title_content_pairs'):
                        csv_rows = []
                        for i, pair in enumerate(data['title_content_pairs'], 1):
                            csv_rows.append({
                                'section_number': i,
                                'title': pair.get('title', ''),
                                'content': pair.get('content', ''),
                                'content_length': len(pair.get('content', ''))
                            })
                        
                        df = pd.DataFrame(csv_rows)
                        csv_data = df.to_csv(index=False)
                
                if csv_data:
                    st.download_button(
                        label="📊 CSV",
                        data=csv_data,
                        file_name=f"scraped_content_{timestamp}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                html_data = scraper.generate_html_report(data)
                st.download_button(
                    label="🌐 HTML",
                    data=html_data,
                    file_name=f"scraped_content_{timestamp}.html",
                    mime="text/html"
                )
            
            with col4:
                text_data = scraper.generate_formatted_text(data)
                st.download_button(
                    label="📝 TXT",
                    data=text_data,
                    file_name=f"scraped_content_{timestamp}.txt",
                    mime="text/plain"
                )
            
            with col5:
                xml_data = scraper.generate_xml(data)
                st.download_button(
                    label="📋 XML",
                    data=xml_data,
                    file_name=f"scraped_content_{timestamp}.xml",
                    mime="application/xml"
                )
            
            # Raw data preview
            st.markdown("---")
            st.subheader("🔍 Raw Data Preview")
            
            format_tabs = st.tabs(["JSON", "Formatted Text", "HTML Preview"])
            
            with format_tabs[0]:
                st.json(data)
            
            with format_tabs[1]:
                st.text(scraper.generate_formatted_text(data))
            
            with format_tabs[2]:
                st.components.v1.html(scraper.generate_html_report(data), height=600, scrolling=True)
        
        else:
            st.error("❌ Failed to scrape the URL. Please check if the URL is accessible and try again.")
    
    # Instructions
    else:
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
        
        ## 🕷️ Website Crawler Features
        
        - **Breadth-First Search**: Efficiently discovers all linked pages
        - **Configurable Limits**: Set maximum pages and crawl depth
        - **Domain Restriction**: Option to stay on the same domain
        - **Pattern Exclusion**: Skip admin pages, files, and unwanted content
        - **Progress Tracking**: Real-time progress updates during crawling
        - **Smart URL Normalization**: Handles relative links and removes duplicates
        - **Sitemap Integration**: Optionally uses sitemaps for faster discovery
        
        ## 🗺️ Sitemap Scraper Features
        
        - **Auto-Discovery**: Automatically finds sitemap.xml at common locations
        - **Custom Sitemap URLs**: Support for specific sitemap URLs
        - **Nested Sitemaps**: Handles sitemap indexes and nested sitemaps
        - **Fast Processing**: Direct URL extraction without crawling
        - **WordPress Support**: Special handling for WordPress sitemaps
        - **Progress Tracking**: Real-time updates during sitemap parsing
        
        ## 🎨 Output Formats
        
        - **JSON**: Structured data for programmatic use (includes page numbers for websites)
        - **CSV**: Tabular data for spreadsheets and analysis (includes page URLs for websites)
        - **HTML**: Beautiful interactive report with styling
        - **TXT**: Formatted text report with borders and sections
        - **XML**: Structured XML for data exchange
        
        ## 🔧 CSS Selector Examples
        
        ```
        title:h1                    # Extract h1 text as "title"
        price:.price               # Extract elements with class "price"
        description:#desc          # Extract element with id "desc"
        links:a[href]              # Extract all links
        images:img                 # Extract all images
        ```
        
        ## 🕷️ Crawler Exclusion Examples
        
        ```
        \.(pdf|jpg|jpeg|png|gif)$   # Skip image and PDF files
        /admin                      # Skip admin pages
        /login                      # Skip login pages
        \?                          # Skip URLs with query parameters
        #                           # Skip anchor links
        ```
        
        ---
        **Made with ❤️ using Streamlit and Beautiful Soup**
        """)

if __name__ == "__main__":
    main()
