#!/usr/bin/env python3
"""
Standalone script to convert raw Pep-Pedia CSV to AI-enhanced CSV.
"""

import sys
import os
import pandas as pd
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.pep_pedia_ai_processor import PepPediaAIProcessor

def convert_raw_to_enhanced(input_csv_path: str, output_csv_path: str = None) -> str:
    """Convert raw CSV to AI-enhanced CSV."""
    
    print("🤖 Raw CSV to AI-Enhanced CSV Converter")
    print("=" * 50)
    
    # Check if input file exists
    if not os.path.exists(input_csv_path):
        print(f"❌ Input file not found: {input_csv_path}")
        return None
    
    # Get OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("💡 Set it with: export OPENAI_API_KEY='your-key-here'")
        return None
    
    # Initialize AI processor
    ai_processor = PepPediaAIProcessor(openai_key)
    
    # Generate output filename if not provided
    if not output_csv_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv_path = f"pep_pedia_enhanced_{timestamp}.csv"
    
    # Process the CSV
    print(f"📄 Input CSV: {input_csv_path}")
    print(f"📄 Output CSV: {output_csv_path}")
    print()
    
    success = ai_processor.process_csv_with_ai(input_csv_path, output_csv_path)
    
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📄 Enhanced CSV: {output_csv_path}")
        
        # Show file sizes
        input_size = os.path.getsize(input_csv_path)
        output_size = os.path.getsize(output_csv_path)
        print(f"📊 Input size: {input_size:,} bytes")
        print(f"📊 Output size: {output_size:,} bytes")
        
        return output_csv_path
    else:
        print(f"\n❌ Conversion failed!")
        return None

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python convert_raw_to_enhanced.py <input_csv> [output_csv]")
        print()
        print("Examples:")
        print("  python convert_raw_to_enhanced.py peptide_raw_20260108_030222.csv")
        print("  python convert_raw_to_enhanced.py peptide_raw_20260108_030222.csv enhanced_output.csv")
        print()
        print("Note: Make sure OPENAI_API_KEY is set in environment")
        return
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = convert_raw_to_enhanced(input_csv, output_csv)
    
    if result:
        print(f"\n🚀 Success! Check your enhanced file: {result}")
    else:
        print(f"\n💥 Conversion failed!")

if __name__ == "__main__":
    main()
