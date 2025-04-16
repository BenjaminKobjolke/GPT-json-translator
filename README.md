# GPT JSON Translator

A powerful tool for translating JSON files to multiple languages using OpenAI's GPT models.

## Overview

GPT JSON Translator is a Python script that automates the translation of JSON files to multiple languages. It uses OpenAI's GPT models to provide high-quality translations while preserving the structure of your JSON files. The tool is particularly useful for localizing applications, websites, or any content stored in JSON format.

## Features

-   Translates JSON files to multiple languages simultaneously
-   Preserves JSON structure (only translates values, not keys)
-   Supports 40+ languages out of the box
-   Handles existing translations (only translates new or changed content)
-   Supports translation overrides for specific terms
-   Provides translation hints for proper names or specific terminology

## Requirements

-   Python 3.6+
-   OpenAI API key

## Installation

1. Clone this repository:

    ```
    git clone https://github.com/yourusername/GPT-json-translator.git
    cd GPT-json-translator
    ```

2. Install the required dependencies:

    ```
    pip install -r requirements.txt
    ```

3. Create a `config.py` file with your OpenAI API key:
    ```python
    API_KEY = "your-openai-api-key"
    SOURCE_PATH = "./locales/en.json"  # Default source file path (optional)
    ```

## Usage

### Basic Usage

Run the script with a path to your source JSON file:

```
python json_translator.py path/to/your/source.json
```

If no path is provided, the script will use the default path specified in `config.py` or prompt you to enter a path.

### Directory Structure

The script expects the following directory structure:

```
project/
├── locales/
│   ├── en.json           # Source file (English)
│   ├── de.json           # German translation
│   ├── fr.json           # French translation
│   └── ...               # Other language files
│   └── _overrides/       # Translation overrides
│       ├── de.json       # German overrides
│       └── ...           # Other language overrides
```

### Translation Hints

You can include special keys in your source JSON that serve as hints for the translation process. These keys should start and end with an underscore (e.g., `_hint_`).

Example:

```json
{
    "_hint_": "SUMMERA AI is a proper name and should not be translated",
    "title": "Welcome to SUMMERA AI",
    "description": "SUMMERA AI helps you with daily tasks"
}
```

The hint will be sent to the AI translator but won't be included in the final translated files. This is useful for:

-   Proper names that should remain untranslated
-   Brand names or product names
-   Technical terms with specific translations
-   Context information for ambiguous terms

### Translation Overrides

You can create override files for specific languages to ensure certain terms are always translated consistently. Place these files in the `_overrides` directory with the language code as the filename.

Example (`_overrides/de.json`):

```json
{
    "app_name": "MeineApp",
    "special_term": "SpezialBegriff"
}
```

## Project Structure

The project is organized into a modular structure:

```
GPT-json-translator/
├── json_translator.py        # Main entry point script
├── config.py                 # Configuration file
├── src/                      # Source code directory
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Main entry point
│   ├── config.py             # Configuration manager
│   ├── translator.py         # Translation service
│   ├── file_handler.py       # File I/O operations
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   └── translation_data.py
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── locales/                  # Translation files directory
│   ├── en.json               # Source file (English)
│   ├── de.json               # German translation
│   └── _overrides/           # Translation overrides
│       └── de.json           # German overrides
└── requirements.txt          # Dependencies
```

## Supported Languages

The script supports translation to the following languages:

-   Italian (it-IT)
-   French (fr-FR)
-   Spanish (es-ES)
-   German (de-DE)
-   Portuguese (pt-PT, pt-BR)
-   Dutch (nl-NL)
-   Russian (ru-RU)
-   Polish (pl-PL)
-   Turkish (tr-TR)
-   Chinese (zh-CN)
-   Japanese (ja-JP)
-   Korean (ko-KR)
-   Arabic (ar-AR)
-   Hindi (hi-IN)
-   Swedish (sv-SE)
-   Norwegian (no-NO)
-   Finnish (fi-FI)
-   Danish (da-DK)
-   Czech (cs-CZ)
-   Slovak (sk-SK)
-   Hungarian (hu-HU)
-   Romanian (ro-RO)
-   Ukrainian (uk-UA)
-   Bulgarian (bg-BG)
-   Croatian (hr-HR)
-   Serbian (sr-SP)
-   Slovenian (sl-SI)
-   Estonian (et-EE)
-   Latvian (lv-LV)
-   Lithuanian (lt-LT)
-   Hebrew (he-IL)
-   Persian (fa-IR)
-   Urdu (ur-PK)
-   Bengali (bn-IN)
-   Tamil (ta-IN)
-   Telugu (te-IN)
-   Marathi (mr-IN)
-   Malayalam (ml-IN)
-   Thai (th-TH)
-   Vietnamese (vi-VN)

## Advanced Configuration

You can modify the list of target languages by editing the `LANGUAGES` variable in your `config.py` file:

```python
LANGUAGES = [
    "it-IT", "fr-FR", "es-ES", "de-DE"
    # Add or remove languages as needed
]
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Original code by Leonardo Rignanese (twitter.com/leorigna)
Refactored structure by [Your Name]
