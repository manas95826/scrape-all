#!/usr/bin/env python3
"""
Simple runner script for the web scraper application.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())
