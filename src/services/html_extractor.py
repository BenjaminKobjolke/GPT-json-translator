"""HTML/Twig text extraction service - main orchestration."""

import glob
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from src.models.extraction_data import (
    HtmlExtractionConfig,
    ExtractedText,
    FileExtractionResult,
    ExtractionResult
)
from src.extractors.html_parser import HtmlParser
from src.extractors.key_generator import KeyGenerator
from src.extractors.twig_replacer import TwigReplacer
from src.file_handler import FileHandler


class HtmlExtractor:
    """Orchestrates HTML/Twig text extraction workflow."""

    @staticmethod
    def extract_and_replace(config: HtmlExtractionConfig) -> ExtractionResult:
        """
        Main entry point: extract text, generate JSON, replace in files.

        Args:
            config: Extraction configuration

        Returns:
            ExtractionResult with statistics and details
        """
        # 1. Find files to process
        files = HtmlExtractor._find_files(config.input_pattern)

        if not files:
            return ExtractionResult(
                files_processed=0,
                total_strings_extracted=0,
                strings_added=0,
                strings_skipped=0,
                files_modified=0,
                json_output_path=Path(config.output_path),
                errors=[f"No files found matching: {config.input_pattern}"],
                file_results=[]
            )

        # 2. Load existing JSON (for merging)
        output_path = Path(config.output_path)
        existing_json = HtmlExtractor._load_existing_json(output_path)

        # 3. Process each file
        file_results: List[FileExtractionResult] = []
        all_extracted: Dict[str, Dict[str, str]] = {}  # Nested: {prefix: {key_suffix: text}}

        for file_path in files:
            result = HtmlExtractor._process_file(file_path, config)
            file_results.append(result)

            # Collect extracted items into nested structure
            for item in result.extracted_items:
                prefix, suffix = item.key.rsplit('.', 1)
                if prefix not in all_extracted:
                    all_extracted[prefix] = {}
                all_extracted[prefix][suffix] = item.text

        # 4. Merge with existing JSON
        merged_json, strings_added, strings_skipped = HtmlExtractor._merge_json(
            existing_json, all_extracted
        )

        # 5. Save JSON output
        if not config.dry_run:
            HtmlExtractor._save_json(output_path, merged_json)

        # 6. Save modified Twig files (with backup)
        files_modified = 0
        if not config.dry_run:
            for result in file_results:
                if result.extracted_items:
                    if config.create_backup:
                        HtmlExtractor._create_backup(result.file_path)
                    result.file_path.write_text(result.modified_content, encoding='utf-8')
                    files_modified += 1

        # 7. Build and return result
        total_extracted = sum(len(r.extracted_items) for r in file_results)
        all_errors: List[str] = []
        for r in file_results:
            all_errors.extend(r.errors)

        return ExtractionResult(
            files_processed=len(files),
            total_strings_extracted=total_extracted,
            strings_added=strings_added,
            strings_skipped=strings_skipped,
            files_modified=files_modified,
            json_output_path=output_path,
            errors=all_errors,
            file_results=file_results
        )

    @staticmethod
    def _find_files(pattern: str) -> List[Path]:
        """Find files matching the input pattern."""
        path = Path(pattern)

        # Check if it's a single file
        if path.is_file():
            return [path]

        # Check if it's a glob pattern
        if '*' in pattern or '?' in pattern:
            matches = glob.glob(pattern, recursive=True)
            return [Path(m) for m in matches if Path(m).is_file()]

        # Check if it's a directory (process all .twig and .html files)
        if path.is_dir():
            files: List[Path] = []
            for ext in ['*.twig', '*.html', '*.htm']:
                files.extend(path.glob(f'**/{ext}'))
            return files

        return []

    @staticmethod
    def _process_file(
        file_path: Path,
        config: HtmlExtractionConfig
    ) -> FileExtractionResult:
        """Process a single file: extract and prepare replacements."""
        errors: List[str] = []

        try:
            # Generate key prefix from filename
            key_prefix = KeyGenerator.get_key_prefix(file_path)

            # Parse and extract
            extracted = HtmlParser.parse_file(file_path, config, key_prefix)

            # Apply replacements to content
            content = file_path.read_text(encoding='utf-8')
            modified_content = TwigReplacer.apply_replacements(
                content,
                extracted,
                config.translation_function
            )

            return FileExtractionResult(
                file_path=file_path,
                extracted_items=extracted,
                modified_content=modified_content,
                errors=errors
            )

        except Exception as e:
            errors.append(f"Error processing {file_path}: {str(e)}")
            return FileExtractionResult(
                file_path=file_path,
                extracted_items=[],
                modified_content='',
                errors=errors
            )

    @staticmethod
    def _load_existing_json(path: Path) -> Dict:
        """Load existing JSON file or return empty dict."""
        if path.exists():
            try:
                return FileHandler.load_json_file(str(path))
            except Exception:
                return {}
        return {}

    @staticmethod
    def _merge_json(
        existing: Dict,
        extracted: Dict[str, Dict[str, str]]
    ) -> Tuple[Dict, int, int]:
        """
        Merge extracted translations with existing JSON.

        Returns:
            Tuple of (merged_dict, strings_added, strings_skipped)
        """
        merged = existing.copy()
        strings_added = 0
        strings_skipped = 0

        for prefix, items in extracted.items():
            if prefix not in merged:
                merged[prefix] = {}
            elif not isinstance(merged[prefix], dict):
                # If existing value is not a dict, skip this prefix
                strings_skipped += len(items)
                continue

            for key_suffix, text in items.items():
                if key_suffix in merged[prefix]:
                    strings_skipped += 1
                else:
                    merged[prefix][key_suffix] = text
                    strings_added += 1

        return merged, strings_added, strings_skipped

    @staticmethod
    def _save_json(path: Path, data: Dict) -> None:
        """Save JSON with proper formatting."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _create_backup(file_path: Path) -> None:
        """Create a .bak backup of the file."""
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        shutil.copy2(file_path, backup_path)
