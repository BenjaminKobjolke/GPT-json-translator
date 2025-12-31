"""HTML/Twig parsing and text extraction."""

import re
from pathlib import Path
from typing import List, Dict, Set

from src.models.extraction_data import ExtractedText, HtmlExtractionConfig
from src.extractors.key_generator import KeyGenerator
from src.utils.html_utils import (
    is_translatable_content,
    contains_inline_html,
    ALREADY_TRANSLATED_PATTERN
)


class HtmlParser:
    """Parses HTML/Twig files and extracts translatable content."""

    @staticmethod
    def parse_file(
        file_path: Path,
        config: HtmlExtractionConfig,
        key_prefix: str
    ) -> List[ExtractedText]:
        """
        Parse an HTML/Twig file and extract translatable text.

        Args:
            file_path: Path to the file to parse
            config: Extraction configuration
            key_prefix: Prefix for generated keys (usually filename without extension)

        Returns:
            List of ExtractedText items found in the file
        """
        content = file_path.read_text(encoding='utf-8')
        extracted: List[ExtractedText] = []

        # Track counters for key generation per element type
        counters: Dict[str, int] = {}

        # Extract from text content
        extracted.extend(
            HtmlParser._extract_text_content(content, config, key_prefix, counters)
        )

        # Extract from attributes
        extracted.extend(
            HtmlParser._extract_attributes(content, config, key_prefix, counters)
        )

        return extracted

    @staticmethod
    def _extract_text_content(
        content: str,
        config: HtmlExtractionConfig,
        key_prefix: str,
        counters: Dict[str, int]
    ) -> List[ExtractedText]:
        """Extract text content from HTML tags."""
        extracted: List[ExtractedText] = []

        # Build regex for target tags
        tags_pattern = '|'.join(config.extract_tags)

        # Match opening tag, content, closing tag
        # This regex captures: full match, tag name, attributes, inner content
        pattern = re.compile(
            rf'<({tags_pattern})(\s[^>]*)?>(.+?)</\1>',
            re.IGNORECASE | re.DOTALL
        )

        for match in pattern.finditer(content):
            tag_name = match.group(1).lower()
            inner_content = match.group(3)

            # Skip if already translated
            if ALREADY_TRANSLATED_PATTERN.search(inner_content):
                continue

            # Skip if content is not translatable
            if not is_translatable_content(inner_content):
                continue

            text = inner_content.strip()

            # Check for inline HTML tags
            has_html = contains_inline_html(text)

            # Generate key
            counters[tag_name] = counters.get(tag_name, 0) + 1
            key = KeyGenerator.generate_key(key_prefix, tag_name, counters[tag_name])

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            extracted.append(ExtractedText(
                key=key,
                text=text,
                element_type=tag_name,
                line_number=line_number,
                contains_html=has_html,
                original_match=match.group(0)
            ))

        return extracted

    @staticmethod
    def _extract_attributes(
        content: str,
        config: HtmlExtractionConfig,
        key_prefix: str,
        counters: Dict[str, int]
    ) -> List[ExtractedText]:
        """Extract translatable attributes from HTML tags."""
        extracted: List[ExtractedText] = []

        for attr in config.extract_attributes:
            # Match attribute="value" or attribute='value'
            pattern = re.compile(
                rf'\b({attr})\s*=\s*(["\'])(.+?)\2',
                re.IGNORECASE
            )

            for match in pattern.finditer(content):
                attr_name = match.group(1).lower()
                value = match.group(3).strip()

                # Skip if already translated
                if ALREADY_TRANSLATED_PATTERN.search(value):
                    continue

                # Skip if not translatable
                if not is_translatable_content(value):
                    continue

                # Generate key
                counters[attr_name] = counters.get(attr_name, 0) + 1
                key = KeyGenerator.generate_key(key_prefix, attr_name, counters[attr_name])

                # Calculate line number
                line_number = content[:match.start()].count('\n') + 1

                extracted.append(ExtractedText(
                    key=key,
                    text=value,
                    element_type=attr_name,
                    line_number=line_number,
                    contains_html=False,  # Attributes shouldn't contain HTML
                    original_match=match.group(0)
                ))

        return extracted
