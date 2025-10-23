"""
Language code manipulation utilities for the JSON Translator.
"""
from typing import List, Optional


def parse_language_code(full_language_code: str) -> str:
    """
    Extract the base language code from a full language code.

    Args:
        full_language_code: Full language code (e.g., 'en-US')

    Returns:
        Base language code (e.g., 'en')
    """
    return full_language_code.split('-')[0]


def filter_excluded_languages(
    target_languages: List[str],
    excluded_languages: Optional[List[str]]
) -> List[str]:
    """
    Filter out excluded languages from the target language list.

    Args:
        target_languages: List of target language codes
        excluded_languages: List of language codes to exclude

    Returns:
        Filtered list of target languages
    """
    if not excluded_languages:
        return target_languages

    excluded_bases = [parse_language_code(lang) for lang in excluded_languages]

    # Filter out excluded languages
    filtered = [
        lang for lang in target_languages
        if parse_language_code(lang) not in excluded_bases
    ]

    excluded_count = len(target_languages) - len(filtered)
    if excluded_count > 0:
        print(f"Excluded {excluded_count} language(s): {', '.join(excluded_languages)}")

    return filtered


def filter_source_language(
    target_languages: List[str],
    source_language: Optional[str]
) -> List[str]:
    """
    Filter out the source language from target languages to avoid redundant self-translation.

    Args:
        target_languages: List of target language codes
        source_language: The source language code

    Returns:
        Filtered list of target languages
    """
    if not source_language:
        return target_languages

    source_base = parse_language_code(source_language)
    filtered = [
        lang for lang in target_languages
        if parse_language_code(lang) != source_base
    ]

    excluded_count = len(target_languages) - len(filtered)
    if excluded_count > 0:
        print(f"Skipping source language: {source_language} (avoiding redundant self-translation)")

    return filtered
