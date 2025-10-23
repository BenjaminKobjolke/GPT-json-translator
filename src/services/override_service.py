"""
Override service for applying override files to translation files.
"""
from src.file_handler import FileHandler
from src.models.translation_data import TranslationResult
from src.utils.file_discovery import discover_override_files
from src.utils.path_utils import analyze_input_filename, get_input_path
from typing import Literal, Optional


class OverrideService:
    """
    Service for applying override files to translation files without performing translation.
    """

    @staticmethod
    def apply_overrides(input_path: str) -> None:
        """
        Apply override files to translation files.

        Args:
            input_path: Path to the source JSON/ARB file
        """
        # Analyze the input filename to determine file type and pattern
        file_type, source_language, filename_pattern = analyze_input_filename(input_path)

        # Discover all override files
        override_languages = discover_override_files(input_path, file_type, filename_pattern)

        if not override_languages:
            print("No override files found in _overrides/ directory.")
            return

        print(f"Found {len(override_languages)} override file(s) to apply:")
        for lang in override_languages:
            print(f"  - {lang}")
        print()

        # Process each override file
        applied_count = 0
        for lang_code in override_languages:
            print(f"Processing overrides for {lang_code}...")

            # Load the override file
            overrides = FileHandler.load_overrides(
                input_path,
                lang_code,
                file_type,
                filename_pattern
            )

            if not overrides:
                print(f"  Warning: Override file empty or invalid for {lang_code}")
                continue

            # Load existing translation file (or empty dict if it doesn't exist)
            existing_content = FileHandler.load_existing_translations(
                input_path,
                lang_code,
                file_type,
                filename_pattern
            )

            # Create a TranslationResult to merge the content
            result = TranslationResult(
                language_code=lang_code,
                translated_content={},
                existing_content=existing_content,
                overrides=overrides
            )

            # Save the merged result
            FileHandler.save_translation_result(
                result,
                input_path,
                file_type,
                filename_pattern
            )

            applied_count += 1
            print(f"  Applied {len(overrides)} override(s) to {lang_code}")

        print(f"\nSuccessfully applied overrides to {applied_count} language(s).")
