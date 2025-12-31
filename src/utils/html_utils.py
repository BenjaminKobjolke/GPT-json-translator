"""Utility functions for HTML processing."""

import re
from typing import Set


# Tags whose content should be extracted
DEFAULT_TEXT_TAGS: Set[str] = {
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'span', 'button', 'label', 'a', 'li',
    'th', 'td', 'figcaption', 'legend', 'option'
}

# Inline tags that should be preserved in translations
INLINE_TAGS: Set[str] = {
    'b', 'i', 'strong', 'em', 'u', 'small',
    'mark', 'sub', 'sup', 'br', 'wbr', 'a'
}

# Attributes to extract for translation
DEFAULT_TRANSLATABLE_ATTRIBUTES: Set[str] = {
    'alt', 'title', 'placeholder',
    'aria-label', 'aria-description'
}

# Regex patterns
TWIG_EXPRESSION_PATTERN = re.compile(r'\{\{.*?\}\}|\{%.*?%\}')
ALREADY_TRANSLATED_PATTERN = re.compile(r"\{\{\s*\w+\s*\(['\"]")


def is_translatable_content(text: str) -> bool:
    """
    Check if text content should be translated.

    Returns False for:
    - Empty or whitespace-only strings
    - Strings that are only numbers
    - Strings that are only Twig expressions
    - Already translated content
    """
    if not text or not text.strip():
        return False

    stripped = text.strip()

    # Skip pure numbers
    if stripped.replace('.', '').replace(',', '').replace('-', '').isdigit():
        return False

    # Skip if already translated
    if ALREADY_TRANSLATED_PATTERN.search(stripped):
        return False

    # Skip if only Twig expressions
    without_twig = TWIG_EXPRESSION_PATTERN.sub('', stripped).strip()
    if not without_twig:
        return False

    return True


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text while preserving single spaces."""
    return ' '.join(text.split())


def contains_inline_html(text: str) -> bool:
    """Check if text contains inline HTML tags."""
    for tag in INLINE_TAGS:
        if re.search(rf'<{tag}\b', text, re.IGNORECASE):
            return True
    return False
