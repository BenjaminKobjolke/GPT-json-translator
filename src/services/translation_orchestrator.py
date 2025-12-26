"""
Translation orchestration service for coordinating the translation workflow.
"""
import concurrent.futures
import json
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
        target_language: str,
        use_cdata: bool = False
    ) -> Optional[TranslationResult]:
        """
        Process translation for a single language.

        Args:
            translation_service: The translation service to use
            translation_data: The translation data object
            target_language: The target language code
            use_cdata: For XML files, wrap strings in CDATA sections (default: False)

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
            # Build dual-language content if second input is available
            content_to_send = keys_for_translation
            if translation_data.second_input_json:
                augmented_content, missing_keys = translation_data.build_dual_language_content(
                    keys_for_translation
                )

                # Warn about missing keys
                if missing_keys:
                    print(f"  Warning: {len(missing_keys)} key(s) missing in second input, "
                          f"translating from primary source only:")
                    for key in missing_keys[:5]:  # Show first 5
                        print(f"    - {key}")
                    if len(missing_keys) > 5:
                        print(f"    ... and {len(missing_keys) - 5} more")

                content_to_send = augmented_content

            # Perform translation
            translated_content = translation_service.translate(
                target_language,
                content_to_send,
                translation_data.global_hints,
                translation_data.field_hints,
                translation_data.second_language_code
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

            # Save the result (pass file type info and xml_source_root for XML files)
            FileHandler.save_translation_result(
                result,
                translation_data.input_path,
                translation_data.file_type,
                translation_data.filename_pattern,
                xml_source_root=translation_data.xml_source_root,
                use_cdata=use_cdata
            )

            return None

    @staticmethod
    def process_single_file(
        input_path: str,
        config: Dict[str, Any],
        excluded_languages: Optional[List[str]] = None,
        use_cdata: bool = False,
        second_input_data: Optional[tuple] = None,
        override_languages: Optional[List[str]] = None
    ) -> None:
        """
        Process translation for a single source file.

        Args:
            input_path: Path to the source JSON/ARB/XML file
            config: Configuration dictionary from ConfigManager
            excluded_languages: Optional list of language codes to exclude
            use_cdata: For XML files, wrap strings in CDATA sections (default: False)
            second_input_data: Optional tuple of (second_json, second_language_code) for dual-language mode
            override_languages: Optional list of language codes to override config languages
        """
        # Analyze the input filename
        file_type, source_language, filename_pattern = analyze_input_filename(input_path)

        # Load and validate source content
        print("Validating source file...")
        xml_source_root = None

        try:
            if file_type == 'xml':
                # Load XML file
                from src.utils.xml_handler import load_android_xml
                source_json, xml_source_root = load_android_xml(input_path)
                print("[OK] Source XML file validation passed")
            else:
                # Load JSON/ARB file
                source_json = FileHandler.load_json_file(input_path)
                print("[OK] Source file validation passed")
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON syntax error: {str(e)}")
            return
        except ValueError as e:
            print(f"[ERROR] {str(e)}")
            return
        except Exception as e:
            print(f"[ERROR] Error: {str(e)}")
            return

        # Use override languages if provided, otherwise use config languages
        if override_languages:
            target_languages = override_languages
            print(f"Using command-line languages override: {', '.join(target_languages)}")
        else:
            target_languages = config["languages"]

        # Filter languages based on exclusions
        target_languages = filter_excluded_languages(target_languages, excluded_languages)
        target_languages = filter_source_language(target_languages, source_language)

        # Unpack second input data if provided
        second_input_json = None
        second_language_code = None
        if second_input_data:
            second_input_json, second_language_code = second_input_data
            print(f"Using dual-language mode with second input: {second_language_code}")

            # Automatically exclude the second language from translation targets
            second_base = parse_language_code(second_language_code)
            original_count = len(target_languages)
            target_languages = [
                lang for lang in target_languages
                if parse_language_code(lang) != second_base
            ]
            if len(target_languages) < original_count:
                print(f"Automatically excluded {second_language_code} from translation targets")

        # Create translation data
        translation_data = TranslationData(
            source_json=source_json,
            target_languages=target_languages,
            input_path=input_path,
            file_type=file_type,
            filename_pattern=filename_pattern,
            xml_source_root=xml_source_root,
            second_input_json=second_input_json,
            second_language_code=second_language_code
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
                    target_language,
                    use_cdata
                )
                future_to_language[future] = target_language

            # Process completed translation tasks
            for future in concurrent.futures.as_completed(future_to_language):
                target_language = future_to_language[future]
                try:
                    result = future.result()
                    if result:
                        # Save the result (pass xml_source_root for XML files)
                        FileHandler.save_translation_result(
                            result,
                            translation_data.input_path,
                            translation_data.file_type,
                            translation_data.filename_pattern,
                            xml_source_root=translation_data.xml_source_root,
                            use_cdata=use_cdata
                        )
                except Exception as e:
                    print(f"Error processing translation for {target_language}:")
                    print(f"Error details: {str(e)}")
