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
    discover_override_files
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
    parser.add_argument('input_path', nargs='?', help='Path to the source JSON file')
    parser.add_argument('--exclude-languages', '--exclude',
                        help='Comma-separated list of language codes to exclude (e.g., "he,ko" or "he-IL,ko-KR")')
    parser.add_argument('--apply-overrides', action='store_true',
                        help='Apply override files only, without performing translation')

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

    # Get input path
    input_path = get_input_path(args.input_path, config["source_path"])

    # Analyze the input filename
    file_type, source_language, filename_pattern = analyze_input_filename(input_path)
    # TODO: Optionally add a check here if source_language from filename
    # matches the actual content language if needed.

    # Load source JSON/ARB content
    try:
        source_json = FileHandler.load_json_file(input_path)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    # Filter languages based on exclusions
    target_languages = config["languages"]
    if args.exclude_languages:
        # Parse excluded languages (handle both "he" and "he-IL" formats)
        excluded = [lang.strip() for lang in args.exclude_languages.split(',')]
        excluded_bases = [parse_language_code(lang) for lang in excluded]

        # Filter out excluded languages
        original_count = len(target_languages)
        target_languages = [
            lang for lang in target_languages
            if parse_language_code(lang) not in excluded_bases
        ]

        excluded_count = original_count - len(target_languages)
        if excluded_count > 0:
            print(f"Excluded {excluded_count} language(s): {', '.join(excluded)}")
        else:
            print(f"Warning: No languages were excluded. Check your --exclude-languages values.")

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
        file_type=file_type,          # Pass file_type
        filename_pattern=filename_pattern # Pass filename_pattern
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
                    # Save the result (pass file type info)
                    FileHandler.save_translation_result(
                        result,
                        translation_data.input_path,
                        translation_data.file_type,
                        translation_data.filename_pattern
                    )
            except Exception as e:
                print(f"Error processing translation for {target_language}:")
                print(f"Error details: {str(e)}")
    
    print("Translation process complete.")


if __name__ == "__main__":
    # Print current working directory for debugging
    print(f"Current working directory: {os.getcwd()}")
    
    # Run the translation process
    run_translation()
