"""
Streamlit app entry point for deployment.
This file is specifically for Streamlit Cloud deployment.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from app import main

if __name__ == "__main__":
    main()