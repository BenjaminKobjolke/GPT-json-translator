"""
JSON Attribute Remover - Utility to remove specified attributes from JSON translation files.
"""
import os
import json
import sys
import argparse
from typing import List, Set, Any, Dict, Union
from pathlib import Path


# Source file patterns to always exclude from processing in directory mode
SOURCE_FILE_PATTERNS = {'en.json', 'app_en.arb'}


def load_attributes_to_remove(attributes_file: str) -> Union[List[str], Dict[str, Any]]:
    """
    Load the attributes to remove from a JSON file.

    Supports two formats:
    1. List format (legacy): ["key1", "key2"] - removes top-level keys only
    2. Dict format (nested): {"key1": true, "nested": {"key2": true}} - supports nested removal
       - Use `true` to mark a key for removal
       - Use `"*"` to remove all keys under a parent
       - Nest objects to remove nested keys

    Args:
        attributes_file: Path to the JSON file containing attributes to remove

    Returns:
        List of attribute names (legacy) or dict with nested structure (new format)

    Raises:
        FileNotFoundError: If the attributes file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the JSON is neither a list nor a dict
    """
    attributes_path = Path(attributes_file)

    if not attributes_path.is_file():
        raise FileNotFoundError(f"Attributes file '{attributes_file}' does not exist")

    try:
        with attributes_path.open('r', encoding='utf-8') as file:
            attributes_to_remove = json.load(file)

        # Validate format
        if not isinstance(attributes_to_remove, (list, dict)):
            raise ValueError("Attributes file must contain a JSON array or object")

        return attributes_to_remove

    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse attributes file: {str(e)}",
            e.doc, e.pos
        )


def is_file_or_directory(path: str) -> str:
    """
    Determine if the input path is a file or directory.

    Args:
        path: Path to check

    Returns:
        'file' if path points to a file, 'directory' if it points to a directory

    Raises:
        FileNotFoundError: If the path doesn't exist
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"Path '{path}' does not exist")

    if path_obj.is_file():
        return 'file'
    elif path_obj.is_dir():
        return 'directory'
    else:
        raise ValueError(f"Path '{path}' is neither a file nor a directory")


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


def remove_attributes_recursive(
    data: Dict[str, Any],
    attributes_pattern: Any,
    current_path: str = "",
    file_name: str = ""
) -> int:
    """
    Recursively remove attributes from nested JSON structure.

    Args:
        data: The JSON data to modify (dict)
        attributes_pattern: Removal pattern (dict with nested structure, True, or "*")
        current_path: Current path for logging (e.g., "viewSettings.imageViewer")
        file_name: Name of file being processed (for logging)

    Returns:
        Number of attributes removed
    """
    removed_count = 0

    # If pattern is "*", remove all keys at this level
    if attributes_pattern == "*":
        keys_to_remove = list(data.keys())
        for key in keys_to_remove:
            path = f"{current_path}.{key}" if current_path else key
            print(f"  Removing '{path}' from {file_name}")
            del data[key]
            removed_count += 1
        return removed_count

    # If pattern is not a dict, nothing to process
    if not isinstance(attributes_pattern, dict):
        return 0

    # Process each key in the attributes pattern
    keys_to_remove = []
    for key, pattern_value in attributes_pattern.items():
        if key not in data:
            continue

        path = f"{current_path}.{key}" if current_path else key

        # If pattern value is True, mark for removal
        if pattern_value is True:
            print(f"  Removing '{path}' from {file_name}")
            keys_to_remove.append(key)
            removed_count += 1

        # If pattern value is "*", remove all nested keys
        elif pattern_value == "*":
            if isinstance(data[key], dict):
                nested_removed = remove_attributes_recursive(
                    data[key], "*", path, file_name
                )
                removed_count += nested_removed
                # Mark parent for removal if it's now empty
                if not data[key]:
                    keys_to_remove.append(key)
            else:
                print(f"  Removing '{path}' from {file_name}")
                keys_to_remove.append(key)
                removed_count += 1

        # If pattern value is a dict, recurse into nested structure
        elif isinstance(pattern_value, dict) and isinstance(data[key], dict):
            nested_removed = remove_attributes_recursive(
                data[key], pattern_value, path, file_name
            )
            removed_count += nested_removed
            # Mark parent for removal if it's now empty
            if not data[key]:
                keys_to_remove.append(key)

    # Remove marked keys
    for key in keys_to_remove:
        del data[key]

    return removed_count


def cleanup_empty_parents(data: Dict[str, Any], file_name: str = "", current_path: str = "") -> int:
    """
    Recursively remove empty dict values from nested JSON structure.

    Args:
        data: The JSON data to clean
        file_name: Name of file being processed (for logging)
        current_path: Current path for logging

    Returns:
        Number of empty parents removed
    """
    removed_count = 0
    keys_to_remove = []

    for key, value in list(data.items()):
        path = f"{current_path}.{key}" if current_path else key

        if isinstance(value, dict):
            # Recursively clean nested dicts
            nested_removed = cleanup_empty_parents(value, file_name, path)
            removed_count += nested_removed

            # If nested dict is now empty, mark for removal
            if not value:
                print(f"  Cleaned up empty parent '{path}' from {file_name}")
                keys_to_remove.append(key)
                removed_count += 1

    # Remove marked keys
    for key in keys_to_remove:
        del data[key]

    return removed_count


def remove_attributes_from_file(
    file_path: Path,
    attributes_to_remove: Any
) -> int:
    """
    Remove specified attributes from a single JSON file.

    Supports two formats:
    1. List format (legacy): ["key1", "key2"] - removes top-level keys only
    2. Dict format (nested): {"key1": true, "nested": {"key2": true}} - supports nested removal

    Args:
        file_path: Path to the JSON file
        attributes_to_remove: List of attributes or dict with nested structure

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

    # Handle legacy list format (top-level keys only)
    if isinstance(attributes_to_remove, list):
        for attribute in attributes_to_remove:
            if attribute in data:
                print(f"  Removing '{attribute}' from {file_path.name}")
                del data[attribute]
                removed_count += 1

    # Handle new dict format (nested structure)
    elif isinstance(attributes_to_remove, dict):
        removed_count = remove_attributes_recursive(
            data, attributes_to_remove, "", file_path.name
        )
        # Clean up empty parents after removal
        cleanup_count = cleanup_empty_parents(data, file_path.name)
        removed_count += cleanup_count

    # Write file if any changes were made
    if removed_count > 0:
        with file_path.open('w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    return removed_count


def remove_attributes_excluding_file(
    file_to_exclude: str,
    attributes_file: str
) -> None:
    """
    Remove specified attributes from all JSON files in the directory EXCEPT the specified file.

    Args:
        file_to_exclude: Path to the JSON file to exclude from processing
        attributes_file: Path to the JSON file with attributes to remove

    Raises:
        FileNotFoundError: If file doesn't exist or directory doesn't exist
    """
    file_path = Path(file_to_exclude)

    if not file_path.is_file():
        raise FileNotFoundError(f"File '{file_to_exclude}' does not exist")

    directory_path = file_path.parent
    excluded_filename = file_path.name

    attributes_to_remove = load_attributes_to_remove(attributes_file)
    print(f"Loaded {len(attributes_to_remove)} attributes to remove")
    print(f"Processing JSON files in: {directory_path}")
    print(f"Excluding: {excluded_filename}\n")

    total_files_processed = 0
    total_attributes_removed = 0

    for file_path_iter in directory_path.iterdir():
        # Only exclude the specified file, process all other JSON files (including source files)
        if file_path_iter.name.endswith('.json') and file_path_iter.name != excluded_filename:
            print(f"Processing: {file_path_iter.name}")
            try:
                removed = remove_attributes_from_file(file_path_iter, attributes_to_remove)
                total_files_processed += 1
                total_attributes_removed += removed
                if removed == 0:
                    print(f"  No matching attributes found")
            except Exception as e:
                print(f"  Error processing {file_path_iter.name}: {str(e)}")

    print(f"\nSummary:")
    print(f"  Files processed: {total_files_processed}")
    print(f"  Total attributes removed: {total_attributes_removed}")


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
        description='Remove specified attributes from JSON translation files. '
                    'Supports two modes: directory mode (excludes en.json by default) '
                    'and file mode (excludes only the specified file).'
    )
    parser.add_argument(
        'path',
        help='Directory or file path. If directory: processes all JSON files except source files. '
             'If file: processes all JSON files in the directory except the specified file.'
    )
    parser.add_argument(
        'attributes_file',
        help='JSON file with attributes to remove. Supports two formats: '
             '1) Simple list: ["key1", "key2"] for top-level keys. '
             '2) Nested object: {"parent": {"child": true}} for nested keys. '
             'Use "*" for wildcards: {"parent": "*"} removes all nested keys.'
    )
    parser.add_argument(
        '--exclude-source',
        default=None,
        help='Additional source file pattern to exclude in directory mode (e.g., app_en.arb). '
             'en.json is always excluded in directory mode.'
    )

    args = parser.parse_args()

    try:
        # Determine if path is a file or directory
        path_type = is_file_or_directory(args.path)

        if path_type == 'file':
            # File mode: exclude only the specified file
            remove_attributes_excluding_file(
                args.path,
                args.attributes_file
            )
        else:
            # Directory mode: always exclude en.json, plus any additional patterns
            source_patterns = SOURCE_FILE_PATTERNS.copy()
            if args.exclude_source:
                source_patterns.add(args.exclude_source)

            remove_attributes_from_json_files(
                args.path,
                args.attributes_file,
                source_patterns
            )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
