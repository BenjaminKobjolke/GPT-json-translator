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
Removes specified attributes from all translated JSON files (excluding source `en.json`):
```bash
python json_attribute_remover.py path/to/directory path/to/attributes_to_remove.json
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
- **Hints**: Keys like `_hint_` provide context to GPT but aren't translated or included in output
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

## Translation Hints Example

Source file with hints:
```json
{
  "_hint_": "SUMMERA AI is a proper name and should not be translated",
  "title": "Welcome to SUMMERA AI",
  "description": "Your AI assistant"
}
```

Hints are sent to GPT for context but excluded from output files.

## Error Handling

- **ConfigManager** validates API key presence before proceeding
- **FileHandler** raises specific exceptions: FileNotFoundError, PermissionError, JSONDecodeError
- Translation errors for one language don't block others (concurrent processing)
- Invalid JSON responses from OpenAI return empty dict, allowing process to continue
- ARB files without valid patterns fall back to JSON mode with warnings

## Development Notes

- Uses `concurrent.futures.ThreadPoolExecutor` for parallel language processing
- All file operations centralized in **FileHandler** for consistency
- **TranslationData** model separates hints from translatable content
- OpenAI API uses `response_format={"type": "json_object"}` for structured output
- System prompt emphasizes translating values only, not keys
- UTF-8 encoding enforced throughout for international character support
