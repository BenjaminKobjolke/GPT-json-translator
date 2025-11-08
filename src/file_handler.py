"""
File handling operations for the JSON Translator.
"""
import json
import os
from typing import Dict, Any, Optional, Literal

from src.models.translation_data import TranslationResult
from src.utils.validation_utils import DuplicateKeyDetector


class FileHandler:
    """
    Handles file operations for the JSON Translator.
    """

    @staticmethod
    def _get_language_filename(
        language_code: str,
        file_type: Literal['json', 'arb'],
        filename_pattern: Optional[str] = None
    ) -> str:
        """
        Generate the appropriate filename for a given language and file type.

        Args:
            language_code: Full language code (e.g., 'de-DE')
            file_type: The type of file ('json' or 'arb')
            filename_pattern: The filename pattern for ARB files (e.g., 'app_{lang}.arb')

        Returns:
            The generated filename

        Raises:
            ValueError: If file_type is 'arb' but filename_pattern is not provided
        """
        if file_type == 'arb':
            if not filename_pattern:
                raise ValueError("filename_pattern is required for ARB files")
            # ARB uses base language code in pattern (e.g., 'de' not 'de-DE')
            lang_for_pattern = language_code.split('-')[0]
            return filename_pattern.format(lang=lang_for_pattern)
        elif file_type == 'json':
            return f"{language_code}.json"
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def load_json_file(file_path: str, validate_duplicates: bool = True) -> Dict[str, Any]:
        """
        Load and parse a JSON file with optional duplicate key validation.

        Args:
            file_path: Path to the JSON file
            validate_duplicates: If True, detect and reject duplicate keys (default: True)

        Returns:
            Parsed JSON content as a dictionary

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file can't be read due to permissions
            json.JSONDecodeError: If the file contains invalid JSON
            ValueError: If duplicate keys are detected (when validate_duplicates=True)
            IOError: For other I/O related errors
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Path not found at {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if validate_duplicates:
                # Use enhanced duplicate detection with line numbers
                decoder = DuplicateKeyDetector(source=content)
                return decoder.decode(content)
            else:
                return json.loads(content)
        except PermissionError:
            raise PermissionError(f"Permission denied: Unable to read the file {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error parsing JSON file {file_path}: {str(e)}",
                e.doc,
                e.pos
            )
        except ValueError as e:
            # Duplicate key error from DuplicateKeyDetector
            raise ValueError(f"Validation error in {file_path}: {str(e)}")
        except IOError as e:
            raise IOError(f"Error reading file {file_path}: {str(e)}")
    
    @staticmethod
    def save_json_file(file_path: str, content: Dict[str, Any]) -> None:
        """
        Save content to a JSON file.
        
        Args:
            file_path: Path where the file should be saved
            content: Dictionary content to save as JSON
            
        Raises:
            IOError: If the file can't be written
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Error saving file {file_path}: {str(e)}")

    @staticmethod
    def load_overrides(
        base_path: str,
        language_code: str,
        file_type: Literal['json', 'arb'],
        filename_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load override values for a specific language, handling different file types.

        Args:
            base_path: Base path where the source file is located
            language_code: Language code to load overrides for
            file_type: The type of the file ('json' or 'arb')
            filename_pattern: The filename pattern for ARB files (e.g., 'app_{lang}.arb')

        Returns:
            Dictionary of override values, or empty dict if none exist
        """
        try:
            override_filename = FileHandler._get_language_filename(
                language_code, file_type, filename_pattern
            )
        except ValueError as e:
            print(f"Warning: {str(e)}")
            return {}

        overrides_path = os.path.join(
            os.path.dirname(base_path),
            "_overrides",
            override_filename
        )

        if os.path.exists(overrides_path):
            try:
                return FileHandler.load_json_file(overrides_path)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading overrides for {language_code}: {str(e)}")
                return {}
        return {}

    @staticmethod
    def load_existing_translations(
        base_path: str,
        language_code: str,
        file_type: Literal['json', 'arb'],
        filename_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load existing translations for a specific language, handling different file types.

        Args:
            base_path: Base path where the source file is located
            language_code: Language code to load translations for
            file_type: The type of the file ('json' or 'arb')
            filename_pattern: The filename pattern for ARB files (e.g., 'app_{lang}.arb')

        Returns:
            Dictionary of existing translations, or empty dict if none exist
        """
        try:
            existing_filename = FileHandler._get_language_filename(
                language_code, file_type, filename_pattern
            )
        except ValueError as e:
            print(f"Warning: {str(e)}")
            return {}

        existing_path = os.path.join(
            os.path.dirname(base_path),
            existing_filename
        )

        if os.path.exists(existing_path):
            try:
                return FileHandler.load_json_file(existing_path)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading existing translations for {language_code}: {str(e)}")
                return {}
        return {}

    @staticmethod
    def save_translation_result(
        result: TranslationResult,
        base_path: str,
        file_type: Literal['json', 'arb'],
        filename_pattern: Optional[str] = None
    ) -> None:
        """
        Save a translation result to a file, handling different file types.

        Args:
            result: The TranslationResult object to save
            base_path: Base path where the source file is located
            file_type: The type of the file ('json' or 'arb')
            filename_pattern: The filename pattern for ARB files (e.g., 'app_{lang}.arb')
        """
        try:
            output_filename = FileHandler._get_language_filename(
                result.language_code, file_type, filename_pattern
            )
        except ValueError as e:
            print(f"Warning: {str(e)}")
            return

        output_path = os.path.join(
            os.path.dirname(base_path),
            output_filename
        )

        content_to_save = result.get_merged_content()

        # Add @@locale for ARB files
        if file_type == 'arb':
            # Use the simple language code (e.g., 'de') for @@locale
            locale_code = result.language_code.split('-')[0]
            content_to_save = {"@@locale": locale_code, **content_to_save}
            # Ensure keys are sorted alphabetically, with @@locale first for ARB convention
            content_to_save = dict(sorted(content_to_save.items(), key=lambda item: (item[0] != '@@locale', item[0])))


        try:
            # Use the existing save_json_file method, as ARB is also JSON format
            FileHandler.save_json_file(output_path, content_to_save)
            print(f"Output file saved as {output_path}")
        except IOError as e:
            print(f"Error saving translation file for {result.language_code}:")
            print(f"Error details: {str(e)}")
