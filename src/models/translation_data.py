"""
Data models for the JSON Translator.
"""
from typing import Dict, List, Optional, Any


class TranslationData:
    """
    Class representing translation data including source content, 
    target languages, and translation hints.
    """
    
    def __init__(
        self, 
        source_json: Dict[str, Any],
        target_languages: List[str],
        input_path: str
    ):
        """
        Initialize the TranslationData object.
        
        Args:
            source_json: The source JSON content to be translated
            target_languages: List of target languages for translation
            input_path: Path to the source JSON file
        """
        self.source_json = source_json
        self.target_languages = target_languages
        self.input_path = input_path
        self.hints = self._extract_hints()
    
    def _extract_hints(self) -> Dict[str, str]:
        """
        Extract translation hints from the source JSON.
        Hints are keys that start and end with underscore.
        
        Returns:
            Dictionary of hint keys and their values
        """
        hints = {}
        for key, value in list(self.source_json.items()):
            if key.startswith('_') and key.endswith('_'):
                hints[key] = value
        return hints
    
    def get_filtered_source(self) -> Dict[str, Any]:
        """
        Get a copy of the source JSON with hint keys removed.
        
        Returns:
            Filtered source JSON without hint keys
        """
        filtered_data = self.source_json.copy()
        for key in list(filtered_data.keys()):
            if key.startswith('_') and key.endswith('_'):
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
        Overrides take precedence over both existing and translated content.
        
        Returns:
            Merged content dictionary
        """
        # Start with existing content
        merged = self.existing_content.copy()
        # Add translated content (will overwrite existing keys)
        merged.update(self.translated_content)
        # Add overrides (will overwrite both existing and translated keys)
        merged.update(self.overrides)
        return merged
