"""
Helper functions for the JSON Translator.
"""
import os
import sys
import re
from pathlib import Path
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
        - source_language: The detected language code (e.g., 'en', 'en-US')
        - filename_pattern: The pattern (e.g., 'app_{lang}.arb') if ARB, else None.
    """
    filename = os.path.basename(file_path)
    # Regex to match 'app_{lang}.arb' pattern
    arb_match = re.match(r"^(.*?)_([a-zA-Z]{2}(?:_[a-zA-Z]{2})?)\.arb$", filename)

    if arb_match:
        base_name = arb_match.group(1)
        source_language = arb_match.group(2).replace('_', '-') # Normalize to hyphen like 'en-US'
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


def print_hints_summary(global_hints: Dict[str, str], field_hints: Dict[str, str]) -> None:
    """
    Print a summary of the translation hints.

    Args:
        global_hints: Dictionary of global translation hints
        field_hints: Dictionary of field-specific translation hints
    """
    total_hints = len(global_hints) + len(field_hints)

    if total_hints > 0:
        print(f"Found {total_hints} translation hint(s):")

        if global_hints:
            print(f"  Global hints ({len(global_hints)}):")
            for key, value in global_hints.items():
                print(f"    - {key}: {value}")

        if field_hints:
            print(f"  Field-specific hints ({len(field_hints)}):")
            for field_name, hint_value in field_hints.items():
                print(f"    - {field_name}: {hint_value}")


def discover_override_files(
    base_path: str,
    file_type: Literal['json', 'arb'],
    filename_pattern: Optional[str] = None
) -> List[str]:
    """
    Discover all override files in the _overrides directory.

    Args:
        base_path: Base path where the source file is located
        file_type: The type of the file ('json' or 'arb')
        filename_pattern: The filename pattern for ARB files (e.g., 'app_{lang}.arb')

    Returns:
        List of language codes for which override files exist
    """
    overrides_dir = os.path.join(os.path.dirname(base_path), "_overrides")

    if not os.path.exists(overrides_dir):
        return []

    language_codes = []

    try:
        for filename in os.listdir(overrides_dir):
            file_path = os.path.join(overrides_dir, filename)

            # Skip directories
            if not os.path.isfile(file_path):
                continue

            # Parse filename based on file type
            if file_type == 'arb':
                # Match ARB pattern like 'app_de.arb'
                if filename_pattern:
                    # Extract the base pattern (e.g., 'app' from 'app_{lang}.arb')
                    base_pattern = filename_pattern.replace('_{lang}.arb', '')
                    match = re.match(rf"^{re.escape(base_pattern)}_([a-zA-Z]{{2}}(?:_[a-zA-Z]{{2}})?)\\.arb$", filename)
                    if match:
                        lang_code = match.group(1).replace('_', '-')
                        language_codes.append(lang_code)
            elif file_type == 'json':
                # Match JSON pattern like 'de-DE.json' or 'de.json'
                match = re.match(r"^([a-zA-Z]{2}(?:-[a-zA-Z]{2})?)\\.json$", filename)
                if match:
                    language_codes.append(match.group(1))

    except OSError as e:
        print(f"Error reading overrides directory: {str(e)}")
        return []

    return language_codes


def find_directories_with_source_file(base_dir: str, source_filename: str) -> List[str]:
    """
    Recursively find all directories containing the specified source file.

    Args:
        base_dir: The base directory to start searching from
        source_filename: The filename to search for (e.g., 'en.json')

    Returns:
        List of directory paths containing the source file
    """
    matching_dirs = []
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"Error: Directory not found at {base_dir}")
        return []

    if not base_path.is_dir():
        print(f"Error: Path is not a directory: {base_dir}")
        return []

    # Recursively search for the source file
    for dirpath, _, filenames in os.walk(base_dir):
        if source_filename in filenames:
            matching_dirs.append(dirpath)

    return matching_dirs


def has_only_source_file(directory: str, source_filename: str, file_type: Literal['json', 'arb']) -> bool:
    """
    Check if a directory contains only the source file and no translation files.

    Args:
        directory: The directory to check
        source_filename: The source filename (e.g., 'en.json' or 'app_en.arb')
        file_type: The type of file ('json' or 'arb')

    Returns:
        True if only the source file exists (no translations), False otherwise
    """
    try:
        files = os.listdir(directory)
    except OSError as e:
        print(f"Error reading directory {directory}: {str(e)}")
        return False

    # Filter for relevant files based on file type
    if file_type == 'json':
        # Look for files matching pattern: xx.json or xx-XX.json
        translation_pattern = re.compile(r"^[a-zA-Z]{2}(?:-[a-zA-Z]{2})?\.json$")
        relevant_files = [f for f in files if translation_pattern.match(f)]
    elif file_type == 'arb':
        # Look for files matching pattern: prefix_xx.arb or prefix_xx_XX.arb
        # Extract the base pattern from source filename
        arb_match = re.match(r"^(.*?)_[a-zA-Z]{2}(?:_[a-zA-Z]{2})?\.arb$", source_filename)
        if arb_match:
            base_pattern = arb_match.group(1)
            translation_pattern = re.compile(rf"^{re.escape(base_pattern)}_[a-zA-Z]{{2}}(?:_[a-zA-Z]{{2}})?\.arb$")
            relevant_files = [f for f in files if translation_pattern.match(f)]
        else:
            # Fallback if pattern doesn't match
            relevant_files = [f for f in files if f.endswith('.arb')]
    else:
        return False

    # Check if only the source file exists
    return len(relevant_files) == 1 and source_filename in relevant_files
