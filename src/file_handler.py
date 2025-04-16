"""
File handling operations for the JSON Translator.
"""
import json
import os
from typing import Dict, Any, Optional

from src.models.translation_data import TranslationResult


class FileHandler:
    """
    Handles file operations for the JSON Translator.
    """
    
    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """
        Load and parse a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON content as a dictionary
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file can't be read due to permissions
            json.JSONDecodeError: If the file contains invalid JSON
            IOError: For other I/O related errors
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Path not found at {file_path}")
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except PermissionError:
            raise PermissionError(f"Permission denied: Unable to read the file {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Error parsing JSON file {file_path}: {str(e)}", 
                e.doc, 
                e.pos
            )
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
    def load_overrides(base_path: str, language_code: str) -> Dict[str, Any]:
        """
        Load override values for a specific language.
        
        Args:
            base_path: Base path where the source JSON is located
            language_code: Language code to load overrides for
            
        Returns:
            Dictionary of override values, or empty dict if none exist
        """
        overrides_path = os.path.join(
            os.path.dirname(base_path), 
            "_overrides", 
            f"{language_code}.json"
        )
        
        if os.path.exists(overrides_path):
            try:
                return FileHandler.load_json_file(overrides_path)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading overrides for {language_code}:")
                print(f"Error details: {str(e)}")
                return {}
        return {}
    
    @staticmethod
    def load_existing_translations(base_path: str, language_code: str) -> Dict[str, Any]:
        """
        Load existing translations for a specific language.
        
        Args:
            base_path: Base path where the source JSON is located
            language_code: Language code to load translations for
            
        Returns:
            Dictionary of existing translations, or empty dict if none exist
        """
        existing_path = os.path.join(
            os.path.dirname(base_path), 
            f"{language_code}.json"
        )
        
        if os.path.exists(existing_path):
            try:
                return FileHandler.load_json_file(existing_path)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading existing translations for {language_code}:")
                print(f"Error details: {str(e)}")
                return {}
        return {}
    
    @staticmethod
    def save_translation_result(result: TranslationResult, base_path: str) -> None:
        """
        Save a translation result to a file.
        
        Args:
            result: The TranslationResult object to save
            base_path: Base path where the source JSON is located
        """
        output_path = os.path.join(
            os.path.dirname(base_path), 
            f"{result.language_code}.json"
        )
        
        try:
            FileHandler.save_json_file(output_path, result.get_merged_content())
            print(f"Output file saved as {output_path}")
        except IOError as e:
            print(f"Error saving translation file for {result.language_code}:")
            print(f"Error details: {str(e)}")
