"""
Validation utilities for JSON file processing.

This module provides utilities for validating JSON files, including
detection of duplicate keys at any nesting level with accurate line number reporting.
"""

import json
import re
from typing import Any, List, Tuple


class DuplicateKeyDetector(json.JSONDecoder):
    """
    JSON decoder that detects and reports duplicate keys with accurate line numbers.

    Uses object_pairs_hook for correct duplicate detection at any nesting level,
    then searches for line numbers only when duplicates are found.

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
        self._duplicates_found: List[str] = []
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
        self._duplicates_found = []

        # Parse with object_pairs_hook - handles nesting correctly
        result = super().decode(s, **kwargs)

        # If duplicates found, search for line numbers
        if self._duplicates_found and self._source:
            error_messages = self._find_duplicate_lines(self._source, self._duplicates_found)
            if error_messages:
                raise ValueError('; '.join(error_messages))

        return result

    def _check_duplicates(self, pairs: List[Tuple[str, Any]]) -> dict:
        """
        Check for duplicate keys within a single object scope.

        The JSON parser calls this hook once per object, handling all nesting
        and array scopes correctly.

        Args:
            pairs: List of (key, value) tuples from JSON parsing

        Returns:
            Dictionary constructed from pairs
        """
        seen = {}
        for key, value in pairs:
            if key in seen:
                self._duplicates_found.append(key)
            seen[key] = value
        return seen

    def _find_duplicate_lines(self, content: str, duplicate_keys: List[str]) -> List[str]:
        """
        Find line numbers for duplicate keys.

        Args:
            content: JSON source content
            duplicate_keys: List of keys that were detected as duplicates

        Returns:
            List of error message strings with line numbers
        """
        errors = []
        lines = content.split('\n')

        for dup_key in set(duplicate_keys):
            pattern = re.compile(rf'^\s*"{re.escape(dup_key)}"\s*:')
            line_nums = [i + 1 for i, line in enumerate(lines) if pattern.match(line)]

            if len(line_nums) >= 2:
                errors.append(
                    f"Duplicate key '{dup_key}' found on lines {', '.join(map(str, line_nums))}"
                )

        return errors


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
