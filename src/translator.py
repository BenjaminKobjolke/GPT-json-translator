"""
Translation service for the JSON Translator.
"""
import json
from typing import Dict, Any, List, Optional

import openai

from src.models.translation_data import TranslationResult


class TranslationService:
    """
    Service for translating JSON content using OpenAI API.
    """
    
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
    
    def translate(
        self, 
        target_lang: str, 
        content_to_translate: Dict[str, Any],
        hints: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Translate content to the target language.
        
        Args:
            target_lang: Target language code
            content_to_translate: Dictionary of content to translate
            hints: Optional translation hints
            
        Returns:
            Dictionary of translated content
        """
        print(f"Translating to {target_lang}...")
        
        # Create a hints string if any hints exist
        hints_text = ""
        if hints and len(hints) > 0:
            hints_text = "Translation hints:\n"
            for key, value in hints.items():
                hints_text += f"- {value}\n"
            hints_text += "\n"
        
        print("Language: " + target_lang)
        print("Hints: " + hints_text)
        
        try:
            # Call OpenAI API to translate text
            completion = openai.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are TranslatorGpt, a powerful language model designed for seamless translation of text across multiple languages. You have been trained on a vast corpus of linguistic data and possess a deep understanding of grammar, syntax, and vocabulary of every language in the world. You only translate json values, not json keys.",
                    },
                    {
                        "role": "user",
                        "content": f"{hints_text}Translate the following JSON to {target_lang}:\n\n{content_to_translate}\n",
                    },
                ],
            )
            
            translated_json_str = completion.choices[0].message.content
            print(f"Translation to {target_lang} complete.")
            
            try:
                translated_json = json.loads(translated_json_str)
                return translated_json
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response for {target_lang}:")
                print(f"Error details: {str(e)}")
                print("Problematic JSON string:")
                print(translated_json_str)
                # Return empty dict to allow process to continue for other languages
                return {}
                
        except Exception as e:
            print(f"Error calling OpenAI API for {target_lang}:")
            print(f"Error details: {str(e)}")
            return {}
    
    @staticmethod
    def filter_keys_for_translation(
        source_json: Dict[str, Any],
        existing_json: Dict[str, Any],
        overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter source JSON to only include keys that need translation.
        
        Args:
            source_json: Source JSON content
            existing_json: Existing translations
            overrides: Override values
            
        Returns:
            Dictionary with only the keys that need translation
        """
        # Start with a copy of the source JSON
        keys_for_translation = {
            key: value for key, value in source_json.items() 
            if key not in existing_json and not (key.startswith('_') and key.endswith('_'))
        }
        
        # Remove keys that have overrides
        for key in overrides.keys():
            keys_for_translation.pop(key, None)
            
        return keys_for_translation
