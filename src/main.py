"""
Main entry point for the JSON Translator.
"""
import sys
import os
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
    analyze_input_filename  # Import the new helper
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
            translation_data.hints
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


def run_translation() -> None:
    """
    Run the translation process.
    """
    # Load configuration
    config_manager = ConfigManager()
    if not config_manager.validate():
        sys.exit(1)
    
    config = config_manager.get_config()
    
    # Get input path
    cli_arg = sys.argv[1] if len(sys.argv) > 1 else None
    input_path = get_input_path(cli_arg, config["source_path"])

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
    
    # Create translation data
    translation_data = TranslationData(
        source_json=source_json,
        target_languages=config["languages"],
        input_path=input_path,
        file_type=file_type,          # Pass file_type
        filename_pattern=filename_pattern # Pass filename_pattern
    )

    # Print hints summary
    print_hints_summary(translation_data.hints)
    
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
