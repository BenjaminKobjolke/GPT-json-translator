"""
Main entry point for the JSON Translator.
"""
import sys
import os
import argparse
import concurrent.futures
from typing import Dict, Any, List, Optional

from src.config import ConfigManager
from src.file_handler import FileHandler
from src.translator import TranslationService
from src.models.translation_data import TranslationData, TranslationResult
from src.utils.helpers import (
    get_input_path,
    parse_language_code,
    print_translation_summary,
    print_hints_summary,
    analyze_input_filename,
    discover_override_files,
    find_directories_with_source_file,
    has_only_source_file
)


def process_language(
    translation_service: TranslationService,
    translation_data: TranslationData,
    target_language: str
) -> Optional[TranslationResult]:
    """
    Process translation for a single language.
    
    Args:
        translation_service: The translation service to use
        translation_data: The translation data object
        target_language: The target language code
        
    Returns:
        TranslationResult object if translation was performed, None otherwise
    """
    lang_code = parse_language_code(target_language)
    print(f"Processing language: {lang_code}")
    
    # Load existing translations and overrides using file type info
    existing_json = FileHandler.load_existing_translations(
        translation_data.input_path,
        lang_code,
        translation_data.file_type,
        translation_data.filename_pattern
    )

    overrides = FileHandler.load_overrides(
        translation_data.input_path,
        lang_code,
        translation_data.file_type,
        translation_data.filename_pattern
    )
    
    # Determine which keys need translation (pass file_type to filter)
    keys_for_translation = TranslationService.filter_keys_for_translation(
        translation_data.get_filtered_source(),
        existing_json,
        overrides,
        translation_data.file_type # Pass file type here
    )
    
    print_translation_summary(lang_code, len(keys_for_translation))
    
    if keys_for_translation:
        # Perform translation
        translated_content = translation_service.translate(
            target_language,
            keys_for_translation,
            translation_data.global_hints,
            translation_data.field_hints
        )
        
        # Create and return result
        return TranslationResult(
            language_code=lang_code,
            translated_content=translated_content,
            existing_content=existing_json,
            overrides=overrides
        )
    else:
        # No translation needed, but still save the file with overrides
        result = TranslationResult(
            language_code=lang_code,
            translated_content={},
            existing_content=existing_json,
            overrides=overrides
        )
        
        # Save the result (pass file type info)
        FileHandler.save_translation_result(
            result,
            translation_data.input_path,
            translation_data.file_type,
            translation_data.filename_pattern
        )
        
        return None


def process_single_file(
    input_path: str,
    config: Dict[str, Any],
    excluded_languages: Optional[List[str]] = None
) -> None:
    """
    Process translation for a single source file.

    Args:
        input_path: Path to the source JSON/ARB file
        config: Configuration dictionary from ConfigManager
        excluded_languages: Optional list of language codes to exclude
    """
    # Analyze the input filename
    file_type, source_language, filename_pattern = analyze_input_filename(input_path)

    # Load source JSON/ARB content
    try:
        source_json = FileHandler.load_json_file(input_path)
    except Exception as e:
        print(f"Error: {str(e)}")
        return

    # Filter languages based on exclusions
    target_languages = config["languages"]
    if excluded_languages:
        excluded_bases = [parse_language_code(lang) for lang in excluded_languages]

        # Filter out excluded languages
        original_count = len(target_languages)
        target_languages = [
            lang for lang in target_languages
            if parse_language_code(lang) not in excluded_bases
        ]

        excluded_count = original_count - len(target_languages)
        if excluded_count > 0:
            print(f"Excluded {excluded_count} language(s): {', '.join(excluded_languages)}")

    # Filter out source language to avoid redundant self-translation
    if source_language:
        source_base = parse_language_code(source_language)
        original_count = len(target_languages)
        target_languages = [
            lang for lang in target_languages
            if parse_language_code(lang) != source_base
        ]

        excluded_count = original_count - len(target_languages)
        if excluded_count > 0:
            print(f"Skipping source language: {source_language} (avoiding redundant self-translation)")

    # Create translation data
    translation_data = TranslationData(
        source_json=source_json,
        target_languages=target_languages,
        input_path=input_path,
        file_type=file_type,
        filename_pattern=filename_pattern
    )

    # Print hints summary
    print_hints_summary(translation_data.global_hints, translation_data.field_hints)

    # Create translation service
    translation_service = TranslationService(
        api_key=config["api_key"],
        model=config["model"]
    )

    # Process translations concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_language = {}

        # Submit translation tasks
        for target_language in translation_data.target_languages:
            future = executor.submit(
                process_language,
                translation_service,
                translation_data,
                target_language
            )
            future_to_language[future] = target_language

        # Process completed translation tasks
        for future in concurrent.futures.as_completed(future_to_language):
            target_language = future_to_language[future]
            try:
                result = future.result()
                if result:
                    # Save the result
                    FileHandler.save_translation_result(
                        result,
                        translation_data.input_path,
                        translation_data.file_type,
                        translation_data.filename_pattern
                    )
            except Exception as e:
                print(f"Error processing translation for {target_language}:")
                print(f"Error details: {str(e)}")


def apply_overrides_only() -> None:
    """
    Apply override files to translation files without performing any translation.
    Discovers all override files in _overrides/ and merges them into corresponding translation files.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Apply override files to translation files')
    parser.add_argument('input_path', nargs='?', help='Path to the source JSON file')
    args = parser.parse_args()

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.get_config()

    # Get input path
    input_path = get_input_path(args.input_path, config["source_path"])

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


def run_translation() -> None:
    """
    Run the translation process.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Translate JSON files to multiple languages using OpenAI GPT')
    parser.add_argument('input_path', nargs='?', help='Path to the source JSON file or directory (when using --translate-recursive)')
    parser.add_argument('--exclude-languages', '--exclude',
                        help='Comma-separated list of language codes to exclude (e.g., "he,ko" or "he-IL,ko-KR")')
    parser.add_argument('--apply-overrides', action='store_true',
                        help='Apply override files only, without performing translation')
    parser.add_argument('--translate-recursive',
                        metavar='FILENAME',
                        help='Recursively search for subdirectories containing FILENAME and translate if no translations exist (e.g., "en.json")')

    args = parser.parse_args()

    # If --apply-overrides flag is set, run override application instead
    if args.apply_overrides:
        apply_overrides_only()
        return

    # Load configuration
    config_manager = ConfigManager()
    if not config_manager.validate():
        sys.exit(1)

    config = config_manager.get_config()

    # Parse excluded languages if provided
    excluded_languages = None
    if args.exclude_languages:
        excluded_languages = [lang.strip() for lang in args.exclude_languages.split(',')]

    # Handle recursive translation mode
    if args.translate_recursive:
        source_filename = args.translate_recursive

        # Get base directory
        if args.input_path:
            base_dir = args.input_path
        elif config["source_path"]:
            base_dir = os.path.dirname(config["source_path"])
        else:
            base_dir = input("Enter the base directory to search: ")

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
        dirs_to_process = []
        for directory in matching_dirs:
            if has_only_source_file(directory, source_filename, file_type):
                dirs_to_process.append(directory)

        if not dirs_to_process:
            print(f"All directories already have translations. Nothing to do.")
            return

        print(f"Found {len(dirs_to_process)} director(ies) without translations:")
        for directory in dirs_to_process:
            print(f"  - {directory}")
        print()

        # Process each directory
        processed_count = 0
        for i, directory in enumerate(dirs_to_process, 1):
            source_file_path = os.path.join(directory, source_filename)
            print(f"[{i}/{len(dirs_to_process)}] Processing: {source_file_path}")
            print("-" * 80)

            try:
                process_single_file(source_file_path, config, excluded_languages)
                processed_count += 1
                print()
            except Exception as e:
                print(f"Error processing {source_file_path}: {str(e)}")
                print()

        print("=" * 80)
        print(f"Recursive translation complete. Processed {processed_count}/{len(dirs_to_process)} director(ies).")
        return

    # Regular single-file mode
    # Get input path
    input_path = get_input_path(args.input_path, config["source_path"])

    # Process the single file
    process_single_file(input_path, config, excluded_languages)

    print("Translation process complete.")


if __name__ == "__main__":
    # Print current working directory for debugging
    print(f"Current working directory: {os.getcwd()}")
    
    # Run the translation process
    run_translation()
