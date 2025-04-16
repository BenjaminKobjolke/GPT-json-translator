"""
Configuration settings for the JSON Translator.
"""
from typing import List, Optional, Dict, Any
import os
import importlib.util
import sys


class ConfigManager:
    """
    Manages configuration settings for the JSON Translator.
    """
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.api_key: Optional[str] = None
        self.source_path: Optional[str] = None
        self.model: str = "gpt-4o-mini"  # Default model
        self.languages: List[str] = []
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from config.py file.
        """
        # Default configuration
        self._set_default_languages()
        
        # Try to load from config.py
        config_path = os.path.join(os.getcwd(), "config.py")
        if os.path.exists(config_path):
            try:
                # Load the module dynamically
                spec = importlib.util.spec_from_file_location("config", config_path)
                if spec and spec.loader:
                    config = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config)
                    
                    # Extract configuration values
                    if hasattr(config, "API_KEY"):
                        self.api_key = config.API_KEY
                    
                    if hasattr(config, "SOURCE_PATH"):
                        self.source_path = config.SOURCE_PATH
                    
                    if hasattr(config, "MODEL"):
                        self.model = config.MODEL
                    
                    if hasattr(config, "LANGUAGES"):
                        self.languages = config.LANGUAGES
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
                print("Using default configuration.")
    
    def _set_default_languages(self) -> None:
        """
        Set the default list of languages for translation.
        """
        self.languages = [
            "it-IT", "fr-FR", "es-ES", "de-DE", "pt-PT", "pt-BR", "nl-NL", 
            "ru-RU", "pl-PL", "tr-TR", "zh-CN", "ja-JP", "ko-KR", "ar-AR", 
            "hi-IN", "sv-SE", "no-NO", "fi-FI", "da-DK", "cs-CZ", "sk-SK", 
            "hu-HU", "ro-RO", "uk-UA", "bg-BG", "hr-HR", "sr-SP", "sl-SI", 
            "et-EE", "lv-LV", "lt-LT", "he-IL", "fa-IR", "ur-PK", "bn-IN", 
            "ta-IN", "te-IN", "mr-IN", "ml-IN", "th-TH", "vi-VN"
        ]
    
    def validate(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.api_key:
            print("Error: OpenAI API key is not configured.")
            print("Please set API_KEY in config.py or provide it as an environment variable.")
            return False
        
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration as a dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        return {
            "api_key": self.api_key,
            "source_path": self.source_path,
            "model": self.model,
            "languages": self.languages
        }
