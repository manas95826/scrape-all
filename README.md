# 🕷️ Universal Web Scraper

A powerful and versatile web scraping application built with Streamlit that supports multiple scraping modes and output formats.

## ✨ Features

- **🕷️ Website Crawling**: Discover and scrape entire websites automatically
- **🗺️ Sitemap Support**: Parse XML sitemaps for efficient page discovery
- **🎯 Custom Selectors**: Extract specific data using CSS selectors
- **📊 Multiple Output Formats**: JSON, CSV, HTML, TXT, XML
- **💾 Easy Downloads**: One-click download in any format
- **📱 Responsive Design**: Works on all devices
- **⚡ Fast Processing**: Efficient scraping with proper headers
- **🛡️ Smart Filtering**: Exclude unwanted URLs and stay on domain

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/manas95826/scrape-all.git
   cd scrape-all
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run streamlit_scraper.py
   ```

## 📋 Usage

### Scraping Modes

#### 1. **Basic Content**
Extracts title, headings, paragraphs, links, and images from a single page.

#### 2. **Custom CSS Selectors**
Extract specific elements using CSS selectors from a single page.
- Format: `key:selector` (one per line)
- Example: `title:h1` will extract text from h1 tags and store it as 'title'

#### 3. **Website Crawler**
Discovers and scrapes all pages from an entire website using breadth-first search.
- Configurable maximum pages and crawl depth
- Option to stay on the same domain
- Pattern exclusion for unwanted content
- Optional sitemap integration for faster discovery

#### 4. **Sitemap Scraper**
Uses XML sitemaps to efficiently scrape all listed pages.
- Auto-discovery of sitemaps at common locations
- Support for custom sitemap URLs
- Handles nested sitemaps and sitemap indexes
- Special handling for WordPress sitemaps

### Configuration Options

#### Website Crawler Settings:
- **Max Pages**: Maximum number of pages to discover and scrape (1-500)
- **Max Depth**: Maximum link depth to follow (1-10)
- **Stay on Same Domain**: Only scrape pages from the same domain
- **Use Sitemap**: Try to discover and use XML sitemap for faster discovery
- **Exclude Patterns**: Regex patterns to exclude certain URLs

#### Sitemap Scraper Settings:
- **Sitemap URL**: Optional specific sitemap URL (auto-discovery if empty)
- **Max Pages**: Maximum number of pages to scrape from sitemap (1-1000)

## 🎨 Output Formats

### **JSON**
Structured data for programmatic use. Includes page numbers for websites.

### **CSV**
Tabular data for spreadsheets and analysis. Includes page URLs for websites.

### **HTML**
Beautiful interactive report with styling and proper formatting.

### **TXT**
Formatted text report with borders and sections for easy reading.

### **XML**
Structured XML format for data exchange and integration.

## 🔧 CSS Selector Examples

```css
# Basic selectors
title:h1
description:.description
price:.price

# Attribute selectors
links:a[href]
images:img[src]

# Complex selectors
products:.product-item
article-content:article p
navigation:nav ul li a
```

## 🗺️ Sitemap Support

The scraper automatically checks for sitemaps at these locations:
- `/sitemap.xml`
- `/sitemap_index.xml`
- `/sitemaps.xml`
- `/wp-sitemap.xml` (WordPress)
- Both with and without `www.` prefix

### Sitemap Features:
- **Auto-Discovery**: Automatically finds sitemaps at common locations
- **Custom Sitemap URLs**: Support for specific sitemap URLs
- **Nested Sitemaps**: Handles sitemap indexes and nested sitemaps
- **Fast Processing**: Direct URL extraction without crawling
- **WordPress Support**: Special handling for WordPress sitemaps

## 🛡️ Best Practices

1. **Respectful Scraping**: Built-in delays between requests
2. **User-Agent**: Proper browser headers for better compatibility
3. **Error Handling**: Graceful handling of network errors and timeouts
4. **Rate Limiting**: Configurable delays to avoid overwhelming servers
5. **Domain Restriction**: Option to stay on target domain

## 📊 Progress Tracking

- Real-time progress bars during scraping
- Status updates for each operation
- Detailed error messages
- Completion statistics

## 🐛 Troubleshooting

### Common Issues:

1. **Connection Timeout**: Increase timeout values or check network connectivity
2. **Access Denied**: Some websites may block scraping - try different user agents
3. **Empty Results**: Check if the website uses JavaScript for content loading
4. **Large Sitemaps**: Use max pages limit to avoid memory issues

### Solutions:

- Use custom CSS selectors for specific content
- Adjust exclude patterns to filter unwanted content
- Try sitemap mode for better coverage
- Reduce max pages for faster processing

## 📝 Requirements

```txt
streamlit
requests
beautifulsoup4
pandas
lxml
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- Powered by [Requests](https://requests.readthedocs.io/) for HTTP handling

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the CSS selector examples

---

**Happy Scraping! 🕷️**
