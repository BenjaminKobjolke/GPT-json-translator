"""Data models for HTML/Twig text extraction."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional


@dataclass
class HtmlExtractionConfig:
    """Configuration for HTML extraction operation."""
    input_pattern: str                          # File path or glob pattern
    output_path: str                            # JSON output file path
    translation_function: str = 't'             # Twig function name
    create_backup: bool = True                  # Create .bak files
    dry_run: bool = False                       # Preview only
    extract_tags: Set[str] = field(default_factory=lambda: {
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span',
        'button', 'label', 'a', 'li', 'th', 'td', 'figcaption',
        'legend', 'option'
    })
    extract_attributes: Set[str] = field(default_factory=lambda: {
        'alt', 'title', 'placeholder', 'aria-label', 'aria-description'
    })


@dataclass
class ExtractedText:
    """Represents a single extracted text item."""
    key: str                    # Full translation key (e.g., "overview.h2_1")
    text: str                   # Original text content
    element_type: str           # Tag name or attribute name
    line_number: int            # Line number in source file
    contains_html: bool         # Whether text contains inline HTML tags
    original_match: str         # The full original match for replacement


@dataclass
class FileExtractionResult:
    """Result of extracting from a single file."""
    file_path: Path
    extracted_items: List[ExtractedText]
    modified_content: str       # Content with replacements applied
    errors: List[str]           # Any errors encountered


@dataclass
class ExtractionResult:
    """Overall result of the extraction operation."""
    files_processed: int
    total_strings_extracted: int
    strings_added: int          # New strings added to JSON
    strings_skipped: int        # Already existed in JSON
    files_modified: int
    json_output_path: Path
    errors: List[str]
    file_results: List[FileExtractionResult]
