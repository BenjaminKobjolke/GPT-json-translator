"""
Translation service for the JSON Translator.
"""
import json
from typing import Dict, Any, List, Optional, Literal

import openai

from src.utils.dict_utils import deep_diff

# Note: TranslationResult is not directly used here, consider removing if not needed elsewhere
# from src.models.translation_data import TranslationResult


class TranslationService:
    """
    Service for translating JSON content using OpenAI API.
    """

    SYSTEM_PROMPT = (
        "You are TranslatorGpt, a powerful language model designed for seamless translation "
        "of text across multiple languages. You have been trained on a vast corpus of linguistic "
        "data and possess a deep understanding of grammar, syntax, and vocabulary of every language "
        "in the world. You only translate json values, not json keys."
    )

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the translation service.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use for translation
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    @staticmethod
    def _format_hints(
        global_hints: Optional[Dict[str, str]] = None,
        field_hints: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Format translation hints into a readable string for the AI.

        Args:
            global_hints: Dictionary of global hint keys and values
            field_hints: Dictionary mapping field names to their specific hints

        Returns:
            Formatted hints string, or empty string if no hints
        """
        hints_lines = []

        # Add global hints
        if global_hints:
            hints_lines.append("Translation hints:")
            hints_lines.extend(f"- {value}" for value in global_hints.values())
            hints_lines.append("")  # Add blank line

        # Add field-specific hints
        if field_hints:
            hints_lines.append("Field-specific hints:")
            for field_name, hint_value in field_hints.items():
                hints_lines.append(f"- {field_name}: {hint_value}")
            hints_lines.append("")  # Add blank line

        return "\n".join(hints_lines)
    
    def translate(
        self,
        target_lang: str,
        content_to_translate: Dict[str, Any],
        global_hints: Optional[Dict[str, str]] = None,
        field_hints: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Translate content to the target language.

        Args:
            target_lang: Target language code
            content_to_translate: Dictionary of content to translate
            global_hints: Optional global translation hints
            field_hints: Optional field-specific translation hints

        Returns:
            Dictionary of translated content
        """
        print(f"Translating to {target_lang}...")

        # Format hints for the AI
        hints_text = self._format_hints(global_hints, field_hints)

        if hints_text:
            print(f"Hints: {hints_text}")

        try:
            # Call OpenAI API to translate text
            completion = openai.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"{hints_text}Translate the following JSON to {target_lang}:\n\n{content_to_translate}\n",
                    },
                ],
            )

            translated_json_str = completion.choices[0].message.content
            print(f"Translation to {target_lang} complete.")

            try:
                return json.loads(translated_json_str)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response for {target_lang}: {str(e)}")
                print(f"Problematic JSON string: {translated_json_str}")
                return {}

        except Exception as e:
            print(f"Error calling OpenAI API for {target_lang}: {str(e)}")
            return {}
    
    @staticmethod
    def filter_keys_for_translation(
        source_json: Dict[str, Any],
        existing_json: Dict[str, Any],
        overrides: Dict[str, Any],
        file_type: Literal['json', 'arb', 'xml']
    ) -> Dict[str, Any]:
        """
        Filter source JSON to only include keys that need translation.

        This method performs deep comparison for nested objects, ensuring that
        new nested keys are detected even if the parent key already exists.

        Args:
            source_json: Source JSON content
            existing_json: Existing translations
            overrides: Override values
            file_type: The type of the file ('json', 'arb', or 'xml')

        Returns:
            Dictionary with only the keys/nested-keys that need translation
        """
        # First, filter out hint keys and special keys from source
        filtered_source = {}
        for key, value in source_json.items():
            # Skip global hint keys
            if key.startswith('_') and key.endswith('_'):
                continue
            # Skip field-specific hint keys
            if key.startswith('_hint_'):
                continue
            # Skip @@locale for ARB files
            if file_type == 'arb' and key == '@@locale':
                continue
            filtered_source[key] = value

        # Merge existing translations with overrides (overrides take precedence)
        # This gives us the complete set of already-translated content
        combined_existing = existing_json.copy()
        combined_existing.update(overrides)

        # Use deep_diff to find missing or incomplete nested keys
        keys_for_translation = deep_diff(filtered_source, combined_existing)

        return keys_for_translation
