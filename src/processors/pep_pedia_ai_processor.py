"""
AI-powered CSV processor for Pep-Pedia scraped data.
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
from content_categorizer import ContentCategorizer


class PepPediaAIProcessor:
    """AI processor for Pep-Pedia scraped data."""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the AI processor."""
        self.categorizer = ContentCategorizer(openai_api_key) if openai_api_key else None
        
    def process_csv_with_ai(self, input_csv_path: str, output_csv_path: str) -> bool:
        """Process raw CSV with AI to fill categorized columns."""
        
        print("🤖 AI-Powered CSV Processor")
        print("=" * 50)
        
        if not self.categorizer:
            print("❌ No OpenAI API key provided")
            return False
        
        try:
            # Read the raw CSV
            print(f"📄 Reading raw CSV: {input_csv_path}")
            df = pd.read_csv(input_csv_path)
            
            print(f"📊 Found {len(df)} rows to process")
            
            # Define the columns we want to fill with AI
            category_columns = [
                'Overview', 'Key Benefits', 'Mechanism of Action', 'Molecular Information',
                'Research Indications', 'Research Protocols', 'Peptide Interactions',
                'How to Reconstitute', 'Quality Indicators', 'What to Expect',
                'Side Effects & Safety', 'References', 'Quick Start Guide',
                'Storage', 'Cycle Length', 'Break Between'
            ]
            
            # Process each row
            processed_rows = []
            
            for idx, row in df.iterrows():
                peptide_name = row.get('peptide_name', 'Unknown')
                route = row.get('route', 'unknown')
                print(f"\n🧪 Processing row {idx + 1}/{len(df)}: {peptide_name} ({route})")
                
                # Get the raw content
                route_content = row.get('route_content', '')
                if pd.isna(route_content) or not route_content:
                    print("⚠️  No route content found, skipping...")
                    processed_rows.append(row)
                    continue
                
                # Use AI to categorize the content
                try:
                    print("🤖 Using AI to categorize content...")
                    
                    categorized_data = self.categorizer.categorize_content(
                        title=f"{peptide_name} - {route}",
                        content=route_content,
                        url=row.get('source_url', '')
                    )
                    
                    # Fill the categorized columns
                    for col in category_columns:
                        if col in categorized_data:
                            row[col] = categorized_data[col]
                        else:
                            row[col] = ""
                    
                    print("✅ Content categorized successfully")
                    
                except Exception as e:
                    print(f"⚠️  AI categorization failed: {e}")
                    # Keep original values if AI fails
                    pass
                
                processed_rows.append(row)
            
            # Create new DataFrame with processed data
            processed_df = pd.DataFrame(processed_rows)
            
            # Save the enhanced CSV
            print(f"\n💾 Saving enhanced CSV: {output_csv_path}")
            processed_df.to_csv(output_csv_path, index=False)
            
            print(f"✅ Enhanced CSV saved with {len(processed_df)} rows")
            print(f"📊 Original CSV length: {len(df)} rows")
            print(f"📊 Enhanced CSV length: {len(processed_df)} rows")
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing CSV: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_latest_csv(self, output_dir: str = ".") -> str:
        """Process the latest CSV file and return the enhanced CSV path."""
        
        # Find the most recent CSV file (look for both patterns)
        import glob
        csv_files = glob.glob(os.path.join(output_dir, "pep_pedia_two_peptides_*.csv"))
        if not csv_files:
            # Try single peptide pattern
            csv_files = glob.glob(os.path.join(output_dir, "peptide_raw_*.csv"))
        
        if not csv_files:
            print("❌ No Pep-Pedia CSV files found")
            return None
        
        # Get the most recent file
        latest_csv = max(csv_files, key=os.path.getctime)
        print(f"📄 Found latest CSV: {latest_csv}")
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = os.path.join(output_dir, f"pep_pedia_enhanced_{timestamp}.csv")
        
        # Process with AI
        success = self.process_csv_with_ai(latest_csv, output_csv)
        
        if success:
            print(f"\n🎉 AI processing completed!")
            print(f"📄 Input: {latest_csv}")
            print(f"📄 Output: {output_csv}")
            return output_csv
        else:
            print(f"\n❌ AI processing failed!")
            return None
