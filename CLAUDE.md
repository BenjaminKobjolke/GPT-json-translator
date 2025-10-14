# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPT JSON Translator automates translation of JSON files to multiple languages using OpenAI's GPT models. The tool preserves JSON structure and handles both standard JSON localization files and Flutter ARB (Application Resource Bundle) files.

**Key capabilities:**
- Translates JSON values while preserving keys
- Supports 40+ languages
- Incremental translation (only translates new/changed content)
- Translation overrides for consistent terminology
- Translation hints for proper names and context
- Concurrent translation processing for multiple languages
- Flutter ARB file support with `@@locale` metadata

## Running the Translator

### Main Translation Script
```bash
# Using virtual environment (recommended)
.\.venv\Scripts\python.exe json_translator.py path/to/source.json

# Or directly
python json_translator.py path/to/source.json

# Uses settings.ini default if no path provided
python json_translator.py

# Exclude specific languages from translation
python json_translator.py path/to/source.json --exclude-languages="he,ko,ar"
# Short alias also available
python json_translator.py path/to/source.json --exclude="he,ko"
```

### JSON Attribute Remover
Removes specified attributes from all translated JSON files (excluding source files):
```bash
# Basic usage
python json_attribute_remover.py path/to/directory path/to/attributes_to_remove.json

# Specify custom source file to exclude
python json_attribute_remover.py path/to/directory attributes.json --exclude-source="app_en.arb"

# Get help
python json_attribute_remover.py --help
```

### Batch Files
Multiple `.bat` files exist for different projects. These use the virtual environment and pass project-specific paths:
```bat
call .\.venv\Scripts\python.exe json_translator.py "path\to\source.json"
```

## Configuration

The tool uses `settings.ini` for configuration. Copy `settings_example.ini` to create your own:

```ini
[General]
api_key = your-openai-api-key
source_path = ./locales/en.json  # Optional default path
model = gpt-4o-mini              # OpenAI model to use

[Languages]
# Uncomment to limit languages, otherwise translates to all 40+ supported
# languages = de-DE, fr-FR, es-ES, it-IT
```

If `settings.ini` is missing required values, the tool falls back to legacy `config.py` for backward compatibility.

## Architecture

### Modular Structure
```
json_translator.py          # Entry point wrapper
json_attribute_remover.py   # Utility to remove attributes from translations
src/
├── main.py                 # Orchestrates translation workflow
├── config.py               # ConfigManager - loads settings.ini
├── translator.py           # TranslationService - OpenAI API integration
├── file_handler.py         # FileHandler - all file I/O operations
├── models/
│   └── translation_data.py # TranslationData, TranslationResult models
└── utils/
    └── helpers.py          # Helper functions (path, language parsing, summaries)
```

### Core Flow (src/main.py)
1. **ArgumentParser** parses command-line arguments (input path, exclude languages)
2. **ConfigManager** loads settings.ini (API key, model, languages)
3. **Language filtering** applies exclusions if `--exclude-languages` is provided
4. **analyze_input_filename()** detects file type (JSON vs ARB) and extracts pattern
5. **FileHandler** loads source file, existing translations, and overrides
6. **TranslationData** extracts hints (keys starting/ending with `_`) and filters source
7. **TranslationService.filter_keys_for_translation()** determines what needs translation
8. Concurrent **ThreadPoolExecutor** processes each language in parallel
9. **FileHandler** saves results with proper formatting (JSON or ARB with `@@locale`)

### File Type Support
- **Standard JSON**: Files like `en.json`, outputs `de.json`, `fr.json`, etc.
- **Flutter ARB**: Files like `app_en.arb`, outputs `app_de.arb`, `app_fr.arb`, etc.
  - Pattern detected via regex: `^(.*?)_([a-zA-Z]{2}(?:_[a-zA-Z]{2})?)\.arb$`
  - Automatically includes `@@locale` metadata in output
  - Skips `@@locale` key during translation

### Translation Logic
- **Global Hints**: Keys like `_hint_` provide general context to GPT for all translations
- **Field-Specific Hints**: Keys like `_hint_short_description` provide context for specific fields
- **Overrides**: Files in `_overrides/{lang}.json` force specific translations, taking precedence
- **Incremental**: Only translates keys missing from existing translations or overrides
- **Merging**: Final output = existing translations + new translations + overrides (overrides win)

### Language Code Handling
- Config uses full codes (`de-DE`, `fr-FR`)
- Internal parsing extracts base code (`de`, `fr`) via `parse_language_code()`
- ARB files use base code in filenames (`app_de.arb`) and `@@locale` values
- Standard JSON uses full code in filenames (`de-DE.json`)

### Language Exclusion
- **Command-line flag**: `--exclude-languages="he,ko"` or `--exclude="he,ko"`
- Accepts both short (`he`) and full codes (`he-IL`)
- Filters languages by comparing base codes (so `he` excludes `he-IL`)
- Applied after loading config, before creating TranslationData
- Useful when settings.ini has no languages specified (translates all by default)

## Directory Structure Expectations

```
project/
├── locales/                # Or any directory containing translations
│   ├── en.json             # Source file (standard JSON)
│   ├── de.json             # German translation
│   ├── fr.json             # French translation
│   └── _overrides/         # Optional overrides
│       ├── de.json         # German overrides
│       └── fr.json         # French overrides
```

For ARB files:
```
project/
├── lib/l10n/              # Flutter convention
│   ├── app_en.arb         # Source file
│   ├── app_de.arb         # German translation
│   └── _overrides/
│       └── app_de.arb     # German overrides
```

## Translation Hints Examples

### Global Hints
Global hints apply to all fields in the translation:
```json
{
  "_hint_": "If the language has a formal and an informal way, use the informal way.",
  "title": "Welcome to our app",
  "description": "Your AI assistant"
}
```

### Field-Specific Hints
Field-specific hints provide targeted guidance for individual fields:
```json
{
  "_hint_": "SUMMERA AI is a proper name and should not be translated",
  "short_description": "Explorer with editing, favorites & smart file management",
  "_hint_short_description": "Maximum length is 60 characters, shorten if too long by not adhering 100% to the original language",
  "app_name": "File Explorer Pro",
  "welcome_message": "Welcome to our application!"
}
```

When translating, GPT receives both types of hints:
```
Translation hints:
- If the language has a formal and an informal way, use the informal way.

Field-specific hints:
- short_description: Maximum length is 60 characters, shorten if too long by not adhering 100% to the original language
```

All hints are sent to GPT for context but excluded from output files.

## Error Handling

- **ConfigManager** validates API key presence before proceeding
- **FileHandler** raises specific exceptions: FileNotFoundError, PermissionError, JSONDecodeError
- Translation errors for one language don't block others (concurrent processing)
- Invalid JSON responses from OpenAI return empty dict, allowing process to continue
- ARB files without valid patterns fall back to JSON mode with warnings

## Code Organization Patterns

### Design Principles Applied
The codebase follows modern Python best practices:

1. **DRY (Don't Repeat Yourself)**
   - `FileHandler._get_language_filename()` centralizes filename generation logic
   - `ConfigManager._get_config_value()` handles safe config retrieval
   - `TranslationService._format_hints()` extracts hint formatting

2. **Single Responsibility Principle**
   - Each class has one primary responsibility
   - Methods are focused and typically under 35 lines
   - Helper methods extracted for reusable logic

3. **Type Safety**
   - Comprehensive type hints throughout (95%+ coverage)
   - Uses `Literal['json', 'arb']` for type constraints
   - `Optional[T]` for nullable values

4. **Error Handling Strategy**
   - Specific exception types (FileNotFoundError, JSONDecodeError, ValueError)
   - Graceful degradation: errors in one language don't block others
   - Descriptive error messages with context

### Key Implementation Details

**FileHandler** (src/file_handler.py)
- `_get_language_filename()`: Private helper eliminates code duplication across load/save operations
- All methods are static since no instance state needed
- Consistent error handling pattern across all file operations

**TranslationService** (src/translator.py)
- `SYSTEM_PROMPT`: Class constant for easy modification
- `_format_hints()`: Separates presentation logic from translation logic
- Returns empty dict on errors to allow other translations to continue

**ConfigManager** (src/config.py)
- `_get_config_value()`: Safely retrieves config with defaults and empty string handling
- Dual loading: settings.ini (primary) + config.py (legacy fallback)
- Validates API key presence before allowing translation

**JSON Attribute Remover** (json_attribute_remover.py)
- Uses `pathlib.Path` for modern path handling
- Functional decomposition: load → filter → process → save
- Returns statistics (files processed, attributes removed)
- Configurable source file exclusion via `--exclude-source`

### Concurrency Model
- Uses `concurrent.futures.ThreadPoolExecutor` for parallel language processing
- Each language translation is independent (no shared state)
- Thread-safe file operations (each language writes to different file)
- Errors isolated per language (one failure doesn't affect others)

### Data Flow
```
Input File → FileHandler.load_json_file()
           → TranslationData (extracts hints, filters source)
           → ConfigManager (languages list)
           → Language Filtering (--exclude-languages)
           → ThreadPoolExecutor spawns workers
              → Each worker: TranslationService.filter_keys_for_translation()
                           → TranslationService.translate() (OpenAI API call)
                           → TranslationResult (merges existing + new + overrides)
              → FileHandler.save_translation_result()
```

## Development Notes

- OpenAI API uses `response_format={"type": "json_object"}` for structured output
- System prompt emphasizes translating values only, not keys
- UTF-8 encoding enforced throughout for international character support
- argparse used for CLI interfaces (supports `--help` flag)
- All file I/O operations go through FileHandler for consistency
