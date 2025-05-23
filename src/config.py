"""
Configuration settings for the JSON Translator.
"""
from typing import List, Optional, Dict, Any
import os
import configparser
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
        Load configuration from settings.ini file.
        """
        # Default configuration
        self._set_default_languages()
        
        # Try to load from settings.ini
        config_path = os.path.join(os.getcwd(), "settings.ini")
        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path)
                
                # Extract configuration values from [General] section
                if 'General' in config:
                    if 'api_key' in config['General']:
                        self.api_key = config['General']['api_key']
                    
                    if 'source_path' in config['General']:
                        self.source_path = config['General']['source_path']
                    
                    if 'model' in config['General']:
                        self.model = config['General']['model']
                
                # Extract languages from [Languages] section
                if 'Languages' in config and 'languages' in config['Languages']:
                    languages_str = config['Languages']['languages']
                    if languages_str:
                        # Split by comma and strip whitespace
                        self.languages = [lang.strip() for lang in languages_str.split(',')]
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
                print("Using default configuration.")
                
            # For backward compatibility, try loading from config.py if settings.ini doesn't have API key
            if not self.api_key:
                self._load_legacy_config()
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
    
    def _load_legacy_config(self) -> None:
        """
        Load configuration from config.py file for backward compatibility.
        """
        config_path = os.path.join(os.getcwd(), "config.py")
        if os.path.exists(config_path):
            try:
                # Use environment variables to safely load the config
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_path)
                if spec and spec.loader:
                    config = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(config)
                    
                    # Extract configuration values
                    if hasattr(config, "API_KEY"):
                        self.api_key = config.API_KEY
                    
                    if hasattr(config, "SOURCE_PATH") and not self.source_path:
                        self.source_path = config.SOURCE_PATH
                    
                    if hasattr(config, "MODEL") and self.model == "gpt-4o-mini":
                        self.model = config.MODEL
                    
                    if hasattr(config, "LANGUAGES") and not self.languages:
                        self.languages = config.LANGUAGES
                        
                print("Loaded configuration from config.py (legacy mode)")
            except Exception as e:
                print(f"Error loading legacy configuration: {str(e)}")
    
    def validate(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.api_key:
            print("Error: OpenAI API key is not configured.")
            print("Please set api_key in settings.ini or API_KEY in config.py.")
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
