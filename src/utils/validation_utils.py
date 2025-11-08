"""
Validation utilities for JSON file processing.

This module provides utilities for validating JSON files, including
detection of duplicate keys at any nesting level with accurate line number reporting.
"""

import json
import re
from typing import Any, List, Tuple, Dict, Optional, NamedTuple
from collections import defaultdict


class KeyOccurrence(NamedTuple):
    """Represents a single key occurrence in the JSON file."""
    path: str  # Dot-separated path (e.g., "parent.child")
    key: str   # The key name
    line: int  # Line number where the key appears


class DuplicateKeyDetector(json.JSONDecoder):
    """
    JSON decoder that detects and reports duplicate keys with accurate line numbers.

    Uses line-by-line parsing to build a complete map of all key occurrences
    with their scope paths and line numbers, then checks for duplicates within
    each scope independently.

    Example:
        >>> with open('file.json') as f:
        >>>     content = f.read()
        >>>     data = json.loads(content, cls=DuplicateKeyDetector)

    Raises:
        ValueError: If duplicate keys are found within the same object scope,
                   with accurate line numbers.
    """

    def __init__(self, *args, **kwargs):
        """Initialize decoder with duplicate detection hook and source tracking."""
        self._source = kwargs.pop('source', None)
        self._key_occurrences = []  # List of all key occurrences
        self._duplicates_found = []  # Store detected duplicates for error reporting
        super().__init__(object_pairs_hook=self._check_duplicates, *args, **kwargs)

    def decode(self, s: str, **kwargs) -> Any:
        """
        Decode JSON string with duplicate key detection.

        Args:
            s: JSON string to decode

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If duplicate keys are found
        """
        # First, parse line-by-line to build key occurrence map
        if self._source:
            self._key_occurrences = self._parse_line_by_line(self._source)
            duplicates = self._find_duplicates_in_occurrences()

            if duplicates:
                error_parts = self._build_error_messages(duplicates)
                raise ValueError('; '.join(error_parts))

        # Now do the actual JSON parsing
        return super().decode(s, **kwargs)

    def _check_duplicates(self, pairs: List[Tuple[str, Any]]) -> dict:
        """
        Simple hook that just builds the dictionary.
        Actual duplicate detection is done in decode() method.

        Args:
            pairs: List of (key, value) tuples from JSON parsing

        Returns:
            Dictionary constructed from pairs
        """
        result = {}
        for key, value in pairs:
            result[key] = value
        return result

    def _parse_line_by_line(self, content: str) -> List[KeyOccurrence]:
        """
        Parse JSON line-by-line to build a complete map of key occurrences.

        Args:
            content: JSON string content

        Returns:
            List of KeyOccurrence objects
        """
        occurrences = []
        lines = content.split('\n')
        path_stack = []  # Stack of keys representing current path
        key_pattern = re.compile(r'^\s*"([^"]+)"\s*:')

        for line_num, line in enumerate(lines, start=1):
            # Check for key definition FIRST (before processing braces)
            match = key_pattern.search(line)
            if match:
                key_name = match.group(1)
                # Build current path (exclude the current key itself)
                current_path = '.'.join(path_stack) if path_stack else 'root'
                occurrences.append(KeyOccurrence(path=current_path, key=key_name, line=line_num))

                # If this line opens a new object, push key onto path stack
                # Check if there's a { after the : (and OUTSIDE of quoted strings)
                after_colon = line.split(':', 1)[1] if ':' in line else ''
                # Only count { that's not inside a string value
                # Simple heuristic: if there's a { before any " after the :, it's structural
                if '{' in after_colon:
                    # Check if { appears before the opening quote of the value
                    brace_pos = after_colon.find('{')
                    quote_pos = after_colon.find('"')
                    if quote_pos == -1 or brace_pos < quote_pos:
                        # { appears before any quotes, so it's structural
                        path_stack.append(key_name)

            # Handle closing braces (only structural ones, not in string values)
            # Count } that appear outside of quoted strings
            close_count = self._count_structural_braces(line, '}')
            for _ in range(close_count):
                if path_stack:
                    path_stack.pop()

        return occurrences

    def _count_structural_braces(self, line: str, brace_char: str) -> int:
        """
        Count occurrences of a brace character that are NOT inside quoted strings.

        Args:
            line: The line to check
            brace_char: The brace character to count ('{' or '}')

        Returns:
            Count of structural (non-string) braces
        """
        count = 0
        in_string = False
        escaped = False

        for i, char in enumerate(line):
            if escaped:
                escaped = False
                continue

            if char == '\\':
                escaped = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if not in_string and char == brace_char:
                count += 1

        return count

    def _find_duplicates_in_occurrences(self) -> Dict[Tuple[str, str], List[int]]:
        """
        Find duplicate keys within each scope.

        Returns:
            Dictionary mapping (path, key) to list of line numbers for duplicates only
        """
        # Group occurrences by (path, key)
        grouped = defaultdict(list)
        for occ in self._key_occurrences:
            grouped[(occ.path, occ.key)].append(occ.line)

        # Filter to only duplicates (2+ occurrences)
        duplicates = {k: v for k, v in grouped.items() if len(v) >= 2}
        return duplicates

    def _build_error_messages(self, duplicates: Dict[Tuple[str, str], List[int]]) -> List[str]:
        """
        Build error messages for detected duplicates.

        Args:
            duplicates: Dictionary mapping (path, key) to list of duplicate line numbers

        Returns:
            List of error message strings
        """
        error_parts = []

        for (path, key), line_numbers in duplicates.items():
            original_line = line_numbers[0]
            duplicate_lines = line_numbers[1:]

            if len(duplicate_lines) == 1:
                error_parts.append(
                    f"Duplicate key {repr(key)} found on line {duplicate_lines[0]} "
                    f"(original on line {original_line})"
                )
            else:
                dup_lines_str = ', '.join(str(ln) for ln in duplicate_lines)
                error_parts.append(
                    f"Duplicate key {repr(key)} found on lines {dup_lines_str} "
                    f"(original on line {original_line})"
                )

        return error_parts


def load_json_with_duplicate_detection(content: str) -> Any:
    """
    Load JSON from string with enhanced duplicate key detection.

    Args:
        content: JSON string content

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If duplicate keys are found with line number details
        json.JSONDecodeError: If JSON syntax is invalid
    """
    decoder = DuplicateKeyDetector(source=content)
    return decoder.decode(content)
