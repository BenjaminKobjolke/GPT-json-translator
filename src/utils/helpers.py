"""
Helper functions for the JSON Translator.
"""
import os
import sys
import re
from typing import Dict, Any, List, Optional, Tuple, Literal


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


def analyze_input_filename(file_path: str) -> Tuple[Literal['json', 'arb'], Optional[str], Optional[str]]:
    """
    Analyzes the input filename to determine file type, source language, and pattern.

    Args:
        file_path: The path to the input file.

    Returns:
        A tuple containing:
        - file_type: 'json' or 'arb'
        - source_language: The detected language code (e.g., 'en') if ARB, else None.
        - filename_pattern: The pattern (e.g., 'app_{lang}.arb') if ARB, else None.
    """
    filename = os.path.basename(file_path)
    # Regex to match 'app_{lang}.arb' pattern
    match = re.match(r"^(.*?)_([a-zA-Z]{2}(?:_[a-zA-Z]{2})?)\.arb$", filename)

    if match:
        base_name = match.group(1)
        source_language = match.group(2).replace('_', '-') # Normalize to hyphen like 'en-US'
        filename_pattern = f"{base_name}_{{lang}}.arb"
        return 'arb', source_language, filename_pattern
    elif filename.lower().endswith('.json'):
        # Assuming standard JSON files don't encode language in the name this way
        return 'json', None, None
    else:
        # Default or handle other cases if necessary
        print(f"Warning: Unrecognized file format for {filename}. Assuming standard JSON.")
        return 'json', None, None


def parse_language_code(full_language_code: str) -> str:
    """
    Extract the base language code from a full language code.
    
    Args:
        full_language_code: Full language code (e.g., 'en-US')
        
    Returns:
        Base language code (e.g., 'en')
    """
    return full_language_code.split('-')[0]


def print_translation_summary(language_code: str, keys_count: int) -> None:
    """
    Print a summary of the translation task.
    
    Args:
        language_code: Language code being translated
        keys_count: Number of keys to translate
    """
    if keys_count > 0:
        print(f"Processing {language_code}: {keys_count} keys to translate")
    else:
        print(f"Processing {language_code}: No new keys to translate")


def print_hints_summary(hints: Dict[str, str]) -> None:
    """
    Print a summary of the translation hints.
    
    Args:
        hints: Dictionary of translation hints
    """
    if hints:
        print(f"Found {len(hints)} translation hints:")
        for key, value in hints.items():
            print(f"  - {key}: {value}")
