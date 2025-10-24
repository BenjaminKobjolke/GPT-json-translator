"""
Data models for the JSON Translator.
"""
from typing import Dict, List, Optional, Any, Literal, Tuple

from src.utils.dict_utils import deep_merge


class TranslationData:
    """
    Class representing translation data including source content, 
    target languages, and translation hints.
    """
    
    def __init__(
        self,
        source_json: Dict[str, Any],
        target_languages: List[str],
        input_path: str,
        file_type: Literal['json', 'arb'],
        filename_pattern: Optional[str] = None
    ):
        """
        Initialize the TranslationData object.

        Args:
            source_json: The source JSON content to be translated
            target_languages: List of target languages for translation
            input_path: Path to the source JSON file
            file_type: The type of the input file ('json' or 'arb')
            filename_pattern: The filename pattern for ARB files (e.g., 'app_{lang}.arb')
        """
        self.source_json = source_json
        self.target_languages = target_languages
        self.input_path = input_path
        self.file_type = file_type
        self.filename_pattern = filename_pattern
        self.global_hints, self.field_hints = self._extract_hints()
    
    def _extract_hints(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Extract translation hints from the source JSON.
        Supports both global hints and field-specific hints.

        Global hints: Keys that start and end with underscore (e.g., "_hint_")
        Field-specific hints: Keys that start with "_hint_" followed by field name (e.g., "_hint_short_description")

        Returns:
            Tuple of (global_hints, field_hints) where field_hints maps field names to their hints
        """
        global_hints = {}
        field_hints = {}

        for key, value in list(self.source_json.items()):
            if key.startswith('_hint_'):
                # Check if it's a field-specific hint
                if key != '_hint_' and not key.endswith('_'):
                    # Extract field name: "_hint_short_description" -> "short_description"
                    field_name = key[6:]  # Remove "_hint_" prefix
                    field_hints[field_name] = value
                elif key == '_hint_':
                    # Global hint
                    global_hints[key] = value
            elif key.startswith('_') and key.endswith('_'):
                # Other global hints (backward compatibility)
                global_hints[key] = value

        return global_hints, field_hints
    
    def get_filtered_source(self) -> Dict[str, Any]:
        """
        Get a copy of the source JSON with hint keys removed.

        Returns:
            Filtered source JSON without hint keys
        """
        filtered_data = self.source_json.copy()
        for key in list(filtered_data.keys()):
            # Remove global hints (start and end with _)
            if key.startswith('_') and key.endswith('_'):
                filtered_data.pop(key, None)
            # Remove field-specific hints (start with _hint_)
            elif key.startswith('_hint_'):
                filtered_data.pop(key, None)
        return filtered_data


class TranslationResult:
    """
    Class representing the result of a translation operation.
    """
    
    def __init__(
        self, 
        language_code: str,
        translated_content: Dict[str, Any],
        existing_content: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the TranslationResult object.
        
        Args:
            language_code: The language code for this translation
            translated_content: The newly translated content
            existing_content: Any existing translations for this language
            overrides: Any override values for this language
        """
        self.language_code = language_code
        self.translated_content = translated_content
        self.existing_content = existing_content or {}
        self.overrides = overrides or {}
    
    def get_merged_content(self) -> Dict[str, Any]:
        """
        Merge translated content with existing content and overrides.

        Uses deep merge to preserve nested structures. This ensures that when
        translating nested objects incrementally, both old and new nested keys
        are preserved.

        Overrides take precedence over both existing and translated content.

        Returns:
            Merged content dictionary with deep merging applied
        """
        # Start with existing content
        merged = self.existing_content.copy()
        # Deep merge translated content (preserves nested structures)
        merged = deep_merge(merged, self.translated_content)
        # Deep merge overrides (will override both existing and translated keys)
        merged = deep_merge(merged, self.overrides)
        return merged
