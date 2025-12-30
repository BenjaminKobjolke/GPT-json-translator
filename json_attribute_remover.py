"""
JSON Attribute Remover - Utility to remove specified attributes from JSON translation files.
"""
import os
import json
import sys
import argparse
from typing import List, Set, Any, Dict, Union, Optional
from pathlib import Path

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False


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


def collect_all_attributes_recursive(data: Dict[str, Any], prefix: str = "") -> Set[str]:
    """
    Recursively collect all attribute paths from a JSON structure using dot notation.

    Args:
        data: The JSON data to scan
        prefix: Current path prefix for nested keys

    Returns:
        Set of attribute paths (e.g., {"title", "settings", "settings.theme"})
    """
    attributes = set()
    for key, value in data.items():
        if key.startswith("_"):  # Skip hint keys
            continue
        full_path = f"{prefix}.{key}" if prefix else key
        attributes.add(full_path)
        if isinstance(value, dict):
            attributes.update(collect_all_attributes_recursive(value, full_path))
    return attributes


def collect_all_attributes(directory: Path, exclude_patterns: Set[str]) -> List[str]:
    """
    Scan all JSON files in directory and collect unique attribute paths.

    Args:
        directory: Directory to scan
        exclude_patterns: Set of filenames to exclude

    Returns:
        Sorted list of unique attribute paths
    """
    all_attributes = set()
    for file_path in directory.iterdir():
        if file_path.suffix == ".json" and file_path.name not in exclude_patterns:
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    all_attributes.update(collect_all_attributes_recursive(data))
            except (json.JSONDecodeError, IOError):
                continue  # Skip invalid files
    return sorted(all_attributes)


def collect_attributes_from_file(file_path: Path) -> List[str]:
    """
    Collect all attribute paths from a single JSON file.

    Args:
        file_path: Path to the JSON file to scan

    Returns:
        Sorted list of unique attribute paths

    Raises:
        ValueError: If the file cannot be read or parsed
    """
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return sorted(collect_all_attributes_recursive(data))
        return []
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Error reading {file_path}: {e}")


def collect_attributes_with_values_recursive(
    data: Dict[str, Any],
    prefix: str = ""
) -> Dict[str, Any]:
    """
    Recursively collect all attribute paths with their values from a JSON structure.

    Args:
        data: The JSON data to scan
        prefix: Current path prefix for nested keys

    Returns:
        Dict mapping attribute paths to their values
    """
    attributes = {}
    for key, value in data.items():
        if key.startswith("_"):  # Skip hint keys
            continue
        full_path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            attributes[full_path] = "{...}"  # Show placeholder for nested objects
            attributes.update(collect_attributes_with_values_recursive(value, full_path))
        else:
            attributes[full_path] = value
    return attributes


def collect_attributes_with_values_from_file(file_path: Path) -> Dict[str, Any]:
    """
    Collect all attribute paths with values from a single JSON file.

    Args:
        file_path: Path to the JSON file to scan

    Returns:
        Dict mapping attribute paths to their values

    Raises:
        ValueError: If the file cannot be read or parsed
    """
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return collect_attributes_with_values_recursive(data)
        return {}
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Error reading {file_path}: {e}")


def interactive_select_with_arrows(attributes: Dict[str, Any]) -> Optional[str]:
    """
    Interactive selection with arrow keys using questionary library.

    Args:
        attributes: Dict mapping attribute paths to their values

    Returns:
        Selected attribute path, or None if user quits
    """
    if not attributes:
        print("No attributes found in JSON files.")
        return None

    if not QUESTIONARY_AVAILABLE:
        print("Error: questionary module not installed. Run: pip install questionary", file=sys.stderr)
        sys.exit(1)

    # Build display options with values
    items = sorted(attributes.keys())
    choices = []
    for key in items:
        value = str(attributes[key])
        # Truncate long values
        if len(value) > 50:
            value = value[:47] + "..."
        choices.append(questionary.Choice(title=f"{key}: \"{value}\"", value=key))

    selected = questionary.select(
        "Select attribute to remove:",
        choices=choices,
    ).ask()

    return selected


def interactive_select_attribute(attributes: List[str]) -> Optional[str]:
    """
    Display numbered list of attributes and let user select one to remove.

    Args:
        attributes: List of attribute paths to display

    Returns:
        Selected attribute path, or None if user quits
    """
    if not attributes:
        print("No attributes found in JSON files.")
        return None

    print("\nAvailable attributes found in JSON files:\n")
    for i, attr in enumerate(attributes, 1):
        print(f"  {i}. {attr}")
    print()

    while True:
        choice = input("Enter the number of the attribute to remove (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(attributes):
                return attributes[index]
            print(f"Please enter a number between 1 and {len(attributes)}")
        except ValueError:
            print("Invalid input. Enter a number or 'q' to quit.")


def confirm_removal(attribute: str) -> bool:
    """
    Ask user to confirm attribute removal.

    Args:
        attribute: The attribute path that will be removed

    Returns:
        True if user confirms, False otherwise
    """
    response = input(f"Are you sure you want to remove '{attribute}' from all files? (y/n): ").strip().lower()
    return response == 'y'


def build_attributes_dict_from_path(attribute_path: str) -> Dict[str, Any]:
    """
    Convert a dot-notation path to a nested dict structure for removal.

    Args:
        attribute_path: Dot-notation path (e.g., "settings.theme")

    Returns:
        Nested dict structure (e.g., {"settings": {"theme": True}})
    """
    parts = attribute_path.split(".")
    if len(parts) == 1:
        return {parts[0]: True}

    # Build nested structure from inside out
    result: Dict[str, Any] = {parts[-1]: True}
    for part in reversed(parts[:-1]):
        result = {part: result}
    return result


def deep_merge_dicts(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two nested dicts, combining nested structures.

    Args:
        base: Base dictionary
        overlay: Dictionary to merge on top

    Returns:
        Merged dictionary with nested structures combined
    """
    result = base.copy()
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def convert_list_to_nested_dict(attributes: List[str]) -> Dict[str, Any]:
    """
    Convert list of dot-notation paths to nested dict structure.

    Supports both simple keys ("title") and dot-notation paths ("queue.clearAll").

    Args:
        attributes: List of attribute paths

    Returns:
        Nested dict structure for removal
    """
    result: Dict[str, Any] = {}
    for attr in attributes:
        attr_dict = build_attributes_dict_from_path(attr)
        result = deep_merge_dicts(result, attr_dict)
    return result


def remove_attributes_from_file(
    file_path: Path,
    attributes_to_remove: Any
) -> int:
    """
    Remove specified attributes from a single JSON file.

    Supports two formats:
    1. List format: ["key1", "nested.key2"] - supports dot-notation for nested keys
    2. Dict format (nested): {"key1": true, "nested": {"key2": true}} - explicit nested structure

    Args:
        file_path: Path to the JSON file
        attributes_to_remove: List of attributes (with dot-notation) or dict with nested structure

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

    # Convert list format to dict format for unified processing
    if isinstance(attributes_to_remove, list):
        attributes_to_remove = convert_list_to_nested_dict(attributes_to_remove)

    # Process using recursive removal (handles nested structures)
    if isinstance(attributes_to_remove, dict):
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


def remove_attributes_excluding_file_with_attrs(
    file_to_exclude: str,
    attributes_to_remove: Any
) -> None:
    """
    Remove specified attributes from all JSON files in the directory EXCEPT the specified file.

    Args:
        file_to_exclude: Path to the JSON file to exclude from processing
        attributes_to_remove: List of attributes or dict with nested structure (already loaded)

    Raises:
        FileNotFoundError: If file doesn't exist or directory doesn't exist
    """
    file_path = Path(file_to_exclude)

    if not file_path.is_file():
        raise FileNotFoundError(f"File '{file_to_exclude}' does not exist")

    directory_path = file_path.parent
    excluded_filename = file_path.name

    attr_count = len(attributes_to_remove) if isinstance(attributes_to_remove, (list, dict)) else 0
    print(f"Removing {attr_count} attribute(s)")
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


def remove_attributes_from_json_files_with_attrs(
    directory: str,
    attributes_to_remove: Any,
    source_patterns: Set[str] = None
) -> None:
    """
    Remove specified attributes from all JSON files in a directory.

    Args:
        directory: Path to the directory containing JSON files
        attributes_to_remove: List of attributes or dict with nested structure (already loaded)
        source_patterns: Set of source file patterns to exclude (default: SOURCE_FILE_PATTERNS)

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if source_patterns is None:
        source_patterns = SOURCE_FILE_PATTERNS

    directory_path = Path(directory)

    if not directory_path.is_dir():
        raise FileNotFoundError(f"Directory '{directory}' does not exist")

    attr_count = len(attributes_to_remove) if isinstance(attributes_to_remove, (list, dict)) else 0
    print(f"Removing {attr_count} attribute(s)")
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
        nargs='?',
        default=None,
        help='JSON file with attributes to remove. If not provided, interactive mode is used. '
             'Supports two formats: '
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
        path = Path(args.path)
        path_type = is_file_or_directory(args.path)

        # Determine source patterns for file exclusion
        if path_type == 'file':
            directory = path.parent
            exclude_patterns = {path.name}
        else:
            directory = path
            exclude_patterns = SOURCE_FILE_PATTERNS.copy()
            if args.exclude_source:
                exclude_patterns.add(args.exclude_source)

        # Check if interactive mode or file-based mode
        if args.attributes_file:
            # File-based mode: load attributes from file
            attributes_to_remove = load_attributes_to_remove(args.attributes_file)
        else:
            # Interactive mode: let user select attribute to remove
            # Determine source file for attribute scanning
            if path_type == 'file':
                # File mode: scan ONLY the specified file for attributes
                source_file = path
            else:
                # Directory mode: default to en.json
                source_file = directory / "en.json"
                if not source_file.exists():
                    print(f"Error: Source file '{source_file}' not found.", file=sys.stderr)
                    sys.exit(1)

            all_attributes = collect_attributes_with_values_from_file(source_file)
            selected = interactive_select_with_arrows(all_attributes)

            if selected is None:
                print("No attribute selected. Exiting.")
                return

            if not confirm_removal(selected):
                print("Removal cancelled.")
                return

            attributes_to_remove = build_attributes_dict_from_path(selected)

        # Process files based on mode
        if path_type == 'file':
            # File mode: exclude only the specified file
            remove_attributes_excluding_file_with_attrs(
                args.path,
                attributes_to_remove
            )
        else:
            # Directory mode: process all JSON files except source patterns
            remove_attributes_from_json_files_with_attrs(
                args.path,
                attributes_to_remove,
                exclude_patterns
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
