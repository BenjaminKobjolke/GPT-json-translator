"""
Recursive translation service for batch processing directories.
"""
import os
import sys
from typing import Dict, Any, List, Optional

from src.services.translation_orchestrator import TranslationOrchestrator
from src.utils.file_discovery import find_directories_with_source_file, has_only_source_file
from src.utils.path_utils import analyze_input_filename


class RecursiveTranslator:
    """
    Service for recursive translation across directory hierarchies.
    """

    @staticmethod
    def find_and_translate(
        base_dir: str,
        source_filename: str,
        config: Dict[str, Any],
        excluded_languages: Optional[List[str]] = None,
        use_cdata: bool = False,
        second_input_path: Optional[str] = None,
        override_languages: Optional[List[str]] = None
    ) -> None:
        """
        Find directories with untranslated source files and translate them.

        Args:
            base_dir: Base directory to search
            source_filename: Source filename to search for (e.g., 'en.json')
            config: Configuration dictionary
            excluded_languages: Optional list of language codes to exclude
            use_cdata: For XML files, wrap strings in CDATA sections (default: False)
            second_input_path: Optional path to second language file for dual-language mode
            override_languages: Optional list of language codes to override config languages
        """
        # Validate base directory
        if not os.path.exists(base_dir):
            print(f"Error: Directory not found at {base_dir}")
            sys.exit(1)

        if not os.path.isdir(base_dir):
            print(f"Error: Path is not a directory: {base_dir}")
            sys.exit(1)

        print(f"Searching for '{source_filename}' in subdirectories of: {base_dir}")
        print()

        # Find all directories containing the source file
        matching_dirs = find_directories_with_source_file(base_dir, source_filename)

        if not matching_dirs:
            print(f"No directories found containing '{source_filename}'")
            return

        print(f"Found {len(matching_dirs)} director(ies) containing '{source_filename}'")
        print()

        # Analyze file type from the source filename
        dummy_path = os.path.join(base_dir, source_filename)
        file_type, _, _ = analyze_input_filename(dummy_path)

        # Filter directories that have only the source file (no translations)
        dirs_to_process = RecursiveTranslator._filter_directories(
            matching_dirs,
            source_filename,
            file_type
        )

        if not dirs_to_process:
            print(f"All directories already have translations. Nothing to do.")
            return

        print(f"Found {len(dirs_to_process)} director(ies) without translations:")
        for directory in dirs_to_process:
            print(f"  - {directory}")
        print()

        # Load second input file if provided (used for all directories)
        second_input_data = None
        if second_input_path:
            from src.cli.commands import _load_second_input
            second_input_data = _load_second_input(second_input_path)
            if second_input_data:
                print(f"Using same second input for all directories: {second_input_path}")
                print()

        # Process batch
        RecursiveTranslator._process_batch(
            dirs_to_process,
            source_filename,
            config,
            excluded_languages,
            use_cdata,
            second_input_data,
            override_languages
        )

    @staticmethod
    def _filter_directories(
        directories: List[str],
        source_filename: str,
        file_type: str
    ) -> List[str]:
        """
        Filter directories to only those with source file but no translations.

        Args:
            directories: List of directories to filter
            source_filename: Source filename
            file_type: File type ('json' or 'arb')

        Returns:
            Filtered list of directories
        """
        filtered = []
        for directory in directories:
            if has_only_source_file(directory, source_filename, file_type):
                filtered.append(directory)
        return filtered

    @staticmethod
    def _process_batch(
        directories: List[str],
        source_filename: str,
        config: Dict[str, Any],
        excluded_languages: Optional[List[str]],
        use_cdata: bool = False,
        second_input_data: Optional[tuple] = None,
        override_languages: Optional[List[str]] = None
    ) -> None:
        """
        Process a batch of directories for translation.

        Args:
            directories: List of directories to process
            source_filename: Source filename
            config: Configuration dictionary
            excluded_languages: Optional list of language codes to exclude
            use_cdata: For XML files, wrap strings in CDATA sections (default: False)
            second_input_data: Optional tuple of (second_json, second_language_code) for dual-language mode
            override_languages: Optional list of language codes to override config languages
        """
        processed_count = 0

        for i, directory in enumerate(directories, 1):
            source_file_path = os.path.join(directory, source_filename)
            print(f"[{i}/{len(directories)}] Processing: {source_file_path}")
            print("-" * 80)

            try:
                TranslationOrchestrator.process_single_file(
                    source_file_path,
                    config,
                    excluded_languages,
                    use_cdata,
                    second_input_data,
                    override_languages
                )
                processed_count += 1
                print()
            except Exception as e:
                print(f"Error processing {source_file_path}: {str(e)}")
                print()

        print("=" * 80)
        print(f"Recursive translation complete. Processed {processed_count}/{len(directories)} director(ies).")
