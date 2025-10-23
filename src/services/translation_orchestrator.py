"""
Translation orchestration service for coordinating the translation workflow.
"""
import concurrent.futures
from typing import Dict, Any, List, Optional

from src.config import ConfigManager
from src.file_handler import FileHandler
from src.translator import TranslationService
from src.models.translation_data import TranslationData, TranslationResult
from src.utils.language_utils import parse_language_code, filter_excluded_languages, filter_source_language
from src.utils.output_utils import print_translation_summary, print_hints_summary
from src.utils.path_utils import analyze_input_filename


class TranslationOrchestrator:
    """
    Orchestrates the translation workflow for single files.
    """

    @staticmethod
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
            translation_data.file_type
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

    @staticmethod
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
        target_languages = filter_excluded_languages(target_languages, excluded_languages)
        target_languages = filter_source_language(target_languages, source_language)

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
                    TranslationOrchestrator.process_language,
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
