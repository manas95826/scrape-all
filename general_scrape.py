import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin, urlparse
import csv
from datetime import datetime
import os

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
            print(f"Error fetching {url}: {e}")
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
        print(f"Scraping: {url}")
        response = self.get_page(url)
        if response:
            data = self.parse_content(response, selectors)
            data['scraped_url'] = url
            data['scraped_at'] = datetime.now().isoformat()
            return data
        return None
    
    def scrape_multiple_pages(self, urls, selectors=None):
        results = []
        for i, url in enumerate(urls, 1):
            print(f"Scraping page {i}/{len(urls)}: {url}")
            data = self.scrape_single_page(url, selectors)
            if data:
                results.append(data)
            
            if i < len(urls):
                time.sleep(self.delay)
        
        return results
    
    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    
    def save_to_csv(self, data, filename):
        if not data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if isinstance(data, list):
                fieldnames = set()
                for item in data:
                    fieldnames.update(item.keys())
                
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                writer.writeheader()
                writer.writerow(data)
        
        print(f"Data saved to {filename}")
    
    def save_to_html(self, data, filename):
        html_content = self.generate_html_report(data)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report saved to {filename}")
    
    def save_to_txt(self, data, filename):
        txt_content = self.generate_formatted_text(data)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        print(f"Formatted text saved to {filename}")
    
    def save_to_xml(self, data, filename):
        xml_content = self.generate_xml(data)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"XML data saved to {filename}")
    
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
        .stats {{ display: flex; gap: 20px; margin: 10px 0; }}
        .stat {{ background: #007cba; color: white; padding: 10px; border-radius: 3px; text-align: center; }}
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
            for i, para in enumerate(data['paragraphs'][:10], 1):  # Show first 10 paragraphs
                html += f'<div class="paragraph"><strong>Paragraph {i}:</strong> {para}</div>'
            if len(data['paragraphs']) > 10:
                html += f'<p><em>... and {len(data["paragraphs"]) - 10} more paragraphs</em></p>'
            html += '</div></div>'
        
        # Links Section
        if data.get('links'):
            html += '<div class="section"><h2>🔗 Links</h2><div class="links">'
            for link in data['links'][:15]:  # Show first 15 links
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
            for img in data['images'][:10]:  # Show first 10 images
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

def main():
    scraper = WebScraper(delay=1)
    
    url = input("Enter the URL to scrape: ").strip()
    
    print("\nChoose scraping option:")
    print("1. Basic content extraction (title, headings, paragraphs, links, images)")
    print("2. Custom CSS selectors")
    print("3. Multiple URLs from file")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    print("\nChoose output formats (comma-separated):")
    print("Available formats: json, csv, html, txt, xml")
    print("Example: json,html,txt")
    formats = input("Enter formats: ").strip().lower().split(',')
    formats = [f.strip() for f in formats if f.strip()]
    
    if not formats:
        formats = ['json']  # Default to JSON
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if choice == '1':
        data = scraper.scrape_single_page(url)
        if data:
            for fmt in formats:
                filename = f"scraped_content_{timestamp}.{fmt}"
                if fmt == 'json':
                    scraper.save_to_json(data, filename)
                elif fmt == 'csv':
                    scraper.save_to_csv(data, filename)
                elif fmt == 'html':
                    scraper.save_to_html(data, filename)
                elif fmt == 'txt':
                    scraper.save_to_txt(data, filename)
                elif fmt == 'xml':
                    scraper.save_to_xml(data, filename)
                else:
                    print(f"Unsupported format: {fmt}")
            
            print("\n" + "="*60)
            print("🕷️ SCRAPING COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📊 SUMMARY:")
            print(f"  • Title: {data.get('title', 'N/A')}")
            print(f"  • H1 Tags: {len(data.get('headings', {}).get('h1', []))}")
            print(f"  • H2 Tags: {len(data.get('headings', {}).get('h2', []))}")
            print(f"  • H3 Tags: {len(data.get('headings', {}).get('h3', []))}")
            print(f"  • Paragraphs: {len(data.get('paragraphs', []))}")
            print(f"  • Links: {len(data.get('links', []))}")
            print(f"  • Images: {len(data.get('images', []))}")
            print(f"  • Meta Description: {data.get('meta_description', 'N/A')[:50]}...")
            print(f"\n📁 Files created:")
            for fmt in formats:
                print(f"  • scraped_content_{timestamp}.{fmt}")
            print("="*60)
    
    elif choice == '2':
        print("\nEnter custom CSS selectors (format: key:selector, one per line)")
        print("Example:")
        print("title:h1")
        print("price:.price")
        print("description:.product-description")
        print("Enter 'done' when finished:")
        
        selectors = {}
        while True:
            line = input().strip()
            if line.lower() == 'done':
                break
            if ':' in line:
                key, selector = line.split(':', 1)
                selectors[key.strip()] = selector.strip()
        
        if selectors:
            data = scraper.scrape_single_page(url, selectors)
            if data:
                for fmt in formats:
                    filename = f"custom_scrape_{timestamp}.{fmt}"
                    if fmt == 'json':
                        scraper.save_to_json(data, filename)
                    elif fmt == 'csv':
                        scraper.save_to_csv(data, filename)
                    elif fmt == 'html':
                        scraper.save_to_html(data, filename)
                    elif fmt == 'txt':
                        scraper.save_to_txt(data, filename)
                    elif fmt == 'xml':
                        scraper.save_to_xml(data, filename)
                    else:
                        print(f"Unsupported format: {fmt}")
                
                print("\n" + "="*60)
                print("🎯 CUSTOM SCRAPING COMPLETED!")
                print("="*60)
                print(f"📊 Extracted data points:")
                for key, value in data.items():
                    if key not in ['scraped_url', 'scraped_at']:
                        if isinstance(value, list):
                            print(f"  • {key}: {len(value)} items")
                        else:
                            print(f"  • {key}: {str(value)[:50]}...")
                print(f"\n📁 Files created:")
                for fmt in formats:
                    print(f"  • custom_scrape_{timestamp}.{fmt}")
                print("="*60)
        else:
            print("No selectors provided.")
    
    elif choice == '3':
        filename = input("Enter the file path containing URLs (one per line): ").strip()
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            print(f"Found {len(urls)} URLs to scrape")
            results = scraper.scrape_multiple_pages(urls)
            
            if results:
                for fmt in formats:
                    output_file = f"batch_scrape_{timestamp}.{fmt}"
                    if fmt == 'json':
                        scraper.save_to_json(results, output_file)
                    elif fmt == 'csv':
                        scraper.save_to_csv(results, output_file)
                    elif fmt == 'html':
                        scraper.save_to_html(results, output_file)
                    elif fmt == 'txt':
                        scraper.save_to_txt(results, output_file)
                    elif fmt == 'xml':
                        scraper.save_to_xml(results, output_file)
                    else:
                        print(f"Unsupported format: {fmt}")
                
                print("\n" + "="*60)
                print("📦 BATCH SCRAPING COMPLETED!")
                print("="*60)
                print(f"📊 SUMMARY:")
                print(f"  • Total URLs: {len(urls)}")
                print(f"  • Successfully scraped: {len(results)}")
                print(f"  • Failed: {len(urls) - len(results)}")
                print(f"\n📁 Files created:")
                for fmt in formats:
                    print(f"  • batch_scrape_{timestamp}.{fmt}")
                print("="*60)
        except FileNotFoundError:
            print("File not found. Please check the path and try again.")
    
    else:
        print("Invalid choice. Please run the script again.")
    
    # Display formatted text preview if txt format was chosen
    if 'txt' in formats and choice in ['1', '2']:
        print("\n" + "="*60)
        print("📄 FORMATTED TEXT PREVIEW:")
        print("="*60)
        if choice == '1':
            data = scraper.scrape_single_page(url)
        elif choice == '2':
            data = scraper.scrape_single_page(url, selectors)
        
        if data:
            print(scraper.generate_formatted_text(data)[:1000] + "\n... (truncated)")
        print("="*60)

if __name__ == "__main__":
    main()