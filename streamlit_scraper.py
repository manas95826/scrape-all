import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json
import csv
from datetime import datetime
from urllib.parse import urljoin
import pandas as pd
from io import StringIO, BytesIO
import base64

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
    
    # Summary Statistics
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
            ["Basic Content", "Custom CSS Selectors"]
        )
        
        # URL Input
        url = st.text_input(
            "🌐 Enter URL to scrape",
            placeholder="https://example.com",
            help="Enter the full URL including http:// or https://"
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
            else:
                data = scraper.scrape_single_page(url, selectors)
        
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
                # CSV - Create rows for each title-content pair
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
           - **Basic Content**: Extracts title, headings, paragraphs, links, and images
           - **Custom CSS Selectors**: Extract specific elements using CSS selectors
        3. **Configure**: If using custom mode, enter your CSS selectors
        4. **Scrape**: Click the "Start Scraping" button
        5. **Download**: Choose from multiple output formats (JSON, CSV, HTML, TXT, XML)
        
        ## 📋 Features
        
        - **🎯 Multiple Output Formats**: JSON, CSV, HTML, TXT, XML
        - **📊 Beautiful Visualizations**: Interactive charts and statistics
        - **🔍 Custom Selectors**: Extract specific data using CSS selectors
        - **💾 Easy Downloads**: One-click download in any format
        - **📱 Responsive Design**: Works on all devices
        - **⚡ Fast Processing**: Efficient scraping with proper headers
        
        ## 🎨 Output Formats
        
        - **JSON**: Structured data for programmatic use
        - **CSV**: Tabular data for spreadsheets and analysis
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
        
        ---
        **Made with ❤️ using Streamlit and Beautiful Soup**
        """)

if __name__ == "__main__":
    main()
