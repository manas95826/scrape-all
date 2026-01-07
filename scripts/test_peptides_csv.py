#!/usr/bin/env python3
"""
Test script to scrape two peptides and generate CSV output.
"""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scrapers.pep_pedia_bulk import PepPediaBulkScraper
from src.formatters.csv_formatter import CSVFormatter

def test_two_peptides_csv():
    """Test scraping two peptides and generate CSV output."""
    
    # Initialize scraper
    scraper = PepPediaBulkScraper(delay=1.0)
    
    # Test peptides
    test_peptides = [
        "https://pep-pedia.org/peptides/bpc-157"
    ]
    
    print("🧪 Testing Pep-Pedia scraper with toggle functionality")
    print("=" * 60)
    
    all_results = []
    
    for i, url in enumerate(test_peptides, 1):
        print(f"\n📄 [{i}/{len(test_peptides)}] Scraping: {url}")
        
        try:
            # Scrape with toggle functionality
            result = scraper.scrape_with_toggles(url)
            
            if result:
                all_results.append(result)
                print(f"✅ Successfully scraped!")
                
                # Show route information
                if result.custom_data and 'content_by_route' in result.custom_data:
                    routes = result.custom_data['content_by_route']
                    oral_count = len(routes.get('oral', []))
                    injectable_count = len(routes.get('injectable', []))
                    print(f"   📊 Oral sections: {oral_count}")
                    print(f"   💉 Injectable sections: {injectable_count}")
                    
                    # Show peptide info if available
                    if 'peptide_info' in result.custom_data:
                        peptide_info = result.custom_data['peptide_info']
                        if 'oral' in peptide_info and peptide_info['oral'].get('name'):
                            print(f"   🧪 Peptide name (oral): {peptide_info['oral']['name']}")
                        if 'injectable' in peptide_info and peptide_info['injectable'].get('name'):
                            print(f"   🧪 Peptide name (injectable): {peptide_info['injectable']['name']}")
                else:
                    print("   ⚠️  No route-specific content found")
            else:
                print(f"❌ Failed to scrape")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Generate CSV output
    if all_results:
        print(f"\n📊 Generating CSV output for {len(all_results)} peptides...")
        
        try:
            # Initialize CSV formatter
            formatter = CSVFormatter()
            
            # Format the results
            csv_content = formatter.format(all_results)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"pep_pedia_test_results_{timestamp}.csv"
            
            # Save to file
            with open(csv_filename, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            print(f"✅ CSV saved to: {csv_filename}")
            print(f"📄 Total CSV content length: {len(csv_content)} characters")
            
            # Show first few lines of CSV
            print("\n📋 CSV Preview (first 500 characters):")
            print("-" * 50)
            print(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)
            print("-" * 50)
            
            # Also save raw JSON for inspection
            json_filename = f"pep_pedia_test_results_{timestamp}.json"
            json_data = [result.to_dict() for result in all_results]
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Raw JSON saved to: {json_filename}")
            
        except Exception as e:
            print(f"❌ Error generating CSV: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ No results to generate CSV")
    
    # Cleanup
    if hasattr(scraper, 'driver') and scraper.driver:
        scraper.driver.quit()
    
    print(f"\n🎉 Test completed! Scraped {len(all_results)} peptides successfully.")

if __name__ == "__main__":
    test_two_peptides_csv()
