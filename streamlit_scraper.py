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
            data = {
                'title': soup.title.string.strip() if soup.title else '',
                'headings': {
                    'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
                    'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
                    'h3': [h.get_text(strip=True) for h in soup.find_all('h3')]
                },
                'paragraphs': [p.get_text(strip=True) for p in soup.find_all('p')],
                'links': [{'text': a.get_text(strip=True), 'href': a.get('href')} for a in soup.find_all('a', href=True)],
                'images': [{'src': img.get('src'), 'alt': img.get('alt', '')} for img in soup.find_all('img', src=True)],
                'meta_description': soup.find('meta', attrs={'name': 'description'}).get('content', '') if soup.find('meta', attrs={'name': 'description'}) else '',
                'text_content': soup.get_text(strip=True, separator=' ')
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
    <title>Scraped Content Report - {data.get('title', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; background: #f9f9f9; }}
        .section h2 {{ color: #007cba; margin-top: 0; }}
        .headings {{ margin: 10px 0; }}
        .heading-level {{ margin: 10px 0; }}
        .heading-level h4 {{ margin: 5px 0; color: #333; }}
        .heading-list {{ list-style: none; padding: 0; }}
        .heading-list li {{ background: #e9e9e9; margin: 5px 0; padding: 8px; border-radius: 3px; }}
        .paragraphs {{ margin: 10px 0; }}
        .paragraph {{ background: #f0f8ff; padding: 10px; margin: 5px 0; border-radius: 3px; border-left: 3px solid #007cba; }}
        .links {{ margin: 10px 0; }}
        .link {{ display: block; margin: 5px 0; padding: 8px; background: #e8f5e8; border-radius: 3px; }}
        .link a {{ text-decoration: none; color: #007cba; }}
        .link a:hover {{ text-decoration: underline; }}
        .images {{ margin: 10px 0; }}
        .image {{ margin: 5px 0; padding: 8px; background: #fff5e6; border-radius: 3px; }}
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
            <p><strong>Title:</strong> {data.get('title', 'No title found')}</p>
        </div>
        <div class="stats">
            <div class="stat">
                <h3>{len(data.get('headings', {}).get('h1', []))}</h3>
                <p>H1 Tags</p>
            </div>
            <div class="stat">
                <h3>{len(data.get('headings', {}).get('h2', []))}</h3>
                <p>H2 Tags</p>
            </div>
            <div class="stat">
                <h3>{len(data.get('paragraphs', []))}</h3>
                <p>Paragraphs</p>
            </div>
            <div class="stat">
                <h3>{len(data.get('links', []))}</h3>
                <p>Links</p>
            </div>
            <div class="stat">
                <h3>{len(data.get('images', []))}</h3>
                <p>Images</p>
            </div>
        </div>
    </div>"""
        
        # Headings Section
        if data.get('headings'):
            html += '<div class="section"><h2>📋 Headings</h2>'
            for level in ['h1', 'h2', 'h3']:
                headings = data['headings'].get(level, [])
                if headings:
                    html += f'<div class="heading-level"><h4>{level.upper()} Tags ({len(headings)})</h4><ul class="heading-list">'
                    for heading in headings:
                        html += f'<li>{heading}</li>'
                    html += '</ul></div>'
            html += '</div>'
        
        # Paragraphs Section
        if data.get('paragraphs'):
            html += '<div class="section"><h2>📝 Paragraphs</h2><div class="paragraphs">'
            for i, para in enumerate(data['paragraphs'][:10], 1):
                html += f'<div class="paragraph"><strong>Paragraph {i}:</strong> {para}</div>'
            if len(data['paragraphs']) > 10:
                html += f'<p><em>... and {len(data["paragraphs"]) - 10} more paragraphs</em></p>'
            html += '</div></div>'
        
        # Links Section
        if data.get('links'):
            html += '<div class="section"><h2>🔗 Links</h2><div class="links">'
            for link in data['links'][:15]:
                href = link.get('href', '#')
                text = link.get('text', 'No text') or 'No text'
                if href.startswith('/'):
                    base_url = data.get('scraped_url', '')
                    if base_url:
                        href = urljoin(base_url, href)
                html += f'<div class="link"><a href="{href}" target="_blank">{text}</a> → {href}</div>'
            if len(data['links']) > 15:
                html += f'<p><em>... and {len(data["links"]) - 15} more links</em></p>'
            html += '</div></div>'
        
        # Images Section
        if data.get('images'):
            html += '<div class="section"><h2>🖼️ Images</h2><div class="images">'
            for img in data['images'][:10]:
                src = img.get('src', '')
                alt = img.get('alt', 'No alt text')
                if src.startswith('/'):
                    base_url = data.get('scraped_url', '')
                    if base_url:
                        src = urljoin(base_url, src)
                html += f'<div class="image"><strong>Alt:</strong> {alt}<br><strong>Src:</strong> <a href="{src}" target="_blank">{src}</a></div>'
            if len(data['images']) > 10:
                html += f'<p><em>... and {len(data["images"]) - 10} more images</em></p>'
            html += '</div></div>'
        
        # Meta Description
        if data.get('meta_description'):
            html += f'<div class="section"><h2>📄 Meta Description</h2><p>{data["meta_description"]}</p></div>'
        
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
Title: {data.get('title', 'No title found')}
Scraped at: {data.get('scraped_at', 'Unknown')}
Meta Description: {data.get('meta_description', 'No meta description')}

📈 CONTENT STATISTICS
────────────────────────────────────────────────────────────────
H1 Tags: {len(data.get('headings', {}).get('h1', []))}
H2 Tags: {len(data.get('headings', {}).get('h2', []))}
H3 Tags: {len(data.get('headings', {}).get('h3', []))}
Paragraphs: {len(data.get('paragraphs', []))}
Links: {len(data.get('links', []))}
Images: {len(data.get('images', []))}

"""
        
        # Headings
        if data.get('headings'):
            text += "📋 HEADINGS\n────────────────────────────────────────────────────────────────\n"
            for level in ['h1', 'h2', 'h3']:
                headings = data['headings'].get(level, [])
                if headings:
                    text += f"\n{level.upper()} TAGS ({len(headings)}):\n"
                    for i, heading in enumerate(headings, 1):
                        text += f"  {i}. {heading}\n"
            text += "\n"
        
        # Paragraphs
        if data.get('paragraphs'):
            text += "📝 PARAGRAPHS\n────────────────────────────────────────────────────────────────\n"
            for i, para in enumerate(data['paragraphs'][:5], 1):
                text += f"\nParagraph {i}:\n"
                text += f"{'─' * 50}\n"
                text += f"{para}\n"
            if len(data['paragraphs']) > 5:
                text += f"\n... and {len(data['paragraphs']) - 5} more paragraphs\n"
            text += "\n"
        
        # Links
        if data.get('links'):
            text += "🔗 LINKS\n────────────────────────────────────────────────────────────────\n"
            for i, link in enumerate(data['links'][:10], 1):
                href = link.get('href', '#')
                text_content = link.get('text', 'No text') or 'No text'
                text += f"{i}. {text_content}\n   → {href}\n"
            if len(data['links']) > 10:
                text += f"... and {len(data['links']) - 10} more links\n"
            text += "\n"
        
        # Images
        if data.get('images'):
            text += "🖼️ IMAGES\n────────────────────────────────────────────────────────────────\n"
            for i, img in enumerate(data['images'][:5], 1):
                src = img.get('src', '')
                alt = img.get('alt', 'No alt text')
                text += f"{i}. Alt: {alt}\n   → {src}\n"
            if len(data['images']) > 5:
                text += f"... and {len(data['images']) - 5} more images\n"
        
        text += "\n╔══════════════════════════════════════════════════════════════╗\n"
        text += "║                        END OF REPORT                        ║\n"
        text += "╚══════════════════════════════════════════════════════════════╝\n"
        
        return text
    
    def generate_xml(self, data):
        if isinstance(data, list):
            data = data[0] if data else {}
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<scraped_content>\n'
        xml += f'  <url>{data.get("scraped_url", "")}</url>\n'
        xml += f'  <title>{data.get("title", "")}</title>\n'
        xml += f'  <scraped_at>{data.get("scraped_at", "")}</scraped_at>\n'
        xml += f'  <meta_description>{data.get("meta_description", "")}</meta_description>\n'
        
        xml += '  <headings>\n'
        for level in ['h1', 'h2', 'h3']:
            headings = data.get('headings', {}).get(level, [])
            for heading in headings:
                xml += f'    <{level}>{heading}</{level}>\n'
        xml += '  </headings>\n'
        
        xml += '  <paragraphs>\n'
        for para in data.get('paragraphs', []):
            xml += f'    <paragraph>{para}</paragraph>\n'
        xml += '  </paragraphs>\n'
        
        xml += '  <links>\n'
        for link in data.get('links', []):
            xml += f'    <link>\n'
            xml += f'      <text>{link.get("text", "")}</text>\n'
            xml += f'      <href>{link.get("href", "")}</href>\n'
            xml += f'    </link>\n'
        xml += '  </links>\n'
        
        xml += '  <images>\n'
        for img in data.get('images', []):
            xml += f'    <image>\n'
            xml += f'      <src>{img.get("src", "")}</src>\n'
            xml += f'      <alt>{img.get("alt", "")}</alt>\n'
            xml += f'    </image>\n'
        xml += '  </images>\n'
        
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
    
    # CSV Download
    if isinstance(data, dict):
        # Flatten the data for CSV
        flattened_data = {}
        for key, value in data.items():
            if key == 'headings' and isinstance(value, dict):
                for level, headings in value.items():
                    flattened_data[f'{level}_count'] = len(headings)
                    flattened_data[f'{level}_tags'] = '; '.join(headings[:3])  # First 3 headings
            elif key == 'paragraphs' and isinstance(value, list):
                flattened_data['paragraph_count'] = len(value)
                flattened_data['first_paragraph'] = value[0] if value else ''
            elif key == 'links' and isinstance(value, list):
                flattened_data['link_count'] = len(value)
                flattened_data['first_link'] = f"{value[0].get('text', '')} -> {value[0].get('href', '')}" if value else ''
            elif key == 'images' and isinstance(value, list):
                flattened_data['image_count'] = len(value)
                flattened_data['first_image'] = f"{value[0].get('alt', '')} -> {value[0].get('src', '')}" if value else ''
            elif not isinstance(value, (dict, list)):
                flattened_data[key] = value
        
        df = pd.DataFrame([flattened_data])
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
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("H1 Tags", len(data.get('headings', {}).get('h1', [])))
    with col2:
        st.metric("H2 Tags", len(data.get('headings', {}).get('h2', [])))
    with col3:
        st.metric("Paragraphs", len(data.get('paragraphs', [])))
    with col4:
        st.metric("Links", len(data.get('links', [])))
    with col5:
        st.metric("Images", len(data.get('images', [])))
    
    # Basic Info
    st.subheader("🌍 Basic Information")
    st.info(f"""
    **URL:** {data.get('scraped_url', 'Unknown')}  
    **Title:** {data.get('title', 'No title found')}  
    **Scraped at:** {data.get('scraped_at', 'Unknown')}  
    **Meta Description:** {data.get('meta_description', 'No meta description')}
    """)
    
    # Headings
    if data.get('headings'):
        st.subheader("📋 Headings")
        for level in ['h1', 'h2', 'h3']:
            headings = data['headings'].get(level, [])
            if headings:
                with st.expander(f"{level.upper()} Tags ({len(headings)})"):
                    for i, heading in enumerate(headings, 1):
                        st.write(f"{i}. {heading}")
    
    # Paragraphs
    if data.get('paragraphs'):
        st.subheader("📝 Paragraphs")
        with st.expander(f"Paragraphs ({len(data['paragraphs'])})"):
            for i, para in enumerate(data['paragraphs'][:10], 1):
                st.write(f"**Paragraph {i}:** {para}")
            if len(data['paragraphs']) > 10:
                st.info(f"... and {len(data['paragraphs']) - 10} more paragraphs")
    
    # Links
    if data.get('links'):
        st.subheader("🔗 Links")
        with st.expander(f"Links ({len(data['links'])})"):
            for i, link in enumerate(data['links'][:15], 1):
                href = link.get('href', '#')
                text = link.get('text', 'No text') or 'No text'
                st.write(f"{i}. [{text}]({href})")
            if len(data['links']) > 15:
                st.info(f"... and {len(data['links']) - 15} more links")
    
    # Images
    if data.get('images'):
        st.subheader("🖼️ Images")
        with st.expander(f"Images ({len(data['images'])})"):
            for i, img in enumerate(data['images'][:10], 1):
                src = img.get('src', '')
                alt = img.get('alt', 'No alt text')
                st.write(f"{i}. **Alt:** {alt}  \n   **Src:** {src}")
            if len(data['images']) > 10:
                st.info(f"... and {len(data['images']) - 10} more images")

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
                # CSV
                if isinstance(data, dict):
                    flattened_data = {}
                    for key, value in data.items():
                        if key == 'headings' and isinstance(value, dict):
                            for level, headings in value.items():
                                flattened_data[f'{level}_count'] = len(headings)
                                flattened_data[f'{level}_tags'] = '; '.join(headings[:3])
                        elif key == 'paragraphs' and isinstance(value, list):
                            flattened_data['paragraph_count'] = len(value)
                            flattened_data['first_paragraph'] = value[0] if value else ''
                        elif key == 'links' and isinstance(value, list):
                            flattened_data['link_count'] = len(value)
                            flattened_data['first_link'] = f"{value[0].get('text', '')} -> {value[0].get('href', '')}" if value else ''
                        elif key == 'images' and isinstance(value, list):
                            flattened_data['image_count'] = len(value)
                            flattened_data['first_image'] = f"{value[0].get('alt', '')} -> {value[0].get('src', '')}" if value else ''
                        elif not isinstance(value, (dict, list)):
                            flattened_data[key] = value
                    
                    df = pd.DataFrame([flattened_data])
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
