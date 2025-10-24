"""
Dictionary utility functions for deep comparison and merging.
"""
from typing import Dict, Any


def deep_diff(source: Dict[str, Any], existing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively find keys in source that are missing in existing.

    For nested dictionaries, this function preserves the structure and only
    includes keys/nested-keys that are missing (not present in existing).

    Note: This function only checks for missing keys, not for different values.
    If a key exists in both dictionaries, it is not included in the diff unless
    it's a dict and has missing nested keys.

    Args:
        source: Source dictionary to compare from
        existing: Existing dictionary to compare against

    Returns:
        Dictionary containing only the keys that are missing. Returns empty dict
        if all keys exist in existing.

    Examples:
        >>> source = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> existing = {"a": 1, "b": {"c": 2}}
        >>> deep_diff(source, existing)
        {"b": {"d": 3}}

        >>> source = {"a": 1, "b": {"c": 2}}
        >>> existing = {"a": 1}
        >>> deep_diff(source, existing)
        {"b": {"c": 2}}

        >>> source = {"a": 1, "b": 2}
        >>> existing = {"a": 5, "b": 10}  # Different values but keys exist
        >>> deep_diff(source, existing)
        {}
    """
    result = {}

    for key, source_value in source.items():
        # Key doesn't exist in existing - include entire value
        if key not in existing:
            result[key] = source_value
            continue

        existing_value = existing[key]

        # Both values are dicts - recursively compare
        if isinstance(source_value, dict) and isinstance(existing_value, dict):
            nested_diff = deep_diff(source_value, existing_value)
            # Only include this key if there are nested differences
            if nested_diff:
                result[key] = nested_diff
        # If key exists but isn't both dicts, skip it (already translated)

    return result


def deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries, preserving nested structures.

    When both dictionaries have dict values for the same key, they are merged
    recursively. Otherwise, the value from updates takes precedence.

    Args:
        base: Base dictionary (will not be modified)
        updates: Dictionary with updates to apply

    Returns:
        New dictionary with merged content

    Examples:
        >>> base = {"a": 1, "b": {"c": 2}}
        >>> updates = {"b": {"d": 3}, "e": 4}
        >>> deep_merge(base, updates)
        {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

        >>> base = {"a": {"b": 1, "c": 2}}
        >>> updates = {"a": {"c": 3, "d": 4}}
        >>> deep_merge(base, updates)
        {"a": {"b": 1, "c": 3, "d": 4}}
    """
    # Start with a copy of base
    result = base.copy()

    for key, update_value in updates.items():
        # Key doesn't exist in base - add it
        if key not in result:
            result[key] = update_value
            continue

        base_value = result[key]

        # Both values are dicts - recursively merge
        if isinstance(base_value, dict) and isinstance(update_value, dict):
            result[key] = deep_merge(base_value, update_value)
        else:
            # Not both dicts - update value takes precedence
            result[key] = update_value

    return result
