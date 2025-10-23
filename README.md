# GPT JSON Translator

A powerful tool for translating JSON files to multiple languages using OpenAI's GPT models.

## Overview

GPT JSON Translator is a Python script that automates the translation of JSON files to multiple languages. It uses OpenAI's GPT models to provide high-quality translations while preserving the structure of your JSON files. The tool is particularly useful for localizing applications, websites, or any content stored in JSON format.

## Features

-   Translates JSON files to multiple languages simultaneously
-   Preserves JSON structure (only translates values, not keys)
-   Supports 40+ languages out of the box
-   Recursive batch translation across directory hierarchies
-   Exclude specific languages from translation via command-line flag
-   Handles existing translations (only translates new or changed content)
-   Supports translation overrides for specific terms
-   Provides global and field-specific translation hints
-   Supports both standard JSON and Flutter ARB file formats

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

3. Create a `settings.ini` file with your configuration:

    ```ini
    [General]
    api_key = your-openai-api-key
    source_path = ./locales/en.json
    model = gpt-4o-mini

    [Languages]
    languages = it-IT, fr-FR, es-ES, de-DE
    ```

    A template file `settings_example.ini` is provided for reference.

## Usage

### Basic Usage

Run the script with a path to your source JSON file:

```
python json_translator.py path/to/your/source.json
```

If no path is provided, the script will use the default path specified in `settings.ini` or prompt you to enter a path.

### Excluding Languages

You can exclude specific languages from translation using the `--exclude-languages` (or `--exclude`) flag. This is useful when you want to translate to most languages but skip a few:

```
python json_translator.py path/to/source.json --exclude-languages="he,ko"
```

Or use the shorter alias:

```
python json_translator.py path/to/source.json --exclude="he,ko,ar"
```

**Features:**
- Accepts comma-separated language codes
- Works with both short codes (`he`, `ko`) and full codes (`he-IL`, `ko-KR`)
- Can exclude multiple languages at once
- Useful when translating to all languages by default (when `languages` is commented out in `settings.ini`)

**Example:**
```bash
# Translate to all languages except Hebrew and Korean
python json_translator.py ./locales/en.json --exclude="he,ko"
```

### Recursive Translation

The `--translate-recursive` flag enables batch processing of multiple directories that contain the same source filename. This is particularly useful when you have a hierarchical directory structure where each subdirectory needs its own set of translations.

```bash
python json_translator.py "path/to/base/directory" --translate-recursive="en.json"
```

**How it works:**
- Recursively searches all subdirectories of the specified base directory
- Finds all directories containing the specified source file (e.g., `en.json`)
- Filters to only directories that have **no translation files** (only the source file exists)
- Translates each qualifying directory independently

**Example use case:**

If you have release notes organized by version:
```
release-notes/
├── 257/
│   └── en.json           # Has translations - SKIPPED
│       de.json
│       fr.json
├── 258/
│   └── en.json           # Has translations - SKIPPED
│       de.json
│       fr.json
├── 259/
│   └── en.json           # No translations - TRANSLATED
```

Run the recursive translation:
```bash
python json_translator.py "D:\project\release-notes\" --translate-recursive="en.json"
```

This will:
1. Search all subdirectories (257, 258, 259, etc.)
2. Find those containing `en.json`
3. Only translate folders where **only** `en.json` exists (no `de.json`, `fr.json`, etc.)
4. Process each qualifying directory, creating all configured language translations

**Features:**
- Automatically detects file type (JSON or ARB) from the source filename
- Skips directories that already have translations (idempotent)
- Processes each directory independently with full translation workflow
- Supports all translation features (hints, overrides, language exclusions)
- Shows progress for each directory being processed

**Combining with other flags:**

You can combine recursive mode with language exclusions:

```bash
# Recursively translate all subdirectories, excluding Hebrew and Korean
python json_translator.py "D:\project\release-notes\" --translate-recursive="en.json" --exclude="he,ko"
```

**Works with ARB files too:**

```bash
python json_translator.py "D:\flutter\lib\l10n\" --translate-recursive="app_en.arb"
```

### Applying Overrides Only

You can apply override files to translation files without performing any translation using the `--apply-overrides` flag. This is useful when you want to bulk-update translation files with override values without triggering API calls or re-translation.

```bash
python json_translator.py path/to/source.json --apply-overrides
```

**How it works:**
- Scans the `_overrides/` directory for all available override files
- Discovers override files automatically (works with both JSON and ARB formats)
- Applies each override to its corresponding translation file
- Creates new translation files if they don't exist yet
- Merges overrides with existing translations (overrides take precedence)

**Features:**
- No API calls or translation - pure file merging operation
- Automatically detects file type (JSON or ARB) from the source file
- Processes all override files found, regardless of config settings
- Creates missing translation files from override content
- Shows summary of applied overrides for each language

**Example:**
```bash
# Apply all overrides in _overrides/ to translation files
python json_translator.py ./locales/en.json --apply-overrides

# For ARB files
python json_translator.py ./lib/l10n/app_en.arb --apply-overrides
```

**Use cases:**
- Bulk update specific terms across all translations
- Initialize new translation files with predefined values
- Apply terminology changes without re-translating
- Sync override changes to all language files quickly

### JSON Attribute Remover Utility

The `json_attribute_remover.py` utility removes specified attributes from all translated JSON files in a directory. This is useful for cleaning up translation files by removing obsolete or unwanted keys.

**Usage:**

```bash
# Basic usage
python json_attribute_remover.py path/to/directory path/to/attributes_to_remove.json

# Specify custom source file to exclude
python json_attribute_remover.py path/to/directory attributes.json --exclude-source="app_en.arb"

# Get help
python json_attribute_remover.py --help
```

**Attributes file format:**

The attributes file should contain a JSON array of attribute names to remove:

```json
[
  "obsolete_key",
  "deprecated_field",
  "old_translation"
]
```

**Features:**
- Automatically excludes source files (`en.json`, `app_en.arb` by default)
- Only modifies files that contain the specified attributes
- Preserves JSON formatting with proper indentation
- Shows progress and summary statistics

#### Windows Path Issue

**IMPORTANT:** On Windows, when using paths with spaces in batch files or cmd.exe, avoid trailing backslashes in quoted paths as they can escape the closing quote.

**Problem example (causes error):**
```batch
python json_attribute_remover.py "D:\path\to\directory\" "C:\path with spaces\file.json"
```

The trailing `\` before the closing `"` escapes the quote, causing argument parsing to fail.

**Solutions:**

1. **Remove the trailing backslash** (recommended):
   ```batch
   python json_attribute_remover.py "D:\path\to\directory" "C:\path with spaces\file.json"
   ```

2. **Double the trailing backslash**:
   ```batch
   python json_attribute_remover.py "D:\path\to\directory\\" "C:\path with spaces\file.json"
   ```

3. **Use forward slashes** (Windows accepts both):
   ```batch
   python json_attribute_remover.py "D:/path/to/directory" "C:/path with spaces/file.json"
   ```

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

You can provide translation hints to guide the AI translator. Hints are automatically excluded from the translated output files.

#### Global Hints

Global hints apply to all fields in your translation. Use keys that start and end with an underscore (e.g., `_hint_`):

```json
{
    "_hint_": "If the language has a formal and an informal way, use the informal way.",
    "title": "Welcome to SUMMERA AI",
    "description": "SUMMERA AI helps you with daily tasks"
}
```

#### Field-Specific Hints

Field-specific hints provide targeted guidance for individual fields. Use the pattern `_hint_fieldname`:

```json
{
    "_hint_": "SUMMERA AI is a proper name and should not be translated",
    "short_description": "Explorer with editing, favorites & smart file management",
    "_hint_short_description": "Maximum length is 60 characters, shorten if too long by not adhering 100% to the original language",
    "app_name": "File Explorer Pro",
    "welcome_message": "Welcome to our application!"
}
```

When translating, the AI receives both types of hints:
```
Translation hints:
- SUMMERA AI is a proper name and should not be translated

Field-specific hints:
- short_description: Maximum length is 60 characters, shorten if too long by not adhering 100% to the original language
```

**Use cases for hints:**
-   Proper names that should remain untranslated
-   Brand names or product names
-   Technical terms with specific translations
-   Context information for ambiguous terms
-   Length constraints for specific fields
-   Tone or formality requirements (formal vs informal)

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
├── json_attribute_remover.py # Utility to remove attributes from JSON files
├── settings.ini              # Configuration file
├── settings_example.ini      # Example configuration template
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

You can customize the behavior by modifying the following settings in your `settings.ini` file:

### Target Languages

In the `[Languages]` section, specify the languages you want to translate to:

```ini
[Languages]
languages = it-IT, fr-FR, es-ES, de-DE
```

If you comment out or omit the `languages` setting, the script will translate to all 40+ supported languages by default:

```ini
[Languages]
# Uncomment and modify the languages you want to translate to, otherwise all will be translated
#languages = de-DE
```

You can also use the `--exclude-languages` command-line flag to exclude specific languages from translation without modifying your configuration file (see [Excluding Languages](#excluding-languages) section).

### OpenAI Model

In the `[General]` section, specify which OpenAI model to use for translations:

```ini
[General]
model = gpt-4o-mini
```

Other options include "gpt-4o", "gpt-4", "gpt-3.5-turbo", etc. Different models offer different trade-offs between translation quality, speed, and cost. The default is `gpt-4o-mini`, which provides a good balance of quality and performance.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Original code by Leonardo Rignanese (twitter.com/leorigna)
Refactored structure by [Your Name]
