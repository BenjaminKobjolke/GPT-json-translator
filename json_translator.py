#!/usr/bin/env python
"""
JSON Translator - Entry point script.
This script serves as a wrapper around the refactored JSON Translator module.
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main function from the src package
from src.main import run_translation

if __name__ == "__main__":
    # Run the translation process
    run_translation()
