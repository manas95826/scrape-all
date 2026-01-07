#!/usr/bin/env python3
"""
Simple test script to scrape one peptide URL and output CSV.
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scrapers.pep_pedia_bulk import PepPediaBulkScraper
from src.formatters.csv_formatter import CSVFormatter
from src.processors.pep_pedia_ai_processor import PepPediaAIProcessor

def scrape_one_peptide(url: str, use_ai: bool = True):
    """Scrape one peptide and generate CSV output."""
    
    print(f"🧪 Pep-Pedia Single Peptide Scraper")
    print("=" * 50)
    print(f"📄 Target URL: {url}")
    print(f"🤖 AI Enhancement: {'Enabled' if use_ai else 'Disabled'}")
    print()
    
    # Step 1: Scrape the peptide
    print("🔄 Step 1: Scraping peptide...")
    scraper = PepPediaBulkScraper(delay=1.0)
    
    try:
        page_data = scraper.scrape_with_toggles(url)
        
        if not page_data:
            print("❌ Failed to scrape peptide")
            return None
        
        page_dict = page_data.to_dict()
        content_by_route = page_dict.get('content_by_route', {})
        oral_count = len(content_by_route.get('oral', []))
        injectable_count = len(content_by_route.get('injectable', []))
        
        print(f"✅ Scraping completed!")
        print(f"   📊 Oral sections: {oral_count}")
        print(f"   💉 Injectable sections: {injectable_count}")
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return None
    
    # Step 2: Generate raw CSV
    print("\n📊 Step 2: Generating raw CSV...")
    formatter = CSVFormatter()
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_csv_filename = f"peptide_raw_{timestamp}.csv"
        
        csv_content = formatter._format_pep_pedia_csv_multiple([page_data])
        
        with open(raw_csv_filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print(f"✅ Raw CSV saved: {raw_csv_filename}")
        
        # Show preview
        with open(raw_csv_filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_length = sum(len(line) for line in lines)
            print(f"📄 CSV size: {total_length:,} characters")
            
    except Exception as e:
        print(f"❌ CSV generation error: {e}")
        return raw_csv_filename
    
    # Step 3: AI Processing (optional)
    final_csv = raw_csv_filename
    
    if use_ai:
        print("\n🤖 Step 3: AI Processing...")
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if openai_key:
            try:
                ai_processor = PepPediaAIProcessor(openai_key)
                enhanced_csv = ai_processor.process_latest_csv()
                
                if enhanced_csv:
                    final_csv = enhanced_csv
                    print(f"✅ Enhanced CSV saved: {enhanced_csv}")
                else:
                    print("⚠️  AI processing failed, using raw CSV")
            except Exception as e:
                print(f"⚠️  AI processing error: {e}")
                print("📄 Using raw CSV")
        else:
            print("⚠️  No OPENAI_API_KEY found, using raw CSV")
    
    # Step 4: Show final result
    print(f"\n🎉 Final Result:")
    print(f"📄 Output CSV: {final_csv}")
    
    # Show preview of final CSV
    try:
        with open(final_csv, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"📊 Total rows: {len(lines)}")
            print(f"📋 Preview:")
            print("-" * 50)
            print(lines[0][:200] + "..." if lines else "No content")
            print("-" * 50)
    except Exception as e:
        print(f"⚠️  Could not preview CSV: {e}")
    
    return final_csv

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scrape_one_peptide.py <URL> [--no-ai]")
        print("Example: python scrape_one_peptide.py https://pep-pedia.org/peptides/bpc-157")
        print("Example: python scrape_one_peptide.py https://pep-pedia.org/peptides/bpc-157 --no-ai")
        return
    
    url = sys.argv[1]
    use_ai = "--no-ai" not in sys.argv
    
    # Validate URL
    if "pep-pedia.org/peptides/" not in url:
        print("❌ Invalid URL. Must be a Pep-Pedia peptide URL")
        print("Example: https://pep-pedia.org/peptides/bpc-157")
        return
    
    # Scrape the peptide
    result = scrape_one_peptide(url, use_ai)
    
    if result:
        print(f"\n🚀 Success! Check your output file: {result}")
    else:
        print(f"\n❌ Failed to process peptide")

if __name__ == "__main__":
    main()
