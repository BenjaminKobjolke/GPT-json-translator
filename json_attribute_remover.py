"""
JSON Attribute Remover - Utility to remove specified attributes from JSON translation files.
"""
import os
import json
import sys
import argparse
from typing import List, Set
from pathlib import Path


# Source file patterns to exclude from processing
SOURCE_FILE_PATTERNS = {'en.json', 'app_en.arb'}


def load_attributes_to_remove(attributes_file: str) -> List[str]:
    """
    Load the list of attributes to remove from a JSON file.

    Args:
        attributes_file: Path to the JSON file containing attributes to remove

    Returns:
        List of attribute names to remove

    Raises:
        FileNotFoundError: If the attributes file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the JSON doesn't contain a list
    """
    attributes_path = Path(attributes_file)

    if not attributes_path.is_file():
        raise FileNotFoundError(f"Attributes file '{attributes_file}' does not exist")

    try:
        with attributes_path.open('r', encoding='utf-8') as file:
            attributes_to_remove = json.load(file)

        if not isinstance(attributes_to_remove, list):
            raise ValueError("Attributes file must contain a JSON array")

        return attributes_to_remove

    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse attributes file: {str(e)}",
            e.doc, e.pos
        )


def should_process_file(filename: str, source_patterns: Set[str]) -> bool:
    """
    Determine if a JSON file should be processed.

    Args:
        filename: Name of the file
        source_patterns: Set of source file patterns to exclude

    Returns:
        True if the file should be processed, False otherwise
    """
    return filename.endswith('.json') and filename not in source_patterns


def remove_attributes_from_file(
    file_path: Path,
    attributes_to_remove: List[str]
) -> int:
    """
    Remove specified attributes from a single JSON file.

    Args:
        file_path: Path to the JSON file
        attributes_to_remove: List of attributes to remove

    Returns:
        Number of attributes removed

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON
        IOError: If there's an error reading or writing the file
    """
    try:
        with file_path.open('r', encoding='utf-8') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Error parsing {file_path}: {str(e)}",
            e.doc, e.pos
        )

    removed_count = 0
    for attribute in attributes_to_remove:
        if attribute in data:
            print(f"  Removing '{attribute}' from {file_path.name}")
            del data[attribute]
            removed_count += 1

    if removed_count > 0:
        with file_path.open('w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    return removed_count


def remove_attributes_from_json_files(
    directory: str,
    attributes_file: str,
    source_patterns: Set[str] = None
) -> None:
    """
    Remove specified attributes from all JSON files in a directory.

    Args:
        directory: Path to the directory containing JSON files
        attributes_file: Path to the JSON file with attributes to remove
        source_patterns: Set of source file patterns to exclude (default: SOURCE_FILE_PATTERNS)

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if source_patterns is None:
        source_patterns = SOURCE_FILE_PATTERNS

    directory_path = Path(directory)

    if not directory_path.is_dir():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    attributes_to_remove = load_attributes_to_remove(attributes_file)
    print(f"Loaded {len(attributes_to_remove)} attributes to remove")
    print(f"Processing JSON files in: {directory_path}\n")

    total_files_processed = 0
    total_attributes_removed = 0

    for file_path in directory_path.iterdir():
        if should_process_file(file_path.name, source_patterns):
            print(f"Processing: {file_path.name}")
            try:
                removed = remove_attributes_from_file(file_path, attributes_to_remove)
                total_files_processed += 1
                total_attributes_removed += removed
                if removed == 0:
                    print(f"  No matching attributes found")
            except Exception as e:
                print(f"  Error processing {file_path.name}: {str(e)}")

    print(f"\nSummary:")
    print(f"  Files processed: {total_files_processed}")
    print(f"  Total attributes removed: {total_attributes_removed}")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Remove specified attributes from JSON translation files'
    )
    parser.add_argument(
        'directory',
        help='Directory containing JSON files to process'
    )
    parser.add_argument(
        'attributes_file',
        help='JSON file containing list of attributes to remove'
    )
    parser.add_argument(
        '--exclude-source',
        default='en.json',
        help='Source file pattern to exclude (default: en.json)'
    )

    args = parser.parse_args()

    try:
        source_patterns = {args.exclude_source}
        remove_attributes_from_json_files(
            args.directory,
            args.attributes_file,
            source_patterns
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
