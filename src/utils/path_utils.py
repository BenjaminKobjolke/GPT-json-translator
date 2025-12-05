"""
Path and filename utilities for the JSON Translator.
"""
import os
import sys
import re
from typing import Optional, Tuple, Literal


def get_input_path(cli_arg: Optional[str] = None, config_path: Optional[str] = None) -> str:
    """
    Determine the input path for the source JSON file.

    Args:
        cli_arg: Command line argument for the file path
        config_path: Path from configuration

    Returns:
        The resolved input path

    Raises:
        SystemExit: If the path doesn't exist
    """
    # First priority: command line argument
    if cli_arg:
        input_path = cli_arg
    # Second priority: configuration
    elif config_path:
        input_path = config_path
    # Last resort: prompt user
    else:
        input_path = input("Enter the path to the source JSON file: ")

    print(f"Reading input file from {input_path}")

    # Check if path exists
    if not os.path.exists(input_path):
        print(f"Error: Path not found at {input_path}")
        sys.exit(1)

    return input_path


def analyze_input_filename(file_path: str) -> Tuple[Literal['json', 'arb', 'xml'], Optional[str], Optional[str]]:
    """
    Analyzes the input filename to determine file type, source language, and pattern.

    Args:
        file_path: The path to the input file.

    Returns:
        A tuple containing:
        - file_type: 'json', 'arb', or 'xml'
        - source_language: The detected language code (e.g., 'en', 'en-US'), or None for XML
        - filename_pattern: The pattern (e.g., 'app_{lang}.arb') if ARB, filename if XML, else None.
    """
    filename = os.path.basename(file_path)
    # Regex to match 'app_{lang}.arb' pattern
    arb_match = re.match(r"^(.*?)_([a-zA-Z]{2}(?:_[a-zA-Z]{2})?)\.arb$", filename)

    if arb_match:
        base_name = arb_match.group(1)
        source_language = arb_match.group(2).replace('_', '-')  # Normalize to hyphen like 'en-US'
        filename_pattern = f"{base_name}_{{lang}}.arb"
        return 'arb', source_language, filename_pattern
    elif filename.lower().endswith('.json'):
        # Try to extract language code from JSON filename (e.g., 'en.json', 'de-DE.json')
        json_match = re.match(r"^([a-zA-Z]{2}(?:-[a-zA-Z]{2})?)\.json$", filename)
        if json_match:
            source_language = json_match.group(1)
            return 'json', source_language, None
        else:
            # JSON file without language code in name
            return 'json', None, None
    elif filename.lower().endswith('.xml'):
        # Android XML string files (e.g., res/values/strings.xml)
        parent_dir = os.path.basename(os.path.dirname(file_path))
        if parent_dir == 'values':
            # Standard Android values directory, source language assumed to be default
            return 'xml', None, filename
        else:
            print(f"Warning: XML file not in 'values/' directory: {filename}")
            return 'xml', None, filename
    else:
        # Default or handle other cases if necessary
        print(f"Warning: Unrecognized file format for {filename}. Assuming standard JSON.")
        return 'json', None, None
