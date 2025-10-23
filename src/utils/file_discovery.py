"""
File system discovery utilities for the JSON Translator.
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Literal


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
