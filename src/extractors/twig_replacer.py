"""Twig file modification with translation function calls."""

import re
from typing import List

from src.models.extraction_data import ExtractedText
from src.utils.html_utils import DEFAULT_TRANSLATABLE_ATTRIBUTES


class TwigReplacer:
    """Replaces text in Twig files with translation function calls."""

    @staticmethod
    def apply_replacements(
        content: str,
        extracted_items: List[ExtractedText],
        translation_function: str = 't'
    ) -> str:
        """
        Replace extracted text with translation function calls.

        Args:
            content: Original file content
            extracted_items: List of extracted text items with keys
            translation_function: Name of the Twig translation function

        Returns:
            Modified content with translation calls
        """
        modified = content

        for item in extracted_items:
            replacement = TwigReplacer._create_replacement(
                item,
                translation_function
            )

            # Replace the original match with the new version
            modified = TwigReplacer._replace_match(
                modified,
                item,
                replacement
            )

        return modified

    @staticmethod
    def _create_replacement(
        item: ExtractedText,
        func: str
    ) -> str:
        """Create the replacement string for an extracted item."""

        # For text content
        if item.contains_html:
            # Use |raw filter for content with HTML tags
            return f"{{{{ {func}('{item.key}')|raw }}}}"
        else:
            return f"{{{{ {func}('{item.key}') }}}}"

    @staticmethod
    def _replace_match(
        content: str,
        item: ExtractedText,
        replacement: str
    ) -> str:
        """Replace the original match in content."""

        # Normalize attribute name for comparison (aria-label -> aria-label)
        attr_names = {attr.lower() for attr in DEFAULT_TRANSLATABLE_ATTRIBUTES}

        if item.element_type.lower() in attr_names:
            # For attributes: replace the entire original match
            # original_match is like: alt="Windows language switcher"
            # We replace it with: alt="{{ t('key') }}"
            quote_char = '"' if '"' in item.original_match else "'"
            new_attr = f'{item.element_type}={quote_char}{replacement}{quote_char}'
            return content.replace(item.original_match, new_attr, 1)

        else:
            # For text content: replace the entire original match
            # original_match is like: <p>text content</p>
            # Extract the opening tag from original_match
            opening_tag_match = re.match(
                rf'<{item.element_type}[^>]*>',
                item.original_match,
                re.IGNORECASE
            )
            if opening_tag_match:
                opening_tag = opening_tag_match.group(0)
                closing_tag = f'</{item.element_type}>'
                new_element = f'{opening_tag}{replacement}{closing_tag}'
                return content.replace(item.original_match, new_element, 1)

            return content
